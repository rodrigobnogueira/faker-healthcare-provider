"""Screened fictitious Chinese brand names for the zh_CN ``brand_drug()``.

GENERATED FILE - do not edit by hand. Regenerate with::

    python scripts/generate_brand_names.py

TODO(review): these names have had automated screens only; NOT reviewed by a fluent Chinese speaker.
They are two-character combinations of the generic pharmaceutical characters in
``ZH_BRAND_CHARS``, filtered against a denylist of real trademarks and ordinary
words compiled by inspection, and against every Chinese term this package ships.
That denylist is certainly incomplete. Shipping this list rather than generating
30,752 combinations at runtime is what makes a fluent reviewer's pass possible at
all - it is not a substitute for one. Corrections are welcome and land in
ZH_REAL_PRODUCT_DENYLIST, which is append-only.
"""

ZH_BRAND_NAMES: tuple[str, ...] = (
    "乐佳",
    "乐欣",
    "佳元",
    "佳欣",
    "元力",
    "元泰",
    "力华",
    "力泽",
    "华可",
    "华益",
    "博可",
    "博清",
    "可复",
    "可益",
    "和复",
    "和素",
    "复安",
    "复维",
    "宁定",
    "宁舒",
    "安元",
    "安欣",
    "定尔",
    "定诗",
    "尔平",
    "尔达",
    "平施",
    "平迪",
    "康可",
    "康益",
    "恩乐",
    "恩欣",
    "施力",
    "施泽",
    "欣元",
    "欣泽",
    "泰定",
    "泰舒",
    "泽力",
    "泽清",
    "清可",
    "清益",
    "特可",
    "特益",
    "瑞施",
    "瑞通",
    "益宁",
    "益维",
    "素复",
    "素维",
    "维宁",
    "维舒",
    "舒康",
    "舒迪",
    "诗平",
    "诗达",
    "诺恩",
    "诺通",
    "达恩",
    "达通",
    "迪元",
    "迪欣",
    "通元",
    "通欣",
)
