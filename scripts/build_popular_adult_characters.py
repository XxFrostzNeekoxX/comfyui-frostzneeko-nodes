"""
Build nodes/data/popular_adult_characters.txt from TODOS OS CHARACTERS.txt style export.
Keeps only text after the first comma; filters to popular franchises + adult-safe heuristics.

Usage (from repo root):
  python scripts/build_popular_adult_characters.py "path/to/TODOS OS CHARACTERS.txt"
"""

from __future__ import annotations

import os
import sys

ALLOW_SET = frozenset(
    {
        "hololive",
        "nijisanji",
        "vshojo",
        "vtuber",
        "v tuber",
        "vocaloid",
        "hatsune",
        "project sekai",
        "colorful stage",
        "chainsaw man",
        "genshin impact",
        "honkai",
        "star rail",
        "fate",
        "arknights",
        "azur lane",
        "kancolle",
        "kantai collection",
        "girls' frontline",
        "girls frontline",
        "nier automata",
        "nier:",
        "nier replicant",
        "nier:automata",
        "re:zero",
        "konosuba",
        "overlord",
        "persona",
        "spy x family",
        "demon slayer",
        "jujutsu",
        "one piece",
        "naruto",
        "bleach",
        "attack on titan",
        "love live",
        "lovelive",
        "idolmaster",
        "idol master",
        "bang dream",
        "my hero academia",
        "fire emblem",
        "final fantasy",
        "steins;gate",
        "steins gate",
        "code geass",
        "jojo",
        "touhou",
        "sword art online",
        "evangelion",
        "league of legends",
        "cyberpunk",
        "resident evil",
        "street fighter",
        "dragon ball",
        "nikke",
        "umamusume",
        "granblue fantasy",
        "dragon quest",
        "elden ring",
        "dark souls",
        "bloodborne",
        "monster hunter",
        "zelda",
        "metroid",
        "bayonetta",
        "metal gear",
        "devil may cry",
        "ace attorney",
        "danganronpa",
        "octopath",
        "black lagoon",
        "cowboy bebop",
        "ghost in the shell",
        "hellsing",
        "berserk",
        "goblin slayer",
        "vinland saga",
        "psycho-pass",
        "death note",
        "fullmetal",
        "hunter x hunter",
        "gintama",
        "noragami",
    }
)

# Chinese / mixed labels in the source file
ALLOW_CJK = frozenset(
    {
        "原神",
        "星穹",
        "崩坏",
        "明日方舟",
        "碧蓝航线",
        "舰队",
        "少女前线",
        "电锯人",
        "女神异闻录",
        "间谍过家家",
        "鬼灭",
        "咒术",
        "海贼王",
        "火影",
        "死神",
        "进击",
        "赛马娘",
        "偶像大师",
        "东方project",
        "东方",
        "世界计划",
        "初音",
        "尼尔",
        "为美好的世界",
        "公主准则",
        "从零",
        "刀剑神域",
        "新世纪福音",
        "龙珠",
        "胜利女神",
    }
)


def allowed(hay: str) -> bool:
    h = hay.lower()
    if any(a in h for a in ALLOW_SET):
        return True
    return any(cjk in hay for cjk in ALLOW_CJK)


BLOCK_SUBSTR = [
    "光之美少女",
    "precure",
    "请问您今天要来点兔子",
    "gochiusa",
    "点兔",
    "草莓棉花糖",
    "小学生",
    "幼稚园",
    "幼儿园",
    "幼女",
    "萝莉",
    "正太",
    "kindergarten",
    "babylonia",
    "幼少",
]

BLOCK_LOWER = ["shota", "loli", "elementary", "child", "kindergarten"]

CHILD_TAG_MARKERS = (
    "klee (genshin impact)",
    "qiqi (genshin impact)",
    "sayu (genshin impact)",
    "diona (genshin impact)",
    "yaoyao (genshin impact)",
    "nahida (genshin impact)",
    "abigail williams",
    "anya (spy x family)",
    "ana coppola",
    "sharo kirima",
    "kanna kamui",
    "platelet (",
    "elementary school",
)

MALE_TAG_MARKERS = (
    "(male)",
    "9s (nier automata)",
    "aether (genshin impact)",
    "abarai renji (bleach)",
    "agatsuma zenitsu",
    "astolfo (fate)",
    "armin arlert",
    "alphonse elric",
)

TAG_FRANCHISE_MARKERS = (
    "(genshin impact)",
    "(honkai",
    "(fate)",
    "(fate/",
    "(hololive)",
    "(arknights)",
    "(azur lane)",
    "(kancolle)",
    "(girls' frontline)",
    "(chainsaw man)",
    "(nier",
    "(persona)",
    "(spy x family)",
    "(re:zero",
    "(konosuba)",
    "(overlord)",
    "(sao)",
    "(touhou)",
    "(love live",
    "(umamusume)",
    "(idolmaster",
    "(nikke)",
    "(granblue fantasy)",
    "(league of legends)",
)


def blocked(line: str, tag: str) -> bool:
    combo = line + "\n" + tag
    low = combo.lower()
    tlow = tag.lower()
    if "（男）" in line or "（男性）" in line:
        return True
    for b in BLOCK_SUBSTR:
        if b in combo:
            return True
    for b in BLOCK_LOWER:
        if b in low:
            return True
    for c in CHILD_TAG_MARKERS:
        if c in tlow:
            return True
    for m in MALE_TAG_MARKERS:
        if m in tlow:
            return True
    if "-chan (" in tlow and ("azur lane" in tlow or "kancolle" in tlow):
        return True
    if "(blue archive)" in tlow:
        return True
    return False


def collect(src: str) -> list[str]:
    seen: set[str] = set()
    out: list[str] = []

    def add_from_file(need_allow: bool) -> None:
        with open(src, encoding="utf-8", errors="ignore") as f:
            for raw in f:
                line = raw.strip()
                if not line or line.startswith("#"):
                    continue
                if "," not in line:
                    continue
                tag = line.split(",", 1)[1].strip()
                if not tag or tag in seen:
                    continue
                if blocked(line, tag):
                    continue
                hay = line + " " + tag
                if need_allow and not allowed(hay):
                    continue
                if not need_allow:
                    tl = tag.lower()
                    if not any(m in tl for m in TAG_FRANCHISE_MARKERS):
                        continue
                seen.add(tag)
                out.append(tag)

    add_from_file(need_allow=True)
    if len(out) < 1000:
        add_from_file(need_allow=False)
    out.sort(key=str.lower)
    return out


def main() -> None:
    if len(sys.argv) < 2:
        print("Usage: python scripts/build_popular_adult_characters.py <characters.txt>", file=sys.stderr)
        sys.exit(1)
    src = sys.argv[1]
    if not os.path.isfile(src):
        print(f"Not found: {src}", file=sys.stderr)
        sys.exit(1)

    root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    out_dir = os.path.join(root, "nodes", "data")
    os.makedirs(out_dir, exist_ok=True)
    out_path = os.path.join(out_dir, "popular_adult_characters.txt")

    tags = collect(src)
    with open(out_path, "w", encoding="utf-8") as w:
        w.write("# Popular adult-oriented character tags (Danbooru-style). One per line.\n")
        w.write(f"# Source: {os.path.basename(src)} — tag = text after first comma.\n")
        for t in tags:
            w.write(t + "\n")

    print(f"Wrote {len(tags)} tags -> {out_path}")


if __name__ == "__main__":
    main()
