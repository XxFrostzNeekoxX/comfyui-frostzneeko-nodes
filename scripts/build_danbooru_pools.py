"""
Download danbooru_tags.txt (tag,count) and build nodes/data/danbooru_tag_pools.json

Usage:
  python scripts/build_danbooru_pools.py [url_or_path]

Default URL: gist raw from user request.
"""

from __future__ import annotations

import json
import os
import sys
import urllib.request

DEFAULT_URL = (
    "https://gist.githubusercontent.com/WasitSam37/7c8a2609858057bba20b654e4b8bb6fb/raw/"
    "bb46fc69122544f0b1e3e87c08cb5dd89a2ec54e/danbooru_tags.txt"
)

META_SKIP_EXACT = frozenset(
    {
        "1girl",
        "2girls",
        "3girls",
        "4girls",
        "5girls",
        "6+girls",
        "1boy",
        "2boys",
        "multiple_girls",
        "multiple_boys",
        "multiple_tails",
        "solo",
        "solo_focus",
        "duo",
        "highres",
        "absurdres",
        "lowres",
        "commentary_request",
        "commentary",
        "translated",
        "translation_request",
        "english_commentary",
        "bad_id",
        "bad_pixiv_id",
        "bad_twitter_id",
        "bad_tumblr_id",
        "bad_deviantart_id",
        "bad_facebook_id",
        "photoshop_(medium)",
        "monochrome",
        "greyscale",
        "artist_name",
        "comic",
        "sketch",
        "logo",
        "twitter_username",
        "pixiv_id",
        "sample_watermark",
        "third-party_source",
        "third-party_edit",
        "scan",
        "official_art",
    }
)

BLOCK_SUBSTR = ("loli", "shota", "toddler", "infant", "child_abuse")


def should_skip_meta(tag: str) -> bool:
    if tag in META_SKIP_EXACT:
        return True
    if tag.startswith("commentary"):
        return True
    if tag.startswith("bad_"):
        return True
    if tag.endswith("_request"):
        return True
    low = tag.lower()
    if any(b in low for b in BLOCK_SUBSTR):
        return True
    return False


