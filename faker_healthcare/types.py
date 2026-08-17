"""Shared type definitions for the healthcare provider.

A note on optional keys. Two of the shapes below have keys that are present only
sometimes — a demographic constraint may pin sex, an age range, or both, and a patient
record carries an assessment score only for a psychiatric condition. `typing.NotRequired`
expresses that in one class, but it arrived in Python 3.11 and this package supports
3.10 (`requires-python = ">=3.10"` in pyproject.toml, and the Tests workflow runs 3.10),
so the two-class form is used instead: a `TypedDict` holding the required keys, and a
subclass declared `total=False` adding the optional ones. Do not "simplify" it to
`NotRequired` without raising the floor first.
"""

from datetime import date
from typing import Literal, TypedDict


# The direction a condition pushes an analyte or a vital sign in, and the flag a
# generated value carries. Both are locale-neutral IDs, never display text: the words a
# consumer sees come from that locale's CLINICAL_LABELS (`flag_low` / `flag_normal` /
# `flag_high`).
Direction = Literal["low", "high"]
Flag = Literal["low", "normal", "high"]

# The two anthropometric reference classes this package models, and the values `patient()`
# returns in its `sex` field. Locale-neutral IDs, like every other ID here: they are keys
# into BODY_PROFILES and DEMOGRAPHIC_CONSTRAINTS, not display text.
Sex = Literal["male", "female"]


class DiseaseData(TypedDict):
    """Structure for disease correlation data.

    Demographic constraints (a female-only or paediatric condition) are deliberately NOT
    here: sex and age are the same facts in all six languages, so they live once in
    `clinical_values.DEMOGRAPHIC_CONSTRAINTS`, keyed by ICD-10 code, rather than being
    copied into six catalogues that could then disagree.
    """

    icd10: str
    symptoms: list[str]
    medications: list[str]
    medical_specialty: str


class DemographicConstraint(TypedDict, total=False):
    """Who a condition can occur in, in `faker_healthcare.clinical_values`.

    Every key is optional and an entry states only what it actually knows: preeclampsia
    pins `sex` and both age bounds, prostate cancer pins `sex` and a floor, bronchiolitis
    pins only a ceiling. An absent key is "no constraint", never a default.

    Sex comes in two strengths, because most conditions are neither locked to one sex nor
    evenly split between them:

    - `sex` is an **absolute** lock. Preeclampsia is female, full stop.
    - `female_probability` is a **weighting** — the share of patients who are female, a
      float strictly between 0 and 1. Breast cancer is 99% female, not 100%: male breast
      cancer is under 1% of cases and a package that could not generate one would be
      wrong in the other direction. The two keys are mutually exclusive; a weight of 0 or
      1 is a lock and must be written as one.

    Age comes in the same two strengths:

    - `min_age` / `max_age` are inclusive bounds on a plausible patient's age, not on the
      age at diagnosis and not a hard clinical limit. Inside them the draw is uniform.
    - `age_bands` replaces them with a **shape**: a tuple of `(share, lowest, highest)`
      triples, where `share` is the percentage of patients in that band and the draw is
      uniform within it. The bands are contiguous, ascending, and their shares sum to
      100, so the first band's floor and the last band's ceiling are the age bounds —
      which is why `age_bands` is mutually exclusive with `min_age` / `max_age` rather
      than restating them. A condition whose real population is nothing like uniform
      (two-thirds of people living with congenital heart disease are adults) gets a
      band; a condition whose shape nobody here can source keeps the uniform draw.
    """

    sex: Sex
    female_probability: float
    min_age: int
    max_age: int
    age_bands: tuple[tuple[int, int, int], ...]


class PatientScenario(TypedDict):
    """Structure for patient scenario data."""

    disease: str
    icd10: str
    symptoms: list[str]
    medications: list[str]
    medical_specialty: str


class Patient(PatientScenario):
    """A scenario plus demographics that satisfy that condition's constraints.

    `sex` is a locale-neutral ID (`'male'` / `'female'`), not a display word, because it
    is also the argument `body_measurements(sex=...)` takes. `date_of_birth` is
    consistent with `age` on the reference date the patient was generated against.
    """

    sex: Sex
    age: int
    date_of_birth: date


