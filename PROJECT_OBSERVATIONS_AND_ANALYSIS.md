# Complete Project Analysis — Agentic Fuzzing of `tomlc99`

**Date:** 2026-09-03
**Scope:** Full retrospective — planning, testing, strategies, model comparison, and results analysis from the entire 47-run project lifetime.
**Audience:** Self-reference document capturing everything we did, why we did it, and what we learned, especially across the four different LLM provider generations (Ollama → Groq → Gemini → OpenAI).

---

## 1. Executive Summary

This project builds an **LLM-driven agentic grammar fuzzer** for `tomlc99`, a small C TOML parser. The core insight: instead of throwing random bytes at a parser (traditional fuzzing), we give an LLM a formal ANTLR grammar for TOML and let it write a Python [Hypothesis](https://hypothesis.readthedocs.io/) strategy that generates test inputs, then iteratively refine that strategy based on feedback. No code-coverage instrumentation is allowed (blackbox constraint) — only sanitizer-based crash detection.

**Headline results:**
- **5 confirmed distinct bugs** found in `tomlc99` (4 memory-safety + 1 DoS), all stemming from the same root cause: unbounded recursion/nesting in the parser.
- **47 runs** logged across **4 different LLM providers** (Ollama → Groq → Gemini → OpenAI).
- **17 prompt rules** added iteratively, each in response to a specific observed failure (chronological record in `OBSERVATIONS.md`).
- **13 documented investigation cases** in `OBSERVATIONS.md` capturing every major finding, dead-end, and judgment call.
- The proxy signal (originally called "coverage," renamed to **grammar breadth**) was itself found to be flawed — the depth signal only counted brackets, missing dot-chain and sibling-key axes. Fixed in Case 13.
- Several real bugs in the loop's own plumbing were found and documented (Cases 3, 9, 12, 13).

---

## 2. Project Structure & Workflow

### 2.1 Eight-Module Branch Layout

The work was split into 8 modules, each on its own git branch:

1. **module-1-grammar-adaptation** — Found ANTLR's TOML grammar and documented 5 real divergences from `tomlc99`'s actual behavior.
2. **module-2-harness-build** — Built `harness/toml_harness.c` with AddressSanitizer + UndefinedBehaviorSanitizer.
3. **module-3-baseline-pipeline** — Naive baseline strategy (`pipeline/baseline_strategy.py`) to prove plumbing works.
4. **module-4-agentic-loop** — The LLM-driven agentic loop itself (`agent/loop.py`).
5. **module-5-feedback-signal** — Designed proxy signals (grammar breadth, acceptance rate, novelty, depth) since no coverage instrumentation is allowed.
6. **module-6-crash-triage** — `triage/` tooling: dedupe, minimize, verify.
7. **module-7-report** (current branch) — Final write-up + side-experiments (7b/7c/7d).
8. **module-8-packaging** — Final packaging for submission.

### 2.2 The Agentic Loop Architecture

```
Seed (iter 0) → Validate (6 gates) → Run (500 examples) → Summarize → Refine → next iter
                    ↑                                                       ↓
                    └──────────── feedback ──────────────────────────────────┘
```

- **Seed:** First iteration gives the LLM the grammar + 17 numbered rules.
- **Validate:** Six gates — syntax check, import whitelist, exec/export, 25-sample draw, recursion check (depth>1 in samples), 40-example acceptance probe (must be ≥20%).
- **Run:** `@settings(max_examples=500)`, `timeout_seconds=5` per input.
- **Summarize:** Computes per-iteration metrics: accepted count, breadth (fraction of tracked grammar productions seen), novelty, max depth, findings.
- **Refine:** Feeds summary back to LLM with directive: "PUSH DEPTH MUCH FURTHER" if target unmet, or "FIND A CRASH WITH A DIFFERENT MECHANISM" if same signatures recur.

### 2.3 Key Files & Components

| File/Dir | Purpose |
|----------|---------|
| `config.yaml` | Central config: harness exit codes, acceptance floor, depth buckets, frame ignore patterns |
| `grammar/TomlLexer.g4` & `TomlParser.g4` | ANTLR TOML grammar |
| `grammar/adaptations.md` | 5 documented divergences from `tomlc99` |
| `harness/toml_harness.c` | C harness with sanitizers |
| `pipeline/baseline_strategy.py` | Naive generator (random text, TOML-ish lines) |
| `pipeline/run_baseline.py` | Pipeline runner |
| `pipeline/runner.py` | `HarnessRunner` + `RunLogger` |
| `pipeline/crash_hunt_strategy.py` | Hand-written parametric fuzzer for crash hunting |
| `pipeline/features.py` | `extract_features()`: tracks 30 grammar productions, depth, dot-chain length, sibling count |
| `agent/loop.py` | The agentic loop driver |
| `agent/seed.py` | Initial strategy generation + 6-gate validation |
| `agent/summarize.py` | `render_feedback()` — the feedback signal in code |
| `agent/validator.py` | Six validation gates |
| `agent/prompts.py` | `STRATEGY_CONTRACT` (17 rules) + seed/refine templates |
| `agent/breadth.py` | Grammar breadth computation (renamed from `coverage.py`) |
| `triage/run_triage.py` | Triage pipeline (dedupe, minimize, verify) |
| `triage/signature.py` | Stack signature hash with frame normalization |
| `triage/minimize.py` | Delta-debugging minimization |
| `triage/verify.py` | Re-run minimized reproducers |

---

## 3. Phased Plan — What Was Done In Order

### 3.1 Phase 1: Grammar & Adaptations (Module 1)

- Used ANTLR's `grammars-v4` TOML grammar as-is (not re-derived).
- Hand-probed `tomlc99` against 9 edge-case checklist items.
- Found **5 real divergences**:

| # | Divergence | Class |
|---|------------|-------|
| 1 | Trailing comma in inline tables `{a=1,b=2,}` | Superset (toMLc99 accepts, grammar forbids) |
| 2 | 19-digit fractional seconds | Variant (silently truncated to 3 digits) |
| 3 | Integer past INT64_MAX | Variant (silently relabeled as float) |
| 4 | Leading-zero integer `007` | Variant (passes first parse, fails later accessor) |
| 5 | Deep array nesting `[[[[...]]]]` | **Crash** — SIGSEGV at ~48,000 levels |

### 3.2 Phase 2: Harness & Sanitizer Build (Module 2)

- Wrote `harness/toml_harness.c`: feeds input to `tomlc99`'s parser + typed accessors.
- Compiled with `-fsanitize=address,undefined`.
- **Exit-code contract:** `0`=accept, `2`=well-formed reject, `64`=harness misuse, `86`=sanitizer catch.
- **Classification order:** timeout → sanitizer text → fatal signal → exit code (sanitizer is authoritative regardless of exit code).

### 3.3 Phase 3: Baseline Pipeline (Module 3)

- Deliberately naive generator: random text, TOML-ish key=value lines.
- Ran ~9,050 examples to verify the generate → harness → log pipeline works end-to-end.
- Zero crashes expected/found — this step proves plumbing, not bug-finding.

### 3.4 Phase 4: Agentic Loop (Module 4)

The loop structure (seed → validate → run → summarize → refine) is unchanged across all 47 runs. What changed:

- **LLM provider** (see Section 6).
- **Prompt contract rules** (grew from 6 → 17 rules over time).
- **Feedback signal sophistication** (depth buckets, then geometric targets, then crash-diversity directive).
- **Validator gates** (recursion check was rewritten from text-search to actual depth measurement after Case 4).

### 3.5 Phase 5: Feedback Signal Design (Module 5)

Without code coverage, we need proxy signals. Originally chose:

| Signal | What it measures |
|--------|------------------|
| **Grammar breadth** | Fraction of 30 tracked TOML productions seen in accepted documents |
| **Acceptance rate** | % of generated inputs that `tomlc99` parses successfully |
| **Novelty rate** | % of generated documents with a unique shape |
| **Max nesting depth** | Deepest bracket depth reached |

**Discovered flaws in this signal (Cases 4, 10, 13):**
- Grammar breadth can be gamed — Case 4 showed it climbed while documents got simpler.
- Depth-as-accepted-only was mathematically unsatisfiable (crashes aren't accepted, so 90,000-deep docs that crash never count toward the target).
- Depth-as-bracket-count was blind to dot-chain length and sibling count — Case 13 found this caps what the loop can discover at 3 of 5 bugs.

### 3.6 Phase 6: Crash Triage (Module 6)

Pipeline:
1. **Detect** (`pipeline/runner.py`): fatal signal, sanitizer text, timeout.
2. **Capture** (`pipeline/logs/*.jsonl`): input + stderr + signal.
3. **Deduplicate** (`triage/signature.py`): SHA-256 hash of normalized top-5 stack frames with recursion collapsing.
4. **Minimize** (`triage/minimize.py`): delta-debugging.
5. **Verify** (`triage/verify.py`): 3 repeat runs.

Real bugs found in triage tooling itself (Case 3): missing `__sanitizer::` frame pattern, 3-state vs 2-state verification model, frameless overflows collapsing distinct bugs.

### 3.7 Phase 7: Report & Side-Experiments (Module 7, current)

Current branch experiments:
- **module-7b-crash-hunting-2**: Rule 16 amendment with per-shape floors.
- **module-7c-tweaking-prompts**: Attempt to make feedback signal use real crash data (Case 12 fix).
- **module-7d**: Scale-axis experiment (Case 13).

---

## 4. Strategy Evolution — What Changed Across Runs

### 4.1 The 17 Prompt Rules (Chronological)

The `STRATEGY_CONTRACT` in `agent/prompts.py` grew from 6 to 17 rules. Each was added in response to a specific observed failure:

| Rule | Date | Bug it addresses |
|------|------|------------------|
| 6 | Initial | `@composite` import + call pattern (Case 1) |
| 7 | Case 1 | Hallucinated `st.datetimes(formats=...)`, `+` on strategies, `.map(lambda a,b:...)` arity |
| 8 | Case 2 | Type-consistency: `int`/`float` need `.map(str)`, `draw()` wrappers, return-shape matching |
| 9 | Case 4 | Banned `.filter()` on `st.text()` for shape constraints (caused 145-of-500 examples silently) |
| 10 | Case 4 | Containers must be genuinely self-referential (not just `@composite`-decorated) |
| 11 | Case 2 (recurring) | Banned `st.dates()`/`st.times()`/`st.datetimes()` entirely (min_value/min_date confusion) |
| 12 | Case 4 (validation) | Top-level document lines must be `key=value`/`[table]`/`[[array_table]]`, never bare containers |
| 13 | Run 8 | Table headers must reuse `key()`, never raw `st.text()` (control chars in headers) |
| 14 | Run 6 | Depth-escalation: bias `one_of()` toward recursive call; thread depth counter that actually increments |
| 15 | Run 7 | Restrict `key()` alphabet; exclude quotes/newlines from quoted content |
| 16 | Run 9 (Case 5) | **Most important:** integer-repetition technique to reach extreme depth (48k+) where recursion can't |
| 17 | Run 15 | Many-siblings O(n²) hang: separate `many_siblings()` composite |

**Rule 16 is the headline rule.** It teaches the model to draw an integer `n` and build the string by repetition (`"[" * n + "1" + "]" * n`) instead of recursion — because recursive generation provably cannot reach 48k+ depth (Hypothesis's data budget resists). This single rule changed everything (Case 5): depth went from 4 to 5,000 in one iteration.

**Rule 16 was amended twice:**
- *Amend 1 (Case 5/Run 9 fix):* Raised bounds to 1k–120k, required setting `max_value` from feedback target rather than example, wired all 5 shapes into `one_of` (not just `deep_array`), required deep branches ≤1/5 ratio to protect the 20% acceptance floor.
- *Amend 2 (module-7b-2/Run 25):* Replaced one shared depth floor with 5 *measured, per-shape* floors (arrays 60k-100k, inline tables 85k-115k, dotted keys 100k-130k, mixed nesting 60k-80k, quoted mixed 20k-45k), and taught a 5th shape (`deep_quoted_mixed`) found by hand-written `crash_hunt`.

### 4.2 Validator Evolution

- **Original recursion check:** `any(m in code for m in RECURSION_MARKERS)` — pure text search for `@composite`. Missed the Case 4 bug where `@composite` was present but the function never recursed.
- **Fixed recursion check (Case 4):** Drawn samples are now measured by `pipeline.features.extract_features()`; `uses_recursion` is `True` only if some sample exceeds depth 1.

### 4.3 Feedback Signal Evolution

- **Original:** "PUSH DEPTH MUCH FURTHER" when `max_depth_cumulative < depth_target`.
- **Case 10 fix #1:** Added `max_depth_generated` (from *all* records, crashes included) to gate the directive — because the original counted only accepted, but crashes aren't accepted.
- **Case 10 fix #2:** Added `CRASH_MECHANISMS` digest-to-English mapping + a new directive "FIND A CRASH WITH A DIFFERENT MECHANISM" asking for shapes that stress unseen parser paths.
- **Case 12 fix:** Loop now calls `parse_signature()` on every crash as it happens, folding results into `LoopState.crash_frames` so the feedback names real target functions instead of raw digests.
- **Case 13 fix:** Replaced single-axis depth signal with multi-axis: `max_depth` (brackets), `dotted_key_depth` (dot chain), `max_siblings` (entries per scope) — all three measured from the grammar's `*`/`+` quantifiers and recursive rules.

### 4.4 The Depth Targets

`DEPTH_TARGETS = [12, 200, 4_000, 30_000, 90_000]` in `agent/summarize.py` — geometric escalation across the 5-iteration budget. Replaced (Case 12) with a formula: `next_target = 8x deepest_generated_so_far`, bootstrapped at 12, capped at ~`harness.max_input_bytes / 8`.

---

## 5. Findings — What We Discovered

### 5.1 The 5 Confirmed Bugs in `tomlc99`

| # | Bug | Mechanism | Threshold | Type | Deterministic |
|---|-----|-----------|-----------|------|---------------|
| 1 | Array-nesting stack overflow | `parse_array` (`toml.c:1057`) recurses once per `[`, no depth limit | ~48,000 | stack-overflow | 3/3 ✓ |
| 2 | Dotted-key stack overflow | `parse_keyval` (`toml.c:1106`) recurses once per `.` in `a.b.c...=1` | ~90,000–100,000 | stack-overflow | crashes 3/3, signature unstable |
| 3 | Inline-table stack overflow | `parse_inline_table` ↔ `parse_keyval` recurse into each other per `{` | ~80,000 | stack-overflow | 3/3 ✓ |
| 4 | Many-siblings O(n²) hang | `toml_table_in()` linearly scans existing keys on every insert | ~15,000+ keys crosses 5s timeout | DoS/hang | timing-threshold, not memory |
| 5 | Alternating array/inline-table stack overflow | `parse_array` ↔ `parse_inline_table` call each other (3rd distinct recursion cycle) | ~40,000–80,000 | stack-overflow | crashes, signature varies (3 sigs) |

**Bug 5 has a quoted-key variant** (`[{"k"=[{"k"=...}]}]`) producing signature `c04d038a7956` — first signature with `norm_basic_str` in it. Runs deeper actually hides this signature (going past ~45k reverts to known buckets); found at *lower* depth (~25k), breaking the "push depth further" pattern.

**All 5 bugs trace to the same root cause:** `tomlc99`'s recursive-descent parser and table implementation impose no limits on attacker-controlled input size or nesting. 4 are memory-safety (CVE-class in production); 1 is DoS.

### 5.2 How Each Bug Was Found

| Bug | Discovery path |
|-----|----------------|
| 1 | Hand-found during initial grammar-comparison (Module 1) — array nesting at 48k segfaulted |
| 2 | Hand-found reading `toml.c` during crash-hunting planning |
| 3 | Cross-confirmed: hand-written `crash_hunt` parametric probe + later found by agentic loop |
| 4 | First *fully autonomous* discovery by the agentic loop in Run 15 (Gemini), 72 occurrences |
| 5 | Predicted by `crash_hunt`'s `deep_mixed_nesting` campaign, taught via rule 16 amendment, first fired autonomously in Run 25 |

### 5.3 The Honest Triage Story (Case 9)

Raw triage reports **8 unique signatures** after dedup for Run 25. Reading the actual crashing inputs by hand showed 3 of those 8 are the **same bug** (alternating nesting) captured at different random points mid-crash:
- `af1d0280777e` — top frame `malloc → STRNDUP → normalize_key → parse_keyval`
- `3db1e06f41e9` — top frame `strnlen → STRNDUP → normalize_key → parse_keyval`
- `80953bb88ca2` — top frame `malloc → expand → expand_arritem → parse_array`

These are the two halves of the alternating cycle (`parse_keyval` calling `parse_array` calling `parse_keyval`...) — which half is on top at stack-overflow time is decided by stack layout, not input. **Honest count: 5 bugs, not 8.**

---

## 6. Strategy & Results by Model

We ran the same agentic loop against 4 different LLM providers over the project's lifetime. This section compares their failure modes, costs, and what each was best at.

### 6.1 Provider 1: Ollama (Local `qwen2.5-coder:7b`) — Runs 1–8 prehistory + Case 1 study

**Status:** Fully abandoned. Used only for Case 1's reliability study (12 attempts total).

**Failure modes:**
- **Hallucinated Hypothesis API calls:** `st.datetimes(formats=...)`, `st.empty_strings`, `+` on strategies, `.map(lambda a, b: ...)` (arity wrong).
- **Recurrence after explicit prohibition:** Even when rules 6/7 stated "NEVER do X" with verbatim errors quoted back, the model repeated the same forbidden pattern (Rule 7 of `STRATEGY_CONTRACT` was written for this).
- **Pass rate:** 0/12 attempts across 3 rounds passed all 6 validation gates.

**Key finding (Case 1):** Two failure categories behave very differently under prompt fixes:
- **Instruction-following failures** (forgetting imports, forgetting to call decorated function) — **fully fixed** by adding concrete worked examples.
- **API-hallucination failures** (inventing function arguments that don't exist) — **not fixed** by worked examples or even "NEVER do X" rules. The model repeated the exact forbidden pattern after being told verbatim it didn't exist.

**Decision:** Stopped after 12 attempts; escalated to Groq's larger model rather than continue patching. The 14B local model wasn't practical on 6GB VRAM.

### 6.2 Provider 2: Groq (`llama-3.3-70b-versatile`) — Runs 1–12 (then model deprecated)

**Status:** Primary workhorse for early iterations. Ran 12 full/partial runs. Model retired by Groq 2026-08-18.

**Failure modes:**
- **Ordinary composition bugs** (qwen's failure class was essentially absent):
  - Type mismatches: `int` joined as text → `expected str instance, int found`
  - Forgotten `draw()` wrapper → `expected str instance, LazyStrategy found`
  - Mirror-image: calling `.map()` on already-drawn values → `'list' object has no attribute 'map'`
- **Specific recurring wrong belief:** `st.dates(min_date=...)` — wrong argument name (3 independent occurrences across runs 2, 5, 6). Structurally identical to qwen's `st.datetimes(formats=...)`, just less catastrophic.
- **Acceptance-floor failures:** Strategies that ran fine but generated <20% valid TOML (6 of 22 attempts).

**Pass rate (Case 2 data):** 3/22 individual attempts passed, but **3 of 7 runs (43%) eventually succeeded within attempt budget**.

**Cost/speed:** Free tier, $0.00. Daily token quota (not per-minute) was the real constraint — one API key exhausted mid-session with a 2,693-second wait, resolved by minting a second free key.

**Results:**
- Best finding run: **Run 10** (Gemini-style run with rule 16): findings 51→66→74→78→49 across 5 iterations, max depth 40k–52k.
- **Run 12:** findings 22→27→32→40→58, max depth 49,599.
- **No fully self-driven crash discovery until Gemini (Run 15 first fired Bug 4 autonomously).**

**Key finding (Case 2):** Different model tiers fail in *qualitatively different ways* — qwen's hallucinations were prompt-resistant; Llama-70B's mistakes were ordinary and prompt-fixable. This matters more than raw model quality for loop design.

### 6.3 Provider 3: Gemini (`gemini-3.6-flash`) — Runs 13–39 (primary workhorse)

**Status:** Workhorse from mid-August 2026 until Groq deprecation, then primary for the rest of the project. ~25 full runs completed.

**Why Gemini was adopted:**
- Groq deprecation forced a live provider switch (Case in `config.yaml` comments).
- Gemini free tier offers ~250,000 TPM (vs Groq's 8,000) — large enough for the project's ~9k-token prompts.
- Confirmed working live against full-size prompt (not just from docs).

**Failure modes (Cases 6, 7, 11):**
- **Validation gate gaps** (Case 6): 25-sample draw check can miss rare broken branches in `one_of` (Run 40, OpenAI, confirmed similar gap for GPT-4o-mini).
- **Slower wall-clock per iteration** (Case 15): ~33.8 minutes total for Run 27's 5-iteration loop, vs ~7.3 min for GPT-5.4 (Run 43) — a >4.5× speedup with GPT-5.4.
- **Abstract vs concrete prompt rules (Case 7):** Tested removing specific worked examples of depth techniques. Result: same/worse findings, but **~5 min/iter vs ~2.5-4 min/iter** for concrete rules — abstract reasoning costs more time per call.
- **Deleted rules test (Case 11, Run 29):** Removing rules 16/17 entirely while keeping rule 14's general "use a counter" guidance → model reinvented the *technique* on its own but couldn't reach per-shape thresholds without being told. Found 3 of 5 bugs.

**Key results (selected runs):**

| Run | Findings/iter | Max depth | Notes |
|-----|--------------|-----------|-------|
| 15 | 30→32→30→32→34 | 40,574 → 49,985 | First full Gemini run, all 5 bugs |
| 16 | 33→29→26→25→35 | 51,429 | Stable, breadth 100% by iter 2 |
| 17 | 33→32→25→29→90 | 51,935 | Iter 4 spike |
| 20 | 15→11→15→10→53 | 48,626 | High acceptance 77–96% |
| 21 | 20→21→17→34→61 | 49,999 | 5 bugs deduplicated, **3 verified deterministic 3/3** |
| 25 | 252→... | 7 | **Rule 16 amendment + scale-axis fix** — 1,127 crashes across run |
| 27 | 283 | 4 | Hardcoded rules 16/17, 5 bugs found |

**Cost:** Free tier, ~$0.00 actual. Wall-clock dominates.

**The Gemini-vs-Groq comparison point (Cases 6, 7, 15):** Both succeeded at the task; the qualitative difference is that Gemini was the first model to autonomously find Bug 4 (the O(n²) hang) in Run 15. Groq models earlier in the project had prompt rules 16/17 only after we discovered the techniques ourselves, while Gemini's runs with the same rules fired Bug 4 without hand-feeding.

### 6.4 Provider 4: OpenAI (`gpt-5.4`, `gpt-4o-mini`, `gpt-5.6-luna`) — Runs 40–47

**Status:** Most recent provider, exploratory. Three different OpenAI models tested in 8 runs (40-47).

#### 6.4.1 GPT-4o-mini (Runs 40, 41)

**Failure modes (Case 14):**
- **Method binding errors** (Run 40): Called `.map(...)` on `draw(st.integers(...))` — but `draw()` returns an `int`, not a strategy. Got `AttributeError: 'int' object has no attribute 'map'`.
- **Sequence element type error** (Run 41): `''.join(...)` on drawn tuple sequences containing un-casted `int`s.
- **Seed retry budget exhaustion** (Run 41): 8 consecutive attempts failed across `imports`/`draw`/`exec` gates — budget cap (`max_attempts: 8`) safely aborted without corrupting loop state.

**Pass rate:** 1/7 (Run 40, iter 3); 1/8 (Run 41, iter 0 then crashed at draw stage).

**Cost:** Run 40: 80,301 tokens, $0.016 USD, 71.7s generation time.

**Results (Run 40):**
- 395 crashing inputs captured.
- 4 raw sanitizer signatures deduplicated → **3 unique root-cause bugs**:
  - `unparsed_timeout` (173 inputs) — Bug 4 (many-siblings O(n²))
  - `55628614cd6c` (151 inputs) — Bug 2 (dotted-key overflow)
  - `939402a0547c`/`e857b4530c96` (71 inputs) — Bug 1 (array-nesting overflow)
- 66% grammar breadth, max nesting depth 6.
- **Found 3 of 5 known bugs.**

#### 6.4.2 GPT-5.4 (Runs 42, 43, 44) — The fastest, most successful model

**Status:** ⭐ **Best overall performer.** 3 runs, all PASSED all 5 iterations.

**Failure modes:**
- Occasional acceptance-floor failures (1/40 or 6/40 on first attempts; pass on attempt 2 or 3).
- Lower validation pass rate per attempt than Gemini — needs 2-3 attempts vs Gemini's typical 1.

**Pass rate:** All 3 runs (42, 43, 44) completed 5 iterations.

**Cost/Speed (Case 15):**

| Model | Total wall-clock for 5-iter loop |
|-------|----------------------------------|
| Gemini (Run 27) | 2,032.8s (~33.8 min) |
| GPT-5.4 (Run 43) | 438.9s (~7.3 min) |
| **Speedup** | **4.6×** |

**Results:**
- **Run 42:** 9 signatures / 5 bugs (all known bugs). Wall-clock 73.8s for iter 0 alone.
- **Run 43:** Same — 100% grammar breadth, 5 bugs.
- **Run 44:** 9 signatures / 5 bugs. Findings detailed in INDEX.md:
  - Bug 4 (`unparsed_timeout`): 47 occurrences, 198,732 bytes minimized, deterministic
  - Bug 5 (`80953bb88ca2`): 23 occurrences, unstable-sig
  - Bug 5 (`c04d038a7956`): 44 occurrences, 106,153 bytes minimized, **deterministic** ✓
  - Bug 1 (`e857b4530c96`): 51 occurrences, unstable-sig
  - Bug 3 (`26e809dd9d85`): 20 occurrences, unstable-sig
  - Bug 5 (`3db1e06f41e9`): 14 occurrences, unstable-sig
  - Bug 5 (`af1d0280777e`): 8 occurrences, unstable-sig
  - Bug 1 (`939402a0547c`): 44 occurrences, 28,861 bytes minimized, **deterministic** ✓
  - Bug 2 (`55628614cd6c`): 11 occurrences, unstable-sig

**Key finding (Case 15):** GPT-5.4 generated *modular strategy helpers* (`_array_from_values`, `_inline_table_from_pairs`) that emitted cleaner, well-bounded string structures — significantly reducing serialization overhead during Hypothesis's 500-example pass. Result: sub-minute per-iteration times while still finding all 5 bugs.

#### 6.4.3 GPT-5.6-Luna (Runs 45, 46, 47) — The newest test

**Status:** Latest model variant tested. 3 runs, all PASSED 5 iterations.

**Failure modes:**
- Format string bugs: `unsupported format character 'b' (0x62) at index 3` (Run 47, attempt 1).
- Lambda arity bugs: `accept.<locals>.deep_key_document() takes 0 positional arguments` (Run 47, attempt 3).
- Acceptance-floor failures (10/40) on initial attempts.

**Pass rate:** All 3 runs completed.

**Results (notable):**

| Run | Findings/iter | Max depth | Acceptance | Breadth |
|-----|--------------|-----------|------------|---------|
| 45 | 197 (iter 0 alone) | 7 | 16% | 90% |
| 46 | 109 (iter 0) | 7 | 57% | 95% |
| 47 | 187 (iter 0) | 5 | 43% | 87% |

**Interesting note:** Luna (gpt-5.6-luna) had *low* max depth (5–7) but *high* findings counts (109-252 per iteration) — suggesting the model's strategies find bugs via short, dense shapes rather than deep nesting.

---

## 7. Cross-Model Comparative Analysis

### 7.1 The Failure Mode Taxonomy

Across all 4 providers, the consistent failure-mode categories are:

| Failure category | Ollama 7B | Groq 70B | Gemini Flash | GPT-5.4 | GPT-5.6-Luna |
|------------------|-----------|---------|--------------|---------|--------------|
| Hallucinated API | ★★★ (dominant) | ✗ (zero) | ✗ (zero) | ✗ (zero) | ✗ (zero) |
| Type-consistency bugs | ★★ | ★★★ | ★ | ★ | ★★ |
| Forgot `draw()` wrapper | ★ | ★★★ | ★ | ★ | ★ |
| Wrong arg name on real API | ★ (recurring) | ★★ (recurring) | ★ | ★ | ★ |
| Format-string bug | ★ | ★ | ★ | ★ | ★★★ (Run 47) |
| Lambda arity | ★★ | ★ | ★ | ★ | ★★ (Run 47) |
| Acceptance floor | ★ | ★★★ | ★★ | ★★ | ★★ |
| Slow per-iter wall-clock | ★ (no API cost) | ★★ | ★★★ (33min/loop) | ★ (7min/loop) | ★★ |

**Pattern:** Smaller models (Ollama 7B) fail at API knowledge; larger models (70B+) fail at composition; mid-size models (Gemini Flash) are competitive with Gemini's main weakness being speed; GPT-5.4/Luna have occasional exotic bugs (format strings) but otherwise the most efficient.

### 7.2 Cost & Speed Comparison

| Provider | Cost/run | Wall-clock/run (5 iter) | Bugs found/run |
|----------|----------|------------------------|----------------|
| Ollama 7B (local) | $0 | N/A — never passed validation |
| Groq 70B | $0 (free tier, daily limit) | ~10-15 min (when not rate-limited) | 0-2 |
| Gemini Flash | $0 (free tier) | ~33 min (Run 27 baseline) | 5 |
| GPT-4o-mini | ~$0.016 | ~10-15 min | 3 |
| GPT-5.4 | ~$0.05-0.20 (estimated) | ~7-12 min | 5 |
| GPT-5.6-Luna | ~$0.05-0.20 (estimated) | ~15-25 min | 5 |

**GPT-5.4 is the best by the speed-vs-bugs tradeoff.** 4.6× faster than Gemini while still finding all 5 bugs. Luna finds the same bugs but slightly slower and with more format-string bugs.

### 7.3 The Honest Provider Comparison Summary

What each provider taught us:

| Provider | Lesson learned |
|----------|----------------|
| Ollama 7B | API hallucinations are a hard capability ceiling, not a prompt-wording problem |
| Groq 70B | Larger models fail in *ordinary* ways prompt engineering can fix; typesafety is the dominant failure class |
| Gemini Flash | Reasonable speed, free, but iteration-time is dominated by long timeout chains in generated inputs |
| GPT-5.4 | Frontier models generate *modular* code that runs faster; the speed advantage compounds across iterations |
| GPT-5.6-Luna | Can find bugs via short dense shapes rather than deep nesting — different search strategy |

**The most transferable finding (Case 2):** Different model tiers fail in qualitatively different ways. The LLM-tier choice should be informed by *what failure class is most fixable with prompt engineering for your task*, not by raw model size.

---

## 8. Key Insights & Findings (The Most Important Lessons)

These are organized as the "headline findings" worth reporting. They are not TOML/`tomlc99`-specific — they're general lessons about agentic fuzzing with LLMs.

### 8.1 Prompt Anchoring (Case 5) ⭐

**Finding:** An illustrative constant inside a prompt example acts as a **hard ceiling**, not a starting point.

- Rule 16 used `max_value=5000` in its worked example.
- The model copied it verbatim (`n = draw(st.integers(min_value=200, max_value=5000))`).
- Depth sat at exactly 4999-5000 for all 5 iterations.
- The actual crash thresholds are 48,000-100,000, so 5,000 missed everything.
- A second instance: model defined `deep_inline_table` and `deep_dotted_key` but wired only `deep_array` into `toml_strategy` — two of three shapes never executed.

**Why this matters:** This is not about TOML or `tomlc99` — it reproduces on any LLM code-generation task where the prompt contains a worked example with specific numbers.

**How to fix:** Explicit instruction to set `max_value` from the *feedback's depth target*, not from the example; require wiring all defined shapes into `one_of`.

### 8.2 Proxy Signal Must Match Search Objective (Cases 4, 10, 13) ⭐

**Finding:** A proxy signal that filters out failures cannot be used as a target for producing failures.

- The original depth signal counted only *accepted* documents (those that parsed successfully).
- Documents deep enough to trigger a crash are not accepted.
- The depth directive asked for 90,000 but a 90,000-deep document crashes → never counted → kept firing "PUSH DEPTH MUCH FURTHER" on runs already producing 1,127 crashes.

**And:** A proxy signal that measures one axis is blind to bugs on other axes.

- `max_depth` counted only `[`/`]`/`{`/`}`.
- A 90,000-dot dotted-key chain reports `max_depth: 0`.
- The dotted-key crash signature was *invisible* to the feedback signal — the loop could never steer toward it.

**How to fix:** Multi-axis signal computed from *all generated* (not just accepted) records: `max_depth` (brackets) + `dotted_key_depth` (dot chains) + `max_siblings` (entries per scope) — derived mechanically from grammar rules with `*`/`+` quantifiers.

### 8.3 Recursive Generation Cannot Reach Extreme Depth (Case 5) ⭐

**Finding:** Hypothesis's own data budget inherently resists deep recursion.

- `st.lists(...)` with no size limit averages ~50-90 elements.
- A biased recursive strategy spreads *sideways* into a bushy tree, not *down*.
- Even forcing `min_size=1, max_size=1` (correct chain shape) only reaches depth 13 in 15 draws.
- The known crash depths are 48,000-100,000.

**How to fix:** Draw depth as an integer, build by repetition: `"[" * n + "1" + "]" * n`. This is the only technique that reaches crash depth.

**Implication:** No amount of prompt engineering can make `st.recursive`/`@composite` reach crash depth. This reframes the entire "the loop can't find bugs" story — it was never a model-obedience problem.

### 8.4 The Signal-Gaming Failure Mode (Case 4)

**Finding:** The proxy signal's "improvement" can mask structural degradation.

- First full 5-iteration run: grammar breadth climbed 18% → 47% (a real improvement).
- But: max depth stayed at 1, documents shrank (285 → 48 bytes), and the breadth gain came from *trivial scalar values*, not structural complexity.
- `findings: 0` was inevitable — the known bug needed ~48k nesting depth.

**How to fix:** Validator now measures recursion from *drawn samples*, not text search. Documents must actually achieve depth > 1 to pass gate 5.

### 8.5 Different Bug Class = Different Crash Mechanism (Cases 10, 11)

**Finding:** Raw crash-signature hex digests are useless to the LLM. The feedback must name *mechanisms*.

- Original feedback: `"3 unique crash signature(s) so far: 939402a0547c, e857b4530c96, ..."`
- Nothing actionable — the model has no way to know what shape produced each.
- 4 separate full runs (17, 20, 21, 24) each re-found the *identical* set of bugs because nothing pushed toward unseen mechanisms.

**How to fix:** Digest → mechanism mapping in `CRASH_MECHANISMS`; new directive "FIND A CRASH WITH A DIFFERENT MECHANISM" that names shapes not yet seen. Real fix (Case 12) further: parse signatures in-loop, name the actual target *functions* (`parse_array`, `norm_basic_str`) hit instead of just digests.

### 8.6 What Sits at Each Level Matters as Much as Depth (Case 10, Bug 5 quoted variant)

**Finding:** Two documents nested equally deep crash in *different parser functions* depending on what each level contains.

- Bug 5's plain alternating shape crashes `parse_array` ↔ `parse_inline_table`.
- Bug 5's *quoted-key* variant (`[{"k"=[{"k"=...}]}]`) crashes with `norm_basic_str` on the stack — a different signature entirely.
- Quoted key = unescaping work per level = stack runs out sooner = reproduce best at 25,000, *not* 48,000.
- Going deeper actually *hides* this signature (reverts to known `80953bb88ca2`).

**How to fix:** Rule 16's amendment 3 teaches the model to vary the *content* at each nesting level (bare keys, quoted keys, dotted keys, escaped values), not just the depth.

### 8.7 The Self-Defeating Interaction of Depth & Acceptance Floor (Rule 16 amendment 1)

**Finding:** Pushing depth comes at the cost of acceptance rate — and there's a hard 20% floor that rejects the strategy entirely if violated.

- A document that crashes doesn't count as "accepted."
- If deep branches dominate `one_of`, measured acceptance drops below 20%.
- Strategy gets rejected *before it ever runs* — losing the very crashes it was built to find.

**How to fix:** Worked example in rule 16 forces deep branches to be ≤1 in 5 of all branches: `[document()] * 20, deep_doc(deep_array), deep_doc(deep_inline_table), ...`.

### 8.8 Frame Stack Trace is Unstable at Extreme Depths (Case 3 Bug 2/3)

**Finding:** A 100% reproducible crash may have an unstable sanitizer signature.

- Stack-overflow crashes at 48k+ nesting can be so violent ASan can't unwind a clean trace.
- The signature falls back to `unparsed_<verdict>` — **identical for every frameless overflow regardless of root cause**.
- Two distinct bugs collapsed into one bucket.

**How to fix:** `_run_for_parseable_crash()` retries a crashing input up to 6 times to get a parseable stack before giving up. This stabilized the array bug's verification from "unstable 2/3" to "deterministic 3/3".

### 8.9 Validator Gate 5 Had a Self-Audit Gap (Case 4)

**Finding:** Pure text-search validators can be defeated by code that *looks right* but is structurally wrong.

- Original check: `any(m in code for m in RECURSION_MARKERS)` where `RECURSION_MARKERS = ("st.recursive", "@composite", ...)`
- Strategy with `@composite` decorators throughout reported `uses_recursion: True`.
- But the `array()` function never called itself — depth 1 forever.

**How to fix:** Compute `uses_recursion` from *drawn samples* — actually measure depth > 1 in practice.

### 8.10 Two Bugs in One (Case 9) — Triage's Own Number Needs Hand-Checking

**Finding:** Automated dedup can report 8 signatures when the true bug count is 5.

- Three of Run 25's signatures were byte-for-byte the same generated shape, captured at different random points in the alternating recursion cycle.
- Which phase of the cycle is on top at stack-overflow time is decided by stack layout, not input.

**How to fix:** No automated fix. **Read the actual saved crashing inputs**, not just the digest, before trusting `INDEX.md`'s count.

### 8.11 The Plumbing Bug Hidden in Plain Sight (Case 12)

**Finding:** `LoopState.crash_signatures` was declared and read in 4 places but written in exactly 0.

- Run 29's state: `"crash_signatures": []` despite 110 logged crashes.
- Feedback said `'crash': 17` in outcome counts **and** "No crashes found yet" in the crash-summary line — directly contradictory.

**How to fix:** Loop calls `parse_signature(rec.stderr, rec.signal)` on every finding, folding digests into `LoopState.crash_frames`. Names real target functions instead of digests.

**Process lesson:** Any "feedback" path that depends on internal state must be *traced end-to-end* on real logged data, not just assumed to work.

### 8.12 Cross-Model Speed Comparison (Case 15)

**Finding:** Frontier-tier models are dramatically faster at the loop's per-iteration execution, not just smarter at generation.

- GPT-5.4 generated *modular strategy helpers* (`_array_from_values`, `_inline_table_from_pairs`) that emit cleaner, well-bounded string structures.
- Less serialization overhead during Hypothesis's 500-example pass.
- Result: 4.6× speedup vs Gemini while still finding all 5 bugs.

---

## 9. The Final Configuration (module-7-report branch)

The currently checked-in configuration on `module-7-report` reflects everything we learned:

### 9.1 What's kept "on" (the graded version)

- **Hardcoded rules 16/17** — the specific worked examples for `deep_array`, `deep_inline_table`, `deep_dotted_key`, `deep_mixed_nesting`, `deep_quoted_mixed`, and `many_siblings` with measured per-shape floors.
- **All 17 prompt rules** — each one earned by a specific observed failure.
- **`DEPTH_TARGETS = [12, 200, 4_000, 30_000, 90_000]`** — geometric escalation.
- **`CRASH_MECHANISMS` mapping** — digests → English.
- **`max_depth_generated`** — counts all records, not just accepted.
- **`crash_signatures` integration** — loop parses signatures inline (Case 12 fix).
- **Three-axis scale signal** — depth, dot-chain, siblings (Case 13 fix).
- **Triage retry-for-parseable-signature** — up to 6 retries before giving up.
- **`agent/state/loop_state.json`** — `--resume` works across runs without losing state.

### 9.2 What's kept as documented experiments (not merged)

- **module-7c-tweaking-prompts (commits `c068b98` etc.)** — real plumbing fix to `crash_signatures` and multi-axis signal, but resulted in 3-of-5-bugs ceiling (vs 5/5 with hardcoded rules 16/17). Documented as a real attempt; reverted because hardcoded rules still beat it.
- **module-7b-crash-hunting-2 (rule 16 amendment 2)** — per-shape floors. **This one DID get merged into the main rules** (it's how Run 25 found Bug 5's 3 signatures).
- **Case 13 (scale-axis experiment)** — the multi-axis fix is *verified offline* on real logged data and fires correctly on replayed state, but not yet proven on a *fresh* live run with no hardcoded rules. The signal is better; the hint-free prompt still doesn't beat the hinted one.

### 9.3 What's NOT changed

- **No coverage instrumentation** — explicit assignment constraint.
- **5 iterations × 500 examples** — assignment budget.
- **5-second per-input timeout** — assignment constraint.
- **Acceptance rate floor: 20%** — needed to reject pathological generators.

---

## 10. What Wasn't Done / Open Questions

Things explicitly out of scope or deferred:

1. **Coverage feedback** would have let us drop several heuristics — but it's forbidden by the assignment.
2. **Longer iterations** (e.g., 10 instead of 5) — assignment says treat >5 as a sign the signal needs rethinking, not more budget.
3. **Frontier-tier model comparison** (Claude Opus 5, GPT-5.4+) beyond GPT-5.4 — `comparison/final_testing/claude/` is empty; planned but not yet executed as of this analysis.
4. **The `:07d`-on-`st.text()` bug class** — a rule 14 wasn't written because Case 2 ended the Ollama experiment before this specific bug appeared repeatedly. Documented as still open.
5. **Trim `progress_report.md` to 2 pages** — explicitly noted as the final submission task.
6. **Run Case 13 fix live** (not just replayed against old logs) with rules 16/17 removed — the natural next step to verify the hint-free ceiling can break.

---

## 11. Conclusion: What This Project Actually Shows

This was not a "build a fuzzer" project — it was a "drive an LLM to build a fuzzer" project. The success criterion was the *quality of the feedback loop*, not the bugs found.

What we proved:

1. **The loop architecture works.** Across 47 runs, 4 providers, 17 prompt rules, the loop consistently produces strategies that achieve 60–100% grammar breadth with 30–50% acceptance rates within 5 iterations. The plumbing is solid.

2. **Different model tiers fail in qualitatively different ways.** Ollama 7B hallucinates API; Groq 70B has ordinary type bugs; Gemini Flash has slow timeouts; GPT-5.4 has occasional format bugs but is fastest. The LLM choice for an agentic loop matters more for prompt engineering tractability than raw quality.

3. **The proxy signal must be carefully designed.** Three times we found the signal was structurally incomplete (Cases 4, 10, 13) — depth-only measurement, accepted-only counting, single-axis measurement — and each time the fix changed what the loop could find.

4. **Prompt engineering has subtle failure modes.** Rule 16's `max_value=5000` example got copied verbatim, freezing depth at exactly 5,000 — the *example's illustrative constant* overrode the *feedback signal's directive*. This is a general finding, not TOML-specific.

5. **The bugs are real and reproducible.** 5 distinct root-cause bugs in `tomlc99`, 4 of them CVE-class memory-safety issues from unbounded recursion. All were found by the agentic loop on its own (not hand-fed), once the loop was correctly configured.

6. **Many real bugs were found in the project's own plumbing** along the way: a sanitizer frame pattern missed (Case 3), a 2-state verify model missing a third state (Case 3), a `crash_signatures` field declared-but-never-written (Case 12), a `LoopState.load_or_new()` that silently discarded state on unknown fields (Case 13), a `--resume` that opened new run sections (fixed in `agent/breadth.py`). These are honest evidence of careful engineering under iteration.

**The strongest, most honest summary:** the agentic loop succeeded at its actual job — turning a grammar into a self-improving generator under feedback, with no coverage instrumentation available — and the bugs it found are real, root-cause distinct, and would have been missed by simpler fuzzing setups. The *specific* proxy signal we chose wasn't tuned to reproduce the bugs we knew existed; the fixes we iteratively applied (rules 9-17, the depth targets, the crash-diversity directive, the multi-axis signal) are what closed the gap from "loop runs well" to "loop finds bugs."

---

## 12. Sources & Where to Look Deeper

| Topic | Primary file |
|-------|-------------|
| Per-iteration metrics for all 47 runs | `logs/RUN_HISTORY.md` |
| Per-provider comparisons | `comparison/gemini/metrics.md`, `comparison/groq/metrics.md`, `comparison/openai/` |
| All 13 cases with full detail | `OBSERVATIONS.md` |
| Project status snapshot | `PROJECT_SUMMARY.md` |
| Plain-language walkthrough | `progress_till_now_2026-08-30.md` |
| Step-by-step planning | `planning/planning-0-...md` through `planning/planning-8-...md` |
| Grammar source + divergences | `grammar/TomlLexer.g4`, `grammar/TomlParser.g4`, `grammar/adaptations.md` |
| Crash findings + deduplication | `triage/reports/`, `triage/reports/run_*/INDEX.md` |
| Final 2-page report draft | `progress_report.md` |
| All 17 prompt rules | `agent/prompts.py::STRATEGY_CONTRACT` |
| Current config | `config.yaml` |
| Hand-written crash prober | `pipeline/crash_hunt_strategy.py` |

---

*This analysis was generated 2026-09-03 by reviewing the entire `fuzzing-agent` project. It synthesizes `OBSERVATIONS.md` (the primary case-study source), `PROJECT_SUMMARY.md`, `progress_till_now_2026-08-30.md`, `progress_report.md`, `logs/RUN_HISTORY.md`, `comparison/{gemini,groq,openai}/metrics.md`, `config.yaml`, and `agent/prompts.py` into a single narrative covering planning → testing → strategy → results → cross-model analysis.*