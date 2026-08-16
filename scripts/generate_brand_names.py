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

# How many Chinese names to ship. Deliberately small: unlike the Latin list, this one
# has had no fluent-speaker review (see ZH_REVIEW_STATUS below), so the set is kept
# short enough for one reviewer to read in a sitting.
ZH_TARGET_SIZE = 64

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
# is 30,752 more unscreened identifiers. The same fix applies — ship a static list — but
# with one honest difference from the Latin list, recorded here and in the generated
# module so nobody mistakes one for the other.
# --------------------------------------------------------------------------------------
ZH_REVIEW_STATUS = "automated screens only; NOT reviewed by a fluent Chinese speaker"

# APPEND-ONLY, same rule as REAL_PRODUCT_DENYLIST. Two-character names reachable from
# ZH_BRAND_CHARS that are real trademarks, company names, or ordinary Chinese words that
# would read as a real term rather than an invented brand. Compiled by inspection, which
# is exactly why ZH_REVIEW_STATUS says what it says: this list is certainly incomplete,
# and a fluent reviewer should expect to add to it.
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
    """The shipped Chinese names: an even sample of what the screens leave standing."""
    catalogue = catalogue_terms(("zh_CN",))
    survivors = [name for name in zh_space() if not screen_zh(name, catalogue)]
    return even_sample(survivors, ZH_TARGET_SIZE, key=lambda name: name[0])


def unreviewed_survivors() -> list[str]:
    """Latin names that pass every screen and are not already reviewed."""
    catalogue = catalogue_terms(LOCALES)
    reviewed = set(REVIEWED_LATIN_NAMES)
    return [name for name in latin_space() if name not in reviewed and not screen_latin(name, catalogue)]


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
        "TODO(review): these names have had "
        f"{ZH_REVIEW_STATUS}.\n"
        "They are two-character combinations of the generic pharmaceutical characters in\n"
        "``ZH_BRAND_CHARS``, filtered against a denylist of real trademarks and ordinary\n"
        "words compiled by inspection, and against every Chinese term this package ships.\n"
        "That denylist is certainly incomplete. Shipping this list rather than generating\n"
        "30,752 combinations at runtime is what makes a fluent reviewer's pass possible at\n"
        "all - it is not a substitute for one. Corrections are welcome and land in\n"
        "ZH_REAL_PRODUCT_DENYLIST, which is append-only.\n",
        "ZH_BRAND_NAMES",
        "tuple[str, ...]",
        names,
    )


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--check", action="store_true", help="fail if the generated modules are out of date")
    parser.add_argument("--propose", type=int, metavar="N", help="print N unreviewed survivors for human review")
    args = parser.parse_args(argv)

    if args.propose is not None:
        for name in even_sample(unreviewed_survivors(), args.propose):
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
