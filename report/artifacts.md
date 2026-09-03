# Artifacts index

Maps each item on the assignment's deliverables checklist to its location.

## 1. Grammar source + noted adaptations
- `grammar/TomlLexer.g4`, `grammar/TomlParser.g4` — unmodified ANTLR grammar
- `grammar/GRAMMAR_SOURCE.txt` — provenance (source URL, fetch date)
- `grammar/PINNED_COMMIT.txt` — the exact tomlc99 commit under test
- `grammar/adaptations.md` — **the divergence analysis**
- `grammar/sample_inputs/` — hand-written probes, one per construct
- `grammar/probe.sh` — accept/reject sweep
- `grammar/investigate_divergences.sh` — full evidence, incl. crash bisection

## 2. Build script + harness source
- `harness/toml_harness.c` — the driver
- `harness/build.sh` — pinned checkout + ASan/UBSan build
- `harness/sanitizer_env.sh` — runtime sanitizer configuration
- `harness/samples/run_samples.sh` — correctness gate (21/21)
- `harness/build/BUILD_INFO.txt` — build provenance

## 3. Baseline strategy + pipeline demonstration
- `pipeline/baseline_strategy.py` — three deliberately naive tiers
- `pipeline/run_baseline.py` — driver + health check
- `pipeline/logs/baseline_*.jsonl` — raw results
- Result: `random_text` 1% accepted vs `keyvalue_lines` 47% accepted —
  both pipeline paths exercised, no harness errors

## 4. Agentic loop + final generator + iteration log
- `agent/loop.py` — the loop
- `agent/prompts.py`, `agent/validator.py` — seeding and the six gates
- `agent/strategies/iter_00..NN_strategy.py` — every generated strategy,
  **including rejected candidates** (`*_rejected_attempt*.py`)
- `agent/state/loop_state.json` — cumulative breadth/novelty/crash state
- `agent/state/iteration_NN_feedback.md` — exactly what the model was told
- `agent/state/prompts/` — full prompt/reply transcripts

## 5. Deduplicated, minimized crash reports
- `triage/reports/run_N/INDEX.md` — one row per triaged signature, per run
  (latest: `run_27`; see `report.md` §2 for why 9 signatures there are 5 real bugs)
- `triage/reports/run_N/<bug-name>-<signature>/report.md` — per-signature report
- `triage/reports/run_N/<bug-name>-<signature>/minimized.toml` — verified reproducer
- `grammar/early_findings/` — the pre-loop stack overflow, found by hand
- `OBSERVATIONS.md` Case 9 — the full reasoning for the 9-signatures-to-5-bugs count

## 6. Written report
- `report/report.md` — the two-page report
- `report/generated/` — every table, regenerated from data
- `report/generated/summary.json` — all numbers, machine-readable

## Reproducing everything
```bash
./harness/build.sh                      # build target + harness
./harness/samples/run_samples.sh        # verify harness correctness
python -m pipeline.run_baseline         # Module 3 baseline
python -m agent.loop                    # Modules 4-5 agentic loop
python -m triage.run_triage             # Module 6 triage
python -m report.generate_artifacts     # Module 7 tables
```