# Progress Report — Agentic Fuzzing of `tomlc99`

**Prepared for:** course instructor
**Project:** LLM-driven grammar fuzzer targeting `tomlc99` (a C TOML parser)
**Status:** 5 of 6 deliverables complete; the agentic loop has autonomously
found real memory-safety bugs

---

## 1. What the assignment asks for

The task is to build a **test generator (fuzzer)** that finds crashing
bugs in a small C library, using an **agentic** approach rather than a
traditional coverage-guided fuzzer: an LLM is given a formal grammar for
the library's input format and asked to write a
[Hypothesis](https://hypothesis.readthedocs.io/) strategy — a program
that generates test inputs — then **iteratively refine** that strategy
based on feedback, for up to 5 iterations or a fixed cost budget.

Critically, this is a **blackbox** exercise: no code-coverage
instrumentation of the target library is allowed, only sanitizer output
(crash detection). The graded skill is not "did you build a fuzzing
engine" — it's **how well you can drive an LLM to turn a formal grammar
into an effective generator, and how well you design the feedback loop
around it**, given that you can't see which lines of the target's code
actually ran.

The assignment is structured in six steps: (1) find a formal grammar for
the target format, (2) build a sanitizer-instrumented test harness, (3) a
naive baseline generator to prove the pipeline works, (4) the agentic
loop itself, (5) crash triage (deduplicate, minimize, verify), and (6) a
written report. It's graded on: correctly interpreting the grammar,
whether the generated strategy reflects real grammar structure (not just
"big random string"), engineering rigor in the harness, the design of the
feedback signal (since there's no coverage available), triage instinct,
and judgment under a fixed budget.

---

## 2. Design

**Grammar.** Sourced the TOML grammar from ANTLR's `grammars-v4` repository
(`TomlLexer.g4` + `TomlParser.g4`), used as-is per the assignment's
instructions — not re-derived from the library's own source. Before
building anything, I hand-probed the pinned `tomlc99` build against a
checklist of TOML edge cases and found **5 real divergences** between the
formal grammar and the library's actual behavior: it silently accepts
trailing commas in inline tables (grammar forbids them), silently
truncates over-long fractional seconds, silently re-types integers past
`INT64_MAX` as floats, lets a leading-zero integer through its first parse
stage only to fail a later, separate accessor call, and — critically —
has no depth limit on nested arrays, which segfaults at extreme depth.
That last one became the seed for everything found later.

**Harness and crash classification.** `harness/toml_harness.c` is a small
C driver, compiled with `-fsanitize=address,undefined`, that feeds one
input to `tomlc99`'s real parser and to its typed value accessors (a
config file can parse successfully but still fail a later
`toml_rtoi`/`toml_rtod` call — that's a genuine finding, not just "did
`toml_parse` return 0"). Classification is deliberately ordered: a
per-input timeout is checked first, then sanitizer output (authoritative
regardless of how the process finally died), then a fatal signal, then
the harness's own exit code. Getting the sanitizer-before-exit-code order
wrong is the classic bug here — it would file a real memory-safety issue
as a clean rejection.

**The agentic loop and its proxy signal.** The loop (`agent/loop.py`)
runs seed → validate → run 500 examples → summarize → refine, up to 5
iterations. Since code coverage of `tomlc99` is off-limits, the proxy
signal I chose combines four externally-observable things, computed by
reading the *generated text itself*, never the target's internals:
**grammar-production coverage** (how many of ~30 tracked TOML constructs
have appeared in *accepted* documents), **acceptance rate** (a generator
rejected 99% of the time is testing nothing), **novelty** (structural
shape diversity, to stop the model regenerating the same document shape),
and **max nesting depth reached**. I expected this to work because
`tomlc99`'s parser is structured around the same constructs the grammar
names — it has functions literally called `parse_array`,
`parse_inline_table`, `parse_keyval` — so "which grammar productions
reached the parser" is a structural shadow of "which parser code ran."
Rejected inputs are deliberately excluded from coverage/depth accounting,
since a rejected input barely touches the parser at all.

---

## 3. Findings

**The loop found real crashes, autonomously.** In the most recent full
run, the agentic loop's own generated strategy produced **318 crashing
inputs**, which triage deduplicated into **3 distinct, mechanism-confirmed
stack-overflow bugs** in `tomlc99` — via deeply nested arrays
(`parse_array` recursion), extremely long dotted keys (`parse_keyval`
recursion), and deeply nested inline tables (a `parse_inline_table` ↔
`parse_keyval` mutual recursion). None of these were hand-fed; every
crashing input traces back to the LLM-written generator's own logs.

**How the strategy evolved, and what drove each change.** Early
iterations exposed a sequence of concrete, real failures, each fixed by a
targeted prompt rule: recursion that looked real but never actually
nested (the strategy used `@composite` but never let a container hold
another instance of itself — depth stuck at 1 for a whole run); banned
API calls the model kept hallucinating (`st.dates(min_date=...)`, which
doesn't exist); a document generator that put bare arrays/tables at the
top level, producing invalid TOML at any depth. The most significant
finding, by far: **recursive generation is structurally incapable of
reaching crash-triggering depth, no matter how it's biased.** A measured
A/B test — same recursion-bias ratio, same depth counter, only changing
list-branching width — showed even the *correctly shaped* recursive
chain plateaus around depth 13, against bugs that need 48,000–105,000
levels of nesting. Hypothesis's own data-generation budget resists deep
recursion; this is not a prompt-quality problem, it's a property of the
tool. The fix was to stop recursing entirely for the extreme-depth case:
draw an integer, build the string by direct repetition. That one change
took measured max depth from single digits to over 50,000 in one
iteration, and is what produced the first loop-found crashes.

**What's still under-tested.** Two divergences from the initial grammar
probing — silent int→float re-typing and the leading-zero integer that
splits parse-success from accessor-failure — hint at shaky type-handling
that the depth-focused generator hasn't specifically targeted yet. I also
identified, but haven't yet confirmed through the agentic loop itself, an
**algorithmic-complexity bug**: `tomlc99` looks up every key via a linear
scan, so many sibling keys in one table cost quadratic time overall —
measured directly, 15,000+ sibling keys already exceed the 5-second
timeout. This is a structurally different bug class (a hang, not a
memory-safety crash) that the prompt has now been updated to also target,
but a fresh run hasn't confirmed the loop finds it independently yet.

---

## 4. Challenges

**The single most transferable finding: an illustrative constant in a
prompt example is read as a hard ceiling, not a suggestion.** After
teaching the model the integer-repetition depth technique, depth jumped
1,250× in one iteration — genuinely correct code — but then froze at
*exactly* the number used in my own worked example, because the model
copied that literal bound instead of the depth target the feedback signal
was concurrently requesting. The model obeyed instructions exactly and
still missed the objective, because a detail chosen purely for
illustration got treated as a constraint. This reframes a lot of the
project's earlier "why isn't depth increasing" debugging: it was never
really about model obedience.

**A real deduplication judgment call, found by the triage tooling's first
real use.** A deep stack-overflow's sanitizer backtrace is inherently
unstable — sometimes it unwinds cleanly, sometimes it doesn't. When it
doesn't, every frameless crash falls back to the same generic signature,
which can silently merge two genuinely distinct bugs into one bucket (or
worse, mislabel a distinct bug as a repeat of an existing one). The fix —
retry a crashing input until a parseable stack is obtained before
committing to a signature — is a documented, defensible normalization
choice, not an assumption.

**Other judgment calls documented along the way:** timeouts are treated
identically to crashes per the assignment's own policy (a hang is a real
denial-of-service bug); a generator that was mostly getting rejected
(acceptance below a 20% floor) is caught and rejected *before* it ever
runs a full 500-example pass, rather than wasting the budget; and a
mid-project external dependency failure — Groq deprecated the model this
project had been using, mid-session, forcing a live migration to a
replacement model and, separately, hitting a much stricter per-model
token-rate ceiling than before, which is still being worked around.

**What I'd change with more time, or with real coverage feedback:**
resolve one remaining ambiguity where a supplementary hand-written
generator's "mixed nesting" construct fragmented into multiple crash
signatures in triage — unclear yet whether that's one bug over-counted or
several real ones; confirm the algorithmic-complexity hang via the
agentic loop rather than only a hand-written probe; and, if real coverage
instrumentation were available, replace the current external
grammar-shape proxy with actual line/branch coverage, which would remove
the single biggest source of uncertainty in this whole design — whether
"touched this grammar construct" really does track "exercised this code
path" as closely as hoped.

---

## 5. Current progress against the deliverables checklist

- [x] Grammar source + noted adaptations
- [x] Build script + harness source
- [x] Baseline strategy + pipeline demonstration
- [x] Agentic loop implementation + final generator + iteration log
- [x] Deduplicated, minimized crash reports — 3 confirmed distinct bugs,
      autonomously found
- [ ] Two-page written report — this document is the working draft;
      final polish and appendix assembly still pending

Detailed evidence for every claim above — full run history, every prompt
rule and the specific failure it fixed, all triage reports, and a
plain-language explanation log — lives in the repository: `OBSERVATIONS.md`,
`logs/RUN_HISTORY.md`, `triage/reports/`, and `PROJECT_SUMMARY.md`.
