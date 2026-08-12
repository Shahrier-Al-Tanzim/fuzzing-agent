#!/usr/bin/env bash
#
# Proves the harness behaves correctly BEFORE any fuzzing starts.
# Every valid sample must exit 0; every invalid one must exit 2.
# Anything else - a sanitizer abort, a signal, code 64 - is a failure of
# this gate and must be understood before proceeding to Module 3.
set -uo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
HARNESS="$ROOT/harness/build/toml_harness"
# shellcheck source=../sanitizer_env.sh
source "$ROOT/harness/sanitizer_env.sh"

[[ -x "$HARNESS" ]] || { echo "build first: ./harness/build.sh" >&2; exit 1; }

pass=0 fail=0

check() {
  local file="$1" expected="$2"
  local out rc
  out=$(timeout 5s "$HARNESS" "$file" 2>&1)
  rc=$?

  local verdict
  case $rc in
    0)   verdict="ACCEPT" ;;
    2)   verdict="REJECT" ;;
    64)  verdict="USAGE_ERROR" ;;
    86)  verdict="SANITIZER" ;;
    124) verdict="TIMEOUT" ;;
    *)   verdict="UNEXPECTED($rc)" ;;
  esac

  if [[ "$verdict" == "$expected" ]]; then
    printf '  \033[32mok  \033[0m %-34s %s\n' "$(basename "$file")" "$verdict"
    ((pass++))
  else
    printf '  \033[31mFAIL\033[0m %-34s got %s, want %s\n' \
      "$(basename "$file")" "$verdict" "$expected"
    echo "$out" | sed 's/^/         /' | head -20
    ((fail++))
  fi
}

echo "=== valid samples (expect ACCEPT) ==="
for f in "$ROOT"/grammar/sample_inputs/valid/*.toml; do
  [[ -e "$f" ]] && check "$f" ACCEPT
done

echo
echo "=== invalid samples (expect REJECT) ==="
for f in "$ROOT"/grammar/sample_inputs/invalid/*.toml; do
  [[ -e "$f" ]] || continue
  case "$(basename "$f")" in
    06_trailing_comma_inline_table.toml)
      # known divergence, see adaptations.md #1 — library accepts trailing
      # commas in inline tables even though the grammar forbids them
      check "$f" ACCEPT ;;
    07_leading_zero_int.toml)
      # known divergence, see adaptations.md #4 — toml_parse() accepts
      # leading-zero ints; only the typed accessors reject them
      check "$f" ACCEPT ;;
    *)
      check "$f" REJECT ;;
  esac
done


echo
echo "=== harness edge cases ==="
tmp=$(mktemp -d); trap 'rm -rf "$tmp"' EXIT

: > "$tmp/empty.toml"
check "$tmp/empty.toml" ACCEPT                 # empty document is valid TOML

printf 'a = 1' > "$tmp/no_trailing_nl.toml"
check "$tmp/no_trailing_nl.toml" ACCEPT

printf '\xff\xfe\x00binary' > "$tmp/binary.toml"
check "$tmp/binary.toml" REJECT

python3 -c "print('a = ' + '['*300 + ']'*300)" > "$tmp/deep.toml"
echo "  (deep nesting - any verdict is informative, see note below)"
check "$tmp/deep.toml" ACCEPT

echo
echo "passed: $pass  failed: $fail"
[[ $fail -eq 0 ]] || exit 1