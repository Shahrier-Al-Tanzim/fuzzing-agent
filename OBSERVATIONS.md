# Observations Log

Running log of notable challenges, failures, and judgment calls made across
the project. Each entry is a self-contained case: what was tried, what
happened, and what was concluded. New cases are appended below as the
project continues — this is not a single narrative, and later cases are not
assumed to relate to earlier ones unless stated.

---

> ## ⭐ START HERE — the headline finding
>
> **[Case 5: prompt anchoring — an example's constant became a hard
> ceiling](#case-5-prompt-anchoring--an-examples-constant-became-a-hard-ceiling-)**
>
> A prompt rule told the model to reach extreme nesting depth by drawing an
> integer and repeating a string instead of recursing. It worked
> immediately: **max depth went from 4 to 5,000 — a ~1,250× jump, the
> largest single improvement in the project.**
>
> But depth then froze at *exactly* 5,000, because the model had copied the
> rule's own illustrative bound (`max_value=5000`) **verbatim** — treating a
> number written casually into an example as the specification, **in
> preference to the feedback signal that was concurrently asking for
> 30,000–90,000.**
>
> **An illustrative constant in a prompt example acts as a hard ceiling, not
> a starting point.** This is the most transferable finding here — nothing
> about it is specific to TOML, `tomlc99`, or fuzzing.
>
> Runner-up, for the "proxy signal" part of the report:
> **[Case 4](#case-4-the-first-full-5-iteration-loop-run--breadth-climbed-but-the-proxy-signal-got-gamed)**
> — breadth climbed while the generator quietly got structurally simpler,
> the exact signal-gaming failure the assignment warns about.

---

## Bugs found — summary (updated as of Run 25, 2026-08-20)

All real bugs confirmed in `tomlc99` so far, in one place. Signature IDs
are the folder names under `triage/reports/`.

| # | Bug | Mechanism | Signature(s) | How found | Deterministic? |
|---|---|---|---|---|---|
| 1 | Array-nesting stack overflow | `parse_array` (`toml.c:1057`) recurses into itself once per `[`, no depth limit | `939402a0547c`, `e857b4530c96` (frameless variant, same root cause) | Found by hand in Module 1 (`grammar/early_findings/01_...`), then rediscovered by the agentic loop itself in Run 11+ | Yes (3/3) |
| 2 | Dotted-key stack overflow | `parse_keyval` (`toml.c:1106`) recurses into itself once per `.` in `a.b.c...=1`, no depth limit — separate from bug 1's function and separate from the table-header path's depth-10 guard, which doesn't cover this case | `55628614cd6c` | Found by hand reading `toml.c` during crash-hunting planning (`grammar/early_findings/02_...`) | Signature unstable (crashes 3/3, but ASan can't always get a clean backtrace at this depth) |
| 3 | Inline-table stack overflow | `parse_inline_table` and `parse_keyval` recurse into each other once per nested `{`, no depth limit | `26e809dd9d85` | Found via the hand-written `crash_hunt` parametric generator, cross-confirmed by the agentic loop | Yes (3/3) |
| 4 | Many-siblings O(n²) hang | `toml_table_in()` scans existing keys linearly on every insert, so N keys in one table costs O(N²) total — thousands of `kN = 1` lines under one table blows past the 5s timeout | `unparsed_timeout` | Taught to the LLM as prompt rule 17; **first fired autonomously by the agentic loop itself in Run 15** (72 occurrences) — not yet confirmed via a hand-written probe, the reverse order of bugs 1-3 | No — inherently flaky near a timing cutoff, not a memory-safety bug, expected (see Case 6) |
| 5 | Alternating array/inline-table stack overflow | `parse_array` and `parse_inline_table` recurse into EACH OTHER (not into themselves) once per `[{`/`}]` pair — a third, distinct recursion cycle from bugs 1 and 3, which each involve only one of the two functions calling itself | `af1d0280777e`, `3db1e06f41e9`, `80953bb88ca2` (3 signatures, same root cause — see Case 9) | Predicted by the hand-written `crash_hunt` probe (`pipeline/crash_hunt_strategy.py`'s `deep_mixed_nesting` campaign), taught to the LLM via the rule 16 amendment on `module-7b-crash-hunting-2`, **first fired autonomously by the agentic loop in Run 25** | Crashes every run; signature not stable across runs (see Case 9 for why the instability is worse here than for bugs 1-3) |

**Bug class split:** 4 are memory-safety bugs (unbounded recursion →
stack exhaustion, would be a real CVE-class issue in production use); 1 is
an algorithmic-complexity / denial-of-service bug (slow, not unsafe). All
5 stem from the same root pattern: `tomlc99`'s recursive-descent parser
and its table implementation have no limits on attacker-controlled input
size or nesting, anywhere.

**Not a new bug class, just a new confirmation:** Run 15 (Gemini) also
re-found bugs 1-3 (159 crashing inputs total, deduplicating to the same
signatures as before) alongside bug 4. See Case 6 for the acceptance/
breadth numbers from that run, and Case 5 for how bugs 1-3's crash
thresholds were originally discovered.

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

**Addendum, 2026-08-14:** the exact same bug — the two-state `deterministic`/`flaky` model missing the `unstable_signature` case — was found a *third* time, independently, in `report/generate_artifacts.py`'s `crash_table()` while checking Module 7. That file re-derived the same verification-status logic inline instead of reading `metadata.json`'s already-fixed `description` field, and reintroduced the identical mislabeling bug in the process. It was dormant only by coincidence (the crash happened to read as `deterministic: True` at the time), not because the code was correct. Fixed the same way: read the shared `description` field, with a fail-loud fallback rather than a re-derived guess. The recurrence itself is the finding — it's evidence this specific mistake (re-deriving state logic instead of reusing a single computed source of truth) isn't a one-off, but a pattern worth watching for anywhere verification status gets displayed.

### Bug 3: frameless overflows collapse distinct bugs into one bucket (2026-08-16)

Found while adding a *second* hand-found crash (a dotted-key stack overflow, `parse_keyval` recursion at `toml.c:1138`, distinct from the array bug's `parse_array` chain — see `planning/hunting/step-01-second-crash-dotted-key.md`). The dotted-key crash kept getting bucketed under the array bug's frameless signature (`e857b4530c96`, `stack-overflow@unknown`) instead of its own — hiding that it's a genuinely different bug.

**Root cause:** the "unstable signature" property from Bug 2 above has a sharper consequence than first documented. When ASan can't unwind a deep overflow's stack, the report has *zero* frames, and `parse_signature()` falls back to a single `unparsed_<verdict>` key — which is **identical for every frameless overflow regardless of which bug caused it**. So two distinct stack-overflow bugs collapse into one bucket whenever both happen to produce a frameless run. Since `collect_findings()` read each input's signature from a *single* run, one unlucky frameless collection run mislabeled the whole bug. Depth made it worse, not better: past ~120k the overflow is so violent it almost never unwinds, so a "deeper = more reliable crash" instinct actively degraded signature quality.

**Fix:** `_run_for_parseable_crash()` in `triage/run_triage.py` retries a crashing extra input up to 6 times to obtain a run with a *parseable* stack before giving up (still reporting a genuinely-always-frameless crash in the unparsed bucket, just not letting one unlucky roll mislabel a bug that usually does parse). The crash is still the crash; the retry only affects which frames get read for bucketing.

**Bonus effect:** the same retry stabilized the *array* bug's verification. It had been reported as "crashed every run (3/3) but signature unstable (2/3 matched)" — now that minimization and verification start from a parseable-signature baseline, it verifies cleanly as deterministic (3/3). Net result: `2 crashes -> 2 unique bug(s)`, both deterministic, correctly separated by root cause.

**Why this belongs in the report:** it's a concrete, non-obvious deduplication/normalization judgment call — exactly what the assignment asks to be documented. "Prefer a parseable signature over the first observed one, because a frameless fallback key is not bug-specific" is a defensible normalization choice with a real defect (distinct bugs silently merged) traceable to *not* making it. It also sharpens the earlier "unstable signature" finding: the instability doesn't just vary the match ratio, it can erase the discriminating information entirely.

---

## Case 4: the first full 5-iteration loop run — breadth climbed, but the proxy signal got gamed

**Date:** 2026-08-14
**Module:** Module 5 (`agent/loop.py`), first full `python -m agent.loop` run, Groq/`llama-3.3-70b-versatile`
**Status: fixed.** The five fixes originally listed at the end of this case (as "not yet applied") have since been implemented and verified — see the updated section below. Left the original finding text as-is above this line so the before/after is visible; only the fix section itself was rewritten in place.

### TL;DR

- The one real success: **cumulative grammar breadth climbed every iteration — 18% → 26% → 32% → 40% → 47%.** That is the core evidence the feedback signal works, and it's genuine.
- Everything else about this run is a problem, and none of it was visible from the console output alone:
  - Only **9-11% of the configured 500 examples per iteration actually ran** (38, 43, 54, 44, 51) — the console printed "running 500 examples..." regardless, because that line is hardcoded to the config value, not the actual count.
  - **Nesting depth never moved off 1**, across all five iterations, including in *rejected* documents — not merely "deep documents got rejected," the strategy structurally could not produce depth > 1 at all.
  - **Generated documents shrank every iteration** (max bytes 285 → 87 → 69 → 43 → 48; mean 34 → 18 → 18 → 11 → 13), and the breadth gain came from generating more distinct *trivial* scalar values, not more structural complexity.
  - `findings: 0` for all five iterations was therefore inevitable, not informative — the known stack-overflow bug needs ~48,000 levels of nesting, and this generator never exceeded 1.

This is a close-to-textbook case of **a proxy signal being gamed**: breadth (the metric being optimized) went up, while the thing breadth was supposed to be a stand-in for (structural testing depth) went to essentially zero. Worth stating plainly in the report as exactly this — not hidden, not softened.

### The example-count shortfall: two different root causes now observed, not one

This is the **second time** a "fewer examples than configured" shortfall has been measured (see `planning/how/HOW_TO_RUN_EVERYTHING.md` Appendix A for the first), and the root cause this time is **demonstrably different**, not a repeat of the same bug:

- **First observation** (an earlier, separately-generated `iter_00_strategy.py`, tested in isolation with the harness removed entirely): Hypothesis slowed and stopped early as documents grew large/deep, consistent with hitting an internal buffer limit on oversized generated values. ~145 examples in 123s, with visible slowdown (50 examples at 0s, 100 at 44s).
- **This run** (`iter_00`-`iter_04_strategy.py` from the full loop): documents stayed *tiny* (max 285 bytes, shrinking to max 48 by iteration 4) — the opposite of "too large." Reading the actual generated code found the real cause here: several `st.text(...).filter(lambda x: x.startswith('"') and x.endswith('"'))`-style calls, asking Hypothesis to draw random text and then discard nearly all of it because it happens to start and end with a specific character. Hypothesis exhausts its own internal retry budget on these near-impossible filters and gives up well short of `max_examples`, independent of document size.

Both are real, both produce the same visible symptom (way fewer than 500 examples logged), but they are not the same bug — one is "values too big," the other is "values statistically almost impossible to draw." Worth documenting as two distinct instances of the same category of problem (Hypothesis giving up early for a reason the loop's own console output never surfaces), not conflating them into one fix.

### The depth-1 ceiling: `uses_recursion: True` was never actually true

`agent/validator.py`'s recursion check is a pure text search over the generated source:
```python
RECURSION_MARKERS = ("st.recursive", "@composite", "@st.composite", "recursive(")
...
"uses_recursion": any(m in code for m in RECURSION_MARKERS),
```
It checks whether the string `@composite` appears anywhere in the file — not whether anything actually calls itself. The final strategy from this run (`agent/strategies/iter_04_strategy.py`) uses `@composite` throughout and reports `uses_recursion: True`, but reading the actual container functions shows none of them are self-referential:
```python
def array(draw):
    elements = draw(st.lists(st.one_of(pair(), value()), ...))   # never array() itself
def inline_table(draw):
    pairs = draw(st.lists(pair(), ...))                          # never inline_table() itself
```
An array can never contain another array. This is why every generated document — accepted or rejected, all five iterations — never exceeded depth 1: the gate meant to catch exactly this ("the assignment grades whether recursion was flattened," per `prompts.py`'s own comment) cannot actually detect a flattened container, because it never inspects structure, only source text.

### The feedback loop was answered with dead code

The final strategy defines `quoted_key()` and `dotted_key()` — functions that only make sense as a direct response to feedback directives asking the model to "generate `quoted_key`" / "generate `dotted_key`," since those exact names match the missing-productions list verbatim. Neither function is ever called from `document()`, `pair()`, or `value()`. The model appeared to respond to the feedback (it wrote code with the right names) without the response doing anything (the code is unreachable), so those productions correctly kept showing up as missing every subsequent iteration, and the model kept adding more dead functions rather than wiring the existing ones in.

### Fixes applied

All five, verified working before the next real loop run was attempted:

1. **Prompt rule 9** (`agent/prompts.py`'s `STRATEGY_CONTRACT`): forbids `.filter()` on `st.text()` for shape/prefix/suffix constraints, with the exact failing pattern and a corrected `.map()`-based replacement shown side by side — the same worked-example technique that fully fixed rule 6 in Module 4 (Case 1), used here on a different failure class.
2. **Prompt rule 10**: containers must be genuinely self-referential — `array()`'s element strategy must include `array()`/`inline_table()` themselves, with the exact flat (non-nesting) pattern from the real generated code shown as the thing *not* to do.
3. **Validator fix** (`agent/validator.py`, gate 5): `RECURSION_MARKERS`'s text-search was deleted entirely. `uses_recursion` is now computed from the *drawn samples* — `pipeline.features.extract_features()` (already used elsewhere in the project, not reimplemented) measures each sample's actual bracket depth, and `uses_recursion` is `True` only if some sample actually exceeded depth 1. Verified directly: a hand-written strategy reproducing the exact Case 4 bug (uses `@composite`, never nests) now correctly reports `uses_recursion: False, sample_max_depth: 1`; a genuinely self-referential one reports `True, sample_max_depth: 12`. The old check would have reported `True` for both.
4. **Console fix** (`agent/loop.py`): now prints "running up to N examples..." beforehand and the real `len(records)` afterward, with an explicit `!!` warning line (pointing back at this case) whenever the actual count falls short of the configured cap — this can no longer be invisible from the terminal.
5. **Log-contamination fix** (`agent/loop.py`, `run_iteration()`): each iteration's `.jsonl` log is now deleted before that iteration runs, so re-running the same iteration number replaces its log instead of appending a second strategy's records onto the first's (this was a targeted fix inside `agent/loop.py`, not a change to `RunLogger` itself, which correctly still appends for Module 3's baseline runs). The existing contaminated `pipeline/logs/iteration_*.jsonl` files (185 mixed records) were deleted so the next run starts clean.

**Not changed:** whether a flat strategy should now be treated as a hard validation failure (gate 5 rejecting it outright) rather than an accurately-reported statistic. The fix makes the report honest; it doesn't yet make flatness un-passable. Worth deciding explicitly before the next full run, not by default.

### Prompt-rule fix log

A standing, numbered record of every `STRATEGY_CONTRACT` rule added in response to a real observed failure, kept separate from the rule numbers inside `agent/prompts.py` itself (those renumber/shift; this log doesn't - it's chronological, one entry per fix cycle, appended to as new fixes land).

1. **Rules 9 + 10** (2026-08-14) - added together as the direct fix for this case's root cause. Rule 9: banned `.filter()` for shaping random text (the cause of the ~145-vs-500 example shortfall). Rule 10: containers must be genuinely self-referential (the cause of depth being stuck at 1). **Outcome, confirmed on the next real run:** genuine recursion now happens - `sample_max_depth` of 3, 4, 5, 6, 7 across a single run's attempts, versus permanently 1 before. Rule 10 worked.
2. **Rule 11** (2026-08-14) - added after `st.dates(min_value=...)`/`st.times(min_time=...)` kept recurring across multiple sessions (first flagged in Case 2, still happening in the run right before this fix). Bans `st.dates()`/`st.times()`/`st.datetimes()` entirely, since the real fix - passing actual `date`/`time` objects - is unreachable anyway under rule 3's import restriction; redirects to building the string from integers instead. **Outcome, confirmed on the next real run:** zero `dates()`/`times()` errors across all 8 attempts in the very next run, where they had appeared in 3 of 4 attempts the run before. Not a controlled A/B test, but a strong signal in one data point.

3. **Rule 12** (2026-08-14) - added immediately after rule 11's own test run surfaced a new bottleneck once genuine recursion started working: acceptance rate collapsed to 2-5% (floor is 20%). Real generated samples showed the cause directly - bare, standalone lines like `{}` and `[14:36:03, true, 13:19:07]` sitting at the top level of the document with no key in front of them, which is invalid TOML at any depth. `document()` was choosing `array()`/`inline_table()` directly as one of its own top-level options instead of only ever reaching them as a value after `key =`. Rule 12 states the top-level document grammar explicitly: every line must be `key = value`, `[table]`, or `[[array_table]]`, never a bare container. **Outcome: confirmed working, and then some.** The next full 5-iteration loop run passed generation on attempt 1 for *every* iteration (5 API calls total for the whole loop, versus a worst case of 40), all 500/500 examples ran every iteration (the earlier ~145-example shortfall from before rules 9-12 didn't recur once), and acceptance held steady at 31-41% throughout, never approaching the floor. All four fixes (9, 10, 11, 12) validated together in one clean run.
4. **Rule 13** (2026-08-15) - added after a full loop run (logged live in `logs/RUN_HISTORY.md`, the project's new permanent attempt-history file) passed iterations 0-2 cleanly but failed all 7 attempts at iteration 3, every single one at the `acceptance` stage (8-18% accepted, floor 20%) - no crashes, no fabricated APIs, just consistently-too-low acceptance. Checked 5 of the 7 rejected attempts' code directly: **all 5 had the identical bug**, independently generated each time - `table()` built `[header]`/`[[header]]` lines from raw, unrestricted `st.text()` instead of reusing the already-correct `key()` function, which properly quotes or restricts its output. Real generated samples showed the damage directly: bare, unquoted headers like `[[\x9f7]]` and `[衜@¶À]` containing control characters and non-ASCII symbols with no quoting at all - invalid, since TOML's unquoted-key rule only allows ASCII letters/digits/`_`/`-`. Since `document()` picks between `pair()` and `table()` roughly evenly, a broken `table()` drags down a large share of every generated document. Rule 13 states explicitly that table/array-table headers must be built from the same key-generation logic as regular keys, never raw text directly. **Outcome: confirmed working.** The very next full loop run (`logs/RUN_HISTORY.md`, 2026-08-15 09:48-09:53) passed all 5 iterations - specifically iteration 3, the one that had just failed 7/7 attempts in a row, passed on attempt 2. Full run: iter 0 passed on attempt 2, iter 1 on attempt 1, iter 2 on attempt 1, iter 3 on attempt 2, iter 4 on attempt 1 - 6 total attempts for the whole 5-iteration loop.
5. **Rule 14** (2026-08-16, `module-7b-crash-hunting`) - added after crash-hunting work (see `planning/hunting-generation/`) proved the loop's 0-findings history was a *reachability* gap, not an empty search: a hand-written parametric generator (`pipeline/crash_hunt_strategy.py`) found 3-4 distinct stack-overflow bugs the agentic loop never came close to, because `render_feedback()`'s depth directive only ever asked for "12+" against bugs that need 48,000-105,000+ levels of nesting - and even a perfectly-obedient model can't get there with a balanced `st.one_of(value(), array(), inline_table())`, since a uniform 1-in-3 recursion choice decays to near-zero probability of reaching four-to-five-digit depths. Two changes together: `agent/summarize.py`'s flat "aim for 12+" replaced with `DEPTH_TARGETS = [12, 200, 4_000, 30_000, 90_000]`, escalating geometrically per completed iteration; and rule 14 added to `STRATEGY_CONTRACT`, which stops asking for a bigger number past target 200 and instead teaches two concrete biasing techniques with working code - repeating the recursive branch in `one_of()`, and threading a depth counter through `draw()` that is *actually incremented on the recursive call* (directly naming the earlier dead-`current_depth` bug class from this file's "Latest full run (2026-08-14)" entry, so the model is shown the exact mistake to avoid, not just told "don't do that"). **Outcome: not yet confirmed.** Both changes were verified structurally (imports clean, escalation targets correct at every iteration count via direct calls to `render_feedback()` with synthetic data, prompts build without error) but **never tested against a real Groq call** - no `python -m agent.loop` was run this session. Whether the model actually follows rule 14 and reaches meaningfully higher depth in a live run is an open question, not a confirmed result - unlike every earlier entry in this log, which was validated against a real run before being marked done.

**Addendum, 2026-08-16 - the first live test found a real regression in rule 14 itself.** Run 6 (`logs/RUN_HISTORY.md`): depth barely moved (3 -> 4 across 5 iterations, nowhere near the escalating targets), and iteration 4's acceptance collapsed from 42% to 7% - `pipeline/logs/iteration_04.jsonl` showed 389/464 rejects were `"missing ="`. Read the actual generated `agent/strategies/iter_04_strategy.py`: `toml_strategy` was built as `st.one_of(document(), document(), document(), document(), document(), array(), dotted_key(), ml_basic_string(), ..., st.integers(...).map(lambda x: f"0x{x:x}"))` - only 5 of 17 branches were real documents; the other 12 exposed bare fragments (a raw array, a raw dotted key, a raw hex number) directly as if they were whole files, which is invalid TOML at any depth (a file must be `key=value`/table lines, never a bare value alone). **Root cause traced to rule 14's own closing sentence**, which said to "combine both with `st.one_of()` in the final `toml_strategy`" without stating that every branch must still be a complete document - the model took that literally and stopped routing the depth-seeking constructs through `pair()`'s value position (which rule 12 already establishes as the only valid place for `array()`/`inline_table()`), instead giving them a second, unwrapped, top-level home right next to `document()`. **Fixed the same day**, before any further live testing: rule 14's closing paragraph now explicitly forbids bare recursive/scalar strategies inside `toml_strategy`'s own `one_of()`, with a "Wrong" example matching the actual failure verbatim and a "Right" example showing depth-seeking routed through a `document_depth_biased()` variant that still emits full `key =` lines throughout. Not yet re-tested against a live run. Notable process point: this is the *fastest* a new rule has gone from "written" to "found breaking something in production" to "patched" in this log - a single run - which argues for treating any newly-added rule as unverified until it survives at least one live iteration, not just a structural/import check.

6. **Rule 15** (2026-08-16, Run 7) - the rule-14 fix above got its live test immediately, and surfaced a *different*, pre-existing bug that rule 14 wasn't responsible for: acceptance stayed chronically low (12-23%) across *all 5* iterations this time (not just one), and depth barely moved (2-4). `"missing ="` was again the dominant reject reason in every iteration - but this time the generated `toml_strategy = document()` alone, no bare fragments (rule 14's fix held). Traced to the actual generated documents instead of guessed at: `key()`'s unquoted branch was completely unrestricted `st.text(...).map(lambda x: x)`, producing literal keys like `[»\x1aî(\U0008e78b\U00055fad!v9×]` (control characters and symbols; unquoted TOML keys may only contain ASCII letters/digits/`_`/`-`). Separately, `value()`'s quoted-string branches wrapped raw, unrestricted `st.text()` output in quotes with no exclusion of the quote character or control characters, producing `"\nDJ" = 0` - a literal, unescaped newline landing inside a single-line basic string, which doesn't just invalidate that one value but corrupts line-counting for the rest of the document (hence the many "line 2: ..." errors that were actually fallout from line 1's corruption). Rule 15 requires both branches to restrict their alphabet directly at construction time (never `.filter()`, per rule 9) - `string.ascii_letters + string.digits + "-_"` for unquoted keys, and the printable set minus the quote character/backslash/newline/carriage-return for quoted content. **Outcome: not yet tested.** Structurally verified only (15 rules present, prompts build, imports clean) - this fix has not yet survived a live run, and per the process point above should be treated as unconfirmed until it does.

7. **Rule 16** (2026-08-17, Run 8) - **the most important finding in this log for the report's "Challenges" section: recursive generation is structurally incapable of reaching crash depth, and no prompt can fix that.** Rule 15 worked (Run 8 acceptance recovered to 40-53%, the best sustained figures across all 8 runs, and the `"missing ="`/`"invalid key"` rejects that dominated Run 7 vanished entirely - the top reject became the benign `"key exists"`). But depth still sat at 1-4, so the generated `iter_04_strategy.py` was measured directly instead of assumed about. **The model had obeyed rule 14 correctly** - `array()` listed its recursive branch 4x against `VALUE` once and genuinely threaded `depth=depth+1` - yet 30 direct `.example()` draws of that same `array()` never exceeded depth 2. A controlled A/B isolated the cause: holding the bias ratio and depth counter identical and changing only the list size, unconstrained `st.lists(...)` reached **max depth 3** while forcing `min_size=1, max_size=1` reached **max depth 13**. Hypothesis's default `st.lists()` averages ~50-90 elements, so a biased recursive strategy spreads *sideways* into a bushy tree and burns its data budget on width at depth 2-3 - the branching factor, not the recursion bias, was the real cap. **But the deeper conclusion is that even the corrected chain shape only reached 13**, against bugs needing 48,000-105,000: Hypothesis's own generation budget inherently resists deep recursion, so `st.recursive`/`@composite` cannot reach crash depth *by any amount of prompt engineering*. This reframes the whole "loop finds no crashes" story - it was never a model-obedience or prompt-quality failure. Rule 16 therefore teaches the only technique that does work, the same one `pipeline/crash_hunt_strategy.py` already uses to hit 60k-115k reliably: draw the depth as an *integer* and build the string by repetition (`"[" * n + "1" + "]" * n`), no recursion involved, wrapped in a normal `key = value` line per rules 12/14 and kept as one branch beside the shallow ones so grammar breadth survives. **Outcome: not yet tested** (16 rules present, prompts build, imports clean) - though unlike rules 14/15 the underlying *technique* is already proven, since `crash_hunt` uses it to find all four stack-overflow bugs; what's unverified is only whether the model adopts it when told to.

**Addendum, 2026-08-17 - Run 9: rule 16 worked, and immediately exposed prompt-anchoring as a distinct failure mode.** *(Written up as a standalone case — see [Case 5](#case-5-prompt-anchoring--an-examples-constant-became-a-hard-ceiling-) for the report-facing version; this entry keeps the chronological rule-change record.)* Depth went from 4 to **5,000** in a single iteration - a ~1,250x jump, and the single largest metric improvement of the entire project - while acceptance stayed healthy (32-46%) and breadth reached 84%. The model fully adopted the integer-repetition technique, confirming the rule-16 diagnosis was correct. But depth then sat at *exactly* 4999-5000 for all five iterations, which is not a plateau the model discovered - reading the generated `iter_04_strategy.py` showed it had copied the rule's example bounds **verbatim**: `n = draw(st.integers(min_value=200, max_value=5000))`. The measured crash thresholds are ~48,000 (arrays), ~80,000 (inline tables), ~90,000-100,000 (dotted keys), so a hard ceiling of 5,000 put every generated document safely below all of them - hence `findings: 0` again despite the technique working perfectly. **The finding worth reporting: an illustrative constant inside a prompt example acts as a hard ceiling, not a starting point.** The model treated `max_value=5000` as the specification rather than the `DEPTH_TARGETS` escalation (which was concurrently asking for 30,000-90,000) - so a number written casually into an example silently overrode the actual feedback signal. A second, smaller instance of the same class: the model defined `deep_inline_table` and `deep_dotted_key` but wired only `deep_array` into `toml_strategy`, so two of three shapes never executed once. Rule 16 was amended for both: example bounds raised to `1_000`-`120_000` (verified to stay under the 1 MB harness cap - 234 KB, 469 KB, 234 KB respectively at max depth), an explicit instruction to set `max_value` *from the feedback's depth target rather than from the example*, and a requirement to wire all three shapes into `one_of`. Also added a guard against a subtle self-defeating interaction discovered while reasoning about the change: a crashing document is not an "accepted" one, so if deep branches dominate `toml_strategy` the measured acceptance rate drops below the 20% validator floor and the strategy is rejected *before it runs* - losing the very crashes it exists to find. The rule now requires deep branches to stay a minority (~1 per 2 ordinary `document()` branches). Not yet re-tested.

8. **Rule 16 amended again** (2026-08-20, `module-7b-crash-hunting-2`) - added after four consecutive full runs (17, 20, 21, 24) each triaged to the *identical* five buckets (`939402a0547c`, `e857b4530c96`, `26e809dd9d85`, `55628614cd6c`, `unparsed_timeout`). The loop had plateaued: more depth and more iterations only re-found the same four bugs. Reading `pipeline/crash_hunt_strategy.py` against the triage history found the reason, and it was not a model failure - it was a gap in what rule 16 *teaches*. Two distinct defects, fixed together:
   **(a) A proven crash shape was missing from the prompt entirely.** `crash_hunt`'s fourth campaign, `deep_mixed_nesting` (`x = [{a=` … `}]`, arrays and inline tables alternating at every level), is documented in its own docstring as producing signature **`af1d0280777e`** - "a DISTINCT signature from both deep_array and deep_inline_table, reproducing 4/4 with parseable frames - the most stable of the four campaigns." Verified directly: `af1d0280777e` appears **nowhere** in `triage/reports/`. So the hand-written prober had found a fifth bug that the agentic loop has never once reached, purely because rule 16 taught three *pure* shapes and nothing alternating. This maps exactly onto the parser: `toml.c` has four distinct recursion cycles (`parse_array`→itself at 1060; `parse_keyval`→itself at 1138; `parse_keyval`↔`parse_inline_table` at 1180/961; and `parse_array`→`parse_inline_table`→`parse_keyval`→`parse_array` at 1075/961/1171) and the loop was exercising only the first three. Rule 16 now teaches all four shapes and states why the mixed one is not a duplicate.
   **(b) One shared depth floor across shapes with very different thresholds.** Rule 16 told the model to draw `min_value=1_000` for all three shapes, but the measured crash thresholds are ~48,000 (arrays), ~80,000 (inline tables), ~90,000-100,000 (dotted keys), and `crash_hunt` - which reproduces each bug reliably - uses shape-specific ranges far above that floor (60k-100k / 85k-115k / 100k-130k / 60k-80k). With one low floor, most inline-table and dotted-key draws landed *below* their own crash threshold and did nothing at all. The damage is visible in run 24's occurrence counts: the array shape crashed **120** times while the dotted-key shape crashed **3** and the inline-table shape **11** - the two thinnest pieces of evidence in the whole project, and a weakness already flagged in `comparison/gemini/run_24/ANALYSIS.md`. Rule 16 now carries the four measured per-shape floors, reusing `crash_hunt`'s proven constants rather than inventing new ones, and explicitly says to widen the range by raising `max_value`, never by lowering `min_value` (so the Case 5 anti-anchoring instruction and the new floors don't contradict each other).
   **The deliberate trade this forces.** A crashing document does not count as "accepted", and with high per-shape floors almost every deep draw now crashes rather than only ~23-65% of them. At the previous "one deep branch per two ordinary" ratio that would have driven acceptance under the 20% validator floor, getting the strategy rejected *before it ever runs* - the exact self-defeating interaction rule 16 already warned about. So the deep-branch share was cut in the same edit: four deep branches against at least sixteen ordinary `document()` branches (~1 in 5), written as a worked `one_of` example rather than a ratio in prose. The goal is explicitly **not** more crashing documents overall - it is the same or fewer, redistributed so each one lands on a shape that clears its own threshold, including the never-yet-hit mixed shape.
   **Outcome: confirmed working, Run 25.** Acceptance held 29%-58% across all 5 iterations (never threatened the 20% floor), and the mixed-nesting shape fired autonomously - see Case 9 for the full result, including the honest correction that it surfaced as 3 triage signatures (`af1d0280777e`, `3db1e06f41e9`, `80953bb88ca2`) for one root cause rather than the single new row originally expected. The per-shape floor fix also had a large secondary effect: bug 2 went from 3 occurrences (Run 24) to 158, bug 3 from 11 to 120 - both were being drawn too shallow to trigger under the old shared floor, exactly as predicted.

9. **Rule 16 extended with `deep_quoted_mixed`** (2026-08-20, `module-7b-crash-hunting-3`) - the shape was chosen by *measurement, not guesswork*, and the first candidate was discarded after being tested. Candidate A (`deep_mixed_dotted`, `"[{a.b=" * n`) reasoned that adding `parse_keyval`'s dotted self-recursion into bug 5's cycle would make it four functions per level and yield a new signature. Probed directly against the harness at n=40,000/55,000/70,000 before writing any prompt text: it crashes every time, but produced `55628614cd6c`, `80953bb88ca2` and `e857b4530c96` - **all already-known buckets**. It was therefore dropped rather than shipped, since adding a shape that yields no new signature is exactly the mistake rule 18 made. Candidate B changed *what sits at each level* instead of which constructs alternate - a QUOTED key (`'[{"k"=' * n`), which forces `normalize_key` -> `norm_basic_str` (the string-unescaping path) onto the stack. That produced **`c04d038a7956`** - `malloc / expand toml.c:411 / norm_basic_str toml.c:506 / normalize_key toml.c:652 / create_keyarray_in_table toml.c:830` - the **first signature in this project's history with `norm_basic_str` in it**. Reproducibility was measured across a depth sweep (3 trials each): 25,000 gave 3/3, and 20,000-45,000 gave 1-3/3, while 50,000+ reverted to the known `80953bb88ca2` bucket - a quoted key does more work per level, so the stack runs out sooner and going deeper actually *hides* this signature. Hence the deliberately lower `min_value=20_000, max_value=45_000` in the rule, and the rule now states the general principle the experiment established: **what sits at each nesting level matters as much as how deep the nesting goes.** **Outcome: confirmed live, Run 26** - `c04d038a7956` fired autonomously via the agentic loop (145 occurrences), the first time this signature was produced without a hand-written probe.

   **Milestone worth calling out on its own: this bug was found at a LOWER depth than every other one in the project, not a higher one.** Every earlier bug hunt in this log moved in one direction - push depth further (Case 5; rule 16's original three shapes at 48k/80k/90-100k; `DEPTH_TARGETS` climbing to 90,000). `deep_quoted_mixed` breaks that pattern: it reproduces best around ~25,000, roughly half of the *shallowest* of the other four shapes, and gets LESS reliable, not more, past ~45,000 (reverting to the known `80953bb88ca2` bucket by 50,000+). So the newest bug in this project was found by going less deep, not more - direct, concrete evidence for Case 10's Defect 2 finding that raw depth was never the actual lever; what occupies each nesting level is. Worth stating plainly in the report: the project's search strategy shifted from "how far can we push one number" to "what varies at each step," and that shift produced the 5th bug's newest signature - not another round of bigger `max_value`s.

### Latest full run (2026-08-14) — rules 9-12 confirmed working together, plus one new finding

✅ **Status: passing.** All 5 iterations passed generation on attempt 1 (5 total API calls for the whole loop — the best result seen so far), all 500/500 examples ran every iteration, and acceptance held 31-41% throughout without ever threatening the floor. Real numbers:

| Iter | Accept | Breadth | Novelty | Depth | Findings |
|---|---|---|---|---|---|
| 0 | 31% | 60% | 40% | 3 | 0 |
| 1 | 41% | 74% | 20% | 3 | 0 |
| 2 | 34% | 76% | 18% | 3 | 0 |
| 3 | 31% | 76% | 20% | 3 | 0 |
| 4 | 36% | 76% | 20% | 3 | 0 |

**New finding: depth locked at exactly 3 across all 5 iterations, despite 4 rounds of "increase nesting depth" feedback — and the code's own safety cap isn't why.** Reading the final strategy:

```python
def array(draw, max_depth=12, current_depth=0):
    if current_depth >= max_depth:
        elements = draw(st.lists(st.one_of(value(), string())))
    else:
        elements = draw(st.lists(st.one_of(value(), string(), array(), inline_table())))
    return f"[{', '.join(elements)}]"
```

`current_depth` is never incremented on the recursive call - `array()` calls `array()` with no arguments, always falling back to the default `current_depth=0`, so `current_depth >= max_depth` can never be true. The `max_depth=12` cap is dead code. The real limiter is Hypothesis's own default behavior: an unweighted `st.one_of(value(), string(), array(), inline_table())` combined with `st.lists(...)`'s built-in bias toward short/empty lists means the probability of independently choosing to recurse compounds down fast at each level, so depth naturally plateaus low regardless of what the (non-functional) cap allows. This is why the depth-directive in `agent/summarize.py`'s `render_feedback()` had zero measurable effect across 4 iterations of asking for it - it isn't an instruction-following failure, it's that "try to go deeper" can't shift a probability distribution without a concrete technique (e.g. weighting `one_of` toward the recursive options, or raising `min_size` on the recursive branch specifically).

**Not yet fixed** - proposed as the next prompt-rule-fix-log entry (rule 13: bias toward recursion + fix the dead `current_depth` counter), pending confirmation before applying.

### Why this belongs in the report

This is arguably the single most report-worthy finding in the whole project so far. The assignment explicitly warns against a proxy signal that can be gamed, and this run demonstrated exactly that failure mode with real numbers: breadth climbing while the generator quietly got structurally simpler, not more complex. Catching it, tracing it to two specific code defects (a prompt gap and a validator gap that let the defect hide), and fixing and verifying both is stronger evidence of understanding the signal's limitations than a run that happened not to hit this failure mode at all.

### The loop working correctly is not the same as the loop finding bugs (2026-08-16)

Across every real run logged in `logs/RUN_HISTORY.md`, the agentic loop itself has been working as intended - all 5 iterations complete, acceptance/breadth/novelty/depth metrics genuinely improve run over run, and prompt rules 9-13 have driven real, verified fixes. But **zero crashes or timeouts have been found across 2500+ generated examples** (`pipeline/logs/iteration_00.jsonl` through `iteration_04.jsonl`, verified directly: every record is `accept` or `reject`, none `crash`/`timeout`).

This isn't a bug in the loop - it's a structural mismatch between what the loop optimizes for and what the one known bug in this project needs. The one confirmed crash (`triage/reports/939402a0547c/`, `triage/reports/e857b4530c96/` - both from the same hand-found source, `grammar/early_findings/01_array_nesting_stackoverflow.toml`) requires array nesting thousands of levels deep to overflow `tomlc99`'s recursive-descent `parse_array` (`toml.c:1057`). The generator's real inputs plateau at a max nesting depth in the low single digits (see the dead `current_depth` counter finding above) - not because of a bug in this case, but because nothing in the current proxy signal (acceptance/breadth/novelty/depth-as-currently-measured) specifically rewards pushing depth into the thousands the way it rewards touching more grammar productions.

**This is a legitimate, reportable outcome** - the assignment's own Step 5 wording anticipates it directly: *"if none were found, a documented explanation of why, and what you'd try next."* The honest framing for the report: the agentic loop succeeded at its actual job (turning a grammar into a self-improving generator under a feedback signal, with no coverage instrumentation available) but the specific proxy signal chosen wasn't tuned to reproduce the one bug already known to exist in this library, and that gap - between "the loop runs well" and "the loop finds bugs" - is worth stating explicitly rather than implying they're the same success criterion.

**What would change it, if pursued further:** a strategy that deliberately biases toward extreme depth (e.g. weighting `st.one_of()` toward the recursive branch, or a dedicated "generate a pathologically deep array" mode alongside the balanced one), or a feedback directive that rewards depth on a log/exponential scale rather than linearly, since a linear "aim for 12+" directive (as seen in `agent/summarize.py`'s `render_feedback()`) has no mechanism to ever suggest depth 1000+.

**Addendum, 2026-08-16 (`module-7b-crash-hunting`):** pursued further, on a separate branch. A hand-written parametric generator (not the LLM/loop) proved the "dedicated pathologically-deep mode" idea above directly: `pipeline/crash_hunt_strategy.py` found 3-4 distinct stack-overflow bugs (`grammar/early_findings/02_dotted_key_stackoverflow.toml` plus two/three more via `pipeline/run_crash_hunt.py`, see `planning/hunting-generation/`) beyond the one original array bug - confirming this really was a reachability gap, not a fact about `tomlc99` having no more bugs. The "log/exponential feedback directive" idea above was also implemented (`DEPTH_TARGETS` in `agent/summarize.py`, plus prompt rule 14 - see this file's "Prompt-rule fix log" entry 5) but **not yet validated against a live loop run**, so whether the *agentic* loop itself can now reach these depths remains the open question this addendum doesn't answer.

---

## Case 5: prompt anchoring — an example's constant became a hard ceiling ⭐

**Date:** 2026-08-17 (Run 9)
**Branch:** `module-7b-crash-hunting`
**Why this is flagged:** this is the most transferable prompt-engineering
finding in the project — it is not about TOML, `tomlc99`, or fuzzing, and
would reproduce on any LLM-driven code-generation task.

### TL;DR

- Prompt rule 16 told the model to stop trying to reach extreme nesting via
  recursion and instead draw an integer and repeat a string. **It worked
  immediately and spectacularly: max depth went from 4 to 5,000 in one
  iteration — a ~1,250× jump, the single largest metric improvement of the
  entire project** — while acceptance stayed healthy (32–46%) and breadth
  reached 84%.
- **But depth then sat at exactly 4999–5000 for all five iterations.** Not a
  plateau the model discovered — the model had copied the rule's own
  illustrative bounds **verbatim**:
  `n = draw(st.integers(min_value=200, max_value=5000))`.
- The measured crash thresholds are ~48,000 (arrays), ~80,000 (inline
  tables), ~90,000–100,000 (dotted keys). A hard ceiling of 5,000 kept every
  generated document safely below all of them — so `findings: 0` again,
  despite the technique itself working perfectly.

### The finding

**An illustrative constant inside a prompt example acts as a hard ceiling,
not a starting point.** The number `5000` was written casually into a code
example purely to make it concrete. The model treated it as the
specification.

Critically, it did so **in preference to the actual feedback signal**:
`DEPTH_TARGETS` in `agent/summarize.py` was concurrently and explicitly
asking for 30,000 → 90,000. A number embedded in an example silently
overrode a directive written in prose — the example won.

A second, milder instance of the same class appeared in the same run: the
model defined `deep_inline_table` and `deep_dotted_key` but wired only
`deep_array` into `toml_strategy`, so two of the three shapes never
executed once. Anything demonstrated but not explicitly required tended not
to be carried through.

### Fixes applied to rule 16

1. Example bounds raised to `1_000`–`120_000` (verified to stay under the
   1 MB harness cap: 234 KB / 469 KB / 234 KB respectively at max depth).
2. An explicit instruction to set `max_value` **from the feedback's depth
   target rather than from the example**, naming the anchoring failure as a
   real prior failure so it reads as a correction, not a suggestion.
3. A requirement to wire **all three** deep shapes into `one_of`, not just
   define them.
4. A guard against a self-defeating interaction found while reasoning about
   the change: a crashing document does not count as "accepted", so if deep
   branches dominate `toml_strategy`, measured acceptance falls below the
   20% validator floor and the strategy is rejected *before it ever runs* —
   losing the very crashes it exists to find. Deep branches must stay a
   minority (~1 per 2 ordinary `document()` branches).

**Status:** not yet re-tested. 120,000 clears all three measured crash
thresholds, so the next run is the first with a genuine chance of
`findings > 0` from the agentic loop itself.

### Why this belongs in the report

The assignment asks for documented judgment calls and challenges. This is a
clean, measured, causally-traced example of a non-obvious LLM failure mode:
the model obeyed instructions *exactly*, produced correct code, and still
failed the objective — because a detail chosen for illustration was read as
a constraint. It also demonstrates the diagnostic method that caught it:
the metric (depth pinned at a suspiciously round 5,000) prompted reading
the actual generated source rather than trusting the summary line.

### What `crash_hunt` is, and its actual (indirect) role in Run 11

Worth stating plainly, since it's easy to conflate "found the depth
threshold data" with "found the crashes" - they are not the same claim.

**What it is:** `pipeline/crash_hunt_strategy.py` + `pipeline/run_crash_hunt.py`
- a hand-written, non-LLM generator (no model involved in writing it at
all). Four fixed campaigns, each drawing one integer and repeating a
character that many times to build one deliberately pathological
construct: nested arrays, dotted keys, inline tables, and alternating
array/inline-table mixes. This is the exact "draw an integer, repeat a
string" technique that rule 16 later taught the LLM.

**How it connects to the pipeline:** fully - it lives inside `pipeline/`
(originally a separate top-level `crash_hunt/` package, relocated after
review to mirror `baseline_strategy.py`/`run_baseline.py`'s existing
shape), reuses the same `HarnessRunner`/`RunLogger`/`config.yaml` as
everything else, and logs to `pipeline/logs/crashhunt_*.jsonl` in the
same format `triage/` already reads from `iteration_0X.jsonl`.

**Its role in Run 11's actual crash results: none, directly - verified,
not assumed.** Every one of Run 11's 4 triage reports' `sources` fields
trace only to `iteration_00.jsonl`-`iteration_04.jsonl` (the agentic
loop's own logs); `crash_hunt`'s logs were sitting outside
`pipeline/logs/` at the time and contributed zero inputs to that triage
run.

**Its role in Run 11 happening at all: the reason rule 16 existed to be
followed.** `crash_hunt` is what first *proved* the three crash
mechanisms were reachable and *measured* their real thresholds
(~48k/80k/90k) - that evidence became rule 16's worked example, which the
LLM then adopted on its own in Run 11. So: zero direct contribution to
Run 11's crashing inputs, but it is the reason the prompt knew what
number to aim for and which technique to teach. Correlation (both
projects found the same bugs) should not be read as the same claim as
causation (crash_hunt did not generate any of Run 11's crashing inputs).

## Case 6: Run 15 (Gemini, first full 5-iteration run) — acceptance falls every iteration while breadth sits at 100%

Real output, full run, no manual intervention beyond resuming past two
transient Gemini API failures (a read timeout and a 503 - both now
retried automatically, see `agent/gemini_client.py`):

```
iter 0: accept 61%  cov 97%   depth 40574  findings 30
iter 1: accept 56%  cov 100%  depth 49985  findings 32
iter 2: accept 29%  cov 100%  depth 49985  findings 30
iter 3: accept 26%  cov 100%  depth 49985  findings 32
iter 4: accept 24%  cov 100%  depth 49985  findings 34
```

Two things about this table are not self-explanatory from the printed
line alone, so worth recording precisely (traced to code, not guessed):

**What "grammar breadth" actually measures.** `agent/breadth.py`'s
`breadth_fraction` = the fraction of a fixed list of tracked TOML
grammar productions (`pipeline/features.py`'s `PRODUCTIONS` tuple - e.g.
`array`, `inline_table`, `basic_string`, `datetime`) that have appeared
at least once in an *accepted* document, **cumulative across the whole
run**, never reset between iterations. So "100%" does not mean "no more
bugs to find" or "every possible document shape" - it means every
grammar construct we bothered to track has shown up in at least one
successfully-parsed document at some point since iteration 0. It says
nothing about depth, combination, or the pathological shapes that
actually cause crashes. The `+36 this run` figure is also a minor
mislabel worth flagging: it's `len(productions_this_iteration)`, i.e.
"36 distinct productions appeared in *this* iteration's accepted
records" - not "36 newly-reached productions." Once breadth is already
100%, this number is not a "new ground broken" count; it just tracks
this iteration's accepted-document diversity from the fixed set.

**Why acceptance keeps dropping.** "Accepted" here means the harness
process exited 0 - the underlying `tomlc99` library actually parsed the
generated document (`pipeline/schema.py`'s `Verdict.ACCEPT`) - not
Hypothesis's own internal example filtering. Acceptance rate is
per-iteration, not cumulative (unlike breadth), recomputed fresh each
time from that iteration's own records
(`agent/summarize.py::render_feedback`). The decline lines up exactly
with `DEPTH_TARGETS = [12, 200, 4_000, 30_000, 90_000]`
(`agent/summarize.py`): every iteration's feedback explicitly instructs
the model to bias its strategy toward deeper, more unbalanced nesting as
the target climbs, and Run 15's own `max depth` column confirms the
strategy actually did this (40574 → 49985, hitting the ceiling by
iteration 1). Pushing generation toward tens of thousands of nesting
levels makes a document far more likely to be malformed, exceed a
size/depth limit the parser itself enforces, or otherwise fail to parse
- i.e. more REJECT/CRASH/TIMEOUT harness verdicts, not more Hypothesis-
level filtering. This is the deliberate acceptance-for-depth trade the
depth-escalation design makes on purpose (see Case 4/5): the 20%
acceptance floor exists specifically so this trade has a hard stop
before the strategy collapses to producing nothing useful at all. Run
15's iteration 4 (24%) stayed just above that floor.

**Why this belongs in the report:** it is the same escalating-depth
mechanism documented in Case 4/5, now observed end-to-end on a full
5-iteration run with real numbers, and it resolves what could otherwise
look like two unrelated anomalies ("breadth stuck at 100%, is something
broken?" and "why does the model seem to be getting worse?") into one
explained, intentional trade-off.

**Triage of Run 15's 159 crashing inputs (real, run after this write-up):**
rule 17's many-siblings O(n²) hang fired autonomously for the first time
via the agentic loop itself, not just the hand-written `crash_hunt` probe
- 72 timeout occurrences, minimized reproducer is exactly the predicted
shape (`[a]` followed by thousands of `kN = 1` lines). This resolves a
previously-open question (whether rule 17 would ever be confirmed live).
It reports `DID NOT REPRODUCE (0/3)` under `triage`'s verify step, but
that is expected for this bug class specifically: it is a *timing*
threshold (crosses the 5s harness cutoff), not a memory-safety crash, so
pass/fail near the boundary is inherently sensitive to system load at
verify-time - unlike the three stack-overflow bugs, which reproduce
deterministically (3/3) every time. `triage`'s verify step was designed
around deterministic crashes; it doesn't yet have a notion of "reproduces
under load, marginal near a timing cutoff" for hang-class bugs. Worth
noting as a known gap rather than a failure: **the other 4 signatures
found in Run 15 are the same 3-4 stack-overflow bugs already known** -
this run found no new memory-safety bug class, only confirmed the hang
class was reachable by the LLM-driven loop on its own.

## Case 7: abstract prompt rules underperform concrete ones for this model — measured, then reverted

A direct A/B test of a genuine assignment-design question: **should the
prompt hand the model concrete, worked crash-shape examples, or abstract
"go find bugs"-style guidance and let it discover the shapes itself?** The
abstract version is more intellectually appealing (the loop does more of
the discovery), so it was worth actually trying rather than assuming.

**The change tested.** Rules 16-17 were rewritten from concrete to
abstract. The concrete originals gave the model:
- three fully worked deep-nesting composites (`deep_array`,
  `deep_inline_table`, `deep_dotted_key`) with the exact integer-repetition
  technique spelled out, and
- a fully worked `many_siblings` composite for the O(n²) key-count hang.

The abstract rewrite removed every specific shape and magic number,
keeping only: the *technique* ("draw an integer N, build by repetition,
because recursion provably can't reach the scale") and a list of abstract
*dimensions* to stress ("how deeply constructs nest; how many elements a
collection holds; how many entries share a scope; how long a single token
is"), with the model told to work out which TOML constructs map onto each
dimension itself.

**Result (live test, Gemini `gemini-3.6-flash`):** worse on both axes the
project cares about.
- **Findings: did not help** - the abstract prompt did not improve on the
  concrete baseline and, by observation, produced weaker crash-finding.
- **Speed: markedly worse** - roughly ~5 minutes per iteration, versus the
  concrete baseline's ~2.5-4 min/iteration in Run 15 (154s / 181s / 251s /
  234s / 179s). The likely cause: an abstract prompt gives a reasoning
  model more open-ended work to do (decide the dimensions, invent the
  shapes, choose the magnitudes) on every single generation, so it spends
  more tokens/time reasoning and still lands on less effective code.

Evidence note, kept honest: the concrete baseline's per-iteration numbers
are measured (Run 15, logged). The abstract run's underperformance is from
a live test observed during the session (slower wall-clock, no improvement
in findings), not a fully re-logged 5-iteration run with a saved metrics
table - so this is recorded at "observed, decisive enough to revert"
strength, not "fully tabulated" strength. It was decisive enough that the
concrete rules were restored byte-for-byte to the proven Run-15 version.

**Why this belongs in the report.** It directly answers a question the
assignment implicitly raises - how much should the LLM be *told* versus
left to *discover* - with a measured answer for this model/task:
**concrete worked examples of a technique outperform abstract guidance,
both in result quality and in cost.** This is not a claim that abstraction
never works; it is a claim that for a mid-size instruction-following model
pointed at a very specific, high-scale bug class, a concrete demonstration
of the *technique* (not the specific bug - the technique) is what actually
moves the metrics. It also pairs cleanly with Case 5 (prompt anchoring):
together they show the model treats concrete numbers in the prompt as
strong signal - which is a liability when the number is illustrative
(Case 5) but an asset when the whole worked example is the thing you want
followed (this case).

## Case 8: Run 21 (Gemini) — same 4 bugs, but verification quality jumped from "unstable" to deterministic

**Date:** 2026-08-19 (triaged) · **Model:** `gemini-3.6-flash`

Run 21's triage (`triage/reports/run_21/`) produced **5 signatures after
deduplication from 154 crashing/hanging inputs**, and every one maps to a
bug already documented — **no new bug class**.

| Signature | Bug (already known) | Type | Occurrences | Verify |
|---|---|---|---|---|
| `939402a0547c` | Array-nesting overflow, `parse_array` (`toml.c:1057`) | stack overflow | 92 | **deterministic 3/3** |
| `unparsed_timeout` | O(n²) many-siblings hang (bug 4) | hang/DoS | 29 | did-not-reproduce (expected) |
| `e857b4530c96` | Frameless variant of the array bug (crash too violent to unwind) | stack overflow | 23 | crashes 3/3, signature unstable |
| `26e809dd9d85` | Inline-table overflow, `parse_keyval`→`parse_inline_table` (`toml.c:1177`) | stack overflow | 8 | **deterministic 3/3** |
| `55628614cd6c` | Dotted-key overflow, `parse_keyval` self-recursion (`toml.c:1132`) | stack overflow | 2 | **deterministic 3/3** |

**The reportable finding is the verification-quality jump, not a new bug.**
In Run 20 (`triage/reports/run_20/INDEX.md`) the three parseable stack
overflows (`939402a0547c`, `26e809dd9d85`, `55628614cd6c`) all verified as
`unstable-sig` — they crashed every run but the captured stack shifted
between runs. In Run 21 **all three verify cleanly as deterministic (3/3)**,
which is stronger, cleaner evidence for the exact same bugs. The array bug
also fired far more often (92 vs 47 occurrences).

Two rows are *not* separate bugs: `e857b4530c96` is the same array overflow
as `939402a0547c` crashing so violently ASan can't unwind a stack (frameless
bucket, see Case/Bug 3 on frameless collapse); `unparsed_timeout` is the
O(n²) hang, which still reports `DID NOT REPRODUCE (0/3)` under verify — that
is expected for a timing-threshold bug, not a failure (see Case 6).

## Case 9: Run 25 — the rule 16 amendment worked, and triage's own count needed correcting by hand

**Date:** 2026-08-20 · **Branch:** `module-7b-crash-hunting-2` · **Model:**
`gemini-3.6-flash`

This confirms the rule 16 amendment from fix-log entry 8 (four per-shape
depth floors instead of one shared floor, plus a fourth taught shape —
alternating array/inline-table nesting). It also produces the clearest case
yet for why `INDEX.md`'s "N unique bugs after deduplication" line is a
signature count, not a bug count, and must be read by hand before it goes in
the report.

### The floor fix worked exactly as predicted

Total crashing/hanging inputs jumped from Run 24's 219 to **1,127** across
Run 25's five iterations, while acceptance stayed clear of the 20%
validator floor throughout (29%–58%). This is not "more bugs" — it is the
*same* bugs firing far more often, because per-shape floors replaced one
shared low floor. The occurrence counts make the mechanism visible directly:
bug 2 (dotted-key) went from 3 occurrences in Run 24 to **158** in Run 25;
bug 3 (inline-table) went from 11 to **120**. Before the fix, most draws for
these two shapes landed below their own crash threshold and did nothing;
after it, nearly every draw clears its threshold. Exactly the failure mode
predicted in fix-log entry 8, now measured.

### `INDEX.md` said 8 unique bugs. It's 5.

Run 25's triage (`triage/reports/run_25/INDEX.md`) reports **8** signatures
after deduplication: the 4 already-known bugs, plus three that had never
appeared before — `af1d0280777e`, `3db1e06f41e9`, `80953bb88ca2`. Taken at
face value, that reads as three new bugs. It isn't.

**Checked by reading the actual saved crashing input for each of the three,
not just the signature name.** All three are byte-for-byte the same
generated shape: `v = [{a=[{a=[{a=...1...}]}]}]`, the alternating
array/inline-table construct taught in the rule 16 amendment, each roughly
69–73 KB. Their captured stack frames confirm why triage split them:

| Signature | Top frames captured |
|---|---|
| `af1d0280777e` | `malloc → STRNDUP → normalize_key → create_keyarray_in_table (toml.c:830) → parse_keyval (toml.c:1168)` |
| `3db1e06f41e9` | `strnlen → STRNDUP → normalize_key → create_keyarray_in_table (toml.c:830) → parse_keyval (toml.c:1168)` |
| `80953bb88ca2` | `malloc → expand → expand_arritem → create_table_in_array (toml.c:903) → parse_array (toml.c:1072)` |

`parse_keyval` (via `create_keyarray_in_table`, the `key = [` step) and
`parse_array` (via `create_table_in_array`, the `{...}` step) are the two
halves of the *same* alternating recursion cycle — the construct calls one,
which calls the other, which calls the first again, all the way down. Which
half is executing at the exact instant the stack finally runs out is not
controlled by anything in the generated input; it is decided by the
runtime's own stack layout at 60,000+ nested calls. So the same single
overflow gets fingerprinted three different ways depending on which phase
of the cycle it happens to be caught in — `af1d0280777e` and `3db1e06f41e9`
aren't even fully stable between each other (`malloc` vs `strnlen` as the
literal top frame), which is the same instability already seen and named for
bug 1 in Bug 2/Bug 3 above, now hitting a bug with *two* alternating phases
instead of one repeating call, so it has two ways to fragment instead of
one.

**This is a sharper case of the exact normalization problem the assignment
explicitly asks to be documented** ("this is what determines whether you
found one bug or several"). The fix applied for bugs 1/3 (retry a crashing
input up to 6 times to get a parseable stack before giving up) reduces how
often a signature comes back *frameless*, but does nothing for a signature
that is fully parseable and still unstable *between two different real
call sites* — retrying doesn't converge here, because both captured
outcomes are equally valid, equally parseable descriptions of where the
stack happened to be. Automatically merging by "same input shape" isn't a
general fix either — two genuinely different bugs could coincidentally
share an input shape. The honest resolution for this project was manual:
read the actual crashing input, not just the digest, before trusting
`INDEX.md`'s count.

### The number for the report

**5 distinct root-cause bugs, confirmed across every run to date** — not 8,
not 4. Bug 5 (alternating array/inline-table recursion) is real, newly
confirmed in Run 25, predicted correctly in advance by the hand-written
`crash_hunt` probe before the agentic loop ever reached it, and is a
genuinely different recursion cycle from bugs 1 and 3 (two functions taking
turns, not one function repeating) — see the bugs-found summary table above,
row 5, for the canonical three-signature mapping. State the 8-vs-5 gap
explicitly in the report rather than quoting `INDEX.md`'s count unexamined:
it is a real, demonstrated case where the automated triage number needed a
human check before being trustworthy, which is itself evidence of triage
instinct, not a flaw to hide.

## Case 10: two defects in the feedback signal itself — one of them permanently unsatisfiable ⭐

**Date:** 2026-08-20 · **Branch:** `module-7b-crash-hunting-3`

Belongs in the report's **proxy-signal** discussion, which the assignment
asks about directly ("what proxy signal did you choose to make the loop
actually improve the generator across iterations, and why?"). Both defects
are in `agent/summarize.py`'s `render_feedback()` — the function that
*is* the feedback signal — and neither is visible from the loop's console
output. They were found by tracing the data path rather than by observing
a failure, which is why they survived 25 runs.

### Defect 1: the depth directive could never be satisfied

`DEPTH_TARGETS`' final value is **90,000**. The directive fires when
`max_depth_cumulative < depth_target`. But tracing where that number comes
from:

- `summarize()` computes `accepted = [r for r in records if r.verdict ==
  ACCEPT]`, then derives `depths` from `accepted` **only**;
- `LoopState.observe()` likewise updates `max_depth_reached` inside
  `if accepted:`.

So both depth figures count **only documents that did not crash**. Arrays
crash at ~48,000 and inline tables at ~80,000 — therefore *a document deep
enough to reach the 90,000 target crashes, and a crashing document is never
counted*. The target is unreachable by construction.

The consequence is measurable in Run 25: accepted depths were 7 / 14 /
4,194 / 34,899 / 41,802 against a 90,000 target, so `"PUSH DEPTH MUCH
FURTHER"` fired on **every iteration of a run that was already producing
1,127 crashes**. Wasted directive pressure that competed with genuinely
useful directives, and pushed toward exactly the deep-branch dominance that
threatens the 20% acceptance floor.

**Fix:** a new `max_depth_generated` figure computed from *all* records,
crashes included, now gates the directive; the feedback body shows both
numbers with the distinction spelled out. `max_depth_this_iteration` and
`max_depth_cumulative` deliberately keep their accepted-only meaning,
because `comparison/gemini/metrics.{md,csv}` already stores those figures
for runs 15-25 and redefining them would silently break cross-run
comparability.

**The transferable finding:** a metric that filters out failures cannot be
used as a target for producing failures. The depth signal and the crash
objective were in direct contradiction, and the loop had no way to report
that — it just kept asking for something it had already achieved but
refused to measure.

### Defect 2: no crash-diversity term at all

The feedback reported crashes as
`"N unique crash signature(s) so far: 939402a0547c, e857b4530c96, ..."` —
raw hex digests, which carry nothing the model can act on, since nothing
tells it what *shape* produced each one. More importantly, **no directive
in the entire list ever asked for a crash mechanism that had not been seen
yet.** The signal steered on acceptance, missing productions, depth, and
novelty — never on crash variety. Nothing pushed away from re-finding the
same bugs, which is precisely the observed behaviour: runs 17, 20, 21 and
24 each returned the identical five buckets.

**Fix:** a `CRASH_MECHANISMS` table maps each known digest to the input
shape behind it ("nested arrays", "dotted keys", "alternating
array/inline-table nesting", …), so the feedback names mechanisms instead
of digests; and a new directive names the shapes already found and asks for
one that stresses a different parser path. An unrecognised digest
deliberately falls through to the digest itself — a signature missing from
the table is a newly-discovered one, and hiding it behind a generic label
would defeat the purpose.

**Why it points at level *content*, not more depth:** the accompanying
experiment (fix-log entry 9) established that two documents nested equally
deep crash in *different* parser functions depending on what each level
contains. Changing the alternation pattern re-landed in known buckets;
changing a bare key to a **quoted** one produced `c04d038a7956`, the first
signature ever to contain `norm_basic_str`. So the directive asks the model
to vary what sits at each level, which is the lever that actually moves
signatures.

**Status:** both fixes verified against synthetic state — the depth
directive now stops firing once generated depth clears the target, the
diversity directive fires with readable mechanism names, and an unknown
digest survives the mapping. Not yet observed on a live run.

## Case 11: Run 29 — deleting rules 16/17 entirely (not just abstracting them)

Case 7 tested *rewording* rules 16-17 from concrete to abstract, keeping
them in the prompt. This is a stronger test: **delete rules 16 and 17
outright** (commented out, not just softened) and see what a completely
unguided prompt produces on its own, five bugs deep into the project.

**What survived without the rules.** `agent/strategies/iter_02_strategy.py`
(Run 29, iteration 2) shows the model independently reinvented the same
*technique* rule 16 used to spell out — a `deep_toml_value()` composite
that draws a random integer depth and builds the string by repetition
(`"[" * depth + val + "]" * depth`) rather than real recursion. Nobody
told it to do this in Run 29's prompt; it follows from rule 14's general
"recursion can't reach extreme scale, use a counter" guidance, which was
*not* removed. Triage still surfaced 5 of the 9 known signatures
(`e857b4530c96`, `3db1e06f41e9`, `939402a0547c`, `80953bb88ca2`,
`af1d0280777e` — `triage/reports/run_29/INDEX.md`), so the core
overflow-by-deep-nesting idea is robust to losing the worked example.

**What did NOT survive.** Three things dropped out entirely:
- The dotted-key overflow (`55628614cd6c`) and the quoted-key alternating
  variant (`c04d038a7956`) never appeared. `deep_toml_value()` only builds
  `array`/`inline`/`mixed` shapes with a bare key — nothing dotted, nothing
  quoted — because rule 16 was the only place those two specific shapes
  were ever named.
- The sibling-key O(n²) hang (`unparsed_timeout`) never appeared either.
  With rule 17 gone, nothing in the prompt asks for many flat sibling keys
  in one table at all; that bug class needs its own distinct instruction,
  it doesn't fall out of the depth-escalation guidance.

**Why the numbers looked strange at first glance (both explained by
reading the actual code, not guessed):**
- *"findings: 0" in iterations 0, 1, and 3.* `DEPTH_TARGETS = [12, 200,
  4_000, 30_000, 90_000]` (`agent/summarize.py`) ramps the requested depth
  up gradually by iteration index — iterations 0-1 aren't even asking for
  dangerous depth yet (measured max depth 7 and 19 that run), so nothing
  crosses a real crash threshold. Iteration 3's zero is different: the
  model was asking for real depth by then, but `deep_toml_value()` draws
  its depth from **one shared range (100-50,000) for every shape**, unlike
  rule 16's five *measured, per-shape* floors (arrays ~48k, inline tables
  ~80k, dotted keys ~90k-100k, ...). Without differentiated floors, whether
  a given draw actually clears the real threshold for whatever shape it
  happened to pick is down to chance, not design — so a whole iteration can
  legitimately land under threshold on every draw.
- *"max depth" jumping to 10,889 and then staying there.* This field
  (`max_depth_cumulative` in `agent/summarize.py`) is a **running maximum
  across the entire run**, never reset per iteration — it only reports the
  single deepest *accepted* (non-crashing) document seen so far. Iteration
  2 happened to draw a depth (comfortably under the real ~48k array
  threshold) that parsed successfully; that value then persists through
  iterations 3-4 unchanged because nothing later beat it. It does not mean
  iterations 3-4 stopped generating deep documents.

**Why this belongs in the report, alongside Case 7.** Case 7 showed
*rewording* the rules abstractly hurt speed and results. Case 11 shows a
sharper distinction: the general *technique* (rule 14's counter-based
repetition idea) is robust and gets reinvented on its own — but the
*specific, measured parameters* (per-shape thresholds) and the
*deliberately distinct bug classes* (dotted keys, quoted keys, sibling-key
count) do not emerge without being named. This draws an honest line for
the report between "the LLM discovered this" (bugs 1-4's core mechanism,
robust across Case 11) and "the LLM reproduces this because it was told
the recipe" (bugs 1-4's exact thresholds, and bug 5's specific shape,
Case 9) — the same distinction Case 7's revert already implied but this
run makes concrete with signature-level evidence.

**Recommendation: keep both versions, and disclose which bug came from
which.** Neither "rules in" nor "rules out" is simply the better choice —
they answer different questions the assignment cares about:
- **Rules in** (runs 27-28): 9 signatures, all 5 bug types, every run.
  Reliable, but can't honestly be presented as pure LLM discovery for
  bugs 2 (dotted-key), 4 (sibling-key hang), and the quoted-key variant
  of bug 5 - the prompt names the exact shape and measured threshold for
  each.
- **Rules out** (Run 29): only 3 of the 5 bug types (array overflow,
  inline-table overflow, the bare-key alternating variant) - fewer bugs,
  but every one of them is genuinely LLM-driven: the model reinvented the
  underlying repetition technique from rule 14's general guidance alone,
  without being shown the specific shape.
The strongest, most honest thing to put in the report is not "the LLM
found 9 bugs" - it is a one-line attribution per bug: which came from the
loop's own exploration (bugs 1, 3, and the bare-key variant of 5) and
which only appeared after the prompt was deliberately given the exact
recipe (bug 2, bug 4, the quoted-key variant of 5). The assignment's own
Challenges section explicitly asks for judgment calls like this one to be
named, not hidden behind a single combined bug count.

## Terminology note: "grammar breadth", not "coverage"

The metric formerly called "coverage" throughout this project (in code,
logs, and prose) was renamed to **"grammar breadth"** across the entire
repository on `module-7b-crash-hunting-rename`. Worth documenting as its
own entry, because the reasoning is a real judgment call, not a cosmetic
preference.

**Why it mattered.** The assignment explicitly forbids real code coverage
of the target library — no instrumenting `tomlc99`'s compiled binary to
see which lines/branches executed. This project never did that. But the
project's own proxy signal had, since early on, been calling itself
"grammar-production coverage" - a name that shares a word, and therefore
an easy-to-conflate surface, with the thing being forbidden. A reader
skimming the report or the code could reasonably misread "coverage" as a
claim of using the forbidden signal, when the actual mechanism is
completely different: a regex scan over the *generator's own output
text*, computed before that text is ever sent to the parser (see
`pipeline/features.py`'s `PRODUCTIONS` and `_max_depth`-style helpers).
It measures "which grammar constructs has our own generator's output
contained," never "which lines of `tomlc99.c` ran."

**What changed, concretely:** `agent/coverage.py` → `agent/breadth.py`;
`coverage_fraction` → `breadth_fraction`; `cumulative_coverage` →
`cumulative_breadth`; `covered_productions` → `reached_productions`;
every JSON/CSV field, console print, prompt-rule sentence, and prose
mention across `OBSERVATIONS.md`, `progress_report.md`,
`PROJECT_SUMMARY.md`, `explanation.md`, `logs/RUN_HISTORY.{md,jsonl}`,
`comparison/*/metrics.csv`, `comparison/*/README.md`, and
`report/generate_artifacts.py`'s generated tables. Historical data
(already-logged JSONL/CSV records, the persisted `loop_state.json`) was
migrated in place rather than left inconsistent with the renamed code.

**What deliberately did NOT change:** every place the word legitimately
refers to the *forbidden* kind - e.g. `progress_report.md`'s "no
code-coverage instrumentation available" and its own "what I'd change...
with real coverage instrumentation" future-work paragraph, and
`PROJECT_SUMMARY.md`'s "(no code coverage available)" section header.
Those sentences are correctly using the word for what it actually means;
renaming them would have introduced the opposite confusion.

**Why this belongs in the report as its own point, not just a rename:**
it demonstrates the same self-auditing discipline as Case 9 and Case 10 -
noticing that a term this project chose could be misread against the
assignment's own explicit constraint, and fixing it deliberately rather
than leaving it for a grader to puzzle over.
