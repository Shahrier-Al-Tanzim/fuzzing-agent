# Progress Till Now — 2026-08-30

A plain-language walkthrough of what this project is, what we did, in what
order, and where it stands today. This is written as a "catch-up" document
— if you read nothing else, this tells you the whole story.

---

## 1. What the assignment is, in one paragraph

Build a fuzzer — a program that automatically generates test inputs — for a
small C library that parses TOML files (`tomlc99`). Instead of throwing
random bytes at it, the twist is: an LLM reads a formal grammar of TOML and
writes a Python program (a "Hypothesis strategy") that generates valid-ish
TOML text, then the LLM keeps improving that program over several rounds
based on feedback. No code-coverage tools are allowed (we can't see which
lines of the C code ran) — only crash detection. The end goal: find real
crashing bugs, understand them, and write a 2-page report explaining the
design and findings.

---

## 2. The 8-module structure (how the work was organized)

Each module lived on its own git branch, merged into `main` in order:

1. **module-1-grammar-adaptation** — found a formal TOML grammar and
   compared it against what `tomlc99` actually does.
2. **module-2-harness-build** — built the C test harness with sanitizers.
3. **module-3-baseline-pipeline** — a dumb/naive generator, just to prove
   the whole pipeline (generate → run → log) works end-to-end.
4. **module-4-agentic-loop** — the real thing: LLM writes a TOML generator,
   we run it, we feed results back to the LLM, repeat.
5. **module-5-feedback-signal** — designing what "progress" even means
   without code coverage (this is where "grammar breadth" was born).
6. **module-6-crash-triage** — deduplicating and minimizing crashes so we
   report real distinct bugs, not noise.
7. **module-7-report** (current branch) — writing up everything, plus a
   cluster of side-experiments (7b, 7c, 7d) testing whether the loop could
   find bugs *without* hand-holding.

---

## 3. Step-by-step: what we actually built

### Step 1 — The grammar (module-1)

- Took the TOML grammar from ANTLR's public `grammars-v4` repo
  (`grammar/TomlLexer.g4`, `grammar/TomlParser.g4`) — did not write our own
  from scratch, per the assignment's instructions.
- Manually tested the pinned `tomlc99` build against a checklist of TOML
  edge cases to find where reality differs from the formal grammar.
  Found **5 real differences**, documented in `grammar/adaptations.md`:
  1. `tomlc99` silently allows a trailing comma in `{ a=1, b=2, }` (the
     grammar forbids it).
  2. Extremely precise fractional timestamps get silently truncated.
  3. An integer one bigger than the max allowed size gets silently turned
     into a "float" type instead of being rejected.
  4. A number like `007` passes the first parse step, but fails later when
     you actually try to read it as an integer — two separate checks, not
     one.
  5. **The important one**: deeply nested arrays like `[[[[...]]]]` have no
     depth limit at all. Around 48,000 levels deep, the program crashes
     (a stack overflow). This became the seed for everything found later.

### Step 2 — The test harness (module-2)

- Wrote `harness/toml_harness.c`, a small C program that feeds one input
  file into `tomlc99`'s real parser, compiled with AddressSanitizer +
  UndefinedBehaviorSanitizer (`-fsanitize=address,undefined`) — these are
  tools that catch memory-safety bugs (like using freed memory, or writing
  past an array) that would otherwise fail silently or randomly.
- Set up clear exit codes so we can tell "this input was valid," "this
  input was correctly rejected," and "this input triggered a crash" apart
  from each other reliably.
- Important design decision: sanitizer output is checked *before* the exit
  code, because it's the authoritative signal — trusting exit code alone
  could file a real memory bug as "clean rejection."

### Step 3 — Baseline pipeline (module-3)

- Before trusting any LLM output, built a deliberately dumb generator
  (random text, TOML-ish text) and ran ~9,050 examples through the full
  pipeline just to prove the plumbing works: generate → run harness → log
  result. Zero crashes expected and found — this step is about proving the
  machine works, not finding bugs.

### Step 4 — The agentic loop itself (module-4)

