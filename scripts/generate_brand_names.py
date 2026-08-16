#!/usr/bin/env python3
"""Regenerate the screened brand-name catalogues that this package ships.

`brand_drug()` used to build a name at runtime from the morpheme pools, which put
31,500 distinct names (30,752 more for the zh_CN Chinese path) into the public API.
A space that size cannot be screened against real product names, so the package was
promising something it could not check: when the same morphemes were ported to
faker-js (faker-js/faker#3949) a human screen of a ~250-name sample found five names
shadowing real products, and every one of them was reachable from these pools too.

The fix is to screen a set small enough to actually screen, and ship that set:

    morpheme space  ->  automated screens  ->  survivors  ->  reviewed sample  ->  shipped

This script owns every step except the human review, and rewrites the generated
modules from the same inputs every time, so `--check` in CI proves the shipped
tuples are exactly what the screens and the review record produce.

Usage:

    python scripts/generate_brand_names.py            # rewrite the generated modules
    python scripts/generate_brand_names.py --check    # fail if they are out of date
    python scripts/generate_brand_names.py --propose 20
                                                      # print unreviewed survivors,
                                                      # evenly spread across prefixes,
                                                      # as candidates for review

Screening is point-in-time, and none of it is a trademark search. See the "Brand
drug names" sections of README.md and CONTRIBUTING.md for what is and is not claimed.
"""

from __future__ import annotations

import argparse
import importlib
import re
import sys
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from faker_healthcare.constants import (  # noqa: E402
    BRAND_FORBIDDEN_ENDINGS,
    BRAND_INFIXES,
    BRAND_PREFIXES,
    BRAND_SUFFIXES,
)
from faker_healthcare.zh_CN.constants import ZH_BRAND_CHARS  # noqa: E402


LATIN_TARGET = REPO_ROOT / "faker_healthcare" / "brand_names.py"
ZH_TARGET = REPO_ROOT / "faker_healthcare" / "zh_CN" / "brand_names.py"

# The shape `brand_drug()` has always produced, and which tests/test_provider.py pins.
NAME_PATTERN = re.compile(r"[A-Z][a-z]{4,13}")

LOCALES = ("pt_BR", "es_ES", "zh_CN", "fr_FR", "de_DE")


# --------------------------------------------------------------------------------------
# Screen 1: real products.
#
# APPEND-ONLY. A name is never removed from this list, even if the product is
# discontinued or the collision looks marginal: removing one would let a name that a
# reviewer already rejected back into the shipped set, silently. Add the reason.
# --------------------------------------------------------------------------------------
REAL_PRODUCT_DENYLIST: tuple[str, ...] = (
    # Found by the human screen during the faker-js port (faker-js/faker#3949, 2026-07).
    # All five were reachable from these morphemes; the first screen missed them because
    # it only covered well-known *human* brands.
    "Revalor",  # FDA-approved veterinary implant
    "Orbax",  # FDA-approved veterinary antibiotic (orbifloxacin)
    "Orbaex",  # the removed name; it shadowed Orbax
    "Lumemox",  # moxifloxacin eye drop marketed in India and Kenya
    "Nuvizen",  # medication-device trademark
    "Sonadex",  # collides with a marketed product
    # Well-known human brands. These are here so the screen is enforced at generation
    # time and not only in the test suite; tests/test_provider.py checks the same set.
    "Advil",
    "Augmentin",
    "Cosentyx",
    "Dupixent",
    "Eliquis",
    "Entyvio",
    "Glucophage",
    "Humira",
    "Januvia",
    "Jardiance",
    "Keytruda",
    "Lantus",
    "Lipitor",
    "Mounjaro",
    "Nexium",
    "Norvasc",
    "Ozempic",
    "Plavix",
    "Prilosec",
    "Prozac",
    "Skyrizi",
    "Synthroid",
    "Taltz",
    "Tylenol",
    "Ventolin",
    "Wegovy",
    "Xanax",
    "Xolair",
    "Zocor",
    "Zoloft",
)