def classify(tag: str) -> str | None:
    """Return single pool name or None."""
    if should_skip_meta(tag):
        return None
    tl = tag

    # --- Explicit hetero (penetration / male parts / hetero sex) ---
    het_markers = (
        "penis",
        "testicles",
        "scrotum",
        "balls",
        "phallus",
        "vaginal",
        "fellatio",
        "irrumatio",
        "paizuri",
        "deepthroat",
        "hetero",
        "creampie",
        "nakadashi",
        "bukkake",
        "ejaculation",
        "facial",
        "cum_",
        "_cum",
        "cumshot",
        "handjob",
        "footjob",
        "titfuck",
        "titty_fuck",
        "anal_",
        "_anal",
        "rape",
        "imminent_penetration",
        "imminent_vaginal",
        "after_vaginal",
        "after_sex",
        "after_fellatio",
        "after_paizuri",
        "straddling_paizuri",
        "cooperative_fellatio",
        "cooperative_paizuri",
        "male_masturbation",
        "male_pubic_hair",
        "balls_deep",
        "insertion",
        "object_insertion",
        "vaginal_object_insertion",
        "anal_object_insertion",
        "ass_grab",
        "breast_grab",
        "groping",
        "molestation",
        "after_sex",
        "implied_sex",
        "during_sex",
        "rough_sex",
        "doggy",
        "missionary",
        "cowgirl_position",
        "reverse_cowgirl",
        "spooning",
        "leg_lock",
        "standing_sex",
        "against_wall",
        "male_pov",
        "hetero",
        "penetration",
    )
    # Yuri-first (before hetero substring sweep)
    if tl in ("yuri", "implied_yuri") or "tribadism" in tl or "scissoring" in tl:
        return "explicit_yuri"
    if "cunnilingus" in tl and "male" not in tl:
        return "explicit_yuri"
    if "yuri!!!" in tl or "yuru_yuri" in tl or "yurigaoka" in tl:
        return None  # series / school names, not a yuri act tag
    yuri_extra = (
        "symmetrical_docking",
        "mutual_masturbation",
        "breast_press",
        "forehead-to-forehead",
        "interlocked_fingers",
        "nipple-to-nipple",
        "spooning_(lesbian)",
        "lesbian",
    )
    for m in yuri_extra:
        if m in tl:
            return "explicit_yuri"

    for m in het_markers:
        if m in tl:
            return "explicit_hetero"

    # --- Solo / masturbation (female-leaning) ---
    solo_markers = (
        "female_masturbation",
        "masturbation",
        "fingering",
        "dildo",
        "vibrator",
        "egg_vibrator",
        "hitachi_magic_wand",
        "clothed_masturbation",
        "masturbation_through_clothes",
        "implied_masturbation",
    )
    for m in solo_markers:
        if m in tl:
            if "male_masturbation" in tl:
                return "explicit_hetero"
            return "explicit_solo"

    # --- Clothing before soft-nsfw (thighhighs, underwear as outfit) ---
    clothing_markers = (
        "dress",
        "skirt",
        "shirt",
        "blouse",
        "kimono",
        "yukata",
        "sweater",
        "jacket",
        "coat",
        "cape",
        "hoodie",
        "pants",
        "shorts",
        "jeans",
        "leggings",
        "thighhighs",
        "pantyhose",
        "socks",
        "boots",
        "shoes",
        "sneakers",
        "heels",
        "gloves",
        "mittens",
        "hat",
        "beret",
        "cap",
        "hairband",
        "ribbon",
        "bow",
        "necktie",
        "scarf",
        "apron",
        "armor",
        "bikini",
        "swimsuit",
        "school_uniform",
        "serafuku",
        "maid",
        "nurse_cap",
        "uniform",
        "choker",
        "earrings",
        "necklace",
        "jewelry",
        "belt",
        "frills",
        "sleeves",
        "bodysuit",
        "leotard",
        "sarashi",
        "veil",
        "wedding_dress",
        "china_dress",
        "cheerleader",
        "suit",
        "business_suit",
        "labcoat",
        "eyepatch",
        "glasses",
        "sunglasses",
        "mask",
        "headphones",
        "animal_ears",
        "tail",
        "wings",
        "horns",
        "halo",
        "weapon",
        "bag",
        "backpack",
        "phone",
        "microphone",
        "food",
        "drink",
    )
    for m in clothing_markers:
        if m in tl:
            return "clothing"

    # --- NSFW soft (nudity / tease, not full sex act tags) ---
    soft_markers = (
        "nude",
        "nipples",
        "areolae",
        "pussy",
        "pubic_hair",
        "cameltoe",
        "cleavage",
        "underwear",
        "panties",
        "bra",
        "lingerie",
        "see-through",
        "topless",
        "bottomless",
        "undressing",
        "towel",
        "on_bed",
        "sheet_grab",
        "butt",
        "ass_focus",
        "zettai_ryouiki",
    )
    for m in soft_markers:
        if m in tl:
            return "nsfw_soft"

    # --- Background / setting ---
    bg_markers = (
        "background",
        "outdoors",
        "indoors",
        "sky",
        "beach",
        "ocean",
        "forest",
        "city",
        "street",
        "night",
        "day",
        "sunset",
        "pool",
        "onsen",
        "bedroom",
        "bathroom",
        "kitchen",
        "classroom",
        "gym",
        "rooftop",
        "snow",
        "rain",
        "flower",
        "nature",
        "water",
        "cloud",
        "star_(sky)",
        "moon",
    )
    for m in bg_markers:
        if m in tl:
            return "background"

    # --- Pose / action ---
    pose_markers = (
        "standing",
        "sitting",
        "lying",
        "kneeling",
        "squatting",
        "walking",
        "running",
        "jumping",
        "dancing",
        "looking_at_viewer",
        "looking_back",
        "arms_",
        "hand_on_",
        "leg_up",
        "spread_legs",
        "wariza",
        "seiza",
        "hugging",
        "holding",
        "carrying",
        "fighting_stance",
        "contrapposto",
        "bent_over",
        "all_fours",
        "on_side",
        "on_back",
        "on_stomach",
        "straddling",
        "riding",
        "symmetrical_docking",
    )
    for m in pose_markers:
        if m in tl:
            return "pose"

    # --- Expression ---
    expr_markers = (
        "smile",
        "grin",
        "frown",
        "blush",
        "tears",
        "crying",
        "open_mouth",
        "closed_mouth",
        "parted_lips",
        "tongue",
        "wink",
        "one_eye_closed",
        "surprised",
        "angry",
        "embarrassed",
        "sleepy",
        "drunk",
        "ahegao",
        "rolling_eyes",
        "saliva",
        "drooling",
    )
    for m in expr_markers:
        if m in tl:
            return "expression"

    return None


def load_lines(src: str) -> list[tuple[str, int]]:
    if src.startswith("http://") or src.startswith("https://"):
        req = urllib.request.Request(src, headers={"User-Agent": "ComfyUI-FrostzNeeko/1.0"})
        with urllib.request.urlopen(req, timeout=120) as resp:
            text = resp.read().decode("utf-8", errors="ignore")
    else:
        with open(src, encoding="utf-8", errors="ignore") as f:
            text = f.read()
    out: list[tuple[str, int]] = []
    for line in text.splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        if "," not in line:
            continue
        tag, _, rest = line.partition(",")
        tag = tag.strip()
        try:
            cnt = int(rest.strip().replace(",", ""))
        except ValueError:
            continue
        if tag:
            out.append((tag, cnt))
    return out


def main() -> None:
    src = sys.argv[1] if len(sys.argv) > 1 else DEFAULT_URL
    root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    out_path = os.path.join(root, "nodes", "data", "danbooru_tag_pools.json")
    os.makedirs(os.path.dirname(out_path), exist_ok=True)

    rows = load_lines(src)
    buckets: dict[str, list[tuple[str, int]]] = {k: [] for k in (
        "clothing",
        "pose",
        "expression",
        "background",
        "nsfw_soft",
        "explicit_hetero",
        "explicit_yuri",
        "explicit_solo",
    )}

    for tag, cnt in rows:
        cat = classify(tag)
        if cat and cat in buckets:
            buckets[cat].append((tag, cnt))

    CAP = 500
    result: dict[str, list[str]] = {}
    for cat, items in buckets.items():
        items.sort(key=lambda x: -x[1])
        result[cat] = [t for t, _ in items[:CAP]]

    meta = {
        "_source": src,
        "_counts": {k: len(v) for k, v in result.items()},
    }
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump({**meta, **result}, f, indent=0, ensure_ascii=False)
        f.write("\n")

    print(f"Wrote {out_path}")
    print(meta["_counts"])


if __name__ == "__main__":
    main()
