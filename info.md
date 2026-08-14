# Project Glossary (Simple Version)

Personal notes, not graded, not committed to git. Plain language, no
analogies — just what actually happens, in order. If any part still
feels dense, tell me exactly which sentence and I'll break it down more.

---

## Divergence

**What it means:** A divergence is a spot where the TOML grammar rule
and the real `tomlc99` library disagree about whether a piece of TOML
text is valid.

**How we find one:**
1. Take one specific piece of TOML text.
2. Read the grammar file to figure out what it says: valid or invalid.
3. Run that exact same text through the real compiled `tomlc99` program
   and see what it actually does: accept or reject.
4. If step 2 and step 3 don't match, that mismatch is a divergence.

There are 3 possible mismatches:
- **subset** — grammar says valid, but the library rejects it (library
  is stricter than the grammar)
- **superset** — grammar says invalid, but the library accepts it
  (library is looser than the grammar)
- **variant** — library accepts it, matching the grammar, but stores or
  interprets it differently than the grammar implies

**Example 1 (superset) — real result from our project:**
```
input:  x = { a = 1, b = 2, }        (extra comma before closing brace)
grammar says: invalid
library does: accepted, no error
```
Grammar said no. Library said yes anyway. Superset divergence.

**Example 2 (variant) — real result from our project:**
```
input:  x = 9223372036854775808      (too big for a normal 64-bit whole number)
grammar says: valid, and it's a whole number (integer)
library does: accepted, but stored as type "float" (decimal), not integer
```
It didn't get rejected — but its type got silently changed. Variant
divergence.

**Why this matters:** these mismatch spots are the most likely places
for real bugs, because the library's behavior there is doing something
the grammar didn't predict — code that handles that case was probably
tested less carefully by the library's original authors. So the
fuzz-testing tool should generate more inputs like these on purpose.

Full list of everything found so far: `grammar/adaptations.md`.

---

## The Grammar (the rulebook, `.g4` files)

**What it means:** A text file that states, precisely, what counts as
valid TOML — every allowed character combination, spelled out as rules.

**The two files:**
- `TomlLexer.g4` — defines the smallest valid building blocks (example:
  exactly which characters are allowed to form a number)
- `TomlParser.g4` — defines how those building blocks combine into
  bigger structures (example: a word, then `=`, then a value, forms one
  valid line)

**How we actually use it:** we only ever read this file as text, the
same way you'd read any document, to figure out what it says is allowed.
We never turn it into a running program. (It's technically possible to
run a tool called ANTLR that converts this file into an actual working
parser program — but this project doesn't do that step. It's read-only,
by us and later by the LLM.)

**Example — reading one actual rule line by line:**
```
DEC_INT : [+-]? (DIGIT | (DIGIT_1_9 (DIGIT | '_' DIGIT)+)) -> popMode;
```
This line means: a whole number can optionally start with `+` or `-`,
then is either one single digit `0`-`9` by itself, OR starts with a
digit `1`-`9` followed by more digits.

`007` doesn't fit either option — a lone `0` is only allowed by itself,
not followed by more digits. So just from reading this line, we know the
grammar says `007` is not allowed.

---

## Sanitizers (ASan / UBSan)

**What it means:** Extra checking code added into the compiled program
that catches memory mistakes at the exact moment they happen, instead of
letting the program keep running with corrupted memory and crash
somewhere unrelated later (or not visibly crash at all).

**How they get added — this happens at compile time:**
When we compile the C code, we add the flag `-fsanitize=address,undefined`.
This tells the compiler to automatically insert extra checking
instructions all through the program's machine code. We don't write this
checking code ourselves — the compiler generates it.

Two specific checks:
- **ASan** — checks every memory read/write. Catches things like reading
  past the end of a block of memory, or using memory after it was
  already freed.
- **UBSan** — checks for undefined behavior, meaning operations the C
  language says are technically illegal (example: certain kinds of
  integer math overflow).

**How their behavior is controlled — this happens at run time,
separately from compiling:**
Compiling adds the checks, but doesn't decide what happens *when* a
check fails. That's controlled by environment variables, set in
`harness/sanitizer_env.sh`. We set it so that when a sanitizer catches a
problem, the program exits with the specific number `86`. That way, any
script running the program can tell "a sanitizer caught a real bug" just
by checking if the exit number is 86 — instead of it looking identical
to any other kind of crash.

**Example from our project:** we made a TOML file with an array nested
inside itself about 48,000 times, `[[[[...]]]]`. Running it through the
plain program (no sanitizer) made the operating system just kill it with
no explanation ("segmentation fault"). Once the sanitizer-equipped
program exists, the same crash should be caught with an actual
explanation — and specifically exit with code 86 — instead of an
unexplained kill.

---

## Harness

**What it means:** A program we wrote whose only job is: take one piece
of TOML input, run it through the real `tomlc99` library, and report
back a simple, consistent result — a single number — instead of raw,
inconsistent text output.

**What ours (`harness/toml_harness.c`) actually does, in order:**
1. Reads one TOML input — either from a file or from piped-in text.
2. Passes it to `tomlc99`'s real parsing function, `toml_parse()`.
3. If parsing succeeds, it doesn't stop there — it also goes through
   every value found inside and tries converting each one: as text, as
   a whole number, as a decimal number, as true/false, as a date/time.
   This matters because a lot of the library's actual bugs are in these
   conversion steps, not in the initial parsing step. Stopping after
   step 2 would miss most of them.
4. It ends by reporting one of a small, fixed set of numbers, so nothing
   downstream has to read or guess from text output:

