"""
Curated Danbooru-style tag pools for FN Random Prompt Generator.
Tags follow https://danbooru.donmai.us/wiki_pages/help:tagging conventions (underscores, English).
Expand or edit this file to tune generations — the full Danbooru corpus is not bundled.
"""

# Comma-separated, no space after commas (CLIP / user preference). Weights optional.
QUALITY_PREFIX = [
    "masterpiece:1.2,best quality,highly detailed:1.1",
    "masterpiece:1.2,best quality,newest,absurdres,highly detailed:1.1",
    "masterpiece:1.2,best quality,very aesthetic,absurdres,detailed eyes,detailed skin",
    "masterpiece:1.2,best quality,newest,highres,intricate details,sharp focus",
]

EYE_COLOR_EXTRA = [
    "amber eyes",
    "blue eyes",
    "green eyes",
    "red eyes",
    "yellow eyes",
    "purple eyes",
    "pink eyes",
    "heterochromia",
    "glowing eyes",
]

BODY_EXTRA = [
    "huge breasts",
    "large breasts",
    "medium breasts",
    "pregnant",
    "thick thighs",
    "wide hips",
    "slim waist",
    "mole under eye",
    "freckles",
]

# Appended after background tags when non-empty.
CAMERA_FRAMING = [
    "front view",
    "low angle",
    "from above",
    "cowboy shot",
    "dutch angle",
    "from side",
    "three-quarter view",
]

# SFW outfits / states
CLOTHING_SFW = [
    "dress",
    "casual",
    "school uniform",
    "serafuku",
    "kimono",
    "yukata",
    "sundress",
    "sweater",
    "hoodie",
    "tank top",
    "shorts",
    "miniskirt",
    "thighhighs",
    "leggings",
    "sportswear",
    "gym uniform",
    "maid",
    "nurse",
    "office lady",
    "suit",
    "wedding dress",
    "china dress",
    "sailor dress",
    "bikini",
    "one-piece swimsuit",
    "wetsuit",
    "armor",
    "fantasy armor",
    "witch hat, witch dress",
    "cape",
    "coat",
    "scarf",
    "hat",
    "beret",
    "apron",
    "pajamas",
    "yoga pants",
]

# NSFW soft — suggestive clothing / partial nudity / mood (no explicit sex acts)
CLOTHING_NSFW_SOFT = [
    "lingerie",
    "lace lingerie",
    "babydoll",
    "chemise",
    "bustier",
    "fishnets",
    "garter straps",
    "thigh strap",
    "micro bikini",
    "string bikini",
    "underwear only",
    "bra and panties",
    "panties",
    "bra",
    "towel",
    "towel around body",
    "naked towel",
    "nude",
    "partially nude",
    "covered nipples",
    "pasties",
    "bodypaint",
    "see-through",
    "wet clothes",
    "shirt lift",
    "skirt lift",
    "undressing",
    "cleavage",
    "sideboob",
    "bare shoulders",
    "bare legs",
    "barefoot",
    "collarbone",
    "bed sheet",
    "bed sheet only",
]

POSE_ACTION_SFW = [
    "standing",
    "standing on one leg",
    "sitting",
    "sitting on chair",
    "squatting",
    "kneeling",
    "lying",
    "lying on back",
    "lying on stomach",
    "walking",
    "running",
    "stretching",
    "arms up",
    "arms behind head",
    "hand on hip",
    "peace sign",
    "waving",
    "looking at viewer",
    "looking back",
    "profile",
    "from side",
    "from behind",
    "dynamic pose",
    "contrapposto",
    "crossed arms",
    "leaning forward",
    "leaning back",
    "head tilt",
    "hair flip",
    "holding phone",
    "eating",
    "drinking",
    "reading book",
    "sleeping",
    "dancing",
    "jumping",
]

