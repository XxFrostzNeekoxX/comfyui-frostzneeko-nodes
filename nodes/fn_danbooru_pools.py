"""
Load curated Danbooru tag pools (from gist export) built by scripts/build_danbooru_pools.py.
Falls back to empty dict if JSON missing — generator uses legacy pools.
"""

from __future__ import annotations

import json
import os
from typing import Any

_POOLS: dict[str, list[str]] | None = None
_JSON_MTIME: float = 0.0


def _pools_path() -> str:
    return os.path.join(os.path.dirname(os.path.abspath(__file__)), "data", "danbooru_tag_pools.json")


def get_danbooru_pools() -> dict[str, list[str]]:
    global _POOLS, _JSON_MTIME
    path = _pools_path()
    try:
        mtime = os.path.getmtime(path)
    except OSError:
        return {}
    if _POOLS is not None and mtime == _JSON_MTIME:
        return _POOLS
    try:
        with open(path, encoding="utf-8") as f:
            raw: Any = json.load(f)
        if isinstance(raw, dict):
            _POOLS = {
                k: list(v) if isinstance(v, list) else []
                for k, v in raw.items()
                if isinstance(v, list) and not k.startswith("_")
            }
        else:
            _POOLS = {}
        _JSON_MTIME = mtime
    except (OSError, json.JSONDecodeError):
        _POOLS = {}
        _JSON_MTIME = mtime
    return _POOLS or {}


def pool_or_fallback(name: str, fallback: list[str]) -> list[str]:
    p = get_danbooru_pools().get(name) or []
    return p if p else list(fallback)
