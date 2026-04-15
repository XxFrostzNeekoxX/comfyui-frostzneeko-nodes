"""
FN Random Prompt Generator — Danbooru-style tag pools + optional character list (.txt).
Character file: one entry per line as `label, danbooru_tag` (tag = text after the first comma).
"""

from __future__ import annotations

import os
import random
import time

import folder_paths

from .fn_random_prompt_data import (
    BACKGROUND_NSFW,
    BACKGROUND_SFW,
    CLOTHING_NSFW_SOFT,
    CLOTHING_SFW,
    EXPLICIT_PARTNERED_MM,
    EXPLICIT_SOLO,
    EXPLICIT_YURI,
    EXPLICIT_YURI_EXTRA,
    EXPRESSION_NSFW_SOFT,
    EXPRESSION_SFW,
    FALLBACK_CHARACTER_TAGS,
    POSE_ACTION_NSFW_SOFT,
    POSE_ACTION_SFW,
    QUALITY_PREFIX,
)

_CHARACTER_CACHE: dict[str, tuple[float, list[str]]] = {}


def _bundled_popular_characters_path() -> str:
    return os.path.join(os.path.dirname(os.path.abspath(__file__)), "data", "popular_adult_characters.txt")


def _resolve_character_file(path: str) -> str:
    p = (path or "").strip()
    if not p:
        return ""
    if os.path.isabs(p) and os.path.isfile(p):
        return p
    if os.path.isfile(p):
        return os.path.abspath(p)
    out = os.path.join(folder_paths.get_output_directory(), p)
    if os.path.isfile(out):
        return out
    inp = os.path.join(folder_paths.get_input_directory(), p)
    if os.path.isfile(inp):
        return inp
    return ""


def _load_character_tags(
    resolved_path: str,
    exclude_substrings: list[str],
) -> list[str]:
    if not resolved_path:
        return []
    try:
        mtime = os.path.getmtime(resolved_path)
    except OSError:
        return []
    cache_key = resolved_path + "\0" + repr(exclude_substrings)
    hit = _CHARACTER_CACHE.get(cache_key)
    if hit and hit[0] == mtime:
        return hit[1]

    tags: list[str] = []
    excl = [s.lower() for s in exclude_substrings if s.strip()]

    with open(resolved_path, encoding="utf-8", errors="ignore") as f:
        for raw in f:
            line = raw.strip()
            if not line or line.startswith("#"):
                continue
            if "," in line:
                tag = line.split(",", 1)[1].strip()
            else:
                tag = line
            if not tag:
                continue
            low = line.lower()
            if excl and any(s in low for s in excl):
                continue
            tags.append(tag)

    _CHARACTER_CACHE[cache_key] = (mtime, tags)
    return tags


def _pick_unique(rng: random.Random, pool: list[str], n: int) -> list[str]:
    if n <= 0 or not pool:
        return []
    if len(pool) >= n:
        return rng.sample(pool, n)
    out = rng.sample(pool, len(pool))
    while len(out) < n:
        out.append(rng.choice(pool))
    return out[:n]


def _underscore_phrase(s: str) -> str:
    """Turn comma-separated phrases into Danbooru-style tokens (spaces -> underscores)."""
    return ", ".join(p.strip().replace(" ", "_") for p in s.split(",") if p.strip())


def _join_prompt(parts: list[str]) -> str:
    seen: set[str] = set()
    out: list[str] = []
    for chunk in parts:
        if not chunk:
            continue
        for t in chunk.split(","):
            s = t.strip()
            if not s:
                continue
            key = s.lower()
            if key in seen:
                continue
            seen.add(key)
            out.append(s)
    return ", ".join(out)