POSE_ACTION_NSFW_SOFT = [
    "arched back",
    "bent over",
    "on bed",
    "on all fours",
    "spread legs",
    "legs together",
    "straddling",
    "sitting on bed",
    "lying on bed",
    "against wall",
    "wet skin",
    "steam",
    "heavy breathing",
    "seductive smile",
    "half-closed eyes",
    "bedroom eyes",
    "lip bite",
    "blush",
    "sweat",
    "teasing",
    "covering breasts",
    "covering crotch",
    "finger to mouth",
    "pulling clothes",
]

EXPRESSION_SFW = [
    "smile",
    "light smile",
    "grin",
    "open mouth",
    "surprised",
    "embarrassed",
    "shy",
    "serious",
    "determined",
    "sleepy",
    "angry",
    "pout",
    "one eye closed",
    "wink",
    "tears",
    "laughing",
]

EXPRESSION_NSFW_SOFT = [
    "blush",
    "embarrassed",
    "nervous smile",
    "seductive smile",
    "half-closed eyes",
    "parted lips",
    "drooling",
    "tears",
    "ahegao",
    "rolling eyes",
]

BACKGROUND_SFW = [
    "simple background",
    "white background",
    "gradient background",
    "blue sky",
    "clouds",
    "sunset",
    "night sky",
    "stars",
    "cityscape",
    "street",
    "rooftop",
    "bedroom",
    "living room",
    "kitchen",
    "classroom",
    "library",
    "cafe",
    "beach",
    "ocean",
    "forest",
    "flower field",
    "park",
    "garden",
    "onsen",
    "poolside",
    "rain",
    "snow",
    "fantasy landscape",
    "castle interior",
    "dungeon",
    "spaceship interior",
    "neon lights",
]

BACKGROUND_NSFW = [
    "bedroom",
    "on bed",
    "bathroom",
    "shower",
    "steam",
    "locker room",
    "hotel room",
    "dim lighting",
    "candles",
    "curtains closed",
    "mirror",
    "simple background",
    "dark background",
]

# --- Coherent NSFW scenario bundles (one RNG pick = matching pose + acts + flavor) ---
# Generator picks one scenario, chooses 1 pose from "poses", includes all "core", plus 0–2 from "optional".

NSFW_HETERO_PARTNERED_SCENARIOS = [
    {
        "poses": ["kneeling", "on knees", "squatting"],
        "core": ["fellatio", "licking penis", "oral"],
        "optional": ["saliva trail", "hands on another's thighs", "eye contact", "trembling", "blush"],
    },
    {
        "poses": ["lying", "lying on back", "on bed"],
        "core": ["irrumatio", "deepthroat", "fellatio"],
        "optional": ["tears", "saliva", "hands on head", "gagging"],
    },
    {
        "poses": ["straddling", "sitting", "girl on top"],
        "core": ["paizuri", "breasts squeeze"],
        "optional": ["licking penis", "saliva", "cleavage", "nipples"],
    },
    {
        "poses": ["lying", "lying on back", "on bed", "spread legs"],
        "core": ["missionary", "sex", "vaginal"],
        "optional": ["leg lock", "hands intertwined", "pillow grab", "sweat"],
    },
    {
        "poses": ["straddling", "cowgirl position", "girl on top"],
        "core": ["cowgirl position", "sex", "vaginal"],
        "optional": ["bouncing breasts", "hands on chest", "hip grab", "grinding"],
    },
    {
        "poses": ["all fours", "on all fours", "top-down bottom-up"],
        "core": ["doggystyle", "sex", "from behind"],
        "optional": ["ass grab", "hip grab", "hair pull", "looking back"],
    },
    {
        "poses": ["standing", "against wall", "leg up"],
        "core": ["standing sex", "against wall", "sex"],
        "optional": ["leg lock", "lifted", "pinned", "kiss"],
    },
    {
        "poses": ["sitting", "on chair", "spread legs"],
        "core": ["handjob", "penis", "erection"],
        "optional": ["precum", "blush", "looking at penis", "two-handed handjob"],
    },
    {
        "poses": ["lying", "sixty-nine", "on side"],
        "core": ["sixty-nine", "cunnilingus", "fellatio"],
        "optional": ["mutual oral", "spread legs", "trembling"],
    },
    {
        "poses": ["sitting on face", "facesitting", "spread legs"],
        "core": ["facesitting", "cunnilingus", "girl on top"],
        "optional": ["thigh grab", "wet pussy", "trembling", "grab sheets"],
    },
    {
        "poses": ["all fours", "on all fours", "ass up"],
        "core": ["anal sex", "doggystyle", "sex"],
        "optional": ["spread anus", "painful", "tears", "hip grab"],
    },
    {
        "poses": ["lying", "lying on stomach", "on bed"],
        "core": ["prone bone", "sex", "from behind"],
        "optional": ["ass grab", "pinned", "sheets grab"],
    },
]

