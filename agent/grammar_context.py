"""Builds the grammar section of the prompt from Module 1's artifacts.

Deliberate choices:
  * Lexer and parser grammars go in whole - together they are ~200 lines and
    they are the actual specification. Summarizing them would defeat the
    assignment's point.
  * adaptations.md does NOT go in whole. Only the divergence table and the
    "Consequences for generation" section matter to a generator; the method
    notes and scope-cut prose are for human readers.
  * Comments are stripped from the .g4 files - the Apache licence header
    alone is ~18 lines of pure context waste, repeated twice.
"""
from __future__ import annotations

import re

from pipeline.config import PROJECT_ROOT

GRAMMAR_DIR = PROJECT_ROOT / "grammar"


def _strip_block_comments(text: str) -> str:
    text = re.sub(r"/\*.*?\*/", "", text, flags=re.DOTALL)
    text = re.sub(r"^\s*//.*$", "", text, flags=re.MULTILINE)
    return re.sub(r"\n{3,}", "\n\n", text).strip()


def load_grammar() -> str:
    lexer = _strip_block_comments((GRAMMAR_DIR / "TomlLexer.g4").read_text(encoding="utf-8"))
    parser = _strip_block_comments((GRAMMAR_DIR / "TomlParser.g4").read_text(encoding="utf-8"))
    return f"=== TomlLexer.g4 ===\n{lexer}\n\n=== TomlParser.g4 ===\n{parser}"


def load_adaptations() -> str:
    """Only the sections a generator can act on."""
    path = GRAMMAR_DIR / "adaptations.md"
    if not path.exists():
        return "(no adaptations recorded)"
    text = path.read_text(encoding="utf-8")

    keep: list[str] = []
    for header in ("## Divergence table", "## Consequences for generation"):
        start = text.find(header)
        if start == -1:
            continue
        nxt = text.find("\n## ", start + len(header))
        keep.append(text[start:nxt if nxt != -1 else len(text)].strip())
    return "\n\n".join(keep) if keep else text[:4000]


def grammar_context() -> str:
    return (
        "## The ANTLR grammar (the specification)\n\n"
        f"{load_grammar()}\n\n"
        "## Observed divergences: where tomlc99 disagrees with that grammar\n\n"
        "These were measured by running inputs through the real pinned build.\n"
        "They are the most valuable inputs to generate, because they are the\n"
        "places the library is already known to behave unexpectedly.\n\n"
        f"{load_adaptations()}"
    )