# --------------------------------------------------------------------------------------
# Screen 2: offensive substrings.
#
# Concatenating morphemes can produce a slur or profanity that none of the parts
# contains. That shipped once: 2.3.1 ("Fix brand morphemes that could concatenate into
# offensive substrings") swapped the `zia`/`pex` suffixes and the `se`/`ga` infixes
# after 256 of the 31,500 names came out offensive. That check ran in a throwaway
# script, so nothing stopped the morphemes drifting back; this list is that check,
# committed. It is a superset of the one used in 2.3.1 — only ever add terms.
# --------------------------------------------------------------------------------------
OFFENSIVE_SUBSTRINGS: tuple[str, ...] = (
    "anal",
    "anus",
    "arse",
    "ass",
    "bastard",
    "bitch",
    "boob",
    "clit",
    "cock",
    "coon",
    "crap",
    "cunt",
    "dick",
    "dildo",
    "dyke",
    "fag",
    "fuck",
    "gook",
    "homo",
    "jizz",
    "kike",
    "nazi",
    "negro",
    "nigg",
    "paki",
    "penis",
    "piss",
    "poop",
    "porn",
    "prick",
    "pube",
    "queer",
    "rape",
    "rapist",
    "retard",
    "scrotum",
    "semen",
    "sex",
    "shit",
    "slut",
    "spic",
    "sperm",
    "tits",
    "turd",
    "twat",
    "vagina",
    "wank",
    "whore",
)