| Exit code | What it means |
|---|---|
| `0` | Accepted — parsing and all conversions completed fine |
| `2` | Cleanly rejected — the library correctly said "this is not valid TOML" |
| `64` | A problem in our own harness (bad input file, etc.) — NOT a bug in the library, just our test setup |
| `86` | A sanitizer caught a real memory bug (see Sanitizers above) |
| a "signal" number (example: 139) | The operating system killed the program outright — an uncaught crash |

**Why we wrote our own instead of using the library's built-in demo
tool:** the library does ship a small demo program, but it's meant for a
person to read by eye — its output is plain text, not a clean number.
Our harness exists so every later step (the automatic input generator,
the crash-sorting step) can just check one number and know exactly what
happened, every single time, without guessing from text.

---

## Two different compiled programs: `toml_json` vs `toml_harness`

**What it means:** these are two separate programs, built from mostly
the same underlying library, but compiled with different flags — so
they behave differently when something goes wrong.

- **`toml_json`** (`harness/vendor/tomlc99/toml_json`) — built in
  Module 1 with plain `make`, no sanitizer flags at all. When this
  crashes, the operating system just kills it and reports almost
  nothing: "Segmentation fault," and exit code 139. No detail about
  which function was running or why.

- **`toml_harness`** (`harness/build/toml_harness`, Module 2) — built
  with `-fsanitize=address,undefined` added in (see Sanitizers above).
  When something goes wrong here, the sanitizer notices *before* the OS
  has to step in, and prints a **stack trace** — a list of which
  functions were called, in what order, leading up to the problem. That
  detail is what lets you point at the actual responsible line of code,
  instead of just knowing "it died somewhere."

**Current status of our early finding (the array-nesting crash):** it
has only been confirmed with `toml_json` so far, which only proves "yes,
it crashes." It has not yet been re-run through `toml_harness`, which
would give a proper stack trace explaining why, instead of a bare
segfault. That re-check is still pending.

---

## The `timeout` command

**What it means:** `timeout 10 <command>` does not mean "run for 10
seconds." It means "don't let this run for **longer than** 10 seconds."
It's a maximum limit, not a fixed wait.

**How it actually behaves:**
- If the command finishes (or crashes) on its own before 10 seconds are
  up, `timeout` does nothing — it just lets the result through
  immediately, however fast that was.
- If the command is **still running** when 10 seconds pass, only then
  does `timeout` step in and kill it. In that case, the exit code
  becomes `124` — timeout's own "I had to kill it" signal, different
  from a normal crash code.

**Example from our project:** running the array-nesting crash file
through `toml_json` with `timeout 10` finished almost instantly (a
fraction of a second) — the program crashed on its own from running out
of stack space well before the 10-second limit was ever reached. So we
saw exit code `139` (segfault), not `124`. `timeout` was just standing by
as a safety net in case the program hung instead of crashing — it wasn't
needed here.

---

## How to test the array-nesting crash finding (step by step)

**The two files involved:**
1. The crashing input: `grammar/early_findings/01_array_nesting_stackoverflow.toml`
   (a TOML file with an array nested inside itself 60,000 times)
2. The program it gets fed into: `harness/vendor/tomlc99/toml_json`
   (the plain, no-sanitizer demo binary from Module 1)

**Steps:**
```bash
cd ~/fuzzing-agent

# feed the crashing input into the plain demo binary
timeout 10 harness/vendor/tomlc99/toml_json < grammar/early_findings/01_array_nesting_stackoverflow.toml

# check the result
echo $?
```

**Expected output:**
```
Segmentation fault
```
and `echo $?` prints `139` (128 + 11 — killed by signal 11, SIGSEGV).

**Later, once `toml_harness` is fully built** (needs
`harness/sanitizer_env.sh` to exist first), the follow-up test is:
```bash
source harness/sanitizer_env.sh
timeout 10 harness/build/toml_harness grammar/early_findings/01_array_nesting_stackoverflow.toml
echo $?
```
Expected this time: a detailed ASan report printed to the terminal, and
exit code `86`, instead of a bare `139`.

---

## `harness/toml_harness.c` — what the code actually does

**What it means:** the actual C program we run every test input through.
Takes one TOML file, parses it with the real `tomlc99` library, pokes at
every value inside, and exits with a simple number saying what happened.

**Step by step:**
1. Figure out the input — either a filename passed as an argument, or
   piped-in text if no filename given. Wrong usage (bad args, unreadable
   file) → exits immediately with code `64`.
2. Read the whole input into memory. If it's bigger than 1 MB, something
   is wrong with the *test input generator*, not the library — exits
   with `64` again rather than trying to parse something pathological.
3. Call `toml_parse()` — the real library function being tested.
   - Fails → invalid TOML, prints the library's own error message,
     exits `2`. Normal, expected outcome, not a bug.
   - Succeeds → move to step 4.
4. Walk through every key and value found, and try converting each one
   every possible way: as text, as a whole number, as a decimal, as
   true/false, as a date. Recurses into nested tables/arrays too.
   **Why this step exists:** a lot of the library's actual bugs live in
   these conversion functions, not in the initial parse — stopping after
   step 3 would miss most of them.
5. If nothing crashed, cleans up and exits `0` — fully accepted.

**The full set of exit codes:**

| Code | What it means |
|---|---|
| `0` | Accepted — parsed fine, walked every value, nothing wrong |
| `2` | Rejected — library correctly said "not valid TOML" |
| `64` | Problem with *how the program was run* — not a finding about the library |
| (program gets killed, no return code from the table above) | A sanitizer caught a real bug, or the OS killed it with a crash signal (e.g. 139 = SIGSEGV) |

That last row is the entire point of this program existing: because it's
compiled with ASan/UBSan checks baked in, if `toml_parse()` or any
conversion function ever touches memory incorrectly, the program gets
stopped right there — before it ever reaches its own `return` lines —
with a report of exactly what went wrong.
