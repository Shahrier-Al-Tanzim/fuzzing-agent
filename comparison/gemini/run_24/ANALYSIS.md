# Run 24 (Gemini `gemini-3.6-flash`) — triage analysis

Source: `triage/reports/run_24/` (copied verbatim into `triage/` here).
Loop metrics for this run are in `../metrics.md` / `../metrics.csv`.

## Result

**219 crashing/hanging inputs → 5 signatures after deduplication.** Every
signature is a bug already documented in `OBSERVATIONS.md` — **no new bug
class**.

| Signature | Bug | Type | Occurrences | Verify |
|---|---|---|---|---|
| `939402a0547c` | Array-nesting overflow, `parse_array` (`toml.c:1057`) | stack overflow | 120 | unstable-sig |
| `unparsed_timeout` | O(n²) many-siblings hang (bug 4) | hang / DoS | 56 | flaky |
| `e857b4530c96` | Frameless variant of the array bug | stack overflow | 29 | unstable-sig |
| `26e809dd9d85` | Inline-table overflow, `parse_keyval`→`parse_inline_table` (`toml.c:1177`) | stack overflow | 11 | unstable-sig |
| `55628614cd6c` | Dotted-key overflow, `parse_keyval` self-recursion (`toml.c:1132`) | stack overflow | 3 | unstable-sig |

As always, two rows are not separate bugs: `e857b4530c96` is the same array
overflow as `939402a0547c` crashing too violently for ASan to unwind a stack,
and `unparsed_timeout` is the timing-threshold hang.

## Run 24 vs Run 21 — more crashes, weaker evidence

Both runs used the same model and found the same four bugs, which makes the
pair a clean like-for-like comparison. They diverge sharply on *quality*:

| | Run 21 | Run 24 | Change |
|---|---|---|---|
| Total crashing inputs | 154 | **219** | **+42%** |
| Array bug occurrences | 92 | **120** | +30% |
| Timeout occurrences | 29 | **56** | +93% |
| Signatures verifying **deterministic** | **3 of 5** | **0 of 5** | **regressed** |
| Max depth reached | 49,999 | **51,703** | +1,704 |
| Mean acceptance | 44% | **33%** | −11 pts |

**The headline: run 24 found substantially more crashes but produced the
weakest verification quality of any recent Gemini run.** All three stack
overflows that verified cleanly as deterministic (3/3) in run 21 fell back to
`unstable-sig` in run 24 — they still crash every run, but the captured stack
shifts between runs, so the signature isn't stable.

This is not a contradiction; it is the depth trade-off from Case 6 showing up
in the triage output rather than in the acceptance column. Run 24 pushed
deeper (51,703 vs 49,999) and its documents were correspondingly harder to
parse (acceptance 33% vs 44%). Deeper overflows are more violent, and a more
violent overflow is exactly the condition under which ASan fails to unwind a
clean stack — the mechanism already documented under "frameless overflows
collapse distinct bugs". The frameless bucket growing (23 → 29) alongside the
deterministic count collapsing (3 → 0) is the same effect measured two ways.

**Practical read for the report:** occurrence count and evidence quality are
not the same axis, and they moved in opposite directions here. Run 21 is the
better run to cite for *proof* that a bug is real and deterministic; run 24 is
the better run to cite for *how often* the loop can reach the bug. A run that
maximizes findings is not automatically the run that best demonstrates them.

## The iteration-4 spike

Findings by iteration were 45 → 33 → 26 → 17 → **97**. The jump at iteration 4
matches the same pattern in runs 17 (90 findings) and 21 (61): the depth
target escalates to its maximum on the final iteration (`DEPTH_TARGETS`'s
90,000 step), so the strategy commits hardest to deep-nesting branches exactly
when acceptance is allowed to bottom out. Iteration 4 also cost the most wall
clock by a wide margin (366.2s vs 102.6s for iteration 3) — deep documents are
slow to generate and slow to parse.
