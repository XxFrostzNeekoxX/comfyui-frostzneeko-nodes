"""
FN Random Prompt Generator — ordered prompt: quality → subject → outfit → pose → expression
→ (sex acts) → BREAK → (male / partner) → BREAK → background. Uses Danbooru pools JSON when present.
"""

from __future__ import annotations

import os
import random
import time

import folder_paths

from .fn_danbooru_pools import pool_or_fallback
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


def _underscore_token(s: str) -> str:
    return s.strip().replace(" ", "_")


def _join_unique(parts: list[str]) -> str:
    seen: set[str] = set()
    out: list[str] = []
    for chunk in parts:
        if not chunk:
            continue
        for t in chunk.split(","):
            s = t.strip()
            if not s:
                continue
            k = s.lower()
            if k in seen:
                continue
            seen.add(k)
            out.append(s)
    return ", ".join(out)


def _pick(rng: random.Random, pool: list[str], fallback: list[str]) -> str:
    p = pool if pool else fallback
    return rng.choice(p) if p else ""


def _pick_n(rng: random.Random, pool: list[str], fallback: list[str], n: int) -> list[str]:
    p = pool if pool else fallback
    if not p or n <= 0:
        return []
    n = min(n, len(p))
    return rng.sample(p, n)


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
                    [
                        "SFW",
                        "NSFW soft",
                        "NSFW explicit (hetero)",
                        "NSFW explicit (yuri)",
                    ],
                    {"default": "SFW"},
                ),
                "girl_count": (["1girl", "2girls"], {"default": "1girl"}),
                "seed": (
                    "INT",
                    {"default": -1, "min": -1, "max": 0x7FFFFFFF, "step": 1},
                ),
                "include_quality_prefix": ("BOOLEAN", {"default": True}),
                "use_clip_break": (
                    "BOOLEAN",
                    {"default": True},
                ),
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
                "generated_prompt": (
                    "STRING",
                    {
                        "default": "",
                        "multiline": True,
                        "placeholder": "🎲 Generated prompt appears here after you run the workflow…",
                    },
                ),
            },
        }

    RETURN_TYPES = ("STRING",)
    RETURN_NAMES = ("prompt",)
    FUNCTION = "generate"
    OUTPUT_NODE = True
    CATEGORY = "FrostzNeeko 🔹/Prompt"
    DESCRIPTION = (
        "Ordered prompt: quality → 1girl/2girls + characters → clothing → pose → expression → "
        "(sex / soft tags) → BREAK → (male partner, hetero only) → BREAK → background. "
        "Disable use_clip_break for a single-line prompt."
    )

    @classmethod
    def IS_CHANGED(
        cls,
        character_list_path,
        content_mode,
        girl_count,
        seed,
        include_quality_prefix,
        use_clip_break,
        exclude_line_substrings="",
        extra_tags_append="",
        generated_prompt="",
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
        use_clip_break,
        exclude_line_substrings="",
        extra_tags_append="",
        generated_prompt="",
    ):
        rng = random.Random(int(seed)) if int(seed) >= 0 else random.Random()

        pools = {
            "clothing": pool_or_fallback("clothing", CLOTHING_SFW + CLOTHING_NSFW_SOFT),
            "pose": pool_or_fallback("pose", POSE_ACTION_SFW + POSE_ACTION_NSFW_SOFT),
            "expression": pool_or_fallback("expression", EXPRESSION_SFW + EXPRESSION_NSFW_SOFT),
            "background": pool_or_fallback("background", BACKGROUND_SFW + BACKGROUND_NSFW),
            "nsfw_soft": pool_or_fallback("nsfw_soft", CLOTHING_NSFW_SOFT),
            "explicit_hetero": pool_or_fallback("explicit_hetero", EXPLICIT_PARTNERED_MM),
            "explicit_yuri": pool_or_fallback("explicit_yuri", list(EXPLICIT_YURI) + list(EXPLICIT_YURI_EXTRA)),
            "explicit_solo": pool_or_fallback("explicit_solo", EXPLICIT_SOLO),
        }

        excl = [s.strip() for s in exclude_line_substrings.split(",") if s.strip()]
        resolved = _resolve_character_file(character_list_path)
        if not resolved:
            bundled = _bundled_popular_characters_path()
            if os.path.isfile(bundled):
                resolved = bundled
        char_pool = _load_character_tags(resolved, excl)
        if not char_pool:
            char_pool = list(FALLBACK_CHARACTER_TAGS)

        n_girls = 2 if girl_count == "2girls" else 1
        chars = _pick_unique(rng, char_pool, n_girls)

        is_sfw = content_mode == "SFW"
        is_soft = content_mode == "NSFW soft"
        is_het = content_mode == "NSFW explicit (hetero)"
        is_yuri = content_mode == "NSFW explicit (yuri)"

        # --- 1) Quality (optional, still first in order) ---
        quality_str = ""
        if include_quality_prefix:
            quality_str = _underscore_token(rng.choice(QUALITY_PREFIX))

        # --- 2–4) Clothing / pose / expression pools by mode ---
        if is_sfw:
            clothing = _pick(rng, pools["clothing"], CLOTHING_SFW)
            pose = _pick(rng, pools["pose"], POSE_ACTION_SFW)
            expression = _pick(rng, pools["expression"], EXPRESSION_SFW)
            soft_bits: list[str] = []
        elif is_soft:
            clothing = _pick(rng, pools["clothing"], CLOTHING_SFW + CLOTHING_NSFW_SOFT)
            pose = _pick(rng, pools["pose"], POSE_ACTION_NSFW_SOFT + POSE_ACTION_SFW)
            expression = _pick(rng, pools["expression"], EXPRESSION_NSFW_SOFT + EXPRESSION_SFW)
            s1 = _pick(rng, pools["nsfw_soft"], CLOTHING_NSFW_SOFT)
            soft_bits = [s1] if s1 else []
        elif is_yuri:
            clothing = _pick(rng, pools["clothing"], CLOTHING_NSFW_SOFT + CLOTHING_SFW)
            pose = _pick(rng, pools["pose"], POSE_ACTION_NSFW_SOFT + POSE_ACTION_SFW)
            expression = _pick(rng, pools["expression"], EXPRESSION_NSFW_SOFT + EXPRESSION_SFW)
            soft_bits = []
            s1 = _pick(rng, pools["nsfw_soft"], CLOTHING_NSFW_SOFT)
            if s1:
                soft_bits.append(s1)
        else:
            clothing = _pick(rng, pools["clothing"], CLOTHING_NSFW_SOFT + CLOTHING_SFW)
            pose = _pick(rng, pools["pose"], POSE_ACTION_NSFW_SOFT + POSE_ACTION_SFW)
            expression = _pick(rng, pools["expression"], EXPRESSION_NSFW_SOFT + EXPRESSION_SFW)
            soft_bits = []
            s1 = _pick(rng, pools["nsfw_soft"], CLOTHING_NSFW_SOFT)
            if s1:
                soft_bits.append(s1)

        # --- 5) Couple / interaction (non-explicit) ---
        couple_tags: list[str] = []
        if is_sfw and n_girls == 2 and rng.random() < 0.45:
            couple_tags.append(rng.choice(["holding_hands", "looking_at_another", "hugging", "yuri"]))
        if is_soft and n_girls == 2 and rng.random() < 0.55:
            couple_tags.append(rng.choice(["yuri", "looking_at_another", "blush", "symmetrical_docking"]))

        # --- 6) Sex acts (explicit only, girl-side / scene) ---
        sex_tags: list[str] = []
        partnered_het = False
        if is_yuri:
            ypool = pools["explicit_yuri"] or list(EXPLICIT_YURI)
            sex_tags = ["yuri"] + _pick_n(
                rng,
                pools["explicit_yuri"],
                list(EXPLICIT_YURI),
                min(3, max(1, len(ypool))),
            )
        elif is_het:
            if n_girls == 2:
                hpool = pools["explicit_hetero"] or list(EXPLICIT_PARTNERED_MM)
                sex_tags = _pick_n(
                    rng,
                    pools["explicit_hetero"],
                    list(EXPLICIT_PARTNERED_MM),
                    min(3, max(1, len(hpool))),
                )
                partnered_het = bool(sex_tags)
            else:
                if rng.random() < 0.55:
                    act = _pick(rng, pools["explicit_hetero"], list(EXPLICIT_PARTNERED_MM))
                    if act:
                        sex_tags = [act]
                    partnered_het = bool(sex_tags)
                else:
                    sex_tags = _pick_n(rng, pools["explicit_solo"], list(EXPLICIT_SOLO), 2)

        # --- Assemble line 1: quality → count → names → clothing → pose → expression → soft → couple → sex ---
        line1_parts: list[str] = []
        if quality_str:
            line1_parts.append(quality_str)
        line1_parts.append(girl_count)
        line1_parts.extend(chars)
        if clothing:
            line1_parts.append(clothing)
        if pose:
            line1_parts.append(pose)
        if expression:
            line1_parts.append(expression)
        line1_parts.extend(soft_bits)
        line1_parts.extend(couple_tags)
        line1_parts.extend(sex_tags)
        if extra_tags_append.strip():
            line1_parts.append(extra_tags_append.strip())

        line1 = _join_unique(line1_parts)

        # --- Background: 2–4 tags for a coherent scene (always last segment) ---
        bg_n = rng.randint(2, 4)
        fallback_bg = BACKGROUND_SFW if is_sfw else BACKGROUND_NSFW
        bg_tags = _pick_n(rng, pools["background"], fallback_bg, bg_n)
        bg_line = _join_unique(bg_tags)

        brk = "BREAK" if use_clip_break else ""

        # --- Male / partner line (hetero + partnered only) ---
        male_line = ""
        if is_het and partnered_het:
            male_parts = ["faceless_male", "bald", "hetero"]
            if rng.random() < 0.85:
                male_parts.append(rng.choice(["large_penis", "small_penis", "huge_penis"]))
            if rng.random() < 0.35:
                male_parts.append(rng.choice(["muscular_male", "toned_male", "barrel_chest"]))
            male_line = _join_unique(male_parts)

        if use_clip_break:
            if male_line:
                prompt = "\n".join([line1, brk, male_line, brk, bg_line])
            else:
                prompt = "\n".join([line1, brk, bg_line])
        else:
            prompt = _join_unique([line1, male_line, bg_line])

        return {
            "ui": {"generated_prompt": (prompt,)},
            "result": (prompt,),
        }
