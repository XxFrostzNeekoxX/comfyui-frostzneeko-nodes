"""
FN Random Prompt Generator — compact comma-separated tags (no space after commas), optional weights
on quality. Explicit NSFW uses coherent scenario bundles (e.g. BJ → kneeling + fellatio + related tags).
Order: quality → count → characters → body/eyes → outfit → pose → sex acts → expression
→ (hetero partner tags) → background → camera. Optional BREAK only before background when use_clip_break.
"""

from __future__ import annotations

import os
import random
import re
import time

import folder_paths

from .fn_danbooru_pools import pool_or_fallback
from .fn_random_prompt_data import (
    BACKGROUND_NSFW,
    BACKGROUND_SFW,
    CAMERA_FRAMING,
    CLOTHING_NSFW_SOFT,
    CLOTHING_SFW,
    EXPRESSION_NSFW_SOFT,
    EXPRESSION_SFW,
    FALLBACK_CHARACTER_TAGS,
    NSFW_HETERO_PARTNERED_SCENARIOS,
    NSFW_HETERO_TWO_GIRLS_SCENARIOS,
    NSFW_SOFT_SCENARIOS,
    NSFW_SOLO_SCENARIOS,
    NSFW_YURI_PAIR_SCENARIOS,
    NSFW_YURI_SCENARIOS,
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


_ALLOWED_PENIS_SIZE_WORDS = frozenset(
    {"huge", "large", "small", "medium", "big", "gigantic", "micro", "average"}
)
_PENIS_COLOR_WORDS = frozenset(
    {
        "red",
        "blue",
        "green",
        "yellow",
        "purple",
        "pink",
        "black",
        "white",
        "gold",
        "silver",
        "orange",
        "brown",
        "grey",
        "gray",
        "rainbow",
        "glowing",
        "multicolored",
        "two",
    }
)


def _is_spurious_color_penis_tag(tag: str) -> bool:
    """Drop tags like blue_penis from the subject line; keep size words and non-adjective compounds."""
    low = tag.lower().replace(" ", "_")
    m = re.fullmatch(r"([a-z]+)_penis", low)
    if not m:
        return False
    w = m.group(1)
    if w in _ALLOWED_PENIS_SIZE_WORDS:
        return False
    if w in _PENIS_COLOR_WORDS:
        return True
    return False


def _looks_like_danbooru_character_tag(tag: str) -> bool:
    """Pools may leak character tags into act lists; drop name_(copyright) shaped tokens."""
    s = tag.strip().lower().replace(" ", "_")
    if "_(" in s and s.endswith(")"):
        return True
    return bool(re.match(r"^[a-z0-9]+(?:_[a-z0-9]+)*_\([^)]+\)$", s))


def _norm_tag_key(t: str) -> str:
    return t.strip().lower().replace(" ", "_")


def _filter_girl_side_tags(tags: list[str]) -> list[str]:
    out: list[str] = []
    for t in tags:
        if not t or _is_spurious_color_penis_tag(t):
            continue
        if _looks_like_danbooru_character_tag(t):
            continue
        out.append(t)
    return out


def _join_unique(parts: list[str], protected_keys: frozenset[str] | None = None) -> str:
    seen: set[str] = set()
    out: list[str] = []
    prot = protected_keys or frozenset()
    for chunk in parts:
        if not chunk:
            continue
        for t in chunk.split(","):
            s = t.strip()
            if not s:
                continue
            if _looks_like_danbooru_character_tag(s) and _norm_tag_key(s) not in prot:
                continue
            if _is_spurious_color_penis_tag(s):
                continue
            k = s.lower()
            if k in seen:
                continue
            seen.add(k)
            out.append(s)
    return ",".join(out)


def _pick(rng: random.Random, pool: list[str], fallback: list[str]) -> str:
    p = pool if pool else fallback
    return rng.choice(p) if p else ""


def _pick_n(rng: random.Random, pool: list[str], fallback: list[str], n: int) -> list[str]:
    p = pool if pool else fallback
    if not p or n <= 0:
        return []
    n = min(n, len(p))
    return rng.sample(p, n)


def _pick_scenario_tags(rng: random.Random, scenario: dict) -> tuple[str, list[str]]:
    poses = scenario.get("poses") or ["standing"]
    pose = rng.choice(poses)
    core = list(scenario.get("core") or [])
    opt = list(scenario.get("optional") or [])
    if not opt:
        return pose, core
    n_ex = rng.randint(0, min(2, len(opt)))
    extras = rng.sample(opt, n_ex) if n_ex else []
    return pose, core + extras


def _fixed_two_girls_opening() -> str:
    # Keep this opening stable for layout consistency across generations.
    return "masterpiece,best quality,2girls,one girl on the right one on the left"


def _is_relation_style_action(action: str) -> bool:
    a = (action or "").lower()
    relation_keys = (
        "cowgirl",
        "vaginal",
        "sex",
        "missionary",
        "doggystyle",
        "anal",
        "riding",
        "straddling",
    )
    return any(k in a for k in relation_keys)


TWO_BOYS_VAGINAL_POSITIONS = [
    "doggystyle",
    "missionary",
    "cowgirl position",
    "reverse cowgirl position",
    "standing sex",
    "spooning",
    "against wall",
    "legs up",
    "on bed",
    "all fours",
]


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
                    {"default": False},
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
        "Compact tags (comma, no space): explicit NSFW picks coherent scenario bundles (pose + acts). "
        "Order: quality → count → characters → clothing → pose → scene tags → expression → "
        "(hetero partner) → background → camera. Prompt output is always one line."
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
        char_keys = frozenset(_norm_tag_key(c) for c in chars if c)

        is_sfw = content_mode == "SFW"
        is_soft = content_mode == "NSFW soft"
        is_het = content_mode == "NSFW explicit (hetero)"
        is_yuri = content_mode == "NSFW explicit (yuri)"

        # --- 1) Quality (optional, comma-separated in data; no global underscore) ---
        quality_str = ""
        if include_quality_prefix:
            quality_str = rng.choice(QUALITY_PREFIX).strip()

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
            pose = ""
            expression = _pick(rng, pools["expression"], EXPRESSION_NSFW_SOFT + EXPRESSION_SFW)
            soft_bits = []
            s1 = _pick(rng, pools["nsfw_soft"], CLOTHING_NSFW_SOFT)
            if s1:
                soft_bits.append(s1)
        else:
            clothing = _pick(rng, pools["clothing"], CLOTHING_NSFW_SOFT + CLOTHING_SFW)
            pose = ""
            expression = _pick(rng, pools["expression"], EXPRESSION_NSFW_SOFT + EXPRESSION_SFW)
            soft_bits = []
            s1 = _pick(rng, pools["nsfw_soft"], CLOTHING_NSFW_SOFT)
            if s1:
                soft_bits.append(s1)

        if is_soft and rng.random() < 0.38:
            ss = rng.choice(NSFW_SOFT_SCENARIOS)
            pose = rng.choice(ss.get("poses") or ["standing"])
            for t in ss.get("tags") or []:
                if t:
                    soft_bits.append(t)

        # --- 5) Couple / interaction (non-explicit) ---
        couple_tags: list[str] = []
        if is_sfw and n_girls == 2 and rng.random() < 0.45:
            couple_tags.append(rng.choice(["holding_hands", "looking_at_another", "hugging", "yuri"]))
        if is_soft and n_girls == 2 and rng.random() < 0.55:
            couple_tags.append(rng.choice(["yuri", "looking_at_another", "blush", "symmetrical_docking"]))

        # --- 6) Explicit scenes: coherent scenario (pose + core acts + optional flavor) ---
        sex_tags: list[str] = []
        partnered_het = False
        partner_count = 0
        scenario_pose = ""
        if is_yuri:
            scen_pool = NSFW_YURI_PAIR_SCENARIOS if n_girls == 2 else NSFW_YURI_SCENARIOS
            scen = rng.choice(scen_pool)
            scenario_pose, sex_tags = _pick_scenario_tags(rng, scen)
        elif is_het:
            if n_girls == 2:
                scen = rng.choice(NSFW_HETERO_TWO_GIRLS_SCENARIOS)
                scenario_pose, sex_tags = _pick_scenario_tags(rng, scen)
                partnered_het = True
                partner_count = 2 if rng.random() < 0.75 else 1
            elif rng.random() < 0.55:
                scen = rng.choice(NSFW_HETERO_PARTNERED_SCENARIOS)
                scenario_pose, sex_tags = _pick_scenario_tags(rng, scen)
                partnered_het = True
                partner_count = 1
            else:
                scen = rng.choice(NSFW_SOLO_SCENARIOS)
                scenario_pose, sex_tags = _pick_scenario_tags(rng, scen)
                partnered_het = False

        if is_yuri or is_het:
            pose = scenario_pose

        sex_tags = _filter_girl_side_tags(sex_tags)

        # --- Male / partner tags (hetero + partnered only), inline before background ---
        male_inline = ""
        if is_het and partnered_het:
            # 2girls template keeps action clean; avoid male appearance clutter.
            if n_girls == 2:
                male_inline = ""
            else:
                male_parts = ["faceless_male", "bald", "hetero"]
                male_parts.append("1boy")
                if rng.random() < 0.88:
                    male_parts.append(rng.choice(["large_penis", "small_penis", "huge_penis"]))
                male_inline = _join_unique(male_parts, char_keys)

        # --- Assemble main stack: quality → count → names → clothing → pose →
        #     sex → soft → couple → expression → male (hetero) ---
        main_parts: list[str] = []
        if quality_str:
            main_parts.append(quality_str)
        main_parts.append(girl_count)
        main_parts.extend(chars)
        if clothing:
            main_parts.append(clothing)
        if pose:
            main_parts.append(pose)
        main_parts.extend(sex_tags)
        main_parts.extend(soft_bits)
        main_parts.extend(couple_tags)
        if expression:
            main_parts.append(expression)
        if male_inline:
            main_parts.append(male_inline)
        if extra_tags_append.strip():
            main_parts.append(extra_tags_append.strip())

        main_line = _join_unique(main_parts, char_keys)

        # --- Background + optional camera (always last) ---
        bg_n = rng.randint(2, 4)
        fallback_bg = BACKGROUND_SFW if is_sfw else BACKGROUND_NSFW
        bg_tags = _pick_n(rng, pools["background"], fallback_bg, bg_n)
        bg_tags = [t for t in bg_tags if t and not _looks_like_danbooru_character_tag(t)]
        tail_parts: list[str] = list(bg_tags)
        if rng.random() < 0.5:
            tail_parts.append(rng.choice(CAMERA_FRAMING))
        tail_line = _join_unique(tail_parts, char_keys)

        prompt = _join_unique([main_line, tail_line], char_keys)

        # --- Special stable template for 2girls ---
        # Fixed opening → girl names → location → clothing → action/interaction
        if n_girls == 2:
            girl1 = chars[0] if len(chars) > 0 else "original"
            girl2 = chars[1] if len(chars) > 1 else "original"
            girls_with_break = _join_unique([girl1, "BREAK", girl2], char_keys)
            # Use curated fallback locations here to keep the fixed template clean.
            location = _pick(rng, BACKGROUND_NSFW if (is_soft or is_het or is_yuri) else BACKGROUND_SFW, BACKGROUND_SFW)
            action_parts: list[str] = []
            primary_action = ""
            suppress_primary_action = False
            if sex_tags:
                primary_action = sex_tags[0]
            elif couple_tags:
                primary_action = couple_tags[0]
            elif pose:
                primary_action = pose
            # Keep action focused: male count (when present) + single primary interaction.
            if is_het and partnered_het:
                if "cooperative" in primary_action.lower():
                    action_parts.append("1boy")
                else:
                    male_count_tag = "2boys" if partner_count == 2 else "1boy"
                    action_parts.append(male_count_tag)
                    if male_count_tag == "2boys":
                        action_parts.append("vaginal")
                        action_parts.append(rng.choice(TWO_BOYS_VAGINAL_POSITIONS))
                        if rng.random() < 0.8:
                            action_parts.append("fertilized ovum")
                        suppress_primary_action = True
            if primary_action and not suppress_primary_action:
                action_parts.append(primary_action)
            # Stable framing tail.
            action_parts.extend(["front view", "looking at viewer", "detailed faces"])
            if extra_tags_append.strip():
                action_parts.append(extra_tags_append.strip())
            action_block = _join_unique(action_parts, char_keys)
            prompt = _join_unique(
                [
                    _fixed_two_girls_opening(),
                    girls_with_break,
                    location,
                    clothing,
                    action_block,
                ],
                char_keys,
            )

        return {
            "ui": {"generated_prompt": (prompt,)},
            "result": (prompt,),
        }
