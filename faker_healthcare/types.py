"""Shared type definitions for the healthcare provider."""

from typing import TypedDict


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
