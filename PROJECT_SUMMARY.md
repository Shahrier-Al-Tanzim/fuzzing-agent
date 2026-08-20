# Project Summary — LLM-Driven Grammar Fuzzer for tomlc99

Comprehensive internal summary of the project as it stands, consolidating
everything verified across design docs, real run data, and code — not
the polished 2-page assignment report (`report/report.md`, still empty),
but the source material that report should be built from.

---

## 1. What this project is

An agentic fuzzer that turns a formal ANTLR grammar for TOML into a
self-improving Hypothesis test-input generator, targeting `tomlc99` (a C
TOML parser), refined over up to 5 iterations of LLM-driven feedback,
with no code-coverage instrumentation available (blackbox constraint).

- **Target:** `tomlc99`, pinned commit `5221b3d3d66c25a1dc6f0372b4f824f1202fe398`.
- **LLM:** Groq-hosted `llama-3.3-70b-versatile` (config: `llm.provider: groq`).
  Originally local Ollama `qwen2.5-coder:7b` — switched after the 7B model
  hit a real reliability ceiling (`OBSERVATIONS.md` Case 1).
- **Structure:** 8 modules, one git branch per module. Currently on
  `module-7-report`.

---

## 2. Step-by-step status against the assignment

| Step | Deliverable | Status | Key files |
|---|---|---|---|
| 1 | Grammar + adaptations | ✅ Done | `grammar/TomlLexer.g4`, `grammar/TomlParser.g4`, `grammar/adaptations.md` |
| 2 | Harness + sanitizer build | ✅ Done | `harness/toml_harness.c`, `harness/build.sh` |
| 3 | Baseline strategy + pipeline demo | ✅ Done | `pipeline/baseline_strategy.py`, `pipeline/run_baseline.py` |
| 4 | Agentic loop + final generator + iteration log | ✅ Done | `agent/loop.py`, `agent/strategies/accepted/`, `logs/RUN_HISTORY.md` |
| 5 | Deduplicated crash reports (or documented "none found") | ⚠️ Partial — see §5 | `triage/reports/939402a0547c/`, `triage/reports/e857b4530c96/` |
| 6 | Two-page written report | ❌ Not started | `report/report.md` is 0 bytes |

---

## 3. Step 1 — Grammar and real divergences found

Source: ANTLR `grammars-v4` TOML grammar (`TomlLexer.g4` + `TomlParser.g4`),
describes TOML v1.0.0. Probed by hand against the pinned build across an
8-9 point checklist (`planning/planning-1-grammar-adaptation.md`); 5
came back as real divergences, 4 came back conformant.

| # | Construct | Class | What actually happens |
|---|---|---|---|
| 1 | Trailing comma in inline table `{ a=1, b=2, }` | superset | Grammar forbids it; `tomlc99` accepts it silently |
| 2 | 19-digit fractional seconds | variant | Accepted, but silently truncated to 3-digit precision, no warning |
| 3 | Integer one past `INT64_MAX` | variant | Accepted, but silently relabeled as a `float` |
| 4 | Leading-zero integer `007` | variant | First-stage parse lets it through; a *later*, separate typed-accessor call rejects it — revealed `toml_parse()` succeeding ≠ value usable |
| 5 | Array nesting `[[[[...]]]]` | crash, not divergence | **SIGSEGV** at ~48,000 levels deep — no depth guard, one native stack frame per nesting level. **The one confirmed bug in this project.** |

Full detail, evidence, and reasoning: `grammar/adaptations.md`.

---

## 4. Step 2/3 — Harness and baseline (plumbing correctness)

- `harness/toml_harness.c` compiled with `-fsanitize=address,undefined`.
  Exit-code contract: `0`=accept, `2`=well-formed reject, `64`=harness's
  own misuse (never a library finding), `86`=sanitizer catch, negative
  return code = fatal signal.
- Classification order in `pipeline/runner.py` is deliberate: timeout →
  sanitizer text (checked *before* exit code, since it's authoritative
  regardless of how the process died) → fatal signal → exit code.
- Baseline (`pipeline/baseline_strategy.py`) ran 9,050 deliberately naive
  examples (random text / TOML-ish text / key-value lines) purely to
  prove the pipeline itself works. Zero crashes expected and found here
  — this step is not about finding bugs.

---

## 5. Step 4 — The agentic loop, as actually run

### Structure
`agent/loop.py`: Seed (iteration 0, grammar + adaptations only) → Validate
(`agent/validator.py`, 25-sample draw check + 40-example acceptance-floor
probe at 20%) → Run (500 real examples via `@given`/`@settings`) →
Summarize (`agent/summarize.py`) → Refine (feedback prompt back to LLM) →
repeat up to 5 iterations or the cost/time cap, whichever hits first.

