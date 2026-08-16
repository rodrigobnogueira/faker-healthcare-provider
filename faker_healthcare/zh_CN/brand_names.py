"""Screened fictitious Chinese brand names for the zh_CN ``brand_drug()``.

GENERATED FILE - do not edit by hand. Regenerate with::

    python scripts/generate_brand_names.py

These are two-character combinations of the pharmaceutical characters in
``ZH_BRAND_CHARS``, screened against a denylist of real trademarks, company names,
ordinary words and personal names; against the characters that read as a generic
drug rather than as a brand (``ZH_GENERIC_MORPHEMES``); and against every Chinese
term this package ships.

**Review status.** Every candidate was
read one by one in Simplified Chinese on 2026-08-16 against the criteria below: does the pair
name a real company or product, does it read as an ordinary word, a personal name
or a place, does it read as a substance rather than a brand, and does it read as a
plausible invented brand at all. That pass rejected 58 of the 64 names this module
used to ship; each rejection is recorded, with its reason, in the screens in
``scripts/generate_brand_names.py``. Six survived, and the list is short because
the review was strict, not because the space is.

What that pass was NOT: a trademark search - no register was consulted, and none
of these names is claimed to be unregistered - and not a fluent native speaker's
sign-off, which this repository has not received and does not claim. Chinese
pharmaceutical brands recycle these characters so heavily that a collision is
likelier here than in the Latin catalogue. Reports of one are welcome and land in
ZH_REAL_PRODUCT_DENYLIST, which is append-only.
"""

ZH_BRAND_NAMES: tuple[str, ...] = (
    "复安",
    "宁舒",
    "恩欣",
    "舒迪",
    "达恩",
    "迪欣",
)