NSFW_SOLO_SCENARIOS: list[dict] = [
    {
        "poses": ["sitting", "spread legs", "on bed"],
        "core": ["masturbation", "fingering"],
        "optional": ["wet pussy", "blush", "trembling", "pussy juice"],
    },
    {
        "poses": ["lying", "lying on back", "on bed"],
        "core": ["masturbation", "breast grab", "nipple tweak"],
        "optional": ["spread legs", "arched back", "sweat"],
    },
    {
        "poses": ["kneeling", "on bed"],
        "core": ["dildo", "object insertion", "masturbation"],
        "optional": ["saliva", "blush", "trembling"],
    },
    {
        "poses": ["squatting", "on bed", "spread legs"],
        "core": ["spread pussy", "fingering"],
        "optional": ["mirror", "embarrassed", "wet pussy"],
    },
    {
        "poses": ["lying", "on stomach"],
        "core": ["pillow humping", "grinding"],
        "optional": ["blush", "grab pillow", "sweat"],
    },
    {
        "poses": ["standing", "against wall"],
        "core": ["egg vibrator", "masturbation", "public vibrator"],
        "optional": ["trembling", "biting lip", "hand over mouth"],
    },
]

NSFW_YURI_SCENARIOS = [
    {
        "poses": ["lying", "on bed", "cuddle"],
        "core": ["cunnilingus", "spread legs", "yuri"],
        "optional": ["thigh grab", "trembling", "wet pussy", "blush"],
    },
    {
        "poses": ["all fours", "on all fours"],
        "core": ["cunnilingus", "from behind", "yuri"],
        "optional": ["ass grab", "looking back", "trembling"],
    },
    {
        "poses": ["scissoring", "lying", "on bed"],
        "core": ["tribadism", "scissoring", "yuri"],
        "optional": ["holding hands", "sweat", "kiss", "blush"],
    },
    {
        "poses": ["straddling", "girl on top"],
        "core": ["kissing", "breast sucking", "yuri"],
        "optional": ["groping", "hip grab", "eye contact"],
    },
    {
        "poses": ["lying", "sixty-nine"],
        "core": ["sixty-nine", "cunnilingus", "yuri"],
        "optional": ["mutual masturbation", "trembling", "spread legs"],
    },
    {
        "poses": ["doggystyle", "strap-on"],
        "core": ["strap-on", "sex", "yuri"],
        "optional": ["hip grab", "hair pull", "looking back"],
    },
]

# When girl_count = 2girls + explicit yuri: pair-focused bundles (still one shared scene).
NSFW_YURI_PAIR_SCENARIOS = [
    {
        "poses": ["cuddling", "on bed", "lying"],
        "core": ["yuri", "kissing", "fingering", "2girls"],
        "optional": ["blush", "embrace", "hand on breast", "symmetrical docking"],
    },
    {
        "poses": ["scissoring", "tribadism", "on bed"],
        "core": ["yuri", "tribadism", "scissoring", "2girls"],
        "optional": ["holding hands", "sweat", "trembling"],
    },
    {
        "poses": ["mutual masturbation", "sitting", "facing each other"],
        "core": ["yuri", "mutual masturbation", "2girls"],
        "optional": ["eye contact", "spread legs", "blush"],
    },
    {
        "poses": ["shared dildo", "straddling"],
        "core": ["yuri", "shared dildo", "2girls"],
        "optional": ["cooperative", "kiss", "groping"],
    },
]

