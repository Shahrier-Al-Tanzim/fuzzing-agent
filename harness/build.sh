#!/usr/bin/env bash
#
# Builds tomlc99 (at the pinned commit) + the harness with ASan and UBSan.
#
# -O1 rather than -O0: sanitizers are far slower at -O0, and at 500 examples
# per iteration across 5 iterations that cost is real. -fno-omit-frame-pointer
# and -g keep stack traces symbolized, which Module 6's deduplication needs.
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
VENDOR="$ROOT/harness/vendor/tomlc99"
BUILD="$ROOT/harness/build"
CC="${CC:-clang}"

PINNED=$(grep -oP '(?<=^commit:\s{5})\S+' "$ROOT/grammar/PINNED_COMMIT.txt" 2>/dev/null || true)

# --- fetch/pin -------------------------------------------------------------
if [[ ! -d "$VENDOR/.git" ]]; then
  echo ">> cloning tomlc99"
  mkdir -p "$(dirname "$VENDOR")"
  git clone --quiet https://github.com/cktan/tomlc99.git "$VENDOR"
fi

if [[ -n "$PINNED" ]]; then
  echo ">> checking out pinned commit ${PINNED:0:12}"
  git -C "$VENDOR" checkout --quiet "$PINNED"
else
  echo "!! WARNING: no pinned commit found in grammar/PINNED_COMMIT.txt" >&2
  echo "!! Building against whatever is checked out. Fix this before" >&2
  echo "!! recording any results." >&2
fi

ACTUAL=$(git -C "$VENDOR" rev-parse HEAD)

# --- compile ---------------------------------------------------------------
SAN_FLAGS=(
  -fsanitize=address,undefined
  -fno-omit-frame-pointer
  -fno-sanitize-recover=all      # UBSan must abort, not just warn and continue
)
WARN_FLAGS=( -Wall -Wextra -Wno-unused-parameter )

mkdir -p "$BUILD"
echo ">> compiling with $CC"

"$CC" "${SAN_FLAGS[@]}" "${WARN_FLAGS[@]}" -g -O1 \
  -I "$VENDOR" \
  "$ROOT/harness/toml_harness.c" \
  "$VENDOR/toml.c" \
  -o "$BUILD/toml_harness"

# --- provenance ------------------------------------------------------------
cat > "$BUILD/BUILD_INFO.txt" <<EOF
built:            $(date -Iseconds)
compiler:         $($CC --version | head -1)
tomlc99 commit:   $ACTUAL
sanitizers:       address,undefined (no-recover)
optimization:     -O1 -g -fno-omit-frame-pointer
harness exit codes: 0=accept 2=reject 64=usage
EOF
