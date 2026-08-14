"""Validates a candidate strategy before it is ever trusted.

Six gates, cheapest first, because the expensive ones cost subprocess time:

  1. extraction   - did we get code at all?
  2. syntax       - does it parse? (ast.parse; no execution)
  3. imports      - only the allowed ones? (AST walk; still no execution)
  4. exec+export  - does it run and define `toml_strategy` as a strategy?
  5. draw         - can it produce N `str` examples without raising?
  6. probe        - does the harness accept a reasonable share of them?

Gate 6 is the one the assignment names explicitly: "a generator that's
rejected 99% of the time by the parser's front door isn't testing anything
interesting". The floor comes from config (`loop.acceptance_rate_floor`).

Every failure returns a message written to be pasted back into the next
prompt verbatim. That feedback-into-retry path is what makes a 7B model
usable here.
"""
from __future__ import annotations

import ast
import warnings
from dataclasses import dataclass, field
from typing import Any

from hypothesis.errors import NonInteractiveExampleWarning

from pipeline.config import load

ALLOWED_IMPORTS = {"hypothesis", "hypothesis.strategies"}
REQUIRED_EXPORT = "toml_strategy"


@dataclass
class ValidationResult:
    ok: bool
    stage: str
    error: str = ""
    strategy: Any = None
    namespace: dict = field(default_factory=dict)
    stats: dict = field(default_factory=dict)

    @property
    def feedback(self) -> str:
        return f"[{self.stage}] {self.error}" if self.error else ""


def _check_imports(tree: ast.AST) -> str | None:
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                root = alias.name.split(".")[0]
                if alias.name not in ALLOWED_IMPORTS and root != "hypothesis":
                    return (f"illegal import `{alias.name}`. Only "
                            "`from hypothesis import strategies as st` is allowed.")
        elif isinstance(node, ast.ImportFrom):
            mod = node.module or ""
            if mod.split(".")[0] != "hypothesis":
                return (f"illegal import from `{mod}`. Only "
                        "`from hypothesis import strategies as st` is allowed.")
    return None


def validate_strategy(code: str, probe: bool = True) -> ValidationResult:
    # strategy.example() below is deliberate, non-interactive use - that's
    # the whole point of this validator, so Hypothesis's warning about it
    # is expected noise here, not a real signal.
    warnings.filterwarnings("ignore", category=NonInteractiveExampleWarning)

    cfg = load()
    n_samples = cfg.get("llm.validation_samples", 25)

    # --- gate 1: did we get anything ---
    if not code or not code.strip():
        return ValidationResult(False, "extract",
                                "no Python code block found in the reply.")

    # --- gate 2: syntax ---
    try:
        tree = ast.parse(code)
    except SyntaxError as exc:
        return ValidationResult(
            False, "syntax",
            f"the code does not parse: line {exc.lineno}: {exc.msg}")

    # --- gate 3: imports (static, before any execution) ---
    bad = _check_imports(tree)
    if bad:
        return ValidationResult(False, "imports", bad)

    # --- gate 4: execute and find the export ---
    ns: dict = {}
    try:
        exec(compile(tree, "<generated_strategy>", "exec"), ns)  # noqa: S102
    except Exception as exc:  # noqa: BLE001 - any failure is a retry signal
        return ValidationResult(
            False, "exec",
            f"the module raised on import: {type(exc).__name__}: {exc}")

    strategy = ns.get(REQUIRED_EXPORT)
    if strategy is None:
        defined = [k for k in ns if not k.startswith("__")][:10]
        return ValidationResult(
            False, "export",
            f"no module-level `{REQUIRED_EXPORT}`. Defined instead: {defined}. "
            f"Rename your top-level strategy to `{REQUIRED_EXPORT}`.")

    from hypothesis.strategies import SearchStrategy
    if not isinstance(strategy, SearchStrategy):
        return ValidationResult(
            False, "export",
            f"`{REQUIRED_EXPORT}` is {type(strategy).__name__}, not a "
            "SearchStrategy. It must be a strategy object, not a function - "
            "if you used @composite, call it: toml_strategy = my_doc().")

    # --- gate 5: draw examples ---
    samples: list[str] = []
    try:
        for _ in range(n_samples):
            samples.append(strategy.example())
    except Exception as exc:  # noqa: BLE001
        return ValidationResult(
            False, "draw",
            f"drawing an example raised {type(exc).__name__}: {exc}")

    non_str = [type(s).__name__ for s in samples if not isinstance(s, str)]
    if non_str:
        return ValidationResult(
            False, "draw",
            f"produced non-str values ({sorted(set(non_str))}). Every example "
            "must be a `str` of TOML text - add .map() to join/format.")

    # Whether recursion is real, not just present in the source. A strategy
    # can use @composite throughout and still never let a container hold
    # another instance of itself - Case 4 in OBSERVATIONS.md found exactly
    # that: `uses_recursion` reported True from a text search for
    # "@composite" while every generated document, across an entire 5
    # -iteration run, stayed at nesting depth 1. Checking the *drawn samples*
    # instead is the actual, structural question: did this strategy ever
    # produce something nested more than one level deep?
    from pipeline.features import extract_features
    sample_max_depth = max(
        (extract_features(s)["max_depth"] for s in samples), default=0)

    stats = {
        "samples": len(samples),
        "mean_len": round(sum(len(s) for s in samples) / max(len(samples), 1), 1),
        "max_len": max((len(s) for s in samples), default=0),
        "sample_max_depth": sample_max_depth,
        "uses_recursion": sample_max_depth > 1,
    }

    if not probe:
        return ValidationResult(True, "draw", strategy=strategy,
                                namespace=ns, stats=stats)

    # --- gate 6: does the parser actually accept some of it ---
    from pipeline.runner import HarnessRunner
    from pipeline.schema import Verdict

    n_probe = cfg.get("llm.validation_probe_examples", 40)
    floor = cfg.get("loop.acceptance_rate_floor", 0.20)
    runner = HarnessRunner(iteration=-1)  # -1 marks probe runs, not real runs

    verdicts: list[str] = []
    reject_msgs: list[str] = []
    for i in range(n_probe):
        try:
            text = strategy.example()
        except Exception:  # noqa: BLE001
            break
        rec = runner.run(text, example_index=i)
        verdicts.append(rec.verdict)
        if rec.verdict == Verdict.REJECT.value and rec.reject_message:
            reject_msgs.append(rec.reject_message)

    total = len(verdicts) or 1
    accepted = verdicts.count(Verdict.ACCEPT.value)
    rate = accepted / total
    stats.update({
        "probe_examples": total,
        "acceptance_rate": round(rate, 3),
        "top_rejects": _top(reject_msgs, 3),
    })

    if rate < floor:
        return ValidationResult(
            False, "acceptance",
            f"only {accepted}/{total} ({rate:.0%}) of generated documents were "
            f"accepted by tomlc99; the floor is {floor:.0%}. The most common "
            f"parser errors were: {_top(reject_msgs, 3)}. Fix the syntax "
            "causing these before adding more edge cases.",
            strategy=strategy, namespace=ns, stats=stats)

    return ValidationResult(True, "acceptance", strategy=strategy,
                            namespace=ns, stats=stats)


def _top(msgs: list[str], n: int) -> list[str]:
    from collections import Counter
    return [m for m, _ in Counter(msgs).most_common(n)]