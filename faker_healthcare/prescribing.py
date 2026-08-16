"""Locale-neutral prescribing data: dose ladders, routes, frequencies, order statuses.

MEDICAL DISCLAIMER: these ladders exist so that a **synthetic** medication order carries
a number a prescriber would recognise instead of a random integer. They are not dosing
guidance, they ignore renal and hepatic function, weight, age, interactions and
indication, and several substances are prescribed at doses outside them for good
reasons. Never use them for anything but generating fake data.

Why this module is not per-locale
---------------------------------
A dose is a quantity, and 500 mg is 500 mg in every language, so the ladders live here
once, keyed by a locale-neutral substance ID (`metformin`, `insulin_glargine`), exactly
as `clinical_values.py` keys reference intervals. What IS translated is the substance's
name as that locale's catalogue spells it (`Metformina`, `二甲双胍`), which lives in
`MEDICATION_NAMES` in each `clinical_labels.py`, and the route/frequency/status words,
which live in `CLINICAL_LABELS` beside the analyte names.

Where the doses come from
-------------------------
Typical adult maintenance doses for the licensed indication this package's catalogue
prescribes the drug for, as published in the British National Formulary (BNF) and in the
manufacturers' summaries of product characteristics. Each ladder is a small set of the
strengths that are actually dispensed — metformin comes as 500, 850 and 1000 mg tablets,
so those are the three values `medication_order()` can produce — rather than a range to
draw a random integer from, because 637 mg of metformin is not a thing.

Route and frequency belong to the substance, not to the order
-------------------------------------------------------------
Each ladder carries its own route and its own set of plausible frequencies, so insulin
is never oral, methotrexate is weekly rather than daily, and salbutamol/albuterol is
inhaled as required. Modelling them as three independent draws produced records like
"Insulin 500 mg orally four times daily", which is the class of defect this package
exists to avoid.

What is deliberately NOT here
-----------------------------
- **Cytotoxic chemotherapy** (fluorouracil, carboplatin, paclitaxel, gemcitabine and the
  rest). Real doses are body-surface-area or AUC based and mean nothing as a flat
  milligram figure, so those substances have no ladder and `medication_order()` returns
  `None` for the dose rather than inventing one. Pembrolizumab is the exception that
  proves the rule: it has a genuine flat 200 mg dose.
- **Drug classes.** The catalogue still carries some class names ("Antibiotics",
  "Diuretics", "Statins"); a class has no dose, so it gets no ladder.
- **Paediatric and weight-based dosing.** Everything here is adult, like the rest of the
  measurement API. Paediatric doses are mg/kg and need a real formulary.
- **Titration.** A ladder is a set of maintenance strengths, not a schedule; nothing here
  models starting low and working up.

Unit strings are the international abbreviations (mg, µg, g, mL, IU) and are not
translated, exactly like the laboratory units in `clinical_values.py`. `drop` is written
out because there is no abbreviation for it.
"""

from .types import DoseLadder


__all__ = [
    "DEFAULT_ORDER_COUNT_RANGE",
    "DOSE_LADDERS",
    "FREQUENCY_IDS",
    "MEDICATION_STATUS_BANDS",
    "MEDICATION_STATUS_IDS",
    "ROUTE_IDS",
    "frequency_label_key",
    "route_label_key",
    "status_label_key",
]


# Locale-neutral IDs. Each one has a label under the same key (prefixed) in every
# locale's CLINICAL_LABELS, and a test asserts the two sets agree.
ROUTE_IDS: tuple[str, ...] = (
    "oral",
    "intravenous",
    "subcutaneous",
    "inhaled",
    "sublingual",
    "ophthalmic",
)

FREQUENCY_IDS: tuple[str, ...] = (
    "once_daily",
    "twice_daily",
    "three_times_daily",
    "four_times_daily",
    "at_night",
    "as_required",
    "once_weekly",
    "every_three_weeks",
)