# --------------------------------------------------------------------------------------
# The reviewed Latin sample.
#
# Screens 1-4 are mechanical and reject a name for a reason a machine can state. They
# cannot tell you that a surviving name is somebody's product. That takes a person
# reading the list, which is only possible because the list is ~250 names and not
# 31,500. These names were read one by one during the faker-js port review
# (faker-js/faker#3949, screened 2026-07); the six entries at the top of
# REAL_PRODUCT_DENYLIST are what that review threw out.
#
# To grow this list, run `--propose N`, review the names it prints, and append the ones
# that survive review here. Never append a name that has not been read by a human, and
# never append one without re-running this script: every entry is re-screened at
# generation time, so a name that later collides with a catalogue drug drops out on the
# next run rather than lingering.
# --------------------------------------------------------------------------------------
REVIEWED_LATIN_NAMES: tuple[str, ...] = (
    "Advaen",
    "Advavor",
    "Advavue",
    "Advazen",
    "Advazepral",
    "Aldadiol",
    "Aldatalor",
    "Andelcor",
    "Andelnavia",
    "Andelol",
    "Andelpradyn",
    "Andelsyyl",
    "Andeltor",
    "Andelzen",
    "Brixdara",
    "Brixgis",
    "Brixol",
    "Brixvor",
    "Caeldivex",
    "Caelduzen",
    "Caellor",
    "Caelmira",
    "Caelnix",
    "Caelpravue",
    "Caeltapral",
    "Caeltor",
    "Caelvue",
    "Cavibequel",
    "Cavidyn",
    "Cavipramira",
    "Cetracoyl",
    "Cetrapramira",
    "Cetraprasen",
    "Cetrasen",
    "Corvamira",
    "Corvaplex",
    "Corvavia",
    "Corvazetiva",
    "Elixcomox",
    "Elixdiplex",
    "Elixnopral",
    "Elixxen",
    "Elixzen",
    "Fendafen",
    "Fendamira",
    "Fendanix",
    "Fendaol",
    "Fendasoxen",
    "Gravabedon",
    "Gravadex",
    "Gravataol",
    "Gravavex",
    "Hylodon",
    "Hyloen",
    "Hylogis",
    "Hyloin",
    "Hylotor",
    "Hylozeen",
    "Hylozen",
    "Ixendara",
    "Ixendivor",
    "Ixendutiva",
    "Ixengis",
    "Ixenin",
    "Ixenmidex",
    "Ixenvafen",
    "Ixenvifen",
    "Ixenvor",
    "Juvidara",
    "Juviin",
    "Juvinool",
    "Kesacoyl",
    "Kesaex",
    "Kesagis",
    "Kesalomox",
    "Kesamox",
    "Kesasogis",
    "Kesativa",
    "Kesavadex",
    "Kesavane",
    "Kesavidyn",
    "Kesaviyl",
    "Klargoex",
    "Klarlor",
    "Klarmitor",
    "Klarmox",
    "Klartiva",
    "Klarvavane",
    "Klarxadon",
    "Lumedara",
    "Lumein",
    "Lumevor",
    "Lumeyl",
    "Lyralopral",
    "Lyraplex",
    "Lyrasomox",
    "Lyravane",
    "Lyravex",
    "Lyrayl",
    "Mizamira",
    "Mizaquel",
    "Mizasen",
    "Mizatadex",
    "Mizator",
    "Mizavavia",
    "Morvaplex",
    "Morvavex",
    "Neuvobemox",
    "Neuvodyn",
    "Neuvonix",
    "Neuvovex",
    "Nexanovue",
    "Nexaplex",
    "Nexaric",
    "Nuvicor",
    "Nuvidex",
    "Nuvilocor",
    "Nuviridex",
    "Nuvitamira",
    "Nuvividyn",
    "Ombralydon",
    "Ombrapral",
    "Ombraric",
    "Ombravane",
    "Orbamox",
    "Orbaplex",
    "Orbapral",
    "Orbatagis",
    "Oxadara",
    "Oxadien",
    "Oxaravor",
    "Oxasovue",
    "Oxavue",
    "Praxabecor",
    "Praxayl",
    "Pyraen",
    "Pyraloquel",
    "Pyramira",
    "Pyraplex",
    "Pyraramox",
    "Pyrasosen",
    "Pyravia",
    "Quendara",
    "Quennomox",
    "Quenpraex",
    "Quentor",
    "Quenvia",
    "Quenzen",
    "Quiladon",
    "Quiladumira",
    "Quilamisen",
    "Quilativa",
    "Ravidyn",
    "Raviric",
    "Ravivex",
    "Revalydon",
    "Revapral",
    "Rexacocor",
    "Rexadon",
    "Rexaen",
    "Rexanacor",
    "Rexaplex",
    "Rovendex",
    "Rovendidex",
    "Roventiva",
    "Rovenvia",
    "Rovenzecor",
    "Solitapral",
    "Solixen",
    "Solizedyn",
    "Solvadex",
    "Solvadon",
    "Solvanaol",
    "Solvaol",
    "Solvavane",
    "Solvavisen",
    "Sonaen",
    "Sonaex",
    "Sonagoxen",
    "Sonaprafen",
    "Sonayl",
    "Tavodufen",
    "Tavopral",
    "Tavosonix",
    "Trovadex",
    "Trovamizen",
    "Trovariin",
    "Trovasyvia",
    "Uvelmox",
    "Uvelol",
    "Uvelsyvane",
    "Uvelvivex",
    "Uvelxen",
    "Uvelzen",
    "Valocor",
    "Valopral",
    "Valovia",
    "Valozevex",
    "Valozevia",
    "Vendadon",
    "Vendafen",
    "Vendavane",
    "Vendazen",
    "Vyraen",
    "Vyraex",
    "Vyragoplex",
    "Vyrapral",
    "Vyrasypral",
    "Vyrativa",
    "Wraxalydara",
    "Wraxanopral",
    "Wraxaquel",
    "Wraxavimox",
    "Wraxavue",
    "Xelydon",
    "Xelygis",
    "Xelyol",
    "Ynovanix",
    "Ynovapramira",
    "Ynovaquel",
    "Ynovasen",
    "Ynovasovex",
    "Ynovavane",
    "Zentacor",
    "Zentalygis",
    "Zentamira",
    "Zentanix",
    "Zentavor",
    "Zentavue",
    "Zevalomira",
    "Zevaritiva",
    "Zevasen",
    "Zevataquel",
    "Zevaxanix",
    "Zivadutiva",
    "Zivafen",
    "Zivalydara",
    "Zivalyvor",
    "Zivaol",
    "Zivavia",
    "Zolnodex",
    "Zolpraxen",
    "Zolraric",
    "Zolvia",
    "Zolyl",
)

# --------------------------------------------------------------------------------------
# The zh_CN path.
#
# zh_CN overrides brand_drug() to prepend an invented 2-3 character Chinese name, which
# is 30,752 more unscreened identifiers. The same fix applies — screen a set small enough
# to read, and ship that — with the same two-stage shape as the Latin side: mechanical
# screens, then a reading pass whose verdicts are recorded here. The difference from the
# Latin list is what the reading pass could not do, and the generated module says so
# rather than leaving the reader to assume parity between the two.
# --------------------------------------------------------------------------------------
ZH_REVIEW_STATUS = "read one by one in Simplified Chinese on 2026-08-16 against the criteria below"

