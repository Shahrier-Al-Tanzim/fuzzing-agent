"""One-time maintenance script: renames existing triage output folders from
a bare signature key (e.g. `939402a0547c`, `unparsed_timeout`) to
`<bug-name>-<signature key>` (e.g. `nested_arrays-939402a0547c`), using the
same CRASH_MECHANISMS mapping the feedback loop already uses
(agent/summarize.py) - one source of truth, not a second copy of the names.

Does NOT change how run_triage.py names folders for NEW runs - this only
relabels output that already exists, under:
  - triage/reports/run_*/
  - history/old_traige_reports/*/
  - comparison/*/run_*/triage/

Each folder's report.md contains a hardcoded `Reproduce` command pointing at
its own old path - that line is rewritten in place so it still points at a
real file after the rename. Idempotent: already-renamed folders no longer
match the bare-signature pattern, so re-running this is a no-op for them.

Usage: python -m triage.rename_signature_folders [--dry-run]
"""
from __future__ import annotations

import argparse
import re
from pathlib import Path

from agent.summarize import CRASH_MECHANISMS

REPO_ROOT = Path(__file__).resolve().parent.parent

# A folder name that hasn't been renamed yet: either a 12-char hex digest
# (a real CrashSignature.digest) or "unparsed_<verdict>" (signature.py's
# frameless fallback key). Anything else - including anything already in
# "<name>-<key>" form - is left alone.
_RAW_NAME = re.compile(r"^[0-9a-f]{12}$|^unparsed_[a-zA-Z0-9]+$")


def slugify(text: str) -> str:
    """'nested arrays' -> 'nested_arrays'. Filesystem/shell-safe."""
    slug = re.sub(r"[^a-z0-9]+", "_", text.lower()).strip("_")
    return slug or "unnamed"


def bug_slug(sig_key: str) -> str:
    mechanism = CRASH_MECHANISMS.get(sig_key)
    return slugify(mechanism) if mechanism else "unclassified"


def _run_dirs_holding_raw_signatures(root: Path) -> list[Path]:
    """Every directory under `root` that directly contains at least one
    not-yet-renamed signature folder."""
    if not root.exists():
        return []
    hits = []
    for d in root.rglob("*"):
        if d.is_dir() and any(c.is_dir() and _RAW_NAME.match(c.name)
                              for c in d.iterdir()):
            hits.append(d)
    return hits


def rename_in(run_dir: Path, dry_run: bool) -> list[tuple[str, str]]:
    renamed = []
    for child in sorted(run_dir.iterdir()):
        if not (child.is_dir() and _RAW_NAME.match(child.name)):
            continue
        old_name = child.name
        new_name = f"{bug_slug(old_name)}-{old_name}"
        new_path = child.with_name(new_name)
        if new_path.exists():
            print(f"  ! SKIP {child} - target {new_name} already exists")
            continue

        report = child / "report.md"
        report_text = report.read_text(encoding="utf-8") if report.exists() else None

        if dry_run:
            print(f"  {child.relative_to(REPO_ROOT)}  ->  {new_name}")
        else:
            child.rename(new_path)
            if report_text is not None:
                fixed = report_text.replace(f"/{old_name}/", f"/{new_name}/")
                (new_path / "report.md").write_text(fixed, encoding="utf-8")
            print(f"  {run_dir.relative_to(REPO_ROOT) / old_name}  ->  {new_name}")

        renamed.append((old_name, new_name))
    return renamed


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--dry-run", action="store_true",
                    help="show what would be renamed without touching anything")
    args = ap.parse_args()

    roots = [
        REPO_ROOT / "triage" / "reports",
        REPO_ROOT / "history" / "old_traige_reports",
        REPO_ROOT / "comparison",
    ]

    all_renamed: list[tuple[str, str]] = []
    unclassified: set[str] = set()

    for root in roots:
        for run_dir in _run_dirs_holding_raw_signatures(root):
            print(f"=== {run_dir.relative_to(REPO_ROOT)} ===")
            done = rename_in(run_dir, args.dry_run)
            all_renamed.extend(done)
            for old, new in done:
                if new.startswith("unclassified-"):
                    unclassified.add(old)

    print(f"\n{'Would rename' if args.dry_run else 'Renamed'} "
         f"{len(all_renamed)} folder(s) across {len(roots)} locations.")
    if unclassified:
        print(f"\n{len(unclassified)} signature(s) have NO entry in "
             f"agent.summarize.CRASH_MECHANISMS and were tagged "
             f"'unclassified' - these are worth checking: either a genuinely "
             f"new signature that hasn't been added to the mapping yet, or "
             f"a typo in the mapping's keys.")
        for k in sorted(unclassified):
            print(f"  - {k}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
