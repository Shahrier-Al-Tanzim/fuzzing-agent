# Agentic Grammar Fuzzing of `tomlc99`

**Target:** cktan/tomlc99 @ `5221b3d3d66c25a1dc6f0372b4f824f1202fe398` (2023-09-30)
**Grammar:** antlr/grammars-v4 `toml/TomlLexer.g4` + `TomlParser.g4` (TOML v1.0.0)
**Model:** `gemini-3.6-flash` via Gemini's free tier (the model that generated the
committed strategies — `agent/state/loop_state.json`). Two earlier providers were
tried and dropped: local `qwen2.5-coder:7b` (0/12 valid generations — API
hallucination, see Challenges) and Groq's `llama-3.3-70b-versatile` (deprecated by
the provider mid-project). The provider switch is itself a finding, not incidental.

---

## 1. Design

**Grammar and adaptations.** I probed the pinned build against the ANTLR grammar
by hand before writing any generator and found 5 divergences
(`grammar/adaptations.md`): a silently-accepted trailing comma in inline tables
(grammar forbids it); silently-truncated over-long fractional seconds; an integer
past `INT64_MAX` silently re-typed as a float; a leading-zero integer that passes
`toml_parse()` but fails a later typed-accessor call ("parsed" ≠ "usable"); and —
the one that seeded everything found later — no depth limit on nested arrays.

**Crash vs. valid vs. rejection.** `harness/toml_harness.c` (built with
`-fsanitize=address,undefined`) parses one input then walks the entire tree
through every typed accessor, since much of the library's pointer arithmetic lives
in the conversion paths, not the parser. Classification checks timeout → sanitizer
output (authoritative regardless of how the process died) → fatal signal → exit
code, in that order — exit code first would file a real memory-safety bug as a
clean rejection.

**Agentic loop structure.** `agent/loop.py` runs generate → validate → run 500
examples → summarize → refine, up to 5 iterations. Every generation passes six
validation gates before being trusted; a failed gate's exact error is quoted back
to the model on retry.

**The proxy signal, and why.** With no code coverage of the target permitted, the
signal combines four externally-observable measures computed by regex over the
*generated text itself* — **grammar breadth** (fraction of ~30 tracked TOML
constructs seen in accepted documents; not called "coverage" to avoid implying
the forbidden kind), **acceptance rate** (a 20% floor rejects a broken generator
before it wastes the run), **novelty rate**, and **max nesting depth**. This
tracks real testing depth because `tomlc99`'s parser is organized around the same
constructs the grammar names (`parse_array`, `parse_inline_table`, `parse_keyval`
exist as functions) — but two real defects in the signal itself were found and
fixed mid-project: (1) the depth directive was gated on *accepted* documents only,
and a document deep enough to hit the top target crashes and is never counted —
mathematically unsatisfiable; fixed with a second figure counting all generated
documents. (2) feedback quoted raw crash-signature hex digests with no actionable
meaning and never asked for an unseen mechanism, so nothing pushed the loop away
from re-finding the same bugs across 4 runs — fixed by mapping digests to
plain-English mechanisms and adding a diversity directive.

---

## 2. Findings

### Evolution across iterations (Run 27, final)

| Iter | Accepted | Breadth | Novel | Depth | Findings |
|---|---|---|---|---|---|
| 0 | 28% | 92% | 22% | 4 | 283 |
| 1 | 49% | 100% | 27% | 7 | 210 |
| 2 | 52% | 100% | 26% | 7 | 209 |
| 3 | 51% | 100% | 23% | 7 | 244 |
| 4 | 46% | 100% | 20% | 8 | 259 |

What drove each change (from `agent/state/iteration_NN_feedback.md`): **0→1**,
three never-seen productions (`ML_BASIC_STRING`, `non_ascii`, `LOCAL_DATE`) plus
low novelty (22%) drove new constructs and more structural variety. **1→2, 2→3**,
breadth and depth were healthy, so the directive pushed rare combinations (deep
inline tables inside array-of-tables, extreme values) rather than new constructs.
**3→4**, novelty had fallen to 23%, so the directive re-prioritized variety —
novelty fell further anyway (20%), an honest miss worth naming.

Depth here is *accepted-only* by design: a document deep enough to actually crash
the parser is, by definition, not accepted. Crash-triggering depths run into the
tens of thousands, below.

### Crashes — 5 confirmed root-cause bugs, 9 signatures

