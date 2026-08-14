"""Triage driver: collect crashes, dedupe, minimize, verify, write reports.

Input sources:
  * every pipeline/logs/*.jsonl record whose verdict is a finding
  * any extra files passed with --extra (used for the Module 1 early finding,
    which was found by hand and never went through the pipeline)
"""
from __future__ import annotations

import argparse
import json
import shutil
import sys
from datetime import datetime, timezone
from pathlib import Path

from pipeline.config import load, PROJECT_ROOT
from pipeline.runner import HarnessRunner
from pipeline.schema import read_log
from triage.minimize import minimize_concrete
from triage.signature import parse_signature
from triage.verify import verify


def collect_findings(extra_files: list[str]) -> list[dict]:
    """Every crashing input we know about, from logs plus explicit extras."""
    found: list[dict] = []

    log_dir = load().path("paths.logs")
    for log in sorted(log_dir.glob("*.jsonl")):
        for rec in read_log(log):
            if rec.is_finding:
                found.append({
                    "text": rec.input_text,
                    "stderr": rec.stderr,
                    "signal": rec.signal,
                    "verdict": rec.verdict,
                    "source": f"{log.name}#{rec.example_index}",
                    "sha256": rec.input_sha256,
                })

    # Extras have no stored stderr - run them once to get it.
    runner = HarnessRunner(iteration=-4)
    for f in extra_files:
        p = Path(f)
        if not p.exists():
            print(f"  !! missing: {f}")
            continue
        text = p.read_text(encoding="utf-8", errors="replace")
        rec = runner.run(text)
        if not rec.is_finding:
            print(f"  !! {p.name} did not crash - skipping")
            continue
        found.append({
            "text": text, "stderr": rec.stderr, "signal": rec.signal,
            "verdict": rec.verdict, "source": str(p), "sha256": rec.input_sha256,
        })
    return found


def main() -> int:
    ap = argparse.ArgumentParser(description="Deduplicate and minimize crashes.")
    ap.add_argument("--extra", nargs="*", default=[
        "grammar/early_findings/01_array_nesting_stackoverflow.toml"],
        help="crashing files found outside the pipeline")
    ap.add_argument("--no-minimize", action="store_true")
    args = ap.parse_args()

    out_dir = load().path("paths.crashes")
    out_dir.mkdir(parents=True, exist_ok=True)

    print("=== collecting ===")
    findings = collect_findings(args.extra)
    print(f"  {len(findings)} crashing inputs from logs + extras")
    if not findings:
        print("\nNo crashes to triage. That is a legitimate outcome - the "
              "report must then document why, and what you would try next.")
        return 0

    # --- deduplicate ---
    print("\n=== deduplicating ===")
    buckets: dict[str, dict] = {}
    for f in findings:
        sig = parse_signature(f["stderr"], f["signal"])
        if sig is None:
            sig_key, sig_obj = f"unparsed_{f['verdict']}", None
        else:
            sig_key, sig_obj = sig.digest, sig
        b = buckets.setdefault(sig_key, {"signature": sig_obj, "members": []})
        b["members"].append(f)

    for key, b in buckets.items():
        sig = b["signature"]
        label = sig.short if sig else key
        print(f"  {key}  {label:<44} {len(b['members'])} input(s)")
    print(f"\n  {len(findings)} crashes -> {len(buckets)} unique bug(s)")

    # --- minimize + verify + report ---
    print("\n=== minimizing and verifying ===")
    summary: list[dict] = []
    for key, b in buckets.items():
        sig = b["signature"]
        # Smallest member first: minimization starts from a better place.
        member = min(b["members"], key=lambda m: len(m["text"]))
        original = member["text"]

        if args.no_minimize or sig is None:
            mini, method, steps = original, "none", 0
            reduction = 0.0
        else:
            res = minimize_concrete(original, sig)
            mini, method, steps = res.text, res.method, res.steps
            reduction = res.reduction
            print(f"  {key}: {res.original_bytes} -> {res.minimized_bytes} bytes "
                  f"({reduction:.0%} smaller, {steps} steps)")

        vr = verify(mini, sig.digest if sig else None)
        print(f"  {key}: {vr.describe()}")

        d = out_dir / key
        d.mkdir(parents=True, exist_ok=True)
        (d / "original.toml").write_text(original, encoding="utf-8")
        (d / "minimized.toml").write_text(mini, encoding="utf-8")
        (d / "sanitizer.txt").write_text(member["stderr"], encoding="utf-8")

        meta = {
            "signature": sig.to_dict() if sig else {"digest": key},
            "occurrences": len(b["members"]),
            "sources": [m["source"] for m in b["members"]][:20],
            "original_bytes": len(original.encode()),
            "minimized_bytes": len(mini.encode()),
            "reduction": round(reduction, 3),
            "minimize_method": method,
            "minimize_steps": steps,
            "verification": {
                "runs": vr.runs, "crashes": vr.crashes,
                "signature_matches": vr.signature_matches,
                "deterministic": vr.deterministic, "flaky": vr.flaky,
                "unstable_signature": vr.unstable_signature,
                "description": vr.describe(),
            },
            "triaged_at": datetime.now(timezone.utc).isoformat(),
        }
        (d / "metadata.json").write_text(json.dumps(meta, indent=2),
                                         encoding="utf-8")
        (d / "report.md").write_text(_render_report(key, sig, meta, mini),
                                     encoding="utf-8")
        summary.append(meta)

    idx = out_dir / "INDEX.md"
    idx.write_text(_render_index(summary), encoding="utf-8")
    print(f"\n=== done ===\n  {len(buckets)} report(s) in {out_dir}\n  index: {idx}")
    return 0


