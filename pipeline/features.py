"""Structural feature extraction for generated TOML documents.

Lexical, not semantic: bracket counting and regex. See the planning doc for
why a real parser is the wrong tool here (most inputs are malformed by
design). Features feed two things:

  * grammar breadth - the loop's steering signal (Module 5): of the
    productions tracked below, how many have appeared at least once in an
    accepted generated document. Computed by regex on our own generated
    text, never by instrumenting tomlc99's binary - this is not the code
    coverage the assignment forbids; see OBSERVATIONS.md's terminology note.
  * the report's "which parts of the grammar are still under-tested" section

PRODUCTIONS is intentionally named after the ANTLR rules in
grammar/TomlParser.g4 and grammar/TomlLexer.g4, so a breadth gap can be
quoted straight back to the model in grammar vocabulary it has already seen.
"""
from __future__ import annotations

import re
from typing import Any

# Grammar productions we can detect lexically. Names match the .g4 rules.
PRODUCTIONS: tuple[str, ...] = (
    # keys
    "unquoted_key", "quoted_key", "dotted_key",
    # strings
    "BASIC_STRING", "LITERAL_STRING", "ML_BASIC_STRING", "ML_LITERAL_STRING",
    "escape_sequence", "unicode_escape", "non_ascii",
    # numbers
    "DEC_INT", "HEX_INT", "OCT_INT", "BIN_INT", "FLOAT", "FLOAT_EXP",
    "INF", "NAN", "int_underscore", "int_overflow", "leading_zero_int",
    # other scalars
    "BOOLEAN", "OFFSET_DATE_TIME", "LOCAL_DATE_TIME", "LOCAL_DATE", "LOCAL_TIME",
    # containers
    "array_", "array_nested", "inline_table", "inline_table_nested",
    "standard_table", "array_table", "empty_array", "empty_inline_table",
    # deliberate malformations (divergence territory)
    "trailing_comma", "duplicate_key", "comment", "empty_document",
)

_RE = {
    "quoted_key":        re.compile(r'^\s*(".*?"|\'.*?\')\s*=', re.MULTILINE),
    "dotted_key":        re.compile(r'^\s*[\w"\'-]+(\s*\.\s*[\w"\'-]+)+\s*=', re.MULTILINE),
    "unquoted_key":      re.compile(r'^\s*[A-Za-z0-9_-]+\s*=', re.MULTILINE),
    "ML_BASIC_STRING":   re.compile(r'"""'),
    "ML_LITERAL_STRING": re.compile(r"'''"),
    "BASIC_STRING":      re.compile(r'(?<!")"(?:[^"\\\n]|\\.)*"(?!")'),
    "LITERAL_STRING":    re.compile(r"(?<!')'(?:[^'\n])*'(?!')"),
    "escape_sequence":   re.compile(r'\\[btnfr"\\]'),
    "unicode_escape":    re.compile(r"\\[uU][0-9A-Fa-f]{4}"),
    "HEX_INT":           re.compile(r"\b0x[0-9A-Fa-f_]+"),
    "OCT_INT":           re.compile(r"\b0o[0-7_]+"),
    "BIN_INT":           re.compile(r"\b0b[01_]+"),
    "FLOAT_EXP":         re.compile(r"[-+]?\d[\d_]*(\.\d+)?[eE][-+]?\d+"),
    "FLOAT":             re.compile(r"[-+]?\d[\d_]*\.\d[\d_]*"),
    "INF":               re.compile(r"[-+]?\binf\b"),
    "NAN":               re.compile(r"[-+]?\bnan\b"),
    "int_underscore":    re.compile(r"\b\d[\d_]*_[\d_]*\d\b"),
    "leading_zero_int":  re.compile(r"=\s*[-+]?0\d"),
    "DEC_INT":           re.compile(r"=\s*[-+]?\d+\s*(?:$|[,\]}#\n])", re.MULTILINE),
    "BOOLEAN":           re.compile(r"\b(true|false)\b"),
    "OFFSET_DATE_TIME":  re.compile(r"\d{4}-\d{2}-\d{2}[Tt ]\d{2}:\d{2}:\d{2}(\.\d+)?([Zz]|[-+]\d{2}:\d{2})"),
    "LOCAL_DATE_TIME":   re.compile(r"\d{4}-\d{2}-\d{2}[Tt ]\d{2}:\d{2}:\d{2}"),
    "LOCAL_DATE":        re.compile(r"=\s*\d{4}-\d{2}-\d{2}\s*(?:$|[,\]}#\n])", re.MULTILINE),
    "LOCAL_TIME":        re.compile(r"=\s*\d{2}:\d{2}:\d{2}"),
    "standard_table":    re.compile(r"^\s*\[[^\[\]]+\]\s*$", re.MULTILINE),
    "array_table":       re.compile(r"^\s*\[\[.+?\]\]\s*$", re.MULTILINE),
    "empty_array":       re.compile(r"\[\s*\]"),
    "empty_inline_table": re.compile(r"\{\s*\}"),
    "trailing_comma":    re.compile(r",\s*[\]}]"),
    "comment":           re.compile(r"#.*$", re.MULTILINE),
}

INT64_MAX = 9223372036854775807


def _max_depth(text: str, open_ch: str, close_ch: str) -> int:
    """Max nesting of a bracket pair. Over-counts brackets inside strings;
    see the module docstring - erring high is the safe direction."""
    depth = best = 0
    for ch in text:
        if ch == open_ch:
            depth += 1
            best = max(best, depth)
        elif ch == close_ch:
            depth = max(0, depth - 1)
    return best


def _has_duplicate_key(text: str) -> bool:
    keys = re.findall(r"^\s*([A-Za-z0-9_-]+)\s*=", text, re.MULTILINE)
    return len(keys) != len(set(keys))


def _has_int_overflow(text: str) -> bool:
    return any(
        len(tok) >= 19 and int(tok) > INT64_MAX
        for tok in re.findall(r"\b\d{19,}\b", text)
    )


def extract_features(text: str) -> dict[str, Any]:
    """Structural fingerprint of one generated document."""
    array_depth = _max_depth(text, "[", "]")
    table_depth = _max_depth(text, "{", "}")

    present: set[str] = set()
    for name, rx in _RE.items():
        if rx.search(text):
            present.add(name)

    if not text.strip():
        present.add("empty_document")
    if "[" in text and "]" in text:
        present.add("array_")
    if array_depth >= 2:
        present.add("array_nested")
    if "{" in text and "}" in text:
        present.add("inline_table")
    if table_depth >= 2:
        present.add("inline_table_nested")
    if any(ord(c) > 127 for c in text):
        present.add("non_ascii")
    if _has_duplicate_key(text):
        present.add("duplicate_key")
    if _has_int_overflow(text):
        present.add("int_overflow")

    return {
        "bytes": len(text.encode("utf-8", "surrogatepass")),
        "lines": text.count("\n") + 1 if text else 0,
        "array_depth": array_depth,
        "inline_table_depth": table_depth,
        "max_depth": max(array_depth, table_depth),
        "productions": sorted(present & set(PRODUCTIONS)),
    }


def signature(features: dict[str, Any]) -> str:
    """Coarse shape-fingerprint, for novelty counting.

    Deliberately lossy: exact productions plus a *bucketed* depth. Without
    bucketing, changing depth 7 to 8 would read as a brand-new shape and
    novelty would stay near 100% forever, which is no signal at all.
    """
    depth = features.get("max_depth", 0)
    bucket = 0 if depth <= 1 else (2 if depth <= 3 else (4 if depth <= 8 else 9))
    return f"{bucket}|{','.join(features.get('productions', []))}"