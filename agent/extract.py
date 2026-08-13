"""Pull the Python out of a chat reply.

Small file, but it absorbs the single most common 7B failure mode: the model
obeys the *content* rules and ignores the *formatting* ones - wrapping code
in prose, using ``` without a language tag, or emitting two blocks.
"""
from __future__ import annotations

import re

FENCED = re.compile(r"```(?:python|py)?\s*\n(.*?)```", re.DOTALL | re.IGNORECASE)


def extract_python(text: str) -> str | None:
    """Best-effort extraction. Returns None if nothing plausible is found."""
    blocks = [b.strip() for b in FENCED.findall(text) if b.strip()]

    if blocks:
        # Prefer a block that actually honours the export contract; otherwise
        # take the longest, which beats taking the first when the model opens
        # with a toy example.
        for b in blocks:
            if "toml_strategy" in b:
                return b
        return max(blocks, key=len)

    # No fences at all. If the raw reply looks like a module, accept it.
    if "toml_strategy" in text and ("import" in text or "st." in text):
        return text.strip()
    return None