def _render_report(key: str, sig, meta: dict, minimized: str) -> str:
    frames = "\n".join(f"  #{i}  {f}" for i, f in
                       enumerate(sig.frames if sig else [])) or "  (none parsed)"
    v = meta["verification"]
    return f"""\
# Crash {key} — {sig.short if sig else 'unparsed'}

**Type:** `{sig.bug_type if sig else 'unknown'}`
**Occurrences:** {meta['occurrences']} input(s) mapped to this signature
**Verification:** {v['description']}

## Normalized stack (top {len(sig.frames) if sig else 0} frames)

```
{frames}
```

Raw frames before normalization: {sig.raw_frame_count if sig else 0}
Consecutive identical frames collapsed: \
{sig.collapsed if sig else False}

## Minimized reproducer

{meta['original_bytes']} bytes → {meta['minimized_bytes']} bytes \
({meta['reduction']:.0%} smaller) via `{meta['minimize_method']}` \
in {meta['minimize_steps']} steps.

```toml
{minimized[:1500]}{'\n... (truncated)' if len(minimized) > 1500 else ''}
```

## Reproduce

```bash
source harness/sanitizer_env.sh
harness/build/toml_harness triage/reports/{key}/minimized.toml
echo $?   # expect 86 (sanitizer) or a signal
```

## Deduplication choices applied

- Consecutive identical frames collapsed (recursion bugs otherwise report as
  many distinct bugs depending on where the stack ran out).
- Harness frames (`toml_harness`, sanitizer runtime, libc startup) excluded;
  bucketing uses library frames only.
- Frame identity is `function file:line`; addresses and absolute paths stripped.
"""


def _verify_label(v: dict) -> str:
    """Short column label - kept as one named function rather than an
    inline ternary chain, since a duplicated inline version of this exact
    decision (deterministic/unstable/flaky/no) was the source of a real bug
    where a 100%-crash-rate result got mislabeled 'did not reproduce'."""
    if v["deterministic"]:
        return "yes"
    if v["unstable_signature"]:
        return "unstable-sig"
    if v["flaky"]:
        return "flaky"
    if v["crashes"] == 0:
        return "no"
    raise AssertionError(f"unrecognized verification state: {v}")


def _render_index(summary: list[dict]) -> str:
    rows = "\n".join(
        f"| `{s['signature']['digest']}` | {s['signature'].get('bug_type','?')} "
        f"| {s['occurrences']} | {s['minimized_bytes']} B "
        f"| {_verify_label(s['verification'])} |"
        for s in summary)
    return f"""\
# Crash triage index

{len(summary)} unique bug(s) after deduplication.

| Signature | Type | Occurrences | Minimized | Deterministic |
|---|---|---|---|---|
{rows}

Generated {datetime.now(timezone.utc).isoformat()}
"""


if __name__ == "__main__":
    sys.exit(main())