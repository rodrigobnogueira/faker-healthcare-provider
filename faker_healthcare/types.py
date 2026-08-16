"""Shared type definitions for the healthcare provider."""

from typing import Literal, TypedDict


# The direction a condition pushes an analyte or a vital sign in, and the flag a
# generated value carries. Both are locale-neutral IDs, never display text: the words a
# consumer sees come from that locale's CLINICAL_LABELS (`flag_low` / `flag_normal` /
# `flag_high`).
Direction = Literal["low", "high"]
Flag = Literal["low", "normal", "high"]


class DiseaseData(TypedDict):
    """Structure for disease correlation data."""

    icd10: str
    symptoms: list[str]
    medications: list[str]
    medical_specialty: str


class PatientScenario(TypedDict):
    """Structure for patient scenario data."""

    disease: str
    icd10: str
    symptoms: list[str]
    medications: list[str]
    medical_specialty: str


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
