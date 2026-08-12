"""Loads config.yaml once and exposes it as a plain object.

Kept deliberately dumb - no validation framework, no schema library. The
config is small and read by five modules; a dependency here would be
overhead, not safety.
"""
from __future__ import annotations

import functools
from pathlib import Path
from typing import Any

import yaml

PROJECT_ROOT = Path(__file__).resolve().parent.parent


class Config:
    def __init__(self, data: dict[str, Any]) -> None:
        self._data = data

    def __getitem__(self, key: str) -> Any:
        return self._data[key]

    def get(self, dotted: str, default: Any = None) -> Any:
        """Fetch a nested value: cfg.get('harness.timeout_seconds')."""
        node: Any = self._data
        for part in dotted.split("."):
            if not isinstance(node, dict) or part not in node:
                return default
            node = node[part]
        return node

    def path(self, dotted: str) -> Path:
        """Fetch a config value and resolve it against the project root."""
        value = self.get(dotted)
        if value is None:
            raise KeyError(f"no such config key: {dotted}")
        return (PROJECT_ROOT / value).resolve()


@functools.lru_cache(maxsize=1)
def load() -> Config:
    with open(PROJECT_ROOT / "config.yaml", encoding="utf-8") as fh:
        return Config(yaml.safe_load(fh))