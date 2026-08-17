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
# zh_CN's brand_drug() used to prepend an invented 2-3 character Chinese name built at call
# time, which was 30,752 more unscreened identifiers. The same fix applies — screen a set small enough
# to read, and ship that — with the same two-stage shape as the Latin side: mechanical
# screens, then a reading pass whose verdicts are recorded here. The difference from the
# Latin list is what the reading pass could not do, and the generated module says so
# rather than leaving the reader to assume parity between the two.
# --------------------------------------------------------------------------------------
ZH_REVIEW_STATUS = "read one by one in Simplified Chinese on 2026-08-16 and again on 2026-08-17"

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

# APPEND-ONLY, same rule as REAL_PRODUCT_DENYLIST. Every two-character name reachable from
# ZH_BRAND_CHARS that a reading pass has rejected, whatever the reason it was rejected for:
# a real trademark or company, a place, a name people are called, an ordinary word, an
# efficacy claim, or a pair that simply does not read as an invented brand. The reason is
# beside the entry, because the reasons are what a later reviewer needs; the entry itself
# only has to keep the name out.
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
    # Read one by one in Simplified Chinese on 2026-08-17, after the pool above was widened
    # by eleven characters, because six shipped names is too thin to generate Chinese test
    # data with: the same six Chinese halves repeat for every draw. 370 candidates were read
    # this round — the 300 an even sample over first characters produces, plus every pair
    # among the ten characters that survive in practice (复安宁舒恩欣迪达润灵). Twenty
    # survived. The 337 that did not are below, each with its reason, and the shape of the
    # rejections is the finding:
    #
    #   * The pool splits in two. 复/安/宁/舒/恩/欣/迪/达 and the new 润/灵 are CLINICAL
    #     morphemes and make names that read as medicines. 康/泰/瑞/华/乐/佳/元/力/博/诗/施/
    #     诺/通/清/和/可/益 and the new 悦/怡/明/朗/恒/顺/畅/静/健 are auspicious or corporate
    #     morphemes, and they make company names, given names, places and efficacy claims
    #     almost without exception. Nine of the eleven new characters yielded nothing. They
    #     stay in the pool with their rejections recorded, so the next reviewer inherits the
    #     evidence instead of re-running the experiment.
    #   * Position matters as much as the character. 灵 is the suffix of 感冒灵 in second
    #     position and of 亡灵 in first; 复 heads compound preparations (复方) and reads as
    #     "do it again" when it trails; 安 trails the drug names everyone knows (胃复安) and
    #     reads as a safety claim anywhere else.
    #   * Reading the characters is not enough. 泰佳 is a homophone of 泰嘉 (a marketed
    #     clopidogrel), 力宁 of 利宁 (a marketed lidocaine), 欣舒 of 心舒, 力朗 of 利郎 and
    #     达灵 of 达令 ("darling").
    #
    # One name that was already shipping was withdrawn this round: 复安 is the tail of 胃复安,
    # the household name for metoclopramide in China, which the first pass missed. That is
    # what the append-only rule is for — the denylist grew and the withdrawal is recorded,
    # rather than a shipped name quietly changing meaning.
    # 乐
    "乐健",  # reads as a wellness slogan (乐享健康); used by real health-and-fitness businesses
    "乐博",  # 乐博乐博, a national children's robotics-education brand
    "乐宁",  # 乐宁教育, a Shanghai English-school chain
    "乐恩",  # reads as a transliterated given name (Leon)
    "乐朗",  # reads as a given name
    "乐清",  # 乐清市, a city in Zhejiang
    "乐益",  # 益 reads as an efficacy claim
    "乐达",  # generic company-name reading
    # 佳
    "佳健",  # reads as a health claim, not a name
    "佳可",  # 可-final does not read as a Chinese brand
    "佳安",  # transposition of the denied 安佳 (Anchor); also reads as a safety claim
    "佳悦",  # 佳悦酒店, a hotel brand; also a common given name
    "佳泰",  # common company name
    "佳灵",  # common female given name
    "佳舒",  # 佳 reads as a quality claim in first position, so the pair is a slogan
    "佳迪",  # reads as a transliterated foreign name
    # 健
    "健元",  # 健康元 (Joincare), a listed pharmaceutical group
    "健可",  # 可-final
    "健康",  # the ordinary word 'health'
    "健悦",  # reads as a gym or wellness brand
    "健泰",  # common company name
    "健特",  # 健特药业 (无锡健特), a real pharmaceutical company
    "健舒",  # 健 heads TCM function terms (健脾/健胃), so the pair reads as a claim
    "健通",  # 健-initial claim reading, and 通 is a function verb too
    # 元
    "元华",  # 元华, a well-known Hong Kong actor
    "元复",  # reversal of the denied 复元 ('recuperate'); reads as neither word nor brand
    "元怡",  # reads as a personal name
    "元明",  # 元明粉 is a real substance (mirabilite)
    "元润",  # reads as a personal name or an investment firm
    "元瑞",  # company-name reading
    "元诺",  # 诺 is the morpheme multinationals take in Chinese
    "元静",  # reads as a female given name
    # 力
    "力博",  # reads as an industrial company name
    "力宁",  # homophone of 利宁, a marketed lidocaine brand
    "力恒",  # generic company-name reading
    "力朗",  # homophone of 利郎, a well-known menswear brand
    "力清",  # reads as a personal name
    "力畅",  # reads as a functional claim
    "力达",  # extremely common company name
    "力顺",  # generic company-name reading
    # 华
    "华佳",  # 华 heads a dozen denied company names; reads as one more
    "华和",  # company-name reading
    "华康",  # 华康字体 (DynaFont) and 华康 pharmacies
    "华悦",  # hotel and real-estate brand
    "华朗",  # company-name reading
    "华灵",  # company or personal-name reading
    "华诺",  # 华诺生物; 诺 is the multinationals' morpheme
    "华通",  # 华通线缆, a listed company
    # 博
    "博佳",  # 博 reads as 博士/广博, a corporate morpheme
    "博和",  # 博和汉商, a law firm
    "博康",  # 博康医药
    "博悦",  # gaming and hotel brand
    "博欣",  # company-name reading
    "博灵",  # reads as neither a word nor a brand
    "博舒",  # 博 is a corporate morpheme, not a pharmaceutical one
    "博迪",  # reads as a transliteration (Bodhi/Body)
    # 可
    "可元",  # 可-initial reads as an imported product; 元-final reads as the currency unit
    "可宁",  # 可 opens transliterated imports (可定, 可乐定)
    "可恒",  # 可 opens transliterated imports
    "可明",  # 可 opens transliterated imports; also a personal name
    "可泽",  # 可 opens transliterated imports; 泽 is a given-name character
    "可瑞",  # 可瑞达 is pembrolizumab (Keytruda) in China
    "可诺",  # 可 opens transliterated imports; 诺 is the multinationals' morpheme
    "可静",  # reads as a female given name
    # 和
    "和元",  # 和元生物, a listed CDMO
    "和宁",  # ordinary word; also a historic era name
    "和恒",  # company-name reading
    "和朗",  # reads as neither a word nor a brand
    "和润",  # 光明和润, a marketed yoghurt line
    "和畅",  # 惠风和畅, a line from 兰亭集序
    "和诺",  # 诺 is the multinationals' morpheme
    "和顺",  # ordinary word; also 和顺县, Shanxi
    # 复
    "复安",  # the tail of 胃复安, the household name for metoclopramide in China
    "复乐",  # fragment of 拜复乐 (moxifloxacin, Avelox in China)
    "复华",  # 复华集团
    "复康",  # reversal of the denied 康复 ('rehabilitation')
    "复悦",  # 悦 reads as a hospitality/wellness morpheme, not a pharmaceutical one
    "复益",  # 益 reads as an efficacy claim
    "复达",  # fragment of 复达欣 (ceftazidime, Fortum in China)
    "复润",  # reads as a cosmetic claim ('restore moisture')
    # 宁
    "宁佳",  # 佳-final reads as a given name
    "宁华",  # company-name reading
    "宁康",  # reads as a pharmacy name
    "宁悦",  # 悦 reads as a hospitality/wellness morpheme
    "宁欣",  # common female given name
    "宁灵",  # with 宁 = 'to pacify', 灵 reads as 亡灵 — a funerary reading
    "宁益",  # reversal of the denied 益宁; 益 reads as an efficacy claim
    "宁复",  # reads as the classical 宁复…, not as a brand
    "宁润",  # reads as a 润肺宁咳 claim
    # 安
    "安力",  # company-name reading
    "安和",  # ordinary phrase; also 安和路 in Taipei and the song 安和桥
    "安恒",  # 安恒信息, a listed cybersecurity company
    "安明",  # reads as a personal name
    "安特",  # fragment of 安特尔 (testosterone undecanoate, Andriol)
    "安益",  # 益 reads as an efficacy claim
    "安静",  # the ordinary word 'quiet'
    "安复",  # 复-final reads as 'do it again', not as a brand
    "安舒",  # reads as a comfort-and-safety claim
    "安恩",  # reads as a transliterated Western given name (安恩和奶牛)
    "安灵",  # funerary reading — 安灵 is laying a spirit to rest
    # 康
    "康健",  # ordinary word ('in good health')
    "康怡",  # 康怡 is a Hong Kong district and a pharmacy name
    "康悦",  # 人保康悦, a medical-insurance product line
    "康泽",  # 康泽药业, a pharmacy chain
    "康灵",  # 康 + 灵 is the canonical OTC-name shape on the most saturated character here
    "康畅",  # reads as a laxative claim
    "康达",  # 康达律师事务所 and 康达医疗
    "康静",  # reads as a personal name
    # 怡
    "怡元",  # 元-final reads as the currency unit
    "怡和",  # 怡和集团 (Jardine Matheson)
    "怡恒",  # company-name reading
    "怡明",  # reads as a personal name
    "怡润",  # reads as a cosmetic or dairy name
    "怡瑞",  # company-name reading
    "怡诺",  # fragment of 怡诺思 (venlafaxine, Effexor in China)
    "怡顺",  # company-name reading
    # 恒
    "恒乐",  # company-name reading
    "恒力",  # 恒力集团, a Fortune Global 500 group
    "恒复",  # reads as neither a word nor a brand
    "恒恩",  # reads as a personal or devotional name
    "恒朗",  # company-name reading
    "恒清",  # reads as a personal name
    "恒畅",  # reads as a claim ('constantly unobstructed')
    "恒达",  # a very common company name
    # 恩
    "恩元",  # 元-final reads as the currency unit
    "恩和",  # 恩和, a well-known town in Inner Mongolia
    "恩康",  # pharmacy-name reading
    "恩明",  # reads as a personal name
    "恩瑞",  # company-name reading
    "恩诗",  # 诗 is a transliteration morpheme; the pair reads foreign
    "恩静",  # a common Korean given name
    "恩复",  # 复-final reads as 'do it again'
    "恩安",  # reads as a personal name
    "恩宁",  # 恩宁路, a well-known historic street in Guangzhou
    "恩迪",  # near-homophone of the denied 安迪 ('Andy')
    "恩达",  # reads as a transliterated name; also a common trading-company name
    "恩灵",  # Christian vocabulary (恩典 + 圣灵)
    # 悦
    "悦健",  # gym and wellness reading
    "悦博",  # 悦博体育
    "悦安",  # ordinary phrase
    "悦施",  # 施 opens transliterated foreign companies
    "悦泰",  # common company name
    "悦特",  # transliteration fragment
    "悦舒",  # comfort claim used by personal-care products
    "悦通",  # company-name reading
    # 施
    "施佳",  # 施 opens transliterated foreign companies (施贵宝, 施维雅)
    "施可",  # 可-final; 施 reads as a foreign company's initial
    "施安",  # 施 reads as a foreign company's initial
    "施恩",  # 施恩, an infant-formula brand; also the ordinary phrase 'bestow a kindness'
    "施泰",  # 施 reads as a foreign company's initial
    "施特",  # reads as a transliterated surname (施特劳斯)
    "施舒",  # 施 reads as a foreign company's initial
    "施迪",  # 施 reads as a foreign company's initial
    # 明
    "明力",  # company-name reading
    "明和",  # 明和産業, a Japanese company
    "明怡",  # reads as a personal name
    "明朗",  # the ordinary word 'bright'
    "明润",  # descriptive pair used for jade and cosmetics
    "明畅",  # the ordinary word for lucid prose
    "明诺",  # 明诺生物; 诺 is the multinationals' morpheme
    "明顺",  # company-name reading
    # 朗
    "朗乐",  # company-name reading
    "朗华",  # 朗华供应链
    "朗复",  # reads as neither a word nor a brand
    "朗恒",  # company-name reading
    "朗欣",  # 朗欣科技
    "朗清",  # water-purifier brand and personal-name reading
    "朗益",  # 益 reads as an efficacy claim
    "朗达",  # 朗达锂电
    # 欣
    "欣力",  # company-name reading
    "欣和",  # 欣和食品 (Shinho), a major condiment maker
    "欣怡",  # one of the most common female given names
    "欣施",  # 施 reads as a foreign company's initial
    "欣清",  # reads as a personal name
    "欣畅",  # the ordinary word 欢畅/欣畅
    "欣诺",  # 诺 is the multinationals' morpheme
    "欣静",  # reads as a female given name
    "欣复",  # 复-final; also homophone of 心腹
    "欣安",  # homophone of 心安, 'at ease'
    "欣宁",  # homophone of 心宁, which reads as a cardiac claim
    "欣舒",  # homophone of 心舒; 心舒宝片 is a marketed cardiac TCM
    "欣恩",  # reads as a given name
    "欣润",  # reads as a cosmetic claim
    "欣灵",  # 欣灵电气, a listed manufacturer
    # 泰
    "泰佳",  # homophone of 泰嘉, the marketed clopidogrel brand
    "泰力",  # common company name
    "泰安",  # 泰安市, Shandong
    "泰恩",  # near-homophone of 泰能 (imipenem, Tienam)
    "泰朗",  # reads as a transliterated name
    "泰润",  # company-name reading
    "泰畅",  # company and claim reading
    "泰迪",  # 'Teddy' — the bear and the dog breed
    # 泽
    "泽乐",  # 泽 is a given-name character
    "泽华",  # reads as a male given name
    "泽复",  # reads as neither a word nor a brand
    "泽恒",  # reads as a male given name
    "泽明",  # reads as a male given name
    "泽灵",  # reads as a personal name
    "泽益",  # 益 reads as an efficacy claim
    "泽达",  # 泽达易盛, a listed company
    # 润
    "润力",  # company-name reading
    "润复",  # 复-final reads as 'do it again'
    "润怡",  # reads as a cosmetic name
    "润明",  # 润眼明目 claim; also a personal name
    "润清",  # water-purifier brand
    "润畅",  # 润肠通便 claim
    "润达",  # 润达医疗, a listed IVD company
    "润顺",  # company-name reading
    "润安",  # reads as a claim
    "润宁",  # reads as a 润肺宁咳 claim
    "润舒",  # 润舒滴眼液 is a marketed chloramphenicol eye drop
    "润恩",  # reads as a personal name
    "润欣",  # 润欣科技, a listed company
    "润迪",  # company-name reading
    "润灵",  # reads as a TCM or cosmetic claim
    # 清
    "清健",  # 清 heads TCM function terms (清热健脾)
    "清复",  # reads as neither a word nor a brand
    "清怡",  # reads as a personal name
    "清施",  # 施 reads as a foreign company's initial
    "清泰",  # 清泰街, a Hangzhou thoroughfare
    "清瑞",  # company-name reading
    "清诺",  # 诺 is the multinationals' morpheme
    "清静",  # the ordinary word 'serene'
    # 灵
    "灵佳",  # 灵-initial reads as 灵魂, not as the OTC suffix of 感冒灵
    "灵博",  # 灵-initial reads as 灵魂
    "灵安",  # funerary reading (安灵)
    "灵恩",  # 灵恩派, the Charismatic movement
    "灵欣",  # reads as a female given name
    "灵特",  # transliteration fragment
    "灵舒",  # 灵-initial reads as 灵魂
    "灵通",  # the ordinary word 消息灵通; also 小灵通
    "灵宁",  # funerary reading
    "灵迪",  # 灵-initial reads as 灵魂
    "灵达",  # 灵-initial; also a common company name
    "灵复",  # 灵-initial; 复-final
    "灵润",  # 灵-initial; reads as a cosmetic claim
    # 特
    "特佳",  # reads as 特效 + a quality claim
    "特华",  # 特华投资
    "特宁",  # 特 reads as 特效药, a claim
    "特恒",  # company-name reading
    "特朗",  # 特朗普 — Trump
    "特润",  # 特润修护, a cosmetics line
    "特诗",  # transliteration fragment
    "特通",  # reads as neither a word nor a brand
    # 瑞
    "瑞健",  # 瑞健医疗
    "瑞可",  # 可-final
    "瑞怡",  # reads as a personal name
    "瑞朗",  # company-name reading
    "瑞泽",  # 泽 is a given-name character
    "瑞特",  # 瑞特血糖仪, a marketed glucometer
    "瑞诗",  # transliteration reading
    "瑞顺",  # company-name reading
    # 畅
    "畅乐",  # 畅 is a function word, so 畅X reads as a claim
    "畅力",  # reads as a claim
    "畅复",  # reads as neither a word nor a brand
    "畅恒",  # company-name reading
    "畅明",  # reads as a claim or a personal name
    "畅润",  # reads as a claim
    "畅益",  # 益 reads as an efficacy claim
    "畅达",  # the ordinary word 'unimpeded'
    # 益
    "益元",  # 益元散, a classical TCM formula
    "益和",  # 益 reads as an efficacy claim
    "益恒",  # company-name reading
    "益明",  # 益气明目 claim
    "益泽",  # 泽 is a given-name character
    "益特",  # 益 reads as an efficacy claim
    "益诺",  # 诺 is the multinationals' morpheme
    "益顺",  # company-name reading
    # 舒
    "舒健",  # reads as a health claim
    "舒博",  # 博 is a corporate morpheme
    "舒宁",  # reads like a marketed sedative or hygiene name — not confident enough to ship
    "舒朗",  # 舒朗服饰, a women's-wear brand; also an ordinary adjective
    "舒润",  # transposition of 润舒, a marketed eye drop; also a marketing claim
    "舒瑞",  # company-name reading
    "舒通",  # claim reading, adjacent to the denied 通乐
    "舒复",  # 复-final reads as 'do it again'
    "舒安",  # reads as a comfort-and-safety claim
    "舒欣",  # reads as a personal name (舒 is a surname, 欣 a given name)
    # 诗
    "诗乐",  # 诗 is a transliteration morpheme (诗华 = Ceva)
    "诗力",  # 诗 is a transliteration morpheme
    "诗宁",  # 诗 is a transliteration morpheme
    "诗恒",  # reads as a personal name
    "诗明",  # reads as a personal name
    "诗润",  # reads as a cosmetic name
    "诗瑞",  # transliteration reading
    "诗迪",  # transliteration reading
    # 诺
    "诺元",  # 诺 is the multinationals' morpheme; 元-final reads as the currency unit
    "诺复",  # 诺 is the multinationals' morpheme
    "诺怡",  # 诺 is the multinationals' morpheme
    "诺明",  # reads as a personal name
    "诺泽",  # 泽 is a given-name character
    "诺特",  # transliteration reading
    "诺舒",  # 诺 is the multinationals' morpheme
    "诺顺",  # company-name reading
    # 达
    "达元",  # 元-final reads as the currency unit
    "达可",  # 可-final; also the head of 达可替尼 (dacomitinib)
    "达康",  # 李达康, a household-name television character
    "达明",  # 达明一派, a famous Hong Kong band
    "达泽",  # 泽 is a given-name character
    "达特",  # 'Dart'; transliteration fragment
    "达舒",  # fragment of 斯达舒, a very well-known OTC stomach medicine
    "达顺",  # company-name reading
    "达复",  # 复-final reads as 'do it again'
    "达宁",  # may collide with a marketed analgesic — not confident enough to ship
    "达欣",  # fragment of 复达欣 (ceftazidime, Fortum)
    "达迪",  # reads as the English 'daddy'
    "达润",  # transposition of 润达医疗, a listed company
    "达灵",  # near-homophone of 达令, 'darling'
    # 迪
    "迪健",  # reads as a fitness brand
    "迪可",  # 可-final
    "迪怡",  # reads as a cosmetic or personal name
    "迪明",  # reads as a personal name
    "迪畅",  # reads as a claim
    "迪达",  # 阿迪达斯 (Adidas) contains 迪达
    "迪复",  # 复-final reads as 'do it again'
    "迪恩",  # 'Dean', a common transliterated name
    # 通
    "通健",  # 通 and 健 are both function verbs, so the pair reads as a claim
    "通可",  # 可-final
    "通康",  # reads as a pharmacy name
    "通施",  # 施 reads as a foreign company's initial
    "通润",  # 润肠通便 claim
    "通畅",  # the ordinary word 'unobstructed'
    "通达",  # ordinary word; also 通达系, the express-delivery group
    # 静
    "静力",  # 静力学, a physics term
    "静复",  # reads as neither a word nor a brand
    "静恒",  # reads as a personal name
    "静欣",  # reads as a female given name
    "静灵",  # 静灵口服液, a marketed children's TCM
    "静舒",  # reads as a female given name
    "静顺",  # reads as neither a word nor a brand
    # 顺
    "顺乐",  # 顺-initial reads as a logistics brand (顺丰)
    "顺华",  # company-name reading
    "顺宁",  # 顺宁, the former name of 凤庆县, Yunnan
    "顺恩",  # reads as a personal name
    "顺泰",  # common company name
    "顺特",  # 顺特电气
    "顺诗",  # 诗 is a transliteration morpheme
)