class VitalDefinition(TypedDict):
    """Numeric definition of one vital sign, in `faker_healthcare.clinical_values`.

    `low`/`high` are the adult reference range (an in-range value is drawn between
    them); `min_value`/`max_value` are the outermost values the generator will ever
    produce for this sign, so a condition that pushes it out of range still lands on a
    number seen in practice. Locale-neutral: only the display name is translated.
    """

    unit: str
    low: float
    high: float
    decimals: int
    min_value: float
    max_value: float


class LabDefinition(TypedDict):
    """Numeric definition of one laboratory analyte, in `faker_healthcare.clinical_values`.

    Same contract as `VitalDefinition`, with the reference interval named the way a
    report names it. Units are SI throughout — see the module docstring of
    `clinical_values.py`.
    """

    unit: str
    ref_low: float
    ref_high: float
    decimals: int
    min_value: float
    max_value: float


class VitalMeasurement(TypedDict):
    """One measured vital sign: a localized name, a number, and its unit."""

    name: str
    value: float
    unit: str


class BloodPressure(TypedDict):
    """A blood-pressure reading. `systolic` is always greater than `diastolic`."""

    systolic: int
    diastolic: int
    unit: str


class LabResult(TypedDict):
    """One laboratory result, with the reference interval it is flagged against.

    `analyte` and `flag` are localized display strings; `flag` always agrees with
    `value` compared to `reference_low`/`reference_high`.
    """

    analyte: str
    value: float
    unit: str
    reference_low: float
    reference_high: float
    flag: str


class BodyMeasurements(TypedDict):
    """Height, weight, and the BMI computed from them (never drawn independently)."""

    height_cm: float
    weight_kg: float
    bmi: float


class DoseLadder(TypedDict):
    """The dispensed strengths of one substance, in `faker_healthcare.prescribing`.

    `route` and `frequencies` belong to the substance rather than to the order: insulin
    is subcutaneous whatever it is prescribed for, and methotrexate is weekly. Both are
    locale-neutral IDs whose display words live in each locale's CLINICAL_LABELS.
    """

    unit: str
    doses: tuple[float, ...]
    route: str
    frequencies: tuple[str, ...]


class MedicationOrder(TypedDict):
    """One prescribed medication: what, how much, how, how often, and when.

    `medication`, `route`, `frequency` and `status` are localized display strings; `unit`
    is an international abbreviation and is not translated, like the laboratory units.

    `dose` and `unit` are `None` — and `route` and `frequency` with them — for a
    substance this package has no verified adult dose ladder for (a drug class such as
    "Antibiotics", or a cytotoxic dosed by body surface area). The order still names the
    medication and its status; it does not invent a milligram figure. See
    `faker_healthcare/prescribing.py`.
    """

    medication: str
    dose: float | None
    unit: str | None
    route: str | None
    frequency: str | None
    status: str


class AssessmentScore(TypedDict):
    """One clinical assessment result: the instrument, the number, and the band.

    Deliberately nothing else. See the module docstring of
    `faker_healthcare/assessments.py` for why the items of an instrument are never
    reproduced here.
    """

    instrument: str
    score: int
    max_score: int
    severity: str


class AssessmentInstrument(TypedDict):
    """The scored range of one instrument, in `faker_healthcare.assessments`."""

    name: str
    max_score: int
    higher_is_worse: bool
    bands: tuple[tuple[int, str], ...]
    significant_from: int


class _PatientRecordBase(Patient):
    """The keys every patient record carries (see PatientRecord)."""

    vital_signs: list[VitalMeasurement]
    lab_panel: list[LabResult]
    medication_orders: list[MedicationOrder]


class PatientRecord(_PatientRecordBase, total=False):
    """A complete correlated record: demographics, scenario, measurements, medications.

    `assessment` is the one optional key — it is present only for a psychiatric
    condition, because a PHQ-9 score on a record whose diagnosis is a fractured wrist is
    not a realistic record. Two classes rather than one `NotRequired`, for the 3.10
    reason given in this module's docstring.
    """

    assessment: AssessmentScore