class FNRandomPromptGenerator:
    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "character_list_path": (
                    "STRING",
                    {
                        "default": "",
                        "multiline": False,
                        "placeholder": "Empty = bundled 300 female adult tags. Or path to your own .txt",
                    },
                ),
                "content_mode": (
                    ["SFW", "NSFW soft", "NSFW explicit"],
                    {"default": "SFW"},
                ),
                "girl_count": (["1girl", "2girls"], {"default": "1girl"}),
                "seed": (
                    "INT",
                    {"default": -1, "min": -1, "max": 0x7FFFFFFF, "step": 1},
                ),
                "include_quality_prefix": ("BOOLEAN", {"default": True}),
            },
            "optional": {
                "exclude_line_substrings": (
                    "STRING",
                    {
                        "default": "",
                        "multiline": False,
                        "placeholder": "comma-separated; lines containing any are skipped (character file)",
                    },
                ),
                "extra_tags_append": (
                    "STRING",
                    {"default": "", "multiline": False},
                ),
            },
        }

    RETURN_TYPES = ("STRING",)
    RETURN_NAMES = ("prompt",)
    FUNCTION = "generate"
    CATEGORY = "FrostzNeeko 🔹/Prompt"
    DESCRIPTION = (
        "Random Danbooru-style positive prompt from curated pools. "
        "Leave character_list_path empty to use the bundled list of 300 curated female adult-presenting tags. "
        "Or set a path to a label,tag file. Edit scripts/write_300_female_adult_tags.py to change the 300."
    )

    @classmethod
    def IS_CHANGED(
        cls,
        character_list_path,
        content_mode,
        girl_count,
        seed,
        include_quality_prefix,
        exclude_line_substrings="",
        extra_tags_append="",
    ):
        if int(seed) < 0:
            return time.time_ns()
        return int(seed)

    def generate(
        self,
        character_list_path,
        content_mode,
        girl_count,
        seed,
        include_quality_prefix,
        exclude_line_substrings="",
        extra_tags_append="",
    ):
        rng = random.Random(int(seed)) if int(seed) >= 0 else random.Random()

        excl = [s.strip() for s in exclude_line_substrings.split(",") if s.strip()]
        resolved = _resolve_character_file(character_list_path)
        if not resolved:
            bundled = _bundled_popular_characters_path()
            if os.path.isfile(bundled):
                resolved = bundled
        char_pool = _load_character_tags(resolved, excl)
        if not char_pool:
            char_pool = list(FALLBACK_CHARACTER_TAGS)

        parts: list[str] = []

        if include_quality_prefix:
            parts.append(_underscore_phrase(rng.choice(QUALITY_PREFIX)))

        parts.append(girl_count)

        n_girls = 2 if girl_count == "2girls" else 1
        chars = _pick_unique(rng, char_pool, n_girls)
        for c in chars:
            parts.append(c)

        if content_mode == "SFW":
            parts.append(_underscore_phrase(rng.choice(CLOTHING_SFW)))
            parts.append(_underscore_phrase(rng.choice(POSE_ACTION_SFW)))
            parts.append(_underscore_phrase(rng.choice(EXPRESSION_SFW)))
            parts.append(_underscore_phrase(rng.choice(BACKGROUND_SFW)))
            if n_girls == 2 and rng.random() < 0.45:
                parts.append(_underscore_phrase(rng.choice(["holding hands", "looking at another", "hugging", "yuri"])))
        elif content_mode == "NSFW soft":
            parts.append(_underscore_phrase(rng.choice(CLOTHING_NSFW_SOFT)))
            parts.append(_underscore_phrase(rng.choice(POSE_ACTION_NSFW_SOFT)))
            parts.append(_underscore_phrase(rng.choice(EXPRESSION_NSFW_SOFT)))
            parts.append(_underscore_phrase(rng.choice(BACKGROUND_NSFW)))
            if n_girls == 2:
                parts.append(_underscore_phrase(rng.choice(["yuri", "looking at another", "blush", "symmetrical docking"])))
        else:
            # NSFW explicit
            parts.append(_underscore_phrase(rng.choice(CLOTHING_NSFW_SOFT + CLOTHING_SFW)))
            parts.append(_underscore_phrase(rng.choice(POSE_ACTION_NSFW_SOFT + POSE_ACTION_SFW)))
            parts.append(_underscore_phrase(rng.choice(EXPRESSION_NSFW_SOFT + EXPRESSION_SFW)))
            parts.append(_underscore_phrase(rng.choice(BACKGROUND_NSFW)))
            if n_girls == 2:
                yuri_pool = list(EXPLICIT_YURI)
                if rng.random() < 0.35:
                    yuri_pool.extend(EXPLICIT_YURI_EXTRA)
                k = min(3, len(yuri_pool))
                parts.extend(_underscore_phrase(t) for t in rng.sample(yuri_pool, k))
            else:
                if rng.random() < 0.55:
                    parts.append(_underscore_phrase(rng.choice(EXPLICIT_PARTNERED_MM)))
                    if rng.random() < 0.4:
                        parts.append("hetero")
                    if rng.random() < 0.25:
                        parts.append(_underscore_phrase("faceless male"))
                else:
                    parts.append(_underscore_phrase(rng.choice(EXPLICIT_SOLO)))

        if extra_tags_append.strip():
            parts.append(extra_tags_append.strip())

        prompt = _join_prompt(parts)
        return (prompt,)