# Characters that read as a GENERIC drug marker rather than as part of a brand name. This
# is the Chinese counterpart of BRAND_FORBIDDEN_ENDINGS, and it rejects a name for the
# same reason: a brand that reads as a substance or a drug class is not a brand. It bites
# harder here, because these are also the characters an invented Chinese brand reaches for.
ZH_GENERIC_MORPHEMES: dict[str, str] = {
    "素": "the Chinese ending for a substance class: 维生素, 抗生素, 激素, 胰岛素, 链霉素",
    "维": "reads as 维生素, 'vitamin'",
    "尔": "closes the Chinese transliteration of many INNs, the -洛尔 (-olol) class among them",
    "平": "closes the -地平 (-dipine) and -西平 stems: 氨氯地平, 卡马西平, 喹硫平",
    "定": "reads as a substance: 安定 is diazepam, 可乐定 is clonidine, 可定 is a marketed statin",
}

# APPEND-ONLY, same rule as REAL_PRODUCT_DENYLIST. Two-character names reachable from
# ZH_BRAND_CHARS that are real trademarks, company names, or ordinary Chinese words that
# would read as a real term rather than an invented brand.
ZH_REAL_PRODUCT_DENYLIST: tuple[str, ...] = (
    "诺华",  # Novartis
    "泰诺",  # Tylenol (CN)
    "可定",  # Crestor / rosuvastatin (CN)
    "安素",  # Ensure (Abbott)
    "华素",  # Huasu (chlorhexidine lozenge)
    "泰素",  # Taxol / paclitaxel (CN)
    "欣康",  # isosorbide mononitrate brand (CN)
    "诺和",  # Novo Nordisk product family (诺和灵, 诺和平, …)
    "施维",  # Servier (施维雅)
    "施乐",  # Xerox
    "施华",  # Swarovski (施华洛世奇)
    "诗华",  # Ceva Animal Health (CN)
    "康宁",  # Corning
    "泰康",  # Taikang Insurance
    "康泰",  # Kangtai Biological Products
    "安泰",  # Aetna (CN)
    "华泰",  # Huatai Insurance
    "平安",  # Ping An Insurance
    "华安",  # Huaan Insurance
    "安华",  # Anhua Agricultural Insurance
    "安达",  # Chubb (CN)
    "达安",  # Da An Gene
    "迪安",  # Dian Diagnostics
    "恩华",  # Nhwa Pharmaceutical
    "华瑞",  # Sino-Swed Pharmaceutical
    "瑞康",  # Reachall Pharmaceutical
    "博瑞",  # Bright Gene
    "瑞博",  # Ribo Life Science
    "尔康",  # Erkang Pharmaceutical
    "益达",  # Extra (Wrigley)
    "益力",  # Danone water brand
    "舒达",  # Serta
    "泰达",  # TEDA
    "清华",  # Tsinghua University
    "博通",  # Broadcom
    "华博",  # Huabo Biopharmaceutical
    "安诺",  # Annoroad Gene Technology
    "泰华",  # Taihua Group
    "瑞宁",  # 瑞宁得 / Arimidex (CN)
    "特瑞",  # 特瑞普利单抗 / toripalimab, an INN transliteration
    "泰乐",  # 泰乐菌素 / tylosin, an INN transliteration
    "舒乐",  # 舒乐安定 / estazolam (CN)
    "迪乐",  # marketed gastric-protectant name
    "通乐",  # drain-cleaner brand (管道通乐)
    "康欣",  # Kangxin, marketed name
    "华特",  # Walt (华特迪士尼); also Huate Gas
    "安通",  # Antong Holdings
    "康元",  # Kangyuan, marketed name
    "泰和",  # Taihe New Material; also Taihe County
    "泰瑞",  # Terry / Tairui, marketed name
    "瑞安",  # Shui On Land; also Rui'an City
    "舒尔",  # Shure
    "康力",  # Canny Elevator
    "瑞尔",  # Arrail Dental
    "安迪",  # "Andy", a common transliterated given name
    "泰宁",  # Taining County
    "安佳",  # Anchor (Fonterra dairy, CN)
    "康博",  # Kangbo apparel
    "瑞达",  # Ruida Futures
    "瑞恩",  # "Ryan", a common transliterated given name
    # Ordinary words and proper nouns. A name that is already a word does not read as an
    # invented brand, which is the whole point of generating one.
    "康复",  # "rehabilitation"
    "复元",  # "recuperate"
    "和平",  # "peace"
    "安宁",  # "tranquil"; also a marketed sedative name
    "平安",  # "safe and sound"
    "安康",  # "good health"
    "康乐",  # "health and happiness"
    "安乐",  # reads as 安乐死, "euthanasia" - unacceptable on a drug
    "清定",  # "calm and settled"
    "安平",  # Anping County
    "宁安",  # Ning'an City
    "平乐",  # Pingle County; also the 平乐 school of TCM orthopaedics
    "华清",  # Huaqing, a historic site
    # Read one by one in Simplified Chinese on 2026-08-16, when the shipped list was the
    # 64 names an even sample of the screen survivors produced. Fifty-eight of the 64 were
    # rejected: 16 by the ZH_GENERIC_MORPHEMES screen above, and these 42 individually,
    # each for the reason beside it. The pattern is worth keeping, because it is the
    # finding: the more a two-character name reads like a real Chinese drug brand, the
    # likelier it already is one. 康, 泰, 瑞, 舒, 益 and 欣 are recycled across so many
    # marketed products and company names that a plausible-sounding pair is a poor bet,
    # while an implausible pair is not a brand name at all — which is why the reviewed
    # list below is six names and not sixty.
    "乐佳",  # marketed health-and-nutrition brand element (乐佳善优)
    "乐欣",  # common pharmacy and clinic name; also an everyday given name
    "佳元",  # 元 as the second character reads as "yuan", a unit of currency
    "佳欣",  # one of the most common female given names
    "元力",  # 元力股份, a listed company
    "元泰",  # a real company name (元泰茶业 among others)
    "力华",  # homophone of 利华, as in 联合利华 (Unilever)
    "力泽",  # reads as a personal name
    "华可",  # 可 as the second character does not read as a Chinese brand
    "华益",  # used by real medical and pharmaceutical companies
    "博可",  # 可-final, as above
    "博清",  # reads as a personal name
    "可复",  # ordinary phrase, "recoverable"; one character from 康复 above
    "可益",  # ordinary phrase, "beneficial"
    "和复",  # reads as neither a word nor a brand
    "安元",  # 元-final, as above
    "安欣",  # homophone of 安心, "peace of mind"; also the lead of a 2023 national hit drama
    "康可",  # 可-final; 康 is the most recycled brand morpheme in the pool
    "康益",  # used by real pharmacies and pharmaceutical companies
    "恩乐",  # 乐-final: 泰乐, 舒乐, 迪乐, 通乐, 康乐, 安乐 and 平乐 are all already denied
    "施力",  # ordinary word, "to exert force"
    "施泽",  # ordinary phrase (施恩泽); also a personal name
    "欣元",  # 元-final
    "欣泽",  # reads as a personal name
    "泰舒",  # 泰 is the most trademark-saturated character here — nine 泰 names denied already
    "泽力",  # reads as a personal name or a firm
    "泽清",  # reads as a personal name
    "清可",  # 可-final
    "清益",  # reads as a therapeutic claim (清热益气), not as an invented name
    "特可",  # 可-final
    "特益",  # ordinary phrase, "especially beneficial"
    "瑞施",  # 瑞 has produced seven denied names; 施 is a company morpheme (施维雅, 施乐)
    "瑞通",  # reads as a company name
    "益宁",  # 益 reads as an efficacy claim, and 益达 / 益力 are already denied
    "舒康",  # both characters are saturated; reads as a marketed OTC name
    "诗达",  # reads as a transliterated foreign brand; 诗华 (Ceva) is already denied
    "诺恩",  # 诺 is the morpheme multinationals take in Chinese (诺华, 诺和); also a biotech name
    "诺通",  # 诺-initial, as above
    "达通",  # common company name
    "迪元",  # 元-final
    "通元",  # 元-final; also 通元针法, a named acupuncture technique
    "通欣",  # homophone of the first half of 通心络, a well-known marketed Chinese medicine
)