### The proxy signal (no code coverage available)
Computed entirely externally, by reading generated text with regex —
never touching `tomlc99`'s internals:
- **Grammar breadth** — fraction of 30 tracked productions
  (`pipeline/features.py`'s `PRODUCTIONS`, named 1:1 to the `.g4` rules)
  seen across all accepted documents so far (`agent/breadth.py`).
- **Acceptance rate**, **novelty rate** (shape not seen before), **max
  nesting depth reached**, **top rejection reasons**.

### Most recent full run (Run 4/5, 2026-08-16)

| Iter | Accepted | Breadth | Novelty | Max depth | Findings |
|---|---|---|---|---|---|
| 0 | 39% | 55% | 35% | 3 | 0 |
| 1 | 40% | 68% | 22% | 3 | 0 |
| 2 | 35% | 84% | 21% | 3 | 0 |
| 3 | — | — | — | — | **crashed the Python process itself, see §7** |

### Prompt-rule fix log (all confirmed on real runs, see `OBSERVATIONS.md`)
`agent/prompts.py`'s `STRATEGY_CONTRACT` now has 13 numbered rules.
Rules 9-13 were each added in direct response to an observed failure:

- **9+10** — banned `.filter()` misuse on `st.text()`; required genuinely
  self-referential containers (not just `@composite` present in source
  with no real recursion happening).
- **11** — banned `st.dates()`/`st.times()`/`st.datetimes()` entirely
  (kept hallucinating non-existent call signatures).
- **12** — top-level document lines must be `key=value`/`[table]`/
  `[[array_table]]` only, never a bare container (was causing
  acceptance collapse to 2-5%).
- **13** — table/array-table headers must reuse `key()`, never raw
  `st.text()` (was generating unquoted non-ASCII headers, invalid TOML).

### The dead `current_depth` counter finding
A real, documented bug in an earlier generated strategy: `array()` had a
`max_depth=12` safety cap that was never actually enforced, because
`current_depth` was never incremented on the recursive call. Depth
plateaued low anyway — not because of the (non-functional) cap, but
because of Hypothesis's natural bias toward short/empty lists combined
with an unweighted `one_of()`. This is the same underlying mechanism
still limiting depth today.

---

## 6. Step 4 continued — the honest gap: loop success ≠ crash discovery

**Confirmed directly against the data:** all 2,500+ examples across
`pipeline/logs/iteration_00.jsonl`–`iteration_04.jsonl` are `accept` or
`reject`. Zero `crash`, zero `timeout`. The loop's own metrics (breadth,
acceptance, novelty) genuinely improve run over run — the machinery
works exactly as designed — but it has never found a crash on its own.

**Root cause, precisely identified:**
1. `render_feedback()`'s depth directive only ever asks for **12+**
   (`agent/summarize.py`). The known bug needs **~48,000**. A ~4,000x
   gap a linear "try a bit harder" directive cannot close.
2. `array()`'s `st.one_of(value(), array(), inline_table())` gives
   recursion no special weighting — roughly 1-in-3 odds at every level,
   with nothing pushing harder once depth plateaus.
3. `config.yaml`'s own `features.depth_buckets` tops out at `64`, with an
   explicit comment acknowledging the real bug needs "~48k" — the
   tracked signal itself was never designed to reach into that range.

**Is "none found" an acceptable deliverable here?** Technically yes —
the assignment's checklist explicitly allows it, and Step 5's own wording
anticipates this exact case ("if none were found, a documented
explanation of why, and what you'd try next"). But it's the weaker
outcome, not the strong one: the assignment's own calibration note says a
trial run on a different library (parson/JSON) went from 0 crashes to
finding crashes reliably within 5 iterations, and Step 4.5 explicitly
names "deepening recursion where it hasn't crashed yet" as exactly the
kind of refinement expected. This is squarely still-in-scope work, not
a shortfall to write around.

**Other plausible crash categories not yet explored at all** (not just
depth): Divergence #3 (silent int→float retyping) and #4 (leading-zero
integers breaking a *later*, separate conversion function) both hint at
shaky type-handling in `tomlc99`'s typed accessors (`toml_rtoi`,
`toml_rtod`, etc.) — a different, unexplored crash surface from deep
recursion, and possibly more findable at normal, moderate input sizes.

---

## 7. A real tooling bug found and fixed mid-project (2026-08-16)

