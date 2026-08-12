#!/usr/bin/env bash
# Runs every sample input through the pinned tomlc99 demo binary and reports
# accept/reject, so you can compare reality against the ANTLR grammar.
set -uo pipefail

TOML_JSON="${TOML_JSON:-harness/vendor/tomlc99/toml_json}"

if [[ ! -x "$TOML_JSON" ]]; then
  echo "error: $TOML_JSON not found or not executable" >&2
  echo "build it first: (cd harness/vendor/tomlc99 && make)" >&2
  exit 1
fi

probe_dir() {
  local dir="$1" expected="$2"
  echo "=== $dir (expected: $expected) ==="
  for f in "$dir"/*.toml; do
    [[ -e "$f" ]] || continue
    local out rc
    out=$("$TOML_JSON" < "$f" 2>&1)
    rc=$?
    if [[ $rc -eq 0 ]]; then
      printf '  ACCEPT  %s\n' "$(basename "$f")"
    else
      printf '  REJECT  %-30s %s\n' "$(basename "$f")" "$(echo "$out" | head -1)"
    fi
  done
  echo
}

probe_dir grammar/sample_inputs/valid   ACCEPT
probe_dir grammar/sample_inputs/invalid REJECT
