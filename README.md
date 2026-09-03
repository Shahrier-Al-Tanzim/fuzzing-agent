# LLM-Driven Grammar Fuzzing of `tomlc99`

This repository is the working code, evidence, and write-up for a
class-assignment project that builds a fuzzer for the C library
[`tomlc99`](https://github.com/cktan/tomlc99) using an LLM-driven
agentic loop.

The LLM does not throw random bytes. It reads a formal TOML grammar
(ANTLR's `grammars-v4`) and writes a Python program — a Hypothesis
strategy — that generates TOML-shaped text. We run that program against
the real C parser (compiled with AddressSanitizer + UndefinedBehaviorSanitizer),
measure the result without ever looking at code coverage of the target
library, and feed that summary back to the LLM to improve the strategy
on the next round.

The end goal is to find real, deduplicated, minimized crashing inputs,
understand them, and write up the design and findings.

---

## Quick start (TL;DR)

```bash
# 1. Get the code and enter it
cd /home/tanzim/fuzzing-agent

# 2. Create a Python virtual environment and install deps
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

# 3. Set provider keys (one is enough)
export GROQ_API_KEY=...        # older runs
export GEMINI_API_KEY=...      # middle runs (provider moved)
export OPENAI_API_KEY=...      # current default

# 4. Build the C harness with sanitizers (clang required)
bash harness/build.sh
source harness/sanitizer_env.sh

# 5. (optional) Confirm the plumbing on a dumb generator
python -m pipeline.run --tier random

# 6. Run the agentic loop
python -m agent.loop           # new run
python -m agent.loop --resume  # continue an in-progress run

# 7. Deduplicate + minimize any crashes that showed up
python -m triage.dedupe --input logs/<run>.jsonl
python -m triage.minimize --signature <sig>
```

See **[§6 How to run](#6-how-to-run)** for the full command list.

---

## Table of contents

1. [Project overview](#1-project-overview)
2. [The assignment, restated](#2-the-assignment-restated)
3. [The 8-module journey](#3-the-8-module-journey)
4. [Repository structure](#4-repository-structure)
5. [Environment setup](#5-environment-setup)
6. [How to run](#6-how-to-run)
7. [Findings — what the loop actually found](#7-findings--what-the-loop-actually-found)
8. [Grammar divergences (grammar vs. reality)](#8-grammar-divergences-grammar-vs-reality)
9. [Key turning points and lessons](#9-key-turning-points-and-lessons)
10. [Gaps and open items](#10-gaps-and-open-items)
11. [Where to look for more detail](#11-where-to-look-for-more-detail)

---

## 1. Project overview

**Target.** `tomlc99` — a small, single-file C TOML parser. Pinned to
commit `5221b3d3d66c25a1dc6f0372b4f824f1202fe398` from 2023-09-30
(see [`grammar/PINNED_COMMIT.txt`](grammar/PINNED_COMMIT.txt)).

**Fuzzer.** Property-based, using the Python [`hypothesis`](https://hypothesis.readthedocs.io/)
library. A *strategy* is a Python function that returns a
`hypothesis.strategies.*` value, which the library then uses to draw
random-but-structured examples.

**Driver.** An agentic loop (`agent/loop.py`) — see **[§6.4](#64-run-the-agentic-loop)**.
It runs the cycle: **seed → validate → run → summarize → refine**, up to
5 iterations per run, with the LLM producing a new or improved strategy
each round.

**LLM providers used, in order, and why we kept switching:**

| Phase | Provider | Model | Why we switched |
|---|---|---|---|
| Module-4, runs 1–12 | Groq | `llama-3.3-70b-versatile` | Could not generate a working strategy with the local 7B model — moved to a frontier-tier remote model for sanity. |
| Module-5, runs 15–21 | Gemini | `gemini-3.6-flash` | Groq discontinued the 70B model mid-project. Live switch. |
| Module-7, runs 22+ | OpenAI | `gpt-5.6-luna` | Frontier-tier comparison requested by the assignment. See [`comparison/openai/`](comparison/openai/). |
| Earlier experiments | Ollama (local) | `qwen2.5-coder:7b` | Never produced a single working strategy in 12 tries. Kept in [`comparison/`](comparison/) as a documented failure case. |

The current default is OpenAI; switch via `config.yaml` (`llm.provider`).

**Exit-code contract** (from [`harness/`](harness/README.md)):

| Code | Meaning |
|---|---|
| 0 | Accept — input is valid TOML and parsed cleanly |
| 2 | Reject — input is invalid TOML, rejected as expected |
| 64 | Usage error |
| 86 | **Sanitizer fired** — memory or undefined-behavior bug |
| `<0` | Process died on a signal (often `SIGSEGV` from a stack overflow) |

Sanitizer output is checked *before* the exit code, because the
sanitizer is the authoritative signal for memory safety — trusting
exit code alone could file a real memory bug as "clean rejection."

---

## 2. The assignment, restated

The original brief is in [`assignment_agentic_fuzzing.md`](assignment_agentic_fuzzing.md).
The 6 required steps and what was delivered for each:

| # | Step | Delivered as |
|---|---|---|
| 1 | Find a TOML grammar | [`grammar/TomlLexer.g4`](grammar/TomlLexer.g4), [`grammar/TomlParser.g4`](grammar/TomlParser.g4) — borrowed from ANTLR's public `grammars-v4` repo. |
| 2 | Build a harness that compiles the grammar target with sanitizers and emits clear exit codes | [`harness/`](harness/) — `toml_harness.c`, `build.sh`, `sanitizer_env.sh`. |
| 3 | A baseline (dumb) strategy that exercises the full pipeline | [`pipeline/`](pipeline/) — three tiers: `random`, `tomlsh`, `minimal`. |
| 4 | An agentic loop where the LLM writes the strategy and is shown feedback | [`agent/`](agent/) — `loop.py`, `summarize.py`, `prompts.py`, plus per-iteration strategy storage. |
| 5 | Crash triage — deduplicate, minimize, verify | [`triage/`](triage/) — `dedupe.py`, `minimize.py`, plus `triage/reports/` as the deduplicated, verified evidence archive. |
| 6 | A short (2-page) report explaining the design and findings | [`report/report.md`](report/report.md) (polished target); [`progress_report.md`](progress_report.md) is an intentionally-oversized working draft, kept untrimmed until the cut-down step. |

**Constraints from the assignment (verbatim):**

- 500 examples per iteration
- 10-minute wall-clock budget per iteration
- 5 iterations per run
- 5-second per-input timeout
- Timeouts count as crashes
- **No code-coverage instrumentation of the target library** — only crash detection

---

## 3. The 8-module journey

Each module lived on its own git branch, merged into `main` in order:

1. **module-1-grammar-adaptation** — find a formal TOML grammar and compare it to what `tomlc99` actually does. Documented in [`grammar/adaptations.md`](grammar/adaptations.md) (5 real divergences). Bug 1 (array nesting overflow) was found by hand here, before the agentic loop existed.
2. **module-2-harness-build** — C harness compiled with ASan + UBSan. Exit-code contract, sanitizer-before-exit-code rule.
3. **module-3-baseline-pipeline** — three dumb generators to prove the plumbing works (`random`, `tomlsh`, `minimal`).
4. **module-4-agentic-loop** — the real thing. Seed → validate → run → summarize → refine, LLM-driven.
5. **module-5-feedback-signal** — designing what "progress" means without code coverage. **Grammar breadth** (renamed from "coverage" — see [§9 lesson 3](#9-key-turning-points-and-lessons)) was born here.
6. **module-6-crash-triage** — dedupe + minimize + verify. Consecutive-frame collapse, harness-frame drop, top-5 normalization.
7. **module-7-report** (this branch) — write-up + side-experiments (7b, 7c, 7d) testing whether the loop can find bugs without hand-holding.
8. **module-7-report — Phase 1 validation** — Run 50, ran the loop with the scale-axis fix from Case 13 to confirm Bug 6 (the sixth discovered bug) was real and reproducible. See [`OBSERVATIONS.md` Case 16 + Case 17](OBSERVATIONS.md).

---

## 4. Repository structure

```
fuzzing-agent/
├── README.md                       # this file
├── assignment_agentic_fuzzing.md   # the original brief
├── progress_report.md              # oversized working draft of the report
├── PROJECT_SUMMARY.md              # structured status-by-deliverable
├── OBSERVATIONS.md                 # 17 documented cases (primary source)
├── progress_till_now_2026-08-30.md # plain-language catch-up doc
├── config.yaml                     # central config: provider, models, depth buckets,
│                                   #   exit codes, triage settings
├── requirements.txt                # hypothesis==6.112.1, PyYAML==6.0.2, requests==2.32.3
│
├── grammar/                        # module 1
│   ├── TomlLexer.g4                # borrowed from ANTLR grammars-v4
│   ├── TomlParser.g4
│   ├── PINNED_COMMIT.txt           # tomlc99 commit we're fuzzing
│   ├── adaptations.md              # the 5 grammar-vs-reality divergences
│   └── early_findings/             # bug reproducers found by hand, before the loop
│       ├── 01_array_nesting_stackoverflow.toml
│       ├── 02_dotted_key_stackoverflow.toml
│       └── README.md
│
├── harness/                        # module 2
│   ├── toml_harness.c              # the C program under test
│   ├── build.sh                    # builds tomlc99 + harness, ASan + UBSan, -O1 -g
│   ├── sanitizer_env.sh            # source, not execute — sets ASAN_OPTIONS, UBSAN_OPTIONS
│   ├── vendor/                     # tomlc99 at the pinned commit (gitignored)
│   └── build/                      # compiled binaries (gitignored)
│
├── pipeline/                       # module 3 — baseline generators
│   ├── run.py                      # three tiers: random, tomlsh, minimal
│   ├── generator_random.py
│   ├── generator_tomlsh.py
│   └── generator_minimal.py
│
├── agent/                          # module 4
│   ├── loop.py                     # the agentic loop
│   ├── prompts.py                  # all prompts given to the LLM
│   ├── summarize.py                # what we tell the LLM each round
│   ├── providers.py                # Groq / Gemini / OpenAI / Ollama adapters
│   ├── strategies/                 # per-iteration generated strategies, persisted
│   │   └── accepted/               # accepted-by-validation gate, per run number
│   └── state/                      # loop-resume state (gitignored)
│
├── triage/                         # module 6
│   ├── dedupe.py                   # normalize + group crashes
│   ├── minimize.py                 # delta-debugging shrinker
│   ├── verify.py                   # re-run minimized crashes
│   └── reports/                    # permanent, deduplicated, verified evidence archive
│       └── run_<NN>/               # per-run-number evidence folders
│
├── comparison/                     # side-experiments: Groq vs Gemini vs OpenAI vs Ollama
│   ├── groq/                       # runs 1–12 (metrics only)
│   ├── gemini/                     # runs 15–21 (per-run code + triage)
│   ├── openai/                     # runs 22+ (current)
│   ├── claude/                     # frontier-tier comparison
│   └── README.md
│
├── logs/
│   └── RUN_HISTORY.{jsonl,md}      # permanent, append-only run record
│
└── report/                         # module 7
    ├── report.md                   # polished, 2-page target
    ├── generated/                  # per-run generated reports (markdown)
    └── figures/                    # charts referenced by the report
```

---

## 5. Environment setup

This project was developed on **WSL2 Ubuntu** (Unbuntu on Windows
Subsystem for Linux). Some of the sanitizer tooling (`llvm-symbolizer`,
in particular) does not have a clean Windows port, so use WSL or a
real Linux box. macOS may also work but is untested.

### 5.1 System packages

```bash
sudo apt update
sudo apt install -y \
    build-essential \
    clang \
    llvm-21 \
    python3 python3-venv python3-dev \
    git
```

- `clang` — to compile the harness with ASan/UBSan (gcc works too, but
  clang is what `harness/build.sh` is pinned to).
- `llvm-21` (or whatever `llvm-symbolizer` ships with on your distro) —
  the harness needs to call the symbolizer to turn raw addresses in the
  crash trace into `file:line` frames. `harness/build.sh` checks for it
  at `/usr/lib/llvm-21/bin/llvm-symbolizer` by default; adjust if your
  distro puts it elsewhere.

### 5.2 Python environment

```bash
cd /home/tanzim/fuzzing-agent
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

Pinned versions matter — `hypothesis==6.112.1` in particular has changed
behaviour across recent versions, so don't `pip install --upgrade` blindly.

### 5.3 API keys

Create a `.env` file at the repo root (it is gitignored):

```bash
GROQ_API_KEY=...
GEMINI_API_KEY=...
OPENAI_API_KEY=...
```

One is enough — pick the provider you're using via `config.yaml` →
`llm.provider`. The agent loop loads the keys from `.env` at startup.

### 5.4 Build the C harness

```bash
bash harness/build.sh
source harness/sanitizer_env.sh
```

- `build.sh` clones `tomlc99` into `harness/vendor/`, checks out the
  pinned commit, and compiles `harness/toml_harness.c` against it with
  `-fsanitize=address,undefined -O1 -g -fno-omit-frame-pointer`.
- `sanitizer_env.sh` is **sourced, not executed** (no `./`). It sets:
  - `ASAN_OPTIONS=exitcode=86:abort_on_error=0:detect_leaks=0`
  - `UBSAN_OPTIONS=exitcode=86:halt_on_error=1`
  - `ASAN_SYMBOLIZER_PATH=/usr/lib/llvm-21/bin/llvm-symbolizer`

If you forget to source `sanitizer_env.sh`, sanitizer fires will
silently get exit code 1 (or whatever the C runtime returns) instead of
86, and triage's signature derivation will be wrong.

### 5.5 Config

[`config.yaml`](config.yaml) is the central knob:

```yaml
llm:
  provider: openai            # groq | gemini | openai | ollama
  model: gpt-5.6-luna

loop:
  iterations: 5
  max_examples: 500
  per_input_timeout_seconds: 5

triage:
  top_n_frames: 5
  collapse_recursive: true     # consecutive identical frames → one frame
  drop_harness_frames: true     # strip <harness>.c frames so target-only signature

exit_codes:
  accept: 0
  reject: 2
  usage: 64
  sanitizer: 86
```

---

## 6. How to run

### 6.1 Build (once)

```bash
bash harness/build.sh
source harness/sanitizer_env.sh
```

Smoke-test it:

```bash
echo 'a = 1' | harness/build/toml_harness /dev/stdin
echo $?    # should be 0
```

### 6.2 Baseline (dumb) generators — sanity check

```bash
# Random text — should never crash
python -m pipeline.run --tier random --examples 1000

# TOML-ish text (random identifiers and values) — also should not crash
python -m pipeline.run --tier tomlsh --examples 1000

# Minimal: just "a = 1" repeated — sanity check the accept path
python -m pipeline.run --tier minimal --examples 1000
```

Output is appended to `logs/<run-id>.jsonl`. If these generate a crash,
the harness is broken — stop and investigate before touching the agentic loop.

### 6.3 Inspect grammar divergences

```bash
cat grammar/adaptations.md
```

See **[§8](#8-grammar-divergences-grammar-vs-reality)** for the summary.

### 6.4 Run the agentic loop

```bash
python -m agent.loop                 # new run, fresh run number
python -m agent.loop --resume        # resume an in-progress run
python -m agent.loop --run 50        # re-display an existing run
```

A run does up to 5 iterations, each capped at 500 examples and 10 minutes
wall clock. Per-input timeout is 5 seconds; timeouts count as crashes.

Each iteration:

1. **Seed or refine** — ask the LLM to write (or improve) a Hypothesis
   strategy that emits TOML.
2. **Validate the strategy** — 6 hard gates (`agent/validate.py`):
   syntax, imports, draws, acceptance rate, no live-network calls,
   and a smoke-test run of 5 examples.
3. **Run** — up to 500 examples through the harness.
4. **Summarize** — compute grammar breadth, acceptance rate, novelty rate,
   max nesting depth, total crashes. (Grammar breadth is the renamed
   "coverage" — see [§9 lesson 3](#9-key-turning-points-and-lessons).)
5. **Refine** — feed the summary + the strategy back to the LLM with
   focused prompts ("you haven't tried unicode yet," "push nesting
   deeper," etc.).

Strategies that pass validation are saved to
`agent/strategies/accepted/run_<NN>/`, one file per iteration.

### 6.5 Triage

When the loop reports crashes:

```bash
# Deduplicate by normalized signature, drop duplicates and noise
python -m triage.dedupe --input logs/run_<NN>.jsonl

# Minimize one crash to its smallest reproducer
python -m triage.minimize --signature <sig>

# Verify the minimized input really does still crash
python -m triage.verify --input triage/reports/run_<NN>/<sig>.toml
```

Verified, minimized reproducers are archived under
`triage/reports/run_<NN>/` — this folder is **not** gitignored because
it is the deliverable evidence the report points at.

### 6.6 Compare providers

```bash
# Override the provider on the command line
python -m agent.loop --provider gemini --model gemini-3.6-flash
python -m agent.loop --provider groq   --model llama-3.3-70b-versatile
python -m agent.loop --provider ollama --model qwen2.5-coder:7b
```

Historical comparison runs live in [`comparison/`](comparison/).

### 6.7 Run history

Every run appends one row to `logs/RUN_HISTORY.jsonl` (and a matching
markdown table at `logs/RUN_HISTORY.md`). These are permanent and
git-tracked.

---

## 7. Findings — what the loop actually found

Six distinct bugs were confirmed during the project. Five are
memory-safety bugs from unbounded recursion; one is a denial-of-service
via O(n²) growth.

| # | Bug | Trigger shape | Mechanism | Depth needed | Found by |
|---|---|---|---|---|---|
| 1 | Array nesting overflow | `[[[[…]]]]` | Every `[` adds a recursive call into `parse_array`, no limit | ~48,000 | Manual (Module-1) |
| 2 | Dotted-key overflow | `a.a.a.…k = 1` | `parse_keyval` recurses on itself once per dot, no inline-key guard | ~90,000–105,000 | Manual (Module-7b), then loop |
| 3 | Inline-table overflow | `{ a = { a = { … } } }` | Inline tables and key-values call each other recursively | ~80,000 | Loop |
| 4 | Many-siblings slowdown | 15,000+ sibling keys under one table | Adding a key does a full linear scan → O(n²) | 15,000+ keys | Manual reading of `toml.c`, then loop confirmed |
| 5 | Alternating array/inline-table overflow | `[{a=[{a=[…]}]}]` | A third recursive cycle between arrays and inline tables | ~40,000–80,000 | Loop |
| 6 | Quoted-key dotted-key chain overflow | `"k".a.a.a.…k = 1` | Same mechanism as #2 but reached through a quoted first segment, which Bug 2's signature filter missed | ~90,000 | Loop (Run 48, signature `f3095340ceab`) |

**Honest count, not raw count.** A naive crash-detection tool
initially reported 9 distinct signatures. Reading the actual crashing
files by hand showed 3 of those 9 were really Bug 5 captured at
different random points mid-crash (the backtrace is unstable when the
stack has been half-overflowed). Real bug count after triage: **6**,
not 9.

**Common root cause.** 5 of 6 bugs share the same underlying defect:
nothing in `tomlc99` puts a bound on attacker-controlled input size or
nesting depth. The library does guard table-header paths (`[a.b.c]`)
to a maximum of 10 segments — but inline paths, array nesting, and
inline-table nesting have no equivalent check. Bug 4 (the slowdown)
is a separate algorithmic class — O(n²) growth from a linear scan on
every key insertion.

---

## 8. Grammar divergences (grammar vs. reality)

After checking the pinned `tomlc99` build against a checklist of TOML
edge cases, **5 real differences** between the ANTLR grammar and the
library were found. Documented in full in [`grammar/adaptations.md`](grammar/adaptations.md).

| # | Class | Divergence | Evidence |
|---|---|---|---|
| 1 | Superset (library is more permissive than grammar) | `tomlc99` silently allows a trailing comma in inline tables (`{ a=1, b=2, }`); grammar forbids it. | Probed by hand against the harness. |
| 2 | Variant (library truncates, doesn't reject) | Extremely precise fractional timestamps get silently truncated to one nanosecond. | Probed; exact cutoff documented in `adaptations.md`. |
| 3 | Variant (library silently changes type) | An integer one bigger than the max allowed size gets silently turned into a float instead of being rejected. | Probed; library accepts `9999999999999999999` as a float. |
| 4 | Variant (two-step check mismatch) | A number like `007` passes the first parse step but fails later when read as an integer. Two checks, not one. | Probed; behaviour differs between `toml_parse` and the type-coercion step. |
| 5 | Memory-safety bug (not a grammar divergence) | Deeply nested arrays (`[[[[…]]]]`) have no depth limit; crashes at ~48,000 levels. | Carried into Bug 1 above. |

These matter because if the LLM generates TOML that exercises a
divergence, the loop will read the library's behaviour as "weird" and
feed that signal back. Divergences 1–4 are known-OK; divergence 5
became Bug 1.

---

## 9. Key turning points and lessons

Eight lessons that actually shaped the design, roughly chronological:

### Lesson 1 — Small local models hallucinate; big remote models make ordinary mistakes

The 7B Ollama model invented fake Hypothesis library functions and
kept doing it even after correction. The 70B Groq model's mistakes
were ordinary programming bugs (forgetting to unwrap, type mismatches)
fixable with one clear prompt rule. Bigger models don't just do "a bit
better" — they fail in a completely *different*, and much more
fixable, way. This is why we moved off local models entirely.

### Lesson 2 — An example number in a prompt becomes a hard rule, not a suggestion

We taught the LLM a technique for extreme depth using one example
number. Depth jumped from ~4 to 5,000 immediately — but then froze
at *exactly* that example's number, even while later feedback was
explicitly asking for something bigger. The model treated the
illustration as a ceiling. This pattern repeated with a different
axis later (Case 13), confirming it's a general effect, not a one-off.

**Whenever you give the LLM a concrete number in a prompt, expect it
to anchor to that number.** If you want it to push beyond, change the
number on each iteration.

### Lesson 3 — Renamed "coverage" to "grammar breadth" everywhere

The word "coverage" is ambiguous. The assignment explicitly forbids
*code* coverage of the target library, but our own metric (which only
reads the generator's own output text) had been using that word for
years in this project. A reader skimming the docs could mistake our
allowed technique for the forbidden one. Renamed across code, logs,
and docs. See [`OBSERVATIONS.md`](OBSERVATIONS.md#case-13) for the
incident that triggered the rename.

### Lesson 4 — Hint-free runs can find some bugs on their own, but plateau

We tried deleting the very specific hand-written rules that named
which TOML shapes to target (dotted keys, many siblings) and just
gave the LLM general guidance instead. Result: it reinvented the core
trick on its own, but only found 3 of 6 bugs — the very specific
shapes (dotted keys, many siblings) never came up unless directly
named. Hint-free runs live on the `module-7c` and `module-7d` branches
as documented experiments; the main branch keeps the hardcoded rules
on because they're the only configuration that reliably finds all 6.

### Lesson 5 — The loop never actually learned from its own crashes (a real plumbing bug)

A variable meant to track "which crash signatures have we already seen"
was written in the code but never actually filled in — so the LLM was
told "no crashes found yet" even in iterations where dozens of real
crashes had already happened. Fixed and tested; genuinely improved
results in one run, then made another run *worse* in an unexpected way
(a "stop pushing depth" safety feature kicked in too early after
finding one easy bug). Net result across all trials: still didn't
beat the version with hardcoded rules, so it was kept as a documented
experiment but not merged into the main report branch.

### Lesson 6 — The real root cause behind why hint-free runs kept stalling (the most important recent finding)

Our own measurement tool for "how deep did this get" only counted
brackets (`[`, `{`). A dotted-key chain like `a.a.a.…k` has no
brackets at all — so even when the generator accidentally produced a
90,000-dot crashing input, our own feedback signal reported its depth
as **zero**, and told the LLM to try something else entirely. The bug
wasn't that the LLM couldn't find these crashes — it's that our own
instrument was blind to them.

Fix: identify every place in the grammar that can grow without bound
(not just nesting, but dot-chain length and sibling-key count) and
track all three separately. Validated against old logged data (Case
13) and a fresh live run (Run 50, Phase 1) — see [`OBSERVATIONS.md`](OBSERVATIONS.md#case-16-run-48) for the live confirmation.

### Lesson 7 — The O(n²) bug was found twice, independently

Bug 4 (the many-siblings slowdown) was found by reading `tomlc99`'s
source code and confirming with a timing test, *and* later by the
agentic loop finding it completely on its own in a real run. Two
independent paths to the same bug is strong evidence the conclusion is
correct, even when one of the paths is the loop.

### Lesson 8 — Provider comparison matters more for prompt design than for picking a winner

Ran the same loop against Groq, Gemini, OpenAI, and Ollama over many
runs (archived in [`comparison/`](comparison/)). The useful result
wasn't "which model wins" — it's that different model tiers fail in
qualitatively different ways (hallucination vs. ordinary bugs), which
matters more for how you design the prompt than raw model quality
alone.

---

## 10. Gaps and open items

These are honest things that did *not* get finished, or that remain
under-supported, as of the current branch.

### 10.1 The polished 2-page report is not done

`report/report.md` exists but the current polished target is still in
progress. `progress_report.md` is an intentionally-oversized working
draft (everything included, nothing trimmed yet) that needs to be
cut down to the assignment's 2-page limit. This is the single
remaining concrete task.

### 10.2 The scale-axis fix is documented but not yet "the default"

The Case 13 fix (separate counters for bracket-depth, dot-chain length,
and sibling-key count) was validated against old logs *and* one fresh
live run (Run 50, Phase 1). It has not been run enough times to
demonstrate that it beats the hardcoded-rules version on average. It
is the natural next experiment to run.

### 10.3 The 5th grammar divergence is just a bug, not a grammar-vs-reality gap

The "5 divergences" framing originally described 5 grammar-vs-library
disagreements, but divergence #5 (array nesting) is actually a
memory-safety bug, not a grammar divergence (the grammar doesn't bound
depth either). The number is correct; the framing is slightly loose.
Future revision of `grammar/adaptations.md` should reclassify #5 as
"carried into Bug 1."

### 10.4 Provider comparison is partial

Only Groq, Gemini, OpenAI, and Ollama have been run. The original
plan mentioned a frontier-tier Claude comparison; that branch
(`comparison/claude/`) exists but is sparsely populated.

### 10.5 Hypothesis's recursive strategy budget is the hard ceiling

No matter how the LLM tries to "really recurse," the recursive
Hypothesis combinator plateaus around 13 levels. This is a limitation
of how Hypothesis manages its own test-generation budget, not a
prompting problem. Bugs above ~13 levels of *generator* depth can only
be reached via the "draw a number, repeat a string that many times"
trick — the C parser recurses far deeper than the Python generator
ever does.

### 10.6 The crash-signatures normalization is fragile against very deep stacks

Past ~120,000 levels, ASan cannot unwind a clean backtrace and the
signature collapses to the frameless "unparsed" bucket. This is why
the hand-written reproducers in `grammar/early_findings/` are
deliberately capped below this threshold — past it, distinct bugs
become indistinguishable.

### 10.7 The 7B model failures are documented but not addressed

The Ollama 7B model's inability to generate any working strategy is
documented in [`comparison/ollama/`](comparison/ollama/), but we did
not investigate whether better prompting, fine-tuning, or a different
small model would have closed the gap. This was outside the time
budget for the project.

### 10.8 No timeout-as-crash tuning was done

The assignment says timeouts count as crashes. The harness emits exit
code 124 on timeout, which triage treats correctly, but no special
"this is a timeout not a crash" tag is propagated to the LLM summary.
This is unlikely to matter for the bugs found so far (all of them
were sanitizer or signal kills, not timeouts) but should be fixed
before any meaningful DoS-class bug analysis.

---

## 11. Where to look for more detail

| Want to understand… | Read |
|---|---|
| The full agentic loop in detail | [`agent/README.md`](agent/README.md) |
| The exit-code contract and sanitizer setup | [`harness/README.md`](harness/README.md) |
| The baseline (dumb) generators | [`pipeline/README.md`](pipeline/README.md) |
| Crash deduplication, normalization, minimization | [`triage/README.md`](triage/README.md) |
| Provider comparison (Groq vs Gemini vs OpenAI vs Ollama) | [`comparison/README.md`](comparison/README.md) |
| Every interesting moment in the project's history | [`OBSERVATIONS.md`](OBSERVATIONS.md) (17 documented cases) |
| The structured status-by-deliverable view | [`PROJECT_SUMMARY.md`](PROJECT_SUMMARY.md) |
| A plain-language walkthrough of how we got here | [`progress_till_now_2026-08-30.md`](progress_till_now_2026-08-30.md) |
| Every run that ever happened | `logs/RUN_HISTORY.{jsonl,md}` |
| The original brief | [`assignment_agentic_fuzzing.md`](assignment_agentic_fuzzing.md) |
| The hand-found crash reproducers | [`grammar/early_findings/`](grammar/early_findings/) |
| The pinned tomlc99 commit we are fuzzing | [`grammar/PINNED_COMMIT.txt`](grammar/PINNED_COMMIT.txt) |

---

*Built as a class project — LLM-driven grammar fuzzing without code coverage. The 6 bugs found live in `triage/reports/`, the full per-run evidence is in `logs/RUN_HISTORY.{jsonl,md}`, and every design decision is traceable through `OBSERVATIONS.md`.*