# The temporal split the requester asked for: a record needs medications the patient used
# to take, takes now, and is booked to start. Nothing here is a date — a status is what a
# free-text note or a structured medication table actually carries.
MEDICATION_STATUS_IDS: tuple[str, ...] = ("past", "current", "future")

# (cumulative percentile, status ID). Most drugs on a record are current; a planned future
# medication is the rarest of the three.
MEDICATION_STATUS_BANDS: tuple[tuple[int, str], ...] = (
    (55, "current"),
    (85, "past"),
    (100, "future"),
)

DEFAULT_ORDER_COUNT_RANGE = (1, 4)


def route_label_key(route: str) -> str:
    """Return the CLINICAL_LABELS key holding a route's display word."""
    return f"route_{route}"


def frequency_label_key(frequency: str) -> str:
    """Return the CLINICAL_LABELS key holding a frequency's display words."""
    return f"frequency_{frequency}"


def status_label_key(status: str) -> str:
    """Return the CLINICAL_LABELS key holding a medication status's display word."""
    return f"medication_status_{status}"


# --------------------------------------------------------------------------------------
# Dose ladders, keyed by locale-neutral substance ID
# --------------------------------------------------------------------------------------
#
# `doses` are dispensed strengths, in `unit`, for the adult indication this catalogue
# prescribes the substance for. `frequencies` are the schedules that strength is given
# on. Both are drawn from with `random_element`, so every generated order is a
# combination a prescriber could write.
DOSE_LADDERS: dict[str, DoseLadder] = {
    # Cardiovascular
    "amlodipine": {"unit": "mg", "doses": (5, 10), "route": "oral", "frequencies": ("once_daily",)},
    "apixaban": {"unit": "mg", "doses": (2.5, 5), "route": "oral", "frequencies": ("twice_daily",)},
    "aspirin": {"unit": "mg", "doses": (75, 300), "route": "oral", "frequencies": ("once_daily",)},
    "atorvastatin": {"unit": "mg", "doses": (10, 20, 40, 80), "route": "oral", "frequencies": ("once_daily",)},
    "cilostazol": {"unit": "mg", "doses": (50, 100), "route": "oral", "frequencies": ("twice_daily",)},
    "clopidogrel": {"unit": "mg", "doses": (75,), "route": "oral", "frequencies": ("once_daily",)},
    "digoxin": {"unit": "µg", "doses": (62.5, 125, 250), "route": "oral", "frequencies": ("once_daily",)},
    "diltiazem": {"unit": "mg", "doses": (60, 90, 120), "route": "oral", "frequencies": ("three_times_daily",)},
    "enoxaparin": {"unit": "mg", "doses": (20, 40), "route": "subcutaneous", "frequencies": ("once_daily",)},
    "furosemide": {"unit": "mg", "doses": (20, 40, 80), "route": "oral", "frequencies": ("once_daily",)},
    "hydrochlorothiazide": {"unit": "mg", "doses": (12.5, 25), "route": "oral", "frequencies": ("once_daily",)},
    "lisinopril": {"unit": "mg", "doses": (2.5, 5, 10, 20), "route": "oral", "frequencies": ("once_daily",)},
    "losartan": {"unit": "mg", "doses": (25, 50, 100), "route": "oral", "frequencies": ("once_daily",)},
    "metoprolol": {"unit": "mg", "doses": (25, 50, 100), "route": "oral", "frequencies": ("twice_daily",)},
    "nitroglycerin": {"unit": "µg", "doses": (400, 500), "route": "sublingual", "frequencies": ("as_required",)},
    "propranolol": {"unit": "mg", "doses": (10, 40, 80), "route": "oral", "frequencies": ("twice_daily", "three_times_daily")},
    "rivaroxaban": {"unit": "mg", "doses": (10, 15, 20), "route": "oral", "frequencies": ("once_daily",)},
    "rosuvastatin": {"unit": "mg", "doses": (5, 10, 20, 40), "route": "oral", "frequencies": ("once_daily",)},
    "simvastatin": {"unit": "mg", "doses": (10, 20, 40), "route": "oral", "frequencies": ("at_night",)},
    "spironolactone": {"unit": "mg", "doses": (25, 50, 100), "route": "oral", "frequencies": ("once_daily",)},
    "warfarin": {"unit": "mg", "doses": (1, 3, 5), "route": "oral", "frequencies": ("once_daily",)},
    # Diabetes and endocrine
    "empagliflozin": {"unit": "mg", "doses": (10, 25), "route": "oral", "frequencies": ("once_daily",)},
    "glimepiride": {"unit": "mg", "doses": (1, 2, 4), "route": "oral", "frequencies": ("once_daily",)},
    "glyburide": {"unit": "mg", "doses": (2.5, 5, 10), "route": "oral", "frequencies": ("once_daily",)},
    "insulin": {"unit": "IU", "doses": (10, 20, 30, 40), "route": "subcutaneous", "frequencies": ("once_daily", "twice_daily", "three_times_daily")},
    "insulin_glargine": {"unit": "IU", "doses": (10, 20, 30, 40), "route": "subcutaneous", "frequencies": ("once_daily",)},
    "levothyroxine": {"unit": "µg", "doses": (25, 50, 75, 100, 125, 150), "route": "oral", "frequencies": ("once_daily",)},
    "liraglutide": {"unit": "mg", "doses": (0.6, 1.2, 1.8), "route": "subcutaneous", "frequencies": ("once_daily",)},
    "metformin": {"unit": "mg", "doses": (500, 850, 1000), "route": "oral", "frequencies": ("twice_daily", "three_times_daily")},
    "methimazole": {"unit": "mg", "doses": (5, 10, 20), "route": "oral", "frequencies": ("once_daily",)},
    "pioglitazone": {"unit": "mg", "doses": (15, 30, 45), "route": "oral", "frequencies": ("once_daily",)},
    "sitagliptin": {"unit": "mg", "doses": (25, 50, 100), "route": "oral", "frequencies": ("once_daily",)},
    # Corticosteroids
    "dexamethasone": {"unit": "mg", "doses": (0.5, 2, 4, 8), "route": "oral", "frequencies": ("once_daily",)},
    "hydrocortisone": {"unit": "mg", "doses": (10, 20), "route": "oral", "frequencies": ("twice_daily",)},
    "prednisone": {"unit": "mg", "doses": (5, 10, 20, 30, 40), "route": "oral", "frequencies": ("once_daily",)},
    # Anti-infectives
    "acyclovir": {"unit": "mg", "doses": (200, 400), "route": "oral", "frequencies": ("twice_daily", "three_times_daily")},
    "amoxicillin": {"unit": "mg", "doses": (250, 500), "route": "oral", "frequencies": ("three_times_daily",)},
    "azithromycin": {"unit": "mg", "doses": (250, 500), "route": "oral", "frequencies": ("once_daily",)},
    "ceftriaxone": {"unit": "g", "doses": (1, 2), "route": "intravenous", "frequencies": ("once_daily",)},
    "cefuroxime": {"unit": "mg", "doses": (250, 500), "route": "oral", "frequencies": ("twice_daily",)},
    "cephalexin": {"unit": "mg", "doses": (250, 500), "route": "oral", "frequencies": ("four_times_daily",)},
    "ciprofloxacin": {"unit": "mg", "doses": (250, 500, 750), "route": "oral", "frequencies": ("twice_daily",)},
    "clarithromycin": {"unit": "mg", "doses": (250, 500), "route": "oral", "frequencies": ("twice_daily",)},
    "clindamycin": {"unit": "mg", "doses": (150, 300), "route": "oral", "frequencies": ("four_times_daily",)},
    "doxycycline": {"unit": "mg", "doses": (100,), "route": "oral", "frequencies": ("once_daily", "twice_daily")},
    "levofloxacin": {"unit": "mg", "doses": (250, 500), "route": "oral", "frequencies": ("once_daily",)},
    "metronidazole": {"unit": "mg", "doses": (200, 400), "route": "oral", "frequencies": ("three_times_daily",)},
    "nitrofurantoin": {"unit": "mg", "doses": (50, 100), "route": "oral", "frequencies": ("four_times_daily",)},
    "oseltamivir": {"unit": "mg", "doses": (75,), "route": "oral", "frequencies": ("twice_daily",)},
    "trimethoprim": {"unit": "mg", "doses": (200,), "route": "oral", "frequencies": ("twice_daily",)},
    "valacyclovir": {"unit": "mg", "doses": (500, 1000), "route": "oral", "frequencies": ("twice_daily", "three_times_daily")},
    # Respiratory and allergy
    "albuterol": {"unit": "µg", "doses": (100, 200), "route": "inhaled", "frequencies": ("as_required",)},
    "budesonide": {"unit": "µg", "doses": (100, 200, 400), "route": "inhaled", "frequencies": ("twice_daily",)},
    "cetirizine": {"unit": "mg", "doses": (10,), "route": "oral", "frequencies": ("once_daily",)},
    "fluticasone": {"unit": "µg", "doses": (50, 100, 250), "route": "inhaled", "frequencies": ("twice_daily",)},
    "loratadine": {"unit": "mg", "doses": (10,), "route": "oral", "frequencies": ("once_daily",)},
    "montelukast": {"unit": "mg", "doses": (10,), "route": "oral", "frequencies": ("at_night",)},
    "theophylline": {"unit": "mg", "doses": (200, 400), "route": "oral", "frequencies": ("twice_daily",)},
    "tiotropium": {"unit": "µg", "doses": (18,), "route": "inhaled", "frequencies": ("once_daily",)},
    # Gastrointestinal
    "esomeprazole": {"unit": "mg", "doses": (20, 40), "route": "oral", "frequencies": ("once_daily",)},
    "famotidine": {"unit": "mg", "doses": (20, 40), "route": "oral", "frequencies": ("once_daily", "twice_daily")},
    "lactulose": {"unit": "mL", "doses": (15, 30), "route": "oral", "frequencies": ("twice_daily",)},
    "loperamide": {"unit": "mg", "doses": (2,), "route": "oral", "frequencies": ("as_required",)},
    "mesalamine": {"unit": "mg", "doses": (800, 1200), "route": "oral", "frequencies": ("three_times_daily",)},
    "omeprazole": {"unit": "mg", "doses": (10, 20, 40), "route": "oral", "frequencies": ("once_daily",)},
    "pantoprazole": {"unit": "mg", "doses": (20, 40), "route": "oral", "frequencies": ("once_daily",)},
    "ursodiol": {"unit": "mg", "doses": (250, 500), "route": "oral", "frequencies": ("twice_daily",)},
    # Analgesia, rheumatology and bone
    "acetaminophen": {"unit": "mg", "doses": (500, 1000), "route": "oral", "frequencies": ("four_times_daily",)},
    "alendronate": {"unit": "mg", "doses": (70,), "route": "oral", "frequencies": ("once_weekly",)},
    "allopurinol": {"unit": "mg", "doses": (100, 200, 300), "route": "oral", "frequencies": ("once_daily",)},
    "azathioprine": {"unit": "mg", "doses": (50, 100), "route": "oral", "frequencies": ("once_daily",)},
    "calcium_carbonate": {"unit": "mg", "doses": (500, 1000), "route": "oral", "frequencies": ("once_daily",)},
    "cholecalciferol": {"unit": "IU", "doses": (800, 1000, 2000), "route": "oral", "frequencies": ("once_daily",)},
    "colchicine": {"unit": "mg", "doses": (0.5,), "route": "oral", "frequencies": ("twice_daily",)},
    "febuxostat": {"unit": "mg", "doses": (80, 120), "route": "oral", "frequencies": ("once_daily",)},
    "hydroxychloroquine": {"unit": "mg", "doses": (200, 400), "route": "oral", "frequencies": ("once_daily",)},
    "ibuprofen": {"unit": "mg", "doses": (200, 400, 600), "route": "oral", "frequencies": ("three_times_daily",)},
    "methotrexate": {"unit": "mg", "doses": (7.5, 10, 15, 20, 25), "route": "oral", "frequencies": ("once_weekly",)},
    "naproxen": {"unit": "mg", "doses": (250, 500), "route": "oral", "frequencies": ("twice_daily",)},
    "sulfasalazine": {"unit": "mg", "doses": (500, 1000), "route": "oral", "frequencies": ("twice_daily",)},
    "tramadol": {"unit": "mg", "doses": (50, 100), "route": "oral", "frequencies": ("four_times_daily",)},
    # Haematinics
    "ferrous_sulfate": {"unit": "mg", "doses": (200,), "route": "oral", "frequencies": ("once_daily", "twice_daily")},
    "folic_acid": {"unit": "mg", "doses": (5,), "route": "oral", "frequencies": ("once_daily",)},
    # Neurology
    "carbamazepine": {"unit": "mg", "doses": (100, 200, 400), "route": "oral", "frequencies": ("twice_daily",)},
    "donepezil": {"unit": "mg", "doses": (5, 10), "route": "oral", "frequencies": ("once_daily",)},
    "gabapentin": {"unit": "mg", "doses": (100, 300, 600), "route": "oral", "frequencies": ("three_times_daily",)},
    "galantamine": {"unit": "mg", "doses": (8, 16, 24), "route": "oral", "frequencies": ("once_daily",)},
    "lamotrigine": {"unit": "mg", "doses": (25, 50, 100, 200), "route": "oral", "frequencies": ("once_daily", "twice_daily")},
    "levetiracetam": {"unit": "mg", "doses": (250, 500, 1000), "route": "oral", "frequencies": ("twice_daily",)},
    "memantine": {"unit": "mg", "doses": (5, 10, 20), "route": "oral", "frequencies": ("once_daily",)},
    "phenytoin": {"unit": "mg", "doses": (100, 300), "route": "oral", "frequencies": ("once_daily",)},
    "pregabalin": {"unit": "mg", "doses": (25, 75, 150, 300), "route": "oral", "frequencies": ("twice_daily",)},
    "sumatriptan": {"unit": "mg", "doses": (50, 100), "route": "oral", "frequencies": ("as_required",)},
    "topiramate": {"unit": "mg", "doses": (25, 50, 100), "route": "oral", "frequencies": ("twice_daily",)},
    "valproate": {"unit": "mg", "doses": (200, 500), "route": "oral", "frequencies": ("twice_daily",)},
    "valproic_acid": {"unit": "mg", "doses": (200, 500), "route": "oral", "frequencies": ("twice_daily",)},
    # Mental health
    "acamprosate": {"unit": "mg", "doses": (666,), "route": "oral", "frequencies": ("three_times_daily",)},
    "alprazolam": {"unit": "mg", "doses": (0.25, 0.5, 1), "route": "oral", "frequencies": ("three_times_daily",)},
    "amitriptyline": {"unit": "mg", "doses": (10, 25, 50), "route": "oral", "frequencies": ("at_night",)},
    "aripiprazole": {"unit": "mg", "doses": (5, 10, 15, 30), "route": "oral", "frequencies": ("once_daily",)},
    "atomoxetine": {"unit": "mg", "doses": (40, 80), "route": "oral", "frequencies": ("once_daily",)},
    "buprenorphine": {"unit": "mg", "doses": (8, 16), "route": "sublingual", "frequencies": ("once_daily",)},
    "bupropion": {"unit": "mg", "doses": (150, 300), "route": "oral", "frequencies": ("once_daily",)},
    "buspirone": {"unit": "mg", "doses": (5, 10, 15), "route": "oral", "frequencies": ("three_times_daily",)},
    "duloxetine": {"unit": "mg", "doses": (30, 60), "route": "oral", "frequencies": ("once_daily",)},
    "escitalopram": {"unit": "mg", "doses": (5, 10, 20), "route": "oral", "frequencies": ("once_daily",)},
    "fluoxetine": {"unit": "mg", "doses": (20, 40, 60), "route": "oral", "frequencies": ("once_daily",)},
    "haloperidol": {"unit": "mg", "doses": (0.5, 1.5, 5), "route": "oral", "frequencies": ("twice_daily",)},
    "lithium": {"unit": "mg", "doses": (400, 800), "route": "oral", "frequencies": ("once_daily",)},
    "lorazepam": {"unit": "mg", "doses": (0.5, 1, 2), "route": "oral", "frequencies": ("twice_daily", "as_required")},
    "melatonin": {"unit": "mg", "doses": (2, 3, 5), "route": "oral", "frequencies": ("at_night",)},
    "methadone": {"unit": "mg", "doses": (30, 60, 80), "route": "oral", "frequencies": ("once_daily",)},
    "methylphenidate": {"unit": "mg", "doses": (5, 10, 20), "route": "oral", "frequencies": ("twice_daily",)},
    "naltrexone": {"unit": "mg", "doses": (50,), "route": "oral", "frequencies": ("once_daily",)},
    "olanzapine": {"unit": "mg", "doses": (5, 10, 15, 20), "route": "oral", "frequencies": ("once_daily",)},
    "paroxetine": {"unit": "mg", "doses": (10, 20, 30, 40), "route": "oral", "frequencies": ("once_daily",)},
    "quetiapine": {"unit": "mg", "doses": (25, 100, 200, 300), "route": "oral", "frequencies": ("twice_daily",)},
    "risperidone": {"unit": "mg", "doses": (1, 2, 4, 6), "route": "oral", "frequencies": ("once_daily", "twice_daily")},
    "sertraline": {"unit": "mg", "doses": (25, 50, 100, 200), "route": "oral", "frequencies": ("once_daily",)},
    "venlafaxine": {"unit": "mg", "doses": (37.5, 75, 150), "route": "oral", "frequencies": ("once_daily",)},
    # Urology and men's health
    "dutasteride": {"unit": "mg", "doses": (0.5,), "route": "oral", "frequencies": ("once_daily",)},
    "finasteride": {"unit": "mg", "doses": (5,), "route": "oral", "frequencies": ("once_daily",)},
    "oxybutynin": {"unit": "mg", "doses": (2.5, 5), "route": "oral", "frequencies": ("twice_daily", "three_times_daily")},
    "sildenafil": {"unit": "mg", "doses": (25, 50, 100), "route": "oral", "frequencies": ("as_required",)},
    "solifenacin": {"unit": "mg", "doses": (5, 10), "route": "oral", "frequencies": ("once_daily",)},
    "tadalafil": {"unit": "mg", "doses": (5, 10, 20), "route": "oral", "frequencies": ("as_required",)},
    "tamsulosin": {"unit": "µg", "doses": (400,), "route": "oral", "frequencies": ("once_daily",)},
    "tolterodine": {"unit": "mg", "doses": (2, 4), "route": "oral", "frequencies": ("twice_daily",)},
    # Ophthalmology
    "latanoprost": {"unit": "drop", "doses": (1,), "route": "ophthalmic", "frequencies": ("at_night",)},
    "timolol": {"unit": "drop", "doses": (1,), "route": "ophthalmic", "frequencies": ("twice_daily",)},
    # Oncology — endocrine therapy and the one flat-dose immunotherapy (see the docstring)
    "anastrozole": {"unit": "mg", "doses": (1,), "route": "oral", "frequencies": ("once_daily",)},
    "bicalutamide": {"unit": "mg", "doses": (50, 150), "route": "oral", "frequencies": ("once_daily",)},
    "letrozole": {"unit": "mg", "doses": (2.5,), "route": "oral", "frequencies": ("once_daily",)},
    "pembrolizumab": {"unit": "mg", "doses": (200,), "route": "intravenous", "frequencies": ("every_three_weeks",)},
    "tamoxifen": {"unit": "mg", "doses": (20,), "route": "oral", "frequencies": ("once_daily",)},
}