# The reviewed Chinese sample: what that pass left standing. Six names, and the smallness
# is the point — a short list somebody has actually read beats a long one nobody has.
#
# Each survivor is a pair that is not a word, not a name people are called, not a place,
# not recognisable as a company or a product, does not read as a substance, and still
# reads as a plausible invented pharmaceutical brand. What the review could NOT do is
# search a trademark register, so none of this establishes that a survivor is unregistered
# — see the generated module's docstring, which says so to the reader.
#
# To grow the list, run `--propose-zh N`, read the candidates against those criteria, and
# append the survivors here. Never append one nobody has read, and re-run the script.
REVIEWED_ZH_NAMES: tuple[str, ...] = (
    "复安",
    "宁舒",
    "恩欣",
    "达恩",
    "迪欣",
    "舒迪",
)


def catalogue_terms(locales: tuple[str, ...]) -> set[str]:
    """Every drug, disease, symptom and specialty string the given locales ship.

    Lower-cased. A generated brand that equals one of these is not an invented brand
    but a real substance name the package already ships, which is the failure the
    INN-stem screen only approximates.
    """
    terms: set[str] = set()
    modules = ["faker_healthcare.disease_correlations"]
    modules += [f"faker_healthcare.{locale}.disease_correlations" for locale in locales]
    for module_name in modules:
        correlations = importlib.import_module(module_name).DISEASE_CORRELATIONS
        for disease, data in correlations.items():
            terms.add(disease.lower())
            terms.add(data["medical_specialty"].lower())
            terms.update(term.lower() for term in data["symptoms"])
            terms.update(term.lower() for term in data["medications"])
    return terms