NSFW_HETERO_TWO_GIRLS_SCENARIOS = [
    {
        "poses": ["kneeling", "side by side", "double kneeling", "kneeling facing viewer"],
        "core": ["cooperative fellatio", "2girls", "teamwork"],
        "optional": ["licking penis", "handjob", "eye contact", "blush"],
    },
    {
        "poses": ["paizuri", "2girls", "double paizuri pose", "chest to chest"],
        "core": ["double paizuri", "2girls", "paizuri"],
        "optional": ["cooperative", "saliva", "cleavage"],
    },
    {
        "poses": ["straddling", "cowgirl position", "double cowgirl", "reverse cowgirl position"],
        "core": ["cowgirl position", "2girls", "taking turns"],
        "optional": ["kissing", "breast press", "sweat"],
    },
    {
        "poses": ["lying", "on bed", "split level", "spitroast pose", "sandwich position"],
        "core": ["2girls", "group pose", "taking turns"],
        "optional": ["cunnilingus", "fellatio", "kiss"],
    },
]

# NSFW soft: suggestive coherence (optional in generator).
NSFW_SOFT_SCENARIOS = [
    {
        "poses": ["bent over", "skirt lift", "from behind"],
        "tags": ["panties", "embarrassed", "pantyshot"],
    },
    {
        "poses": ["lying", "on bed", "sheet grab"],
        "tags": ["underwear only", "cleavage", "bed sheet"],
    },
    {
        "poses": ["stretching", "arms up", "shirt lift"],
        "tags": ["midriff", "underboob", "sweat"],
    },
    {
        "poses": ["sitting", "crossed legs"],
        "tags": ["miniskirt", "zettai ryouiki", "smug"],
    },
    {
        "poses": ["towel", "wet hair", "steam"],
        "tags": ["bathroom", "naked towel", "skinny dipping"],
    },
]

# Explicit sex-act tags (Danbooru naming). Used only when content_mode = NSFW explicit.
EXPLICIT_SOLO = [
    "masturbation",
    "fingering",
    "spread pussy",
    "dildo",
    "egg vibrator",
    "object insertion",
]

EXPLICIT_PARTNERED_MM = [
    "vaginal",
    "sex",
    "straddling",
    "cowgirl position",
    "reverse cowgirl position",
    "missionary",
    "doggystyle",
    "spooning",
    "standing sex",
    "against wall",
    "leg lock",
    "fellatio",
    "irrumatio",
    "deepthroat",
    "licking penis",
    "paizuri",
    "handjob",
    "cunnilingus",
    "sixty-nine",
    "anal sex",
    "double penetration",
    "creampie",
    "cum",
    "facial",
    "ejaculation",
]

EXPLICIT_YURI = [
    "yuri",
    "cunnilingus",
    "fingering",
    "tribadism",
    "scissoring",
    "kissing",
    "breast sucking",
    "groping",
    "covered in cum",
]

# Pair dynamics when 2girls + explicit
EXPLICIT_YURI_EXTRA = [
    "mutual masturbation",
    "shared dildo",
    "strap-on",
]

FALLBACK_CHARACTER_TAGS = [
    "original",
    "hatsune miku",
    "rem (re:zero)",
    "raiden shogun",
    "yae miko",
    "frieren",
    "makima (chainsaw man)",
    "2b (nier automata)",
    "tifa lockhart",
    "aqua (konosuba)",
    "megumin",
    "marin kitagawa",
    "power (chainsaw man)",
    "nilou (genshin impact)",
    "furina (genshin impact)",
]