Raw triage reports 9 signatures. **The honest count is 5** — three
(`af1d0280777e`, `3db1e06f41e9`, `80953bb88ca2`) are the same alternating-nesting
bug captured at different points mid-overflow, confirmed by checking the actual
crashing input files (byte-for-byte identical shape) rather than trusting digest
counts — exactly the "new bug vs. repeat" judgment call the assignment asks for.

| # | Bug | Mechanism | Threshold | Deterministic? |
|---|---|---|---|---|
| 1 | Array-nesting stack overflow | `parse_array` recurses per `[`, no depth limit | ~48,000 | Yes |
| 2 | Dotted-key stack overflow | `parse_keyval` recurses per `.` | ~90,000–100,000 | Yes |
| 3 | Inline-table stack overflow | `parse_inline_table` ↔ `parse_keyval` mutual recursion | ~80,000 | Yes |
| 4 | Many-siblings O(n²) hang | Linear key-scan on every insert, O(N²) total | ~15,000+ keys / 5s | N/A — timing threshold |
| 5 | Alternating array/inline-table overflow | `parse_array` ↔ `parse_inline_table`, a 3rd distinct cycle | ~40,000–80,000 | Crashes every run; signature varies |

4 are memory-safety bugs (unbounded recursion → stack exhaustion); 1 is an
algorithmic-complexity DoS. All 5 trace to one root pattern: no limit anywhere on
attacker-controlled input size or nesting. Bug 1 was found by hand during grammar
probing; bugs 2–5 by manual crash-hunting and the agentic loop itself, once the
prompt taught integer-repetition instead of recursion (recursion measurably cannot
reach these depths — plateaus at 13 regardless of bias, a Hypothesis
generation-budget property, not a prompt-quality problem). Bug 5's quoted-key
variant (`c04d038a7956`) reproduces best at a *lower* depth (~25,000) than any
other bug — evidence that what occupies each nesting level matters as much as
how deep it goes.

### Still under-tested

None — all 38 tracked productions were reached by iteration 1 of this run
(`report/generated/breadth_table.md`). Breadth saturating this fast is itself a
limit of the metric, not proof the grammar is exhausted: it says every construct
appeared *somewhere*, not that rare combinations or extreme value ranges within
each construct were exercised — exactly what the iteration-2/3 feedback pivoted
toward once it saturated.

---

## 3. Challenges

**Model reliability forced two provider switches.** Local `qwen2.5-coder:7b`
produced zero valid strategies across 12 attempts, confidently fabricating
Hypothesis API calls (`st.datetimes(formats=...)`) that don't exist — and
repeated the exact fabrication even after an explicit rule quoting the error back
verbatim. Switching to a 70B model (Groq) changed the failure *class* entirely:
ordinary composition bugs, not fabrication, all fixable by one worked-example
rule. Groq was then deprecated by its provider mid-project, forcing a second
switch to Gemini. **The honest conclusion: bigger models are measurably more
reliable here, not immune** — Gemini still has its own errors, just fixable ones.

**An illustrative constant in a prompt example was read as a hard ceiling.**
Teaching the model to draw an integer and repeat a string (instead of recursing)
for extreme depth worked immediately — depth jumped from 4 to 5,000 in one
iteration — but then froze at *exactly* the number used in the worked example,
because the model copied that literal bound over the depth target the feedback
was concurrently requesting. Correct code, missed objective, because a detail
chosen for illustration became a constraint.

**Judgment calls, at least four:** (1) Consecutive identical stack frames are
collapsed before hashing — otherwise one recursion bug reports as dozens,
depending on where the stack happened to run out. (2) Timeouts count as crashes
for grading but are stored and reported separately. (3) An acceptance floor of
20% is enforced as a hard validation gate — a generator below it is rejected
before it burns the run's budget, never patched by lowering the floor. (4) A
20+ occurrence signature captured with an unstable stack trace is still reported
as the same bug, verified by checking the actual crashing input, not re-derived
per-file logic (a mistake made independently in three different files before
being fixed once, at the source).

**With more time, or with real coverage feedback:** confirm whether grammar
breadth actually predicts line coverage — the central structural assumption of
this whole design, argued but never measured; run the provider comparison against
a frontier model to see whether the qwen→Groq failure-class shift continues in
the same direction; and extend the crash-diversity directive now that it can name
mechanisms, since it has only been live for one run so far.

---

## Appendix

See `report/artifacts.md` for the full deliverable-to-path map, and
`OBSERVATIONS.md` for the complete, unabridged case log this report is drawn from.
