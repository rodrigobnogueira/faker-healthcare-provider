from faker.providers import ElementsType

from .. import HealthcareProvider as BaseHealthcareProvider
from ..types import DiseaseData
from .constants import (
    ALLERGIES,
    BLOOD_TYPES,
    BRAND_DRUGS,
    HOSPITAL_DEPARTMENTS,
    INSURANCE_PLANS,
    MEDICAL_PROCEDURES,
    VITAL_SIGNS,
)


class Provider(BaseHealthcareProvider):
    """Proveedor de Faker para generar datos médicos/sanitarios falsos (es_ES)."""

    def _load_disease_correlations(self) -> dict[str, DiseaseData]:
        from .disease_correlations import DISEASE_CORRELATIONS

        return DISEASE_CORRELATIONS

    hospital_departments: ElementsType[str] = HOSPITAL_DEPARTMENTS
    brand_drugs: ElementsType[str] = BRAND_DRUGS
    blood_types: ElementsType[str] = BLOOD_TYPES
    allergies: ElementsType[str] = ALLERGIES
    medical_procedures: ElementsType[str] = MEDICAL_PROCEDURES
    insurance_plans: ElementsType[str] = INSURANCE_PLANS
    vital_signs: ElementsType[str] = VITAL_SIGNS