def screen_latin(name: str, catalogue: set[str]) -> list[str]:
    """Return the reasons `name` must not ship, or an empty list if it may.

    Every reason is stated separately so `--propose` can explain a rejection, and so a
    future screen is added here rather than to one caller.
    """
    reasons: list[str] = []
    lowered = name.lower()
    if not NAME_PATTERN.fullmatch(name):
        reasons.append("does not match the brand-name pattern")
    if lowered.endswith(tuple(BRAND_FORBIDDEN_ENDINGS)):
        reasons.append("ends in a WHO INN class stem")
    if lowered in {denied.lower() for denied in REAL_PRODUCT_DENYLIST}:
        reasons.append("listed in REAL_PRODUCT_DENYLIST")
    hits = [term for term in OFFENSIVE_SUBSTRINGS if term in lowered]
    if hits:
        reasons.append(f"contains an offensive substring: {', '.join(hits)}")
    if lowered in catalogue:
        reasons.append("collides with a term in the shipped catalogue")
    return reasons


def screen_zh(name: str, catalogue: set[str]) -> list[str]:
    """Return the reasons a Chinese brand name must not ship.

    The catalogue check is a *substring* test in both directions, unlike the Latin one:
    a two-character name that appears inside a shipped Chinese medical term is a real
    term's fragment rather than an invented name, and a name that contains one is worse.
    """
    reasons: list[str] = []
    if len(set(name)) != len(name):
        reasons.append("repeats a character")
    generic = [f"{char} — {reason}" for char, reason in ZH_GENERIC_MORPHEMES.items() if char in name]
    if generic:
        reasons.append(f"contains a generic-drug morpheme: {'; '.join(generic)}")
    hits = [denied for denied in ZH_REAL_PRODUCT_DENYLIST if denied in name]
    if hits:
        reasons.append(f"listed in ZH_REAL_PRODUCT_DENYLIST: {', '.join(hits)}")
    if any(name in term for term in catalogue):
        reasons.append("appears inside a term in the shipped catalogue")
    return reasons


def latin_space() -> list[str]:
    """Every name the morpheme pools can produce, sorted. No randomness."""
    names = set()
    for prefix in BRAND_PREFIXES:
        for suffix in BRAND_SUFFIXES:
            names.add(prefix + suffix)
            for infix in BRAND_INFIXES:
                names.add(prefix + infix + suffix)
    return sorted(names)


