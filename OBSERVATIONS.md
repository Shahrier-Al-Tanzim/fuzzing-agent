# Observations Log

Running log of notable challenges, failures, and judgment calls made across
the project. Each entry is a self-contained case: what was tried, what
happened, and what was concluded. New cases are appended below as the
project continues — this is not a single narrative, and later cases are not
assumed to relate to earlier ones unless stated.

---

## Case 1: 7B model reliability in Module 4 (agentic seed generation)

**Date:** 2026-08-13
**Model:** `qwen2.5-coder:7b`, served locally via Ollama (WSL2 → Windows host)
**Command under test:** `python -m agent.seed --iteration 0`
**Task:** Generate a Hypothesis strategy for TOML documents from the ANTLR grammar, validated through six automated gates (extract → syntax → imports → exec/export → draw → parser-acceptance probe).

This case records, in order, every attempt made to get a working generator out of the 7B model, the exact errors produced, the fixes applied between rounds, and why the process was ultimately halted rather than continued indefinitely.

### TL;DR

- **Did the task complete? No.** Across 3 full rounds (12 individual LLM generation attempts total), **zero** attempts produced a strategy that passed all six validation gates. `agent/strategies/iter_00_strategy.py` — the actual deliverable of this step — does not exist.
- **Did the pipeline work? Yes, completely.** The six-gate validator caught a real, code-breaking bug in every single one of the 12 attempts, before any of them were trusted. Nothing broken ever slipped through. The retry-with-quoted-feedback loop, transcript logging, and rejected-candidate storage all functioned exactly as designed.
- **Two distinct failure categories emerged**, and they behaved very differently when corrected:
  - **Instruction-following failures** (forgetting an explicitly-permitted import, forgetting to call a decorated function) — **fully fixed** by adding one concrete worked example to the prompt. Zero recurrence after the fix.
  - **API-knowledge / hallucination failures** (inventing function arguments and operators that don't exist in Hypothesis) — **not fixed** by adding explicit "never do X, do Y instead" rules that quoted the model's own prior errors back to it verbatim. The model repeated two of the three explicitly-forbidden patterns anyway, and produced a brand-new hallucination not covered by any rule.
- That second result is the point at which this was stopped and escalated, rather than patched a third time. See [Why this was stopped here](#why-this-was-stopped-here-rather-than-patched-again).

---

### Round 1 — no prompt fixes yet (baseline behavior)

Command: `python -m agent.seed --iteration 0`, before any changes to `agent/prompts.py`.

| Attempt | Gate failed | Error | What actually went wrong |
|---|---|---|---|
| 1 | `syntax` | `f-string: single '}' is not allowed` | Model wrote malformed Python — a raw syntax mistake, unrelated to Hypothesis specifically. |
| 2 | `export` | `toml_strategy is function, not a SearchStrategy` | Model used `@composite` correctly, but wrote `toml_strategy = my_doc` instead of `toml_strategy = my_doc()` — never called the decorated function. |
| 3 | `exec` | `NameError: name 'composite' is not defined` | Model used `@composite` as a decorator but never wrote `from hypothesis.strategies import composite` — even though that exact import line was explicitly listed as one of only two permitted imports in the prompt's contract. |
| 4 | `exec` | `NameError: name 'composite' is not defined` (identical to attempt 3) | The retry prompt quoted this exact `NameError` back to the model. The model did not connect "this name is undefined" to "add the import for it," and repeated the identical mistake. |

**Round 1 totals:** 4/4 attempts failed · 17,113 tokens · 198.2 s · $0.00

**Diagnosis at this point:** the recurring failure (attempts 3–4) was an instruction-following problem — the model wasn't reliably retaining or applying a rule stated once, ~13,600 characters earlier in the prompt, even when the exact resulting error was quoted directly back to it on retry.

---

### Fix #1 — a concrete worked example for `@composite`

Applied to `agent/prompts.py`, `STRATEGY_CONTRACT`, new rule 6:

```python
6. If you use @composite, MUST import it and MUST call the function.
   Example (correct):
   ```python
   from hypothesis import strategies as st
   from hypothesis.strategies import composite

   @composite
   def my_strategy(draw):
       return draw(st.text())

   toml_strategy = my_strategy()  # Call it to get the strategy object
   ```
```

**Rationale:** a small model is generally more reliable at copying a shown, complete, correct pattern than at deriving the same pattern from a written rule stated in isolation. This targets the exact failure class seen in attempts 2–4 of Round 1.

---

### Round 2 — after Fix #1

| Attempt | Gate failed | Error | What actually went wrong |
|---|---|---|---|
| 1 | `draw` | `TypeError: datetimes() got an unexpected keyword argument 'formats'` | Model called `st.datetimes(formats=...)`. That parameter does not exist anywhere in Hypothesis's real API — a fabricated argument. |
| 2 | `exec` | `TypeError: unsupported operand type(s) for +: 'LazyStrategy' and 'LazyStrategy'` | Model tried to combine two Hypothesis strategies with the `+` operator. Strategies do not support addition; combining requires `st.one_of(...)` or `\|`. |
| 3 | `draw` | `TypeError: datetimes() got an unexpected keyword argument 'formats'` (identical to attempt 1) | Same fabricated `datetimes(formats=...)` call, independently generated. |
| 4 | `draw` | `TypeError: <lambda>() takes 0 positional arguments but 1 was given` | A `.map(lambda: ...)` callback was written to take zero arguments, but Hypothesis always calls `.map()` callbacks with exactly one argument — the drawn value. |

**Round 2 totals:** 4/4 attempts failed · 17,320 tokens · 215.9 s · $0.00

**What Fix #1 actually achieved:** it worked completely. **Zero** `export`/`NameError`/composite-related failures occurred anywhere in this round — the exact class of bug Fix #1 targeted did not recur even once across all 4 attempts. What surfaced instead was a different, previously-hidden category of bug: the earlier `exec`-stage `NameError` had been masking these later `draw`-stage failures, because validation stops at the first gate a candidate fails.

**Diagnosis at this point:** three distinct fabricated/incorrect uses of the real Hypothesis API, one of them (`datetimes(formats=...)`) independently generated twice from two separate model calls — suggesting a persistent, specific wrong "belief" this model holds about that function, not a one-off random slip.

---

### Fix #2 — explicit negative examples for the exact observed hallucinations

Applied to `agent/prompts.py`, `STRATEGY_CONTRACT`, new rule 7, quoting the precise errors from Round 2 and giving a correct alternative for each:

```python
7. Common mistakes to avoid - these are REAL ERRORS from previous attempts:
   - `st.datetimes()` takes NO `formats` argument. It does not exist. If you
     need a date/time string, build it yourself, e.g.:
       st.tuples(st.integers(1970, 2100), st.integers(1, 12), st.integers(1, 28))
           .map(lambda t: f"{t[0]:04d}-{t[1]:02d}-{t[2]:02d}")
   - NEVER combine strategies with `+`. Strategies do not support addition.
     To pick one of several strategies use `st.one_of(a, b, c)` or `a | b | c`.
     To join strings use `.map(lambda parts: "".join(parts))`, not `part1 + part2`.
   - Every `.map(fn)` callback receives exactly ONE argument: the value drawn
     from the strategy it is called on. `st.tuples(a, b).map(lambda x: ...)`
     receives ONE tuple `x`, not two separate arguments. Do not write
     `.map(lambda a, b: ...)` on a single strategy - unpack inside instead:
     `.map(lambda pair: f"{pair[0]}={pair[1]}")`.
```

Note: an implementation bug was caught and corrected before this reached the model — the first draft accidentally double-escaped the curly braces (`{{t[0]:04d}}`), which would have rendered as literally invalid Python inside the model's own prompt. This was verified by printing the rendered prompt text before re-running, and fixed to single braces.

**Rationale:** identical in spirit to Fix #1 — replace an abstract rule with a concrete, correct, copy-able alternative — but this time also stating the forbidden pattern explicitly ("NEVER combine strategies with `+`"), which is a stronger and more direct instruction than Fix #1 required.

---

### Round 3 — after Fix #2

| Attempt | Gate failed | Error | Relationship to Fix #2's explicit rules |
|---|---|---|---|
| 1 | `draw` | `TypeError: datetimes() got an unexpected keyword argument 'formats'` | **Directly contradicts an explicit rule** stating this exact argument does not exist. |
| 2 | `draw` | `TypeError: unsupported operand type(s) for +: 'LazyStrategy' and 'JustStrategy'` | **Directly contradicts an explicit rule** stating "NEVER combine strategies with `+`." |
| 3 | `draw` | `AttributeError: module 'hypothesis.strategies' has no attribute 'empty_strings'` | **New hallucination, not covered by any existing rule.** `st.empty_strings` does not exist in Hypothesis's API at all. |
| 4 | `draw` | `TypeError: datetimes() got an unexpected keyword argument 'formats'` (identical to attempt 1) | Same forbidden pattern, a third independent occurrence across two rounds. |

**Round 3 totals:** 4/4 attempts failed · 18,156 tokens · 179.4 s · $0.00

---

### Cumulative totals across all 3 rounds

| Metric | Value |
|---|---|
| Total generation attempts | 12 |
| Attempts that produced a valid strategy | **0** |
| Total tokens consumed | 52,589 |
| Total wall-clock generation time | 593.5 s (≈ 9.9 minutes) |
| Total cost | $0.00 (local model) |
| Distinct root-cause bugs observed | 7 (syntax error, forgot-to-call-composite, forgot composite import ×2, fabricated `datetimes(formats=...)` ×3, invalid `+` operator ×2, `.map()` lambda arity, fabricated `st.empty_strings`) |

---

### Why this was stopped here rather than patched again

Fix #1 and Fix #2 used the same technique — replace an abstract rule with a concrete, correct example — but had opposite outcomes:

- **Fix #1 fully worked.** The composite-import/export failure class had **zero** recurrences in the very next round (Round 2), across all 4 attempts.
- **Fix #2 did not work.** Two of the three explicitly-forbidden patterns it targeted **recurred anyway** in the very next round (Round 3) — including one case where the model was told, in the same prompt, in plain language, "NEVER combine strategies with `+`," and used `+` to combine strategies regardless. A fourth, entirely new hallucination (`st.empty_strings`) also appeared, which no rule had anticipated.

This is the meaningful distinction:

| | Fix #1 (composite import) | Fix #2 (datetimes/`+`/map arity) |
|---|---|---|
| Failure type | Forgetting a rule stated once, far away in a long prompt | Confidently using fabricated library API that doesn't exist |
| Fixed by a worked example? | Yes — completely | No — recurred despite explicit prohibition |
| Recurrence after fix | 0 / 4 attempts | 2 / 4 attempts repeated forbidden patterns, plus 1 new unrelated hallucination |

The first category (instruction-following) responded to prompt engineering exactly as expected. The second category (API hallucination) did not respond to the same technique even when the instruction was as explicit and direct as language allows ("NEVER do X"). Continuing to patch each newly-observed hallucination one at a time is not a converging process — Round 3 itself produced a hallucination (`empty_strings`) that no prior round had seen, demonstrating the space of possible fabricated API calls is not being exhausted by reacting to whichever one appeared most recently.

---

### What this suggests, and the planned next step

This pattern — reliable correction of instruction-following mistakes, but unreliable correction of confident API fabrication, even under direct and explicit prohibition — is consistent with a known, well-documented capability gap between smaller and larger language models, rather than a prompt-wording problem. It is not evidence that the 7B model is unusable in general; it is evidence that this specific failure mode (accurate recall of a third-party library's real function signatures under strict formatting constraints) is where it is currently hitting a ceiling.

**Next step (not yet attempted):** test whether a larger *still-local, still-free* model (`qwen2.5-coder:14b` via Ollama) resolves this before considering a paid API. This isolates whether the issue is model scale/capability versus something else, at zero cost, before spending anything on an external API key.

---

## Case 2: Groq / Llama-3.3-70B vs. the qwen 7B model — did switching actually help?

**Date:** 2026-08-13
**Model:** `llama-3.3-70b-versatile`, served remotely via Groq's free tier (`agent/groq_client.py`)
**Why this was tried:** Case 1 concluded that qwen2.5-coder:7b was hitting a real capability ceiling on API-hallucination, not something two rounds of prompt fixes could close. A 14B local model wasn't practical on 6GB of VRAM (see the VRAM/CPU-offload math discussed separately), so a free remote API was tested instead, without spending anything, before considering a paid one.

### TL;DR

- **Yes, switching helped — measurably, not just anecdotally.** Across 7 separate runs (22 total attempts) against Groq, **3 runs produced a fully passing strategy** (all six gates, 27.5–40% real-parser acceptance). Across every tested qwen run in Case 1, **zero** ever passed.
- **But it is not hallucination-free.** Llama-70B has its own specific, recurring wrong belief — `st.dates(min_date=...)` — that showed up **three separate times across three different rounds** and was never fixed, the same pattern Case 1 documented for qwen's `datetimes(formats=...)`. The honest conclusion is "meaningfully more reliable," not "immune to this failure class."
- **The failure mix changed shape, and that shape is what actually explains the improvement.** qwen's failures were dominated by fabricated library API (functions/arguments that don't exist). Llama-70B's failures were dominated by ordinary composition bugs (type mismatches, forgetting `draw()`, mismatched data shapes between functions) — the kind rule 8 (added specifically in response to this) could actually fix, and did.

### All seven runs, in order

| Run | Attempts | Result | What failed |
|---|---|---|---|
| 0 (pre-retry-fix) | 2 completed, then crashed | 0/2, crash | `'list' object has no attribute 'map'`; `can only concatenate str (not "bool") to str`; then an unhandled HTTP 429 killed the process (fixed afterward — see `groq_client.py`'s retry-with-backoff) |
| 1 (post-retry-fix, pre-rule-8) | 4 | 0/4 | All four were `draw`-stage type-consistency bugs: raw `int`/`float` joined as text, a `table()`/`toml()` return-shape mismatch (`'float' object is not subscriptable`), and a forgotten `draw()` before joining (`expected str instance, LazyStrategy found`) |
| 2 (post-rule-8) | 3 | **1/3 PASS** (attempt 3) | Attempts 1-2 failed (`dates(min_date=...)`; a `.map()` returning a raw `list`); attempt 3 passed at **40.0%** acceptance |
| 3 | 4 | 0/4 | Attempts 1, 2, 4 failed the **acceptance floor** (2%, 8%, 18% — all under 20%, all improving); attempt 3 hit a new bug, `'list' object has no attribute 'map'` (the mirror image of forgetting `draw()`: calling a strategy-only method on an already-drawn value) |
| 4 (fresh API key) | 4 | 0/4 | `InvalidArgument: Expected a SearchStrategy but got <function ...>` (an un-called function passed where a strategy was needed); `too many values to unpack`; then two acceptance-floor failures at 2% each |
| 5 | 2 | **1/2 PASS** (attempt 2) | Attempt 1 failed (`Expected date but got min_value='1970-01-01' (type=str)` — right argument name this time, wrong type); attempt 2 passed at **27.5%** acceptance |
| 6 | 3 | **1/3 PASS** (attempt 3) | Attempt 1 failed (`dates(min_date=...)` again); attempt 2 failed the acceptance floor at 0%; attempt 3 passed at **37.5%** acceptance |

**Totals: 22 attempts, 3 passes (13.6% of individual attempts, but 3 of 7 runs — 43% — eventually succeeded within their attempt budget).** Every pass is preserved: the live one at `agent/strategies/iter_00_strategy.py`, and all three archived permanently under `agent/strategies/accepted/` after the auto-archive fix (see the note in `planning-4-agentic-loop.md`).

### The recurring bug that fixes never touched: `st.dates(min_date=...)`

This exact mistake appears in runs 2, 5, and 6 — three separate generations, independently written, all making the identical wrong assumption that `st.dates()` takes a `min_date` argument (it doesn't; the real name is `min_value`). This is structurally identical to what Case 1 documented for qwen's `st.datetimes(formats=...)`: a specific, stable, wrong belief about one function's signature that recurs regardless of how many other things get fixed around it. No rule in `STRATEGY_CONTRACT` currently names `st.dates()` specifically — rules 6-8 were written reactively, each one targeting errors already observed at the time, and this one simply hasn't been covered yet. It never blocked a full run, though: unlike qwen, an attempt hitting this error was always followed by a later attempt in the same run that avoided it (except run 4, where it didn't reappear at all, but other bugs did) — the retry-with-quoted-error loop had somewhere to go on the next attempt, which practically never happened for qwen across 12 tested attempts in Case 1.

### Why it actually works better — categorizing every failure

Grouping all 22 Groq attempts by failure type tells a clearer story than pass/fail alone:

| Category | Count | Example | Fixed by rule 8? |
|---|---|---|---|
| Type-consistency (unstringified numbers, forgotten `draw()`, mismatched return shapes) | 7 | `expected str instance, int found`; `expected str instance, LazyStrategy found` | Yes — all 7 occurred in run 1, before rule 8; **zero recurred after** |
| Wrong-argument mistakes on real functions (`dates(min_date=...)`, wrong type for `min_value`) | 4 | `dates() got an unexpected keyword argument 'min_date'` | No — recurred 3 times after rule 8 was added, never targeted by any rule |
| Function/strategy confusion, mirror-image of the `draw()` bug | 3 | `'list' object has no attribute 'map'`; `Expected a SearchStrategy but got <function ...>` | Partially — related to rule 8's third bullet, but not identical, and one instance (run 3) postdates rule 8 |
| Acceptance-floor (code runs fine, generated TOML too often invalid) | 6 | `only 1/40 (2%) accepted` | Not applicable — gate 6 is a content-quality measure, not a code-correctness bug |
| Fabricated API that doesn't exist at all (qwen's Case 1 pattern) | **0** | — | Never observed with this model, across any of the 22 attempts |

The **zero** in the last row is the real finding, not the pass count by itself. Llama-70B never fabricated a Hypothesis function or argument that simply doesn't exist, in 22 independent attempts across 7 runs. Everything it got wrong was either a real-but-wrong detail on a real function (`dates(min_date=...)`), an ordinary logic/composition mistake, or a content-quality shortfall — all categories that a worked-example prompt fix (rule 8) could and did meaningfully reduce. qwen's failures, by contrast, were dominated by invented API surface that no amount of "here is a correct example" fully suppressed (Case 1's rule 7 result). That is the actual mechanism behind "switching helped" — not that the bigger model is flawless, but that its mistakes are the *kind* prompt engineering can act on.

### Cost and speed, for the report

All 22 Groq attempts combined: free tier, $0.00. Per-attempt latency ranged roughly 1.4s–25s (plus occasional rate-limit backoffs of a few seconds to tens of seconds, all handled automatically) — far faster than qwen's 20–115s per attempt on local CPU/GPU-shared inference. The free tier's actual constraint turned out to be a **daily** token quota, not the per-minute one: one API key was fully exhausted mid-session (a 2,693-second/~45-minute wait was reported), resolved by generating a second free key, after which the same prompt completed normally. Worth noting for the report as a practical limitation of relying on a free tier for repeated testing, separate from the model-quality question this case is actually about.

---

## Case 3: Crash-triage tooling — two real bugs found on first real use, plus a genuine finding about the crash itself

**Date:** 2026-08-14
**Module:** Module 6 (`triage/`), first real run against the known stack-overflow crash from Module 1 (`grammar/early_findings/01_array_nesting_stackoverflow.toml`)

Both bugs below were invisible from reading the code alone — both only surfaced the first time `triage/run_triage.py` was actually run against a real crash and the output was read closely rather than just checked for "did it exit 0."

### Bug 1: a sanitizer-internal frame wasn't filtered out

`triage/signature.py`'s `ignore_frame_patterns` (in `config.yaml`) is supposed to drop any frame that isn't part of the actual library being tested — that's judgment call 2 from the module's design ("bucket on library frames only"). The very first real run put `__sanitizer::BufferedStackTrace::UnwindImpl` — AddressSanitizer's own internal stack-unwinding code, not program code at all — at the top of the signature. The ignore list already covered `__asan`/`__ubsan`-prefixed frames but had no entry for the separate `__sanitizer::` prefix, so this one frame slipped through and pushed the real `parse_array toml.c:1057` frame out of the kept top-5 window entirely.

| | Before fix | After fix |
|---|---|---|
| `short` label | `stack-overflow@__sanitizer::BufferedStackTrace::UnwindImpl` | `stack-overflow@malloc` |
| Top frame kept | sanitizer-internal noise | real library frame |
| `digest` | `38e1a362e477` | `939402a0547c` |

Fixed by adding `"__sanitizer"` to `ignore_frame_patterns`. One line, but it directly restored the judgment call the module's whole design depends on — without it, the fingerprint was describing sanitizer internals, not the library's bug.

### Bug 2: a crash that reproduced 100% of the time was labeled "did not reproduce"

`triage/verify.py`'s `VerifyResult` only named two outcomes: **deterministic** (crashed every run, identical signature every time) and **flaky** (crashed some runs, not others). A third, real outcome showed up in actual data: the minimized reproducer crashed on **all 3** verification runs, but the exact stack signature wasn't identical every time (`crashes == runs` but `signature_matches < runs`). Since the code only recognized two named outcomes, this third one silently fell through `describe()`'s final `else` branch — written under the unstated assumption that "not deterministic, not flaky" could only mean zero crashes — producing the literally false message `"DID NOT REPRODUCE (0/3)"` on an input that crashed 3 times out of 3. `run_triage.py`'s `_render_report()` had an independent, duplicated copy of the same two-outcome logic inline, so the same bug existed in two places at once.

**The fix, and the more important part of it:**
- A real third state, `unstable_signature`, was named and described accurately (`"crashed every run (3/3) but signature unstable (2/3 matched)"`).
- The fallback case was changed from a silent guess to a loud failure: `describe()` now explicitly checks for `crashes == 0` as the true "did not reproduce" case, and anything matching *none* of the four known states raises `AssertionError` with the exact numbers involved, instead of quietly producing another plausible-looking wrong label. The four states are provably exhaustive today (`signature_matches <= crashes <= runs` always, by construction), but that proof depends on an invariant nothing enforces long-term — this way, if it's ever broken by a future change, the failure is immediate and visible instead of being a third silent occurrence of the same mistake.

### The finding underneath the bug: this specific crash's signature is genuinely unstable

This isn't just a tooling story. Re-running triage multiple times against the *identical* original 120,006-byte input produced a different `signature_matches` ratio each time — 2/3 matched on one run, 1/3 matched on another, both while still crashing 3/3 times. That's a real, repeatable characteristic of this particular stack-overflow bug, not a fluke of the fix: it plausibly sits right at a recursion-depth threshold sensitive to small run-to-run environment differences — the same kind of sensitivity that separately made `minimize.py`'s achieved reduction vary between runs (87% one time, 75% another, 0% a third). Worth a line in the final report as an observed property of this specific bug, distinct from the tooling bug that happened to reveal it.

### Why this belongs in the report

The assignment explicitly asks for documented normalization choices and judgment calls, not just a working pipeline. Both bugs here are exactly that kind of material: a concrete example of a normalization gap (frame filtering) and a concrete example of an incomplete state model being caught and fixed by choosing to fail loudly rather than silently — a defensible, explainable engineering decision, with the "why" traceable to a real defect it would have prevented.