- `agent/loop.py` runs this cycle, up to 5 times per run:
  **Seed** (give the LLM the grammar) → **Validate** (sanity-check the
  generator isn't garbage) → **Run** (generate 500 real test inputs) →
  **Summarize** (measure what happened) → **Refine** (tell the LLM what to
  improve) → repeat.
- The LLM providers used, in order, and why we kept switching:
  1. **Ollama, local `qwen2.5-coder:7b`** — this small model never
     produced a single working generator in 12 tries. It kept inventing
     Hypothesis library functions that don't actually exist, even after
     being told exactly what it did wrong.
  2. **Groq, `llama-3.3-70b-versatile`** — a much bigger model. Its
     mistakes were normal programming bugs (forgetting to unwrap a value,
     type mismatches), fixable with one clear prompt rule. Big lesson:
     bigger models don't just do "a bit better," they fail in a
     completely different (and much more fixable) way.
  3. **Gemini** — Groq discontinued the model we were using partway
     through the project, forcing a live switch to Gemini, which is the
     current default.

### Step 5 — The feedback signal, since there's no code coverage (module-5)

Since we're not allowed to see which lines of `tomlc99`'s C code actually
ran, we needed some other way to tell if the generator was "getting
better." We measure things purely by reading the *generated TOML text
itself*, before it's even sent to the parser:

- **Grammar breadth** — of ~30-38 known TOML building blocks (arrays,
  dates, quoted strings, etc.), how many has our generator actually
  produced so far? (Originally called "coverage," renamed to "grammar
  breadth" later — see Section 5, it's an important distinction.)
- **Acceptance rate** — what fraction of generated documents does
  `tomlc99` actually accept as valid?
- **Novelty rate** — how often is the generator producing a genuinely new
  shape, not a repeat?
- **Max nesting depth** reached.

This signal is what gets summarized and fed back to the LLM each round to
tell it what to try next ("you haven't tried unicode yet," "push nesting
deeper," etc.).

### Step 6 — Crash triage (module-6)

Built `triage/` tooling to take raw crash logs and turn them into a
trustworthy bug list:
- **Deduplicate** — group crashes by root cause, not by superficial
  differences in the crashing input.
- **Minimize** — shrink a huge crashing input down to the smallest input
  that still crashes (this is called "delta debugging").
- **Verify** — re-run the minimized input to confirm it reliably crashes.

A real judgment call surfaced here: deep stack-overflow crashes sometimes
produce an unstable/incomplete backtrace, which can make one real bug look
like several different ones. Fix: retry a crashing input until we get a
clean, parseable stack trace before deciding it's a "new" bug.

---

## 4. What we actually found — the 5 confirmed bugs

| # | Bug | What causes it | Depth needed | Reliable? |
|---|---|---|---|---|
| 1 | Array nesting overflow | Every `[` adds a recursive call, no limit | ~48,000 | Yes |
| 2 | Dotted-key overflow | Every `.` in a key adds a recursive call | ~90,000–100,000 | Yes |
| 3 | Inline-table overflow | Inline tables and key-values call each other recursively | ~80,000 | Yes |
| 4 | Many-siblings slowdown (hang) | Adding a key does a full linear scan every time → gets slower and slower (O(n²)) | ~15,000+ keys | Times out, not a crash |
| 5 | Alternating array/inline-table overflow | A third distinct recursive cycle between arrays and inline tables | ~40,000–80,000 | Yes, but signature varies |

4 of these are memory-safety bugs (stack overflow from unbounded
recursion); 1 is a denial-of-service via slow algorithmic behavior. All 5
share the same root cause: nothing in `tomlc99` puts a limit on
attacker-controlled input size or nesting depth.

Bug 1 was found by hand during the initial grammar-comparison step. Bugs
2–5 were found later through a mix of manual crash-hunting and the
agentic loop itself, once we taught it the trick of "draw a number, repeat
a string that many times" instead of trying to write real recursive code
(recursion in the generator itself can't reach these depths — it plateaus
around 13 levels no matter what, a limitation of how the Hypothesis
library manages test generation budgets, not a prompting problem).

Also worth noting: after triage, a raw crash-detection tool reported **9
distinct crash signatures**, but reading the actual crashing files by hand
showed 3 of those 9 were really the same bug (#5) captured at different
random points mid-crash. Honest count: **5 bugs**, not 9.

---

## 5. Key turning points and lessons (the interesting part)

These are the moments that actually shaped the design, in roughly
chronological order:

1. **Small local models hallucinate; big remote models make normal
   mistakes.** (module-4) The 7B model invented fake library functions
   and kept doing it even after correction. The 70B model's mistakes were
   ordinary and fixable. This is why we moved off local models entirely.

2. **An example number in a prompt becomes a hard rule, not a suggestion.**
   (Case 5, ⭐) We taught the LLM a technique for extreme depth using one
   example number. Depth jumped from ~4 to 5,000 immediately — but then
   froze at *exactly* that example's number, even while later feedback
   was explicitly asking for something bigger. The model treated the
   illustration as a ceiling. This pattern repeated later (Case 13) with
   a different axis, confirming it's a general effect, not a one-off.

3. **Renamed "coverage" to "grammar breadth" everywhere.** The word
   "coverage" is ambiguous — the assignment explicitly forbids *code*
   coverage of the target library, but our own metric (which only reads
   the generator's own output text) had been using that word for years in
   this project. Renamed across code, logs, and docs to avoid a reader
   mistaking our allowed technique for the forbidden one.

4. **Testing whether the LLM needs hardcoded hints at all (Cases 7, 11).**
   We tried deleting the very specific hand-written rules that told the
   LLM exactly which TOML shapes to target (dotted keys, many siblings,
   etc.) and just gave it general guidance instead. Result: it still
   reinvented the core trick on its own, but only found 3 of the 5 bugs
   instead of 5 — the very specific shapes (dotted keys, many siblings)
   never came up unless directly named.

5. **A real plumbing bug was found: the loop never actually learned from
   its own crashes.** (Case 12) A variable meant to track "which crash
   signatures have we already seen" was written in the code but never
   actually filled in — so the LLM was told "no crashes found yet" even in
   iterations where dozens of real crashes had already happened. Fixed
   and tested; genuinely improved results in one run, then made another
   run *worse* in an unexpected way (a "stop pushing depth" safety
   feature kicked in too early after finding one easy bug). Net result
   across all trials: still didn't beat the version with hardcoded rules,
   so it was kept as a documented experiment but not merged into the main
   report branch.

6. **The real root cause behind why hint-free runs kept stalling at 3/5
   bugs.** (Case 13, ⭐, the most important recent finding) It turned out
   our own measurement tool for "how deep did this get" only counted
   brackets (`[`, `{`). A dotted-key chain like `a.a.a.a...` has no
   brackets at all — so even when the generator accidentally produced a
   90,000-dot crashing input, our own feedback signal reported its depth
   as **zero**, and told the LLM to try something else entirely. The bug
   wasn't that the LLM couldn't find these crashes — it's that our own
   instrument was blind to them. Fixed by identifying every place in the
   grammar that can grow without bound (not just nesting, but dot-chain
   length and sibling-key count) and tracking all three separately. This
   was verified against real logged data, but has not yet been proven out
   on a fresh live run — the fix is documented as a solid experiment, not
   yet the default.

7. **A hard algorithmic bug (#4, the slowdown) was found twice,
   independently** — once by manually reading `tomlc99`'s source code and
   confirming with a timing test, and later a second time by the agentic
   loop finding it completely on its own in a real run.

8. **Provider comparison (Groq vs. Gemini).** Ran the same loop against
   both providers over many runs (archived in `comparison/`). The useful
   result wasn't "which model wins" — it's that different model tiers
   fail in qualitatively different ways (hallucination vs. ordinary bugs),
   which matters more for how you design the prompt than raw model
   quality alone.

---

## 6. Where things stand right now (as of this branch, module-7-report)

- **Grammar + adaptations**: done.
- **Harness + sanitizer build**: done.
- **Baseline pipeline**: done.
- **Agentic loop + final generator**: done, with hardcoded rules 16/17
  (the specific dotted-key / many-siblings hints) currently kept **on**,
  because they're still the only configuration that reliably finds all 5
  bugs across repeated runs. The more "pure," hint-free version (module-7c,
  module-7d branches) is documented as a real experiment but not the
  version actually used for grading, because it maxes out at 3 of 5 bugs.
- **Crash triage**: done — 5 confirmed distinct bugs, deduplicated and
  verified.
- **Written report**: `report/report.md` and `progress_report.md` are both
  substantially written. `progress_report.md` is described as an
  intentionally-oversized working draft (everything included, nothing
  trimmed yet) that still needs to be cut down to the assignment's
  2-page limit — that's the one concrete remaining task.
- Most recent commits (last few days) were about archiving Run 32-33 (the
  scale-axis experiment from Case 13) and reverting back to the
  hardcoded-rules baseline as the "official" configuration on this branch,
  while keeping the experiment fully documented and reproducible on its
  own branch.

## 7. What's left / natural next steps

1. Trim `progress_report.md` down to the assignment's 2-page limit for
   final submission (`report/report.md` is the polished target).
2. Optionally: run the Case 13 scale-axis fix live (not just replayed
   against old logs) to see if it can push the hint-free version past
   3/5 bugs for real.
3. Optionally: run the same comparison against a frontier-tier model
   (mentioned as a "with more time" item), to see if the
   qwen→Groq failure-class improvement continues.

---

*For full detail behind every claim above (exact numbers, code, and
reasoning for each decision), see `OBSERVATIONS.md` (13 documented cases,
the primary source), `progress_report.md` (the full draft report), and
`PROJECT_SUMMARY.md` (a structured deliverable-by-deliverable status
table).*
