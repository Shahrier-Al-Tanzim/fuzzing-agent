#!/usr/bin/env bash
# Reproduces the investigation behind grammar/adaptations.md's divergence
# table. Unlike probe.sh (which just runs sample_inputs/ through toml_json
# and prints ACCEPT/REJECT), this script shows *why* each divergence was
# classified the way it was: full stdout/stderr, and the stack-overflow
# bisection for the array-nesting crash.
#
# Run from repo root: ./grammar/investigate_divergences.sh
set -uo pipefail

BIN="${TOML_JSON:-harness/vendor/tomlc99/toml_json}"

if [[ ! -x "$BIN" ]]; then
  echo "error: $BIN not found or not executable" >&2
  echo "build it first: (cd harness/vendor/tomlc99 && make)" >&2
  exit 1
fi

echo "############################################################"
echo "# Divergence 1: trailing comma in inline table"
echo "############################################################"
"$BIN" < grammar/sample_inputs/invalid/06_trailing_comma_inline_table.toml
echo "exit: $?"
echo

echo "############################################################"
echo "# Divergence 2: fractional-second precision truncation"
echo "############################################################"
echo "input:"
cat grammar/sample_inputs/valid/06_frac_seconds_precision.toml
echo "output:"
"$BIN" < grammar/sample_inputs/valid/06_frac_seconds_precision.toml
echo "exit: $?"
echo

echo "############################################################"
echo "# Divergence 3: integer overflow reinterpreted as float"
echo "############################################################"
"$BIN" < grammar/sample_inputs/valid/07_int_overflow.toml
echo "exit: $?"
echo

echo "############################################################"
echo "# Divergence 4: leading-zero int — parse succeeds, typed read fails"
echo "############################################################"
echo "--- stdout ---"
"$BIN" < grammar/sample_inputs/invalid/07_leading_zero_int.toml 2>/tmp/stderr_$$.txt
rc=$?
echo
echo "exit: $rc"
echo "--- stderr ---"
cat /tmp/stderr_$$.txt
rm -f /tmp/stderr_$$.txt
echo

echo "############################################################"
echo "# Non-divergences (checked, ruled out — see adaptations.md scope cuts)"
echo "############################################################"
for f in grammar/sample_inputs/invalid/08_newline_inline_table.toml \
         grammar/sample_inputs/invalid/09_unicode_bare_key.toml \
         grammar/sample_inputs/valid/08_dotted_key_top_level.toml; do
  echo "--- $f ---"
  "$BIN" < "$f"
  echo "exit: $?"
  echo
done

echo "############################################################"
echo "# Finding: array-nesting stack overflow — bisection"
echo "############################################################"
echo "Saved reproducer: grammar/early_findings/01_array_nesting_stackoverflow.toml"
echo "Bisecting crash threshold on THIS machine (depends on ulimit -s = $(ulimit -s) KB)..."
echo

lo=1000
hi=200000
# quick sanity check that hi actually crashes before bisecting
python3 -c "
depth = $hi
print('x = ' + '[' * depth + '1' + ']' * depth)
" > /tmp/bisect_$$.toml
timeout 10 "$BIN" < /tmp/bisect_$$.toml > /dev/null 2>&1
if [[ $? -le 128 ]]; then
  echo "warning: depth $hi did not crash on this machine — skipping bisection"
else
  while (( hi - lo > 500 )); do
    mid=$(( (lo + hi) / 2 ))
    python3 -c "
depth = $mid
print('x = ' + '[' * depth + '1' + ']' * depth)
" > /tmp/bisect_$$.toml
    timeout 10 "$BIN" < /tmp/bisect_$$.toml > /dev/null 2>&1
    rc=$?
    if [[ $rc -gt 128 ]]; then
      echo "depth $mid: CRASH (signal $((rc-128)))"
      hi=$mid
    else
      echo "depth $mid: ok (exit $rc)"
      lo=$mid
    fi
  done
  echo
  echo "boundary on this machine: $lo OK, $hi crashes"
fi
rm -f /tmp/bisect_$$.toml
echo

echo "############################################################"
echo "# Confirm saved reproducer still crashes"
echo "############################################################"
timeout 10 "$BIN" < grammar/early_findings/01_array_nesting_stackoverflow.toml > /dev/null 2>&1
rc=$?
if [[ $rc -gt 128 ]]; then
  echo "confirmed: killed by signal $((rc-128)) (exit $rc)"
else
  echo "did NOT crash on this machine (exit $rc) — depth may need to be raised for this stack size"
fi
