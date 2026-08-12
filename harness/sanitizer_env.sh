# Shared sanitizer configuration. Source, do not execute.
#
# exitcode=86: a distinct code so the runner can tell "sanitizer fired"
#   from "harness returned 2". 86 is arbitrary but must not collide with
#   0, 2, 64, or any common signal-derived code.
# abort_on_error=0: we want the exit code, not a SIGABRT, so the signal
#   channel stays reserved for genuine crashes the sanitizer didn't catch.
# detect_leaks=0: leaks are real bugs but not *crashing* bugs, and the
#   assignment scopes this to memory-safety/UB. Turning LSan on would
#   flood the log with findings the harness itself provokes by design.
export ASAN_OPTIONS="exitcode=86:abort_on_error=0:detect_leaks=0:allocator_may_return_null=1:log_path=stderr"
export UBSAN_OPTIONS="exitcode=86:halt_on_error=1:print_stacktrace=1"

# Without this, ASan/UBSan print raw addresses instead of function names
# and source lines in crash reports. Ubuntu's llvm-21 package only installs
# a versioned binary (llvm-symbolizer-21), not the plain "llvm-symbolizer"
# name sanitizers look for on PATH by default, so it has to be pointed at
# explicitly. Install it with: sudo apt install llvm-21
if [[ -x /usr/lib/llvm-21/bin/llvm-symbolizer ]]; then
  export ASAN_SYMBOLIZER_PATH=/usr/lib/llvm-21/bin/llvm-symbolizer
fi
