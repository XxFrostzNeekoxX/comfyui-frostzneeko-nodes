"""Writes nodes/data/popular_adult_characters.txt — exactly 300 female adult-presenting tags."""
from pathlib import Path

# One tag per line below (Danbooru-style). Exactly 300 entries — verify with: python write_300_female_adult_tags.py
RAW = r"""
sakura miko
houshou marine
shirakami fubuki
nakiri ayame
minato aqua
tokino sora
azki (hololive)
yozora mel
aki rosenthal
ninomae ina'nis
mori calliope
takanashi kiara
irys (hololive)
ouro kronii
ceres fauna
nanashi mumei
hakos baelz
vestia zeta
kureiji ollie
anya melfissa
pavolia reine
moona hoshinova
ayunda risu
airani iofifteen
amane kanata
himemori luna
tokoyami towa
yukihana lamy
shishiro botan
omaru polka
shiranui flare
shirogane noel
hoshimachi suisei
sakamata chloe
kazama iroha
takane lui
laplus darkness
fuwawa abyssgard
mococo abyssgard
oozora subaru
nekomata okayu
inugami korone
akai haato
yuzuki choco
roboco-san
a-chan (hololive)
raiden shogun
yae miko
beidou (genshin impact)
ningguang (genshin impact)
yelan (genshin impact)
shenhe (genshin impact)
ganyu (genshin impact)
jean (genshin impact)
lisa (genshin impact)
eula (genshin impact)
rosaria (genshin impact)
mavuika (genshin impact)
chiori (genshin impact)
clorinde (genshin impact)
arlecchino (genshin impact)
columbina (genshin impact)
furina (genshin impact)
navia (genshin impact)
chasca (genshin impact)
mualani (genshin impact)
citlali (genshin impact)
kafka (honkai  star rail)
silver wolf (honkai  star rail)
acheron (honkai  star rail)
black swan (honkai  star rail)
robin (honkai  star rail)
firefly (honkai  star rail)
ruan mei (honkai  star rail)
tingyun (honkai  star rail)
natasha (honkai  star rail)
himeko (honkai  star rail)
guinaifen (honkai  star rail)
yukong (honkai  star rail)
raiden mei
yae sakura
durandal (honkai impact)
rita rossweisse
mobius (honkai impact)
elysia (honkai impact)
fu hua
seele vollerei
bronya zaychik
artoria pendragon (fate)
artoria pendragon (lancer) (fate)
morgan le fay (fate)
scathach (fate)
jeanne d'arc (fate)
jeanne d'arc (alter) (fate)
tamamo no mae (fate/extra)
nero claudius (fate)
bb (fate)
meltryllis (fate)
ishtar (fate)
ereshkigal (fate)
miyamoto musashi (fate)
okita souji (fate)
okita souji alter (fate)
shuten douji (fate)
minamoto no raikou (fate)
nitocris (fate)
cleopatra (fate)
yang guifei (fate)
sei shounagon (fate)
murasaki shikibu (fate)
sesshouin kiara (fate)
kama (fate)
parvati (fate)
katsushika hokusai (fate)
quetzalcoatl (fate)
2b (nier automata)
a2 (nier automata)
tifa lockhart
aerith gainsborough
yuna (ff10)
lightning farron
fran (ff12)
jessie rasberry
yuffie kisaragi
lulu (ff10)
terra branford
celes chere
agrias oaks
cindy aurum
lunafreya nox fleuret
jill valentine
claire redfield
ada wong
makoto niijima
ann takamaki
takemi tae
mitsuru kirijo
yukari takeba
rise kujikawa
naoto shirogane
margaret (persona)
elizabeth (persona)
sae niijima
makima (chainsaw man)
power (chainsaw man)
himeno (chainsaw man)
kobeni higashiyama
yoru (chainsaw man)
yor briar
emilia (re:zero)
rem (re:zero)
ram (re:zero)
crusch karsten
aqua (konosuba)
darkness (konosuba)
wiz (konosuba)
albedo (overlord)
shalltear bloodfallen
narberal gamma
lupusregina beta
solution epsilon
nobara kugisaki
maki zenin
mei mei (jujutsu kaisen)
utahime iori
mitsuri kanroji
shinobu kochou
daki (kimetsu no yaiba)
mikasa ackerman
historia reiss
annie leonhart
hange zoe
nami (one piece)
nico robin
boa hancock
yamato (one piece)
reiju vinsmoke
uta (one piece)
perona
kalifa (one piece)
nefertari vivi
matsumoto rangiku
inoue orihime
kuchiki rukia
shihouin yoruichi
tier harribel
neliel tu oderschvank
tsunade (naruto)
hyuuga hinata
haruno sakura
temari (naruto)
mei terumi
konan (naruto)
ch'en (arknights)
hoshiguma (arknights)
siege (arknights)
saria (arknights)
silence (arknights)
ifrit (arknights)
exusiai (arknights)
texas (arknights)
lappland (arknights)
w (arknights)
skadi (arknights)
specter (arknights)
blaze (arknights)
surtr (arknights)
mudrock (arknights)
kal'tsit (arknights)
amiya (arknights)
modernia (nikke)
rapi (nikke)
snow white (nikke)
scarlet (nikke)
volume (nikke)
privaty (nikke)
atago (azur lane)
taihou (azur lane)
new jersey (azur lane)
enterprise (azur lane)
bremerton (azur lane)
sirius (azur lane)
formidable (azur lane)
illustrious (azur lane)
akagi (azur lane)
kaga (azur lane)
prinz eugen (azur lane)
friedrich der grosse (azur lane)
yamato (kancolle)
kongou (kancolle)
kashima (kancolle)
atago (kancolle)
hatsune miku
megurine luka
meiko (vocaloid)
kasane teto
yowane haku
reimu hakurei
marisa kirisame
yakumo yukari
konpaku youmu
patchouli knowledge
izayoi sakuya
kochiya sanae
yasaka kanako
moriya suwako
shameimaru aya
reisen udongein inaba
houraisan kaguya
fujiwara no mokou
byleth (female) (fire emblem)
edelgard von hresvelg
rhea (fire emblem)
camilla (fire emblem)
tharja (fire emblem)
cordelia (fire emblem)
lucina (fire emblem)
pyra (xenoblade)
mythra (xenoblade)
nia (xenoblade)
elma (xenoblade x)
melia antiqua
katsuragi misato
akagi ritsuko
souryuu asuka langley
makinami mari illustrious
chun-li
juri han
cammy white
mai shiranui
kasumi (doa)
nyotengu
tina armstrong
ahri (league of legends)
miss fortune (league of legends)
caitlyn (league of legends)
lux (league of legends)
mercy (overwatch)
widowmaker (overwatch)
tracer (overwatch)
ashe (overwatch)
brigitte (overwatch)
bayonetta
jeanne (bayonetta)
rosa (bayonetta)
samus aran
princess zelda
urbosa
marin kitagawa
fubuki (one-punch man)
tatsumaki
lucy (cyberpunk)
motoko kusanagi
tohsaka rin
matou sakura
kurisu makise
hitagi senjougahara
hanekawa tsubasa
yukinoshita yukino
yuigahama yui
"""


def main() -> None:
    lines = [ln.strip() for ln in RAW.strip().splitlines() if ln.strip() and not ln.strip().startswith("#")]
    seen: set[str] = set()
    uniq: list[str] = []
    for ln in lines:
        k = ln.lower()
        if k in seen:
            continue
        seen.add(k)
        uniq.append(ln)
    n = len(uniq)
    if n != 300:
        raise SystemExit(f"Expected 300 unique tags, got {n}. Edit RAW in this script.")
    root = Path(__file__).resolve().parents[1]
    out = root / "nodes" / "data" / "popular_adult_characters.txt"
    out.parent.mkdir(parents=True, exist_ok=True)
    header = (
        "# 300 curated female adult-presenting character tags (Danbooru-style).\n"
        "# Edit scripts/write_300_female_adult_tags.py (RAW) to change the set.\n"
    )
    out.write_text(header + "\n".join(uniq) + "\n", encoding="utf-8")
    print(f"OK: {n} tags -> {out}")


if __name__ == "__main__":
    main()