def zh_space() -> list[str]:
    """Every two-character Chinese name the pool can produce, sorted.

    The runtime generator also produced three-character names; two characters is the
    shape Chinese pharmaceutical brands overwhelmingly take, and restricting to it drops
    the space from 30,752 to 992 before any screen runs, which is the difference between
    a set a reviewer can read and one they cannot.
    """
    return sorted(first + second for first in ZH_BRAND_CHARS for second in ZH_BRAND_CHARS if first != second)


def group_key(name: str) -> str:
    """The morpheme a name is grouped under when sampling, so no group dominates.

    The longest matching prefix, because `Zol` is also the start of names that begin
    with the longer `Zolva`-style prefixes and would otherwise swallow their group.
    """
    matches = [prefix for prefix in BRAND_PREFIXES if name.startswith(prefix)]
    return max(matches, key=len) if matches else name[:1]


def even_sample(candidates: list[str], target: int, key=group_key) -> list[str]:
    """Take `target` names spread evenly over the groups `key` puts them in.

    Deterministic: the same candidates and target always give the same names, in sorted
    order, with no RNG anywhere. Groups are filled to an equal quota, the remainder goes
    to the earliest groups by name, and within a group the picks are strided across the
    sorted members rather than taken from the front.

    The stride also starts one step further into each successive group. Without that
    rotation every group picks its members at the same sorted positions, and since the
    members of every group are the same endings in the same order, the sample comes back
    as one ending repeated N times - which is how the first zh_CN draft ended up with
    two thirds of its names sharing a second character.
    """
    groups: dict[str, list[str]] = {}
    for name in sorted(candidates):
        groups.setdefault(key(name), []).append(name)

    ordered_keys = sorted(groups)
    if not ordered_keys:
        return []
    quota, remainder = divmod(target, len(ordered_keys))

    picked: list[str] = []
    for index, group in enumerate(ordered_keys):
        members = groups[group]
        want = min(quota + (1 if index < remainder else 0), len(members))
        if want <= 0:
            continue
        size = len(members)
        picked.extend(members[(index + position * size // want) % size] for position in range(want))
    return sorted(picked)


def _render(module_doc: str, constant: str, annotation: str, names: list[str]) -> str:
    """Render a generated module. Formatted the way `ruff format` leaves it."""
    body = "".join(f'    "{name}",\n' for name in names)
    return f'"""{module_doc}"""\n\n{constant}: {annotation} = (\n{body})\n'


def build_latin() -> list[str]:
    """The shipped Latin names: the reviewed sample, minus anything a screen rejects."""
    catalogue = catalogue_terms(LOCALES)
    space = set(latin_space())
    shipped: list[str] = []
    for name in REVIEWED_LATIN_NAMES:
        if name not in space:
            print(f"dropping {name}: not reachable from the morpheme pools", file=sys.stderr)
            continue
        reasons = screen_latin(name, catalogue)
        if reasons:
            print(f"dropping {name}: {'; '.join(reasons)}", file=sys.stderr)
            continue
        shipped.append(name)
    return sorted(set(shipped))


def build_zh() -> list[str]:
    """The shipped Chinese names: the reviewed sample, minus anything a screen rejects.

    Built the same way as the Latin list, and deliberately so: an even sample of the
    screen survivors is what produced the 64-name list that a Simplified-Chinese reading
    pass then rejected 58 of. A machine can say a name is denied; only a reader can say it
    is somebody's product, an ordinary word, or a person's name.
    """
    catalogue = catalogue_terms(("zh_CN",))
    space = set(zh_space())
    shipped: list[str] = []
    for name in REVIEWED_ZH_NAMES:
        if name not in space:
            print(f"dropping {name}: not reachable from ZH_BRAND_CHARS", file=sys.stderr)
            continue
        reasons = screen_zh(name, catalogue)
        if reasons:
            print(f"dropping {name}: {'; '.join(reasons)}", file=sys.stderr)
            continue
        shipped.append(name)
    return sorted(set(shipped))


def unreviewed_survivors() -> list[str]:
    """Latin names that pass every screen and are not already reviewed."""
    catalogue = catalogue_terms(LOCALES)
    reviewed = set(REVIEWED_LATIN_NAMES)
    return [name for name in latin_space() if name not in reviewed and not screen_latin(name, catalogue)]


def unreviewed_zh_survivors() -> list[str]:
    """Chinese names that pass every screen and are not already reviewed."""
    catalogue = catalogue_terms(("zh_CN",))
    reviewed = set(REVIEWED_ZH_NAMES)
    return [name for name in zh_space() if name not in reviewed and not screen_zh(name, catalogue)]


def render_latin(names: list[str]) -> str:
    return _render(
        "Screened fictitious brand names for ``brand_drug()``.\n\n"
        "GENERATED FILE - do not edit by hand. Regenerate with::\n\n"
        "    python scripts/generate_brand_names.py\n\n"
        "Every name here was produced by the morpheme pools in ``constants.py``, passed the\n"
        "screens in that script (WHO INN class stems, the real-product denylist, offensive\n"
        "substrings, and collision with the shipped generic-drug catalogue), and was then\n"
        "read by a human. They are invented names, screened against a documented corpus at a\n"
        "point in time - not the result of a trademark search. If one of them collides with a\n"
        "real product, please open an issue: it will be added to REAL_PRODUCT_DENYLIST, which\n"
        "is append-only.\n",
        "BRAND_DRUG_NAMES",
        "tuple[str, ...]",
        names,
    )


def render_zh(names: list[str]) -> str:
    return _render(
        "Screened fictitious Chinese brand names for the zh_CN ``brand_drug()``.\n\n"
        "GENERATED FILE - do not edit by hand. Regenerate with::\n\n"
        "    python scripts/generate_brand_names.py\n\n"
        "These are two-character combinations of the pharmaceutical characters in\n"
        "``ZH_BRAND_CHARS``, screened against a denylist of real trademarks, company names,\n"
        "ordinary words and personal names; against the characters that read as a generic\n"
        "drug rather than as a brand (``ZH_GENERIC_MORPHEMES``); and against every Chinese\n"
        "term this package ships.\n\n"
        "**Review status.** Every candidate was\n"
        f"{ZH_REVIEW_STATUS}: does the pair\n"
        "name a real company or product, does it read as an ordinary word, a personal name\n"
        "or a place, does it read as a substance rather than a brand, and does it read as a\n"
        "plausible invented brand at all. That pass rejected 58 of the 64 names this module\n"
        "used to ship; each rejection is recorded, with its reason, in the screens in\n"
        "``scripts/generate_brand_names.py``. Six survived, and the list is short because\n"
        "the review was strict, not because the space is.\n\n"
        "What that pass was NOT: a trademark search - no register was consulted, and none\n"
        "of these names is claimed to be unregistered - and not a fluent native speaker's\n"
        "sign-off, which this repository has not received and does not claim. Chinese\n"
        "pharmaceutical brands recycle these characters so heavily that a collision is\n"
        "likelier here than in the Latin catalogue. Reports of one are welcome and land in\n"
        "ZH_REAL_PRODUCT_DENYLIST, which is append-only.\n",
        "ZH_BRAND_NAMES",
        "tuple[str, ...]",
        names,
    )


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--check", action="store_true", help="fail if the generated modules are out of date")
    parser.add_argument("--propose", type=int, metavar="N", help="print N unreviewed Latin survivors for human review")
    parser.add_argument("--propose-zh", type=int, metavar="N", help="print N unreviewed Chinese survivors for human review")
    args = parser.parse_args(argv)

    if args.propose is not None:
        for name in even_sample(unreviewed_survivors(), args.propose):
            print(name)
        return 0

    if args.propose_zh is not None:
        for name in even_sample(unreviewed_zh_survivors(), args.propose_zh, key=lambda name: name[0]):
            print(name)
        return 0

    latin, chinese = build_latin(), build_zh()
    outputs = {LATIN_TARGET: (render_latin(latin), len(latin)), ZH_TARGET: (render_zh(chinese), len(chinese))}

    stale = [path for path, (content, _) in outputs.items() if not path.exists() or path.read_text(encoding="utf-8") != content]
    if args.check:
        for path in stale:
            print(f"out of date: {path.relative_to(REPO_ROOT)}", file=sys.stderr)
        if stale:
            print("run: python scripts/generate_brand_names.py", file=sys.stderr)
        return 1 if stale else 0

    for path, (content, count) in outputs.items():
        path.write_text(content, encoding="utf-8")
        print(f"wrote {path.relative_to(REPO_ROOT)} ({count} names)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