During Run 4, iteration 3 crashed the *Python fuzzing process itself*
(not `tomlc99`) — `ValueError: Unknown format code 'd' for object of
type 'str'`, from `agent/strategies/iter_03_strategy.py:63`:
```python
st.text(min_size=1, max_size=10).map(lambda x: f"{x:07d}"),
```
The LLM tried to generate a leading-zero integer (echoing Divergence #4)
but applied an integer format spec to a string. Validation's 25-sample
draw check missed it by chance (~30 branches in `value()`'s `one_of()`,
too few draws to guarantee hitting the broken one). **This bug in the
LLM-generated code itself has not been fixed** — no new `STRATEGY_CONTRACT`
rule has been added to prevent it recurring (deferred, still open).

Separately, a real bug was found **and fixed** in the tooling: `--resume`
was opening a new "Run N" section in `logs/RUN_HISTORY.md` instead of
continuing the interrupted one, because `run_id` and the resumable
`state.json` were two disconnected systems. Fixed by adding
`LoopState.run_id` (`agent/breadth.py`) and making `agent/loop.py` reuse
it on `--resume` instead of always minting a new number; `agent/run_history.py`'s
`regenerate_markdown()` updated to use the latest `run_complete` record
per run_id, since a resumed run can now log more than one.

---

## 8. Step 5 — Crash triage, as actually implemented

Pipeline: Detect (`pipeline/runner.py`, fatal signal / sanitizer text /
timeout) → Capture (input + stderr + signal, in `pipeline/logs/*.jsonl`)
→ Deduplicate (`triage/signature.py`, SHA-256 hash of normalized top-5
stack frames, recursion-collapsed) → Minimize (`triage/minimize.py`,
delta-debugging) → Verify (`triage/verify.py`, 3 repeat runs).

**Both existing reports trace to the one hand-found crash**
(`grammar/early_findings/01_array_nesting_stackoverflow.toml`), fed in
via `triage/run_triage.py --extra`, not discovered by the automated loop:

- `triage/reports/939402a0547c/` — clean signature (`stack-overflow@malloc`,
  5 parsed frames), verified deterministic (3/3 runs, matching signature).
- `triage/reports/e857b4530c96/` — same underlying bug, but the sanitizer
  output didn't parse into any frames at all (too deep an overflow to
  print a clean backtrace); verified as crashing 3/3 runs but with an
  "unstable signature" (0/3 frame-matches) — a real, documented
  verification-outcome category, not a bug in the triage code.

`triage/run_triage.py`'s input source is **not hardcoded** — it globs
whatever is in the configured logs directory; only the `--extra` default
filename is fixed (CLI-overridable).

---

## 9. Deliverables checklist — real status

- [x] Grammar source + noted adaptations
- [x] Build script + harness source
- [x] Baseline strategy + pipeline demonstration
- [x] Agentic loop implementation + final generator + iteration log
- [~] Deduplicated, minimized crash reports (real, but from the hand-found
      crash, not the loop — "none found by the loop" is honestly the
      current state, and is documented)
- [ ] Two-page written report — not started, `report/report.md` empty

---

## 10. What's next, in priority order

1. **Attempt an actual loop-found crash before writing the report** —
   the highest-value remaining work. Concretely: bias `array()`'s
   `one_of()` toward recursion once depth plateaus (e.g. weighted choice,
   or a `min_size` push on the recursive branch), and/or change
   `render_feedback()`'s depth directive from linear ("aim for 12+") to
   exponential/escalating. This is genuinely still in scope per Step 4.5,
   not a detour.
2. **Fix the still-open `:07d`-on-`st.text()` bug class** — add a rule 14
   to `STRATEGY_CONTRACT` banning integer format specs on non-integer
   strategies, mirroring the rule 9-13 pattern.
3. **Write `report/report.md`** — Design / Findings / Challenges, 2 pages.
   Nearly every sentence it needs already exists in this file,
   `OBSERVATIONS.md`, and `grammar/adaptations.md` — assembly, not new
   research.
4. Consider probing Divergences #3/#4 (type-confusion territory) as a
   second, independent crash-hunting angle alongside depth.

---

## 11. Where the deeper detail lives, if this summary isn't enough

- `OBSERVATIONS.md` — full case-by-case history of every real failure
  hit and fixed, with before/after evidence.
- `planning/how/what_is_done.md` — technical file-by-file mapping of
  every grading criterion and every "how does X actually work" question
  answered so far.
- `planning/later/` — explanations parked for a second pass
  (`runner_workflow.md`, `step4_agentic_loop.md`, `25_vs_500_examples.md`).
- `info.md` — plain-language glossary (gitignored, personal use).
- `logs/RUN_HISTORY.md` — permanent, per-attempt/iteration/run record.