# The reviewed Chinese sample: what those passes left standing. Six names came out of the
# 64 candidates the 2026-08-16 pass read, one of which (复安) was withdrawn on 2026-08-17;
# twenty more came out of the 370 candidates the 2026-08-17 pass read.
#
# Each survivor is a pair that is not a word, not a name people are called, not a place,
# not recognisable as a company or a product, does not read as a substance, and still
# reads as a plausible invented pharmaceutical brand. What the review could NOT do is
# search a trademark register, so none of this establishes that a survivor is unregistered
# — see the generated module's docstring, which says so to the reader.
#
# Twenty-five is short of what a Chinese-language user would want, and it is where honest
# screening landed rather than a target: the second pass read 370 candidates to add twenty,
# a 5% survival rate, because the region of the space that reads like a Chinese drug brand
# is the region real manufacturers have already occupied. Growing this list further needs
# more CLINICAL characters in ZH_BRAND_CHARS (see the denylist header) or a reviewer with
# native fluency, not a longer sample of the same pool.
#
# To grow the list, run `--propose-zh N`, read the candidates against those criteria, and
# append the survivors here. Never append one nobody has read, and re-run the script.
REVIEWED_ZH_NAMES: tuple[str, ...] = (
    "复宁",
    "复恩",
    "复欣",
    "复灵",
    "复舒",
    "复迪",
    "宁恩",
    "宁舒",
    "宁达",
    "宁迪",
    "安润",
    "恩欣",
    "恩润",
    "恩舒",
    "欣达",
    "欣迪",
    "舒恩",
    "舒灵",
    "舒迪",
    "达恩",
    "迪宁",
    "迪欣",
    "迪润",
    "迪灵",
    "迪舒",
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

    Two characters is the shape Chinese pharmaceutical brands overwhelmingly take, and it
    keeps the space at the n*(n-1) ordered pairs of an n-character pool rather than the
    tens of thousands the old two-and-three-character runtime generator produced — the
    difference between a set a reviewer can read and one they cannot.

    Two other shapes were considered on 2026-08-17 and left out. Three-character names are
    a real Chinese brand shape (感冒灵, 优甲乐, 拜复乐), but they multiply the space by the
    pool size again and they read MORE like a specific marketed product, not less, so they
    raise the collision risk exactly where nobody can check it. Reduplication (安安) is not
    a pharmaceutical shape in Chinese at all, which is why `screen_zh` rejects a repeated
    character. Widening happens through the character pool instead, where every added
    candidate goes through the same reading pass.
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
        f"{ZH_REVIEW_STATUS},\n"
        "against the criteria below: does the pair\n"
        "name a real company or product, does it read as an ordinary word, a personal name\n"
        "or a place, does it read as a substance rather than a brand, and does it read as a\n"
        "plausible invented brand at all.\n\n"
        "The first pass read 64 candidates and rejected 58. The second widened the character\n"
        "pool and read 370 more - an even sample across first characters, plus every pair\n"
        "among the ten characters that survive in practice - rejected 337 of them, and\n"
        "withdrew one of the six names the first pass had shipped (复安, the tail of 胃复安,\n"
        "the household name for metoclopramide in China). Every rejection is recorded, with\n"
        f"its reason, in ``scripts/generate_brand_names.py``, and {len(names)} names ship.\n\n"
        "That number is where honest screening landed, not a target: the second pass read\n"
        "370 candidates to add 20. The region of this space that reads like a Chinese drug\n"
        "brand is the region real manufacturers have already occupied, so a stricter-sounding\n"
        "name is usually a likelier collision.\n\n"
        "What those passes were NOT: a trademark search - no register was consulted, and none\n"
        "of these names is claimed to be unregistered - and not a fluent native speaker's\n"
        "sign-off, which this repository has not received and does not claim. They are an LLM\n"
        "reading pass. Chinese pharmaceutical brands recycle these characters so heavily that\n"
        "a collision is likelier here than in the Latin catalogue. Reports of one are welcome\n"
        "and land in ZH_REAL_PRODUCT_DENYLIST, which is append-only.\n",
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
