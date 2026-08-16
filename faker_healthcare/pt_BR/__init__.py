from collections.abc import Mapping

from faker.providers import ElementsType

from .. import HealthcareProvider as BaseHealthcareProvider
from ..types import DiseaseData
from .clinical_labels import CLINICAL_LABELS, MEDICATION_NAMES
from .constants import (
    ALLERGIES,
    BLOOD_TYPES,
    HOSPITAL_DEPARTMENTS,
    INSURANCE_PLANS,
    MEDICAL_PROCEDURES,
    NON_DRUG_INTERVENTIONS,
    VITAL_SIGNS,
)


class Provider(BaseHealthcareProvider):
    """Faker provider for generating healthcare/medical fake data."""

    def _load_disease_correlations(self) -> dict[str, DiseaseData]:
        from .disease_correlations import DISEASE_CORRELATIONS

        return DISEASE_CORRELATIONS

    hospital_departments: ElementsType[str] = HOSPITAL_DEPARTMENTS
    blood_types: ElementsType[str] = BLOOD_TYPES
    allergies: ElementsType[str] = ALLERGIES
    medical_procedures: ElementsType[str] = MEDICAL_PROCEDURES
    insurance_plans: ElementsType[str] = INSURANCE_PLANS
    vital_signs: ElementsType[str] = VITAL_SIGNS
    non_drug_interventions: ElementsType[str] = NON_DRUG_INTERVENTIONS

    # Words only. The units, reference intervals, dose ladders and assessment ranges
    # behind the measurement, prescribing and assessment APIs are locale-neutral and stay
    # in faker_healthcare/clinical_values.py, prescribing.py and assessments.py.
    clinical_labels: Mapping[str, str] = CLINICAL_LABELS
    medication_names: Mapping[str, str] = MEDICATION_NAMES
