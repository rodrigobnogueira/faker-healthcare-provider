"""Screened fictitious Chinese brand names for the zh_CN ``brand_drug()``.

GENERATED FILE - do not edit by hand. Regenerate with::

    python scripts/generate_brand_names.py

These are two-character combinations of the pharmaceutical characters in
``ZH_BRAND_CHARS``, screened against a denylist of real trademarks, company names,
ordinary words and personal names; against the characters that read as a generic
drug rather than as a brand (``ZH_GENERIC_MORPHEMES``); and against every Chinese
term this package ships.

**Review status.** Every candidate was
read one by one in Simplified Chinese on 2026-08-16 and again on 2026-08-17,
against the criteria below: does the pair
name a real company or product, does it read as an ordinary word, a personal name
or a place, does it read as a substance rather than a brand, and does it read as a
plausible invented brand at all.

The first pass read 64 candidates and rejected 58. The second widened the character
pool and read 370 more - an even sample across first characters, plus every pair
among the ten characters that survive in practice - rejected 337 of them, and
withdrew one of the six names the first pass had shipped (复安, the tail of 胃复安,
the household name for metoclopramide in China). Every rejection is recorded, with
its reason, in ``scripts/generate_brand_names.py``, and 25 names ship.

That number is where honest screening landed, not a target: the second pass read
370 candidates to add 20. The region of this space that reads like a Chinese drug
brand is the region real manufacturers have already occupied, so a stricter-sounding
name is usually a likelier collision.

What those passes were NOT: a trademark search - no register was consulted, and none
of these names is claimed to be unregistered - and not a fluent native speaker's
sign-off, which this repository has not received and does not claim. They are an LLM
reading pass. Chinese pharmaceutical brands recycle these characters so heavily that
a collision is likelier here than in the Latin catalogue. Reports of one are welcome
and land in ZH_REAL_PRODUCT_DENYLIST, which is append-only.
"""

ZH_BRAND_NAMES: tuple[str, ...] = (
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
