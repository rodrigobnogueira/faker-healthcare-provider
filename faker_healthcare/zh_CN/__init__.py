from faker.providers import ElementsType

from .. import HealthcareProvider as BaseHealthcareProvider
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
    """Faker provider for generating healthcare/medical fake data (zh_CN)."""

    hospital_departments: ElementsType[str] = HOSPITAL_DEPARTMENTS
    brand_drugs: ElementsType[str] = BRAND_DRUGS
    blood_types: ElementsType[str] = BLOOD_TYPES
    allergies: ElementsType[str] = ALLERGIES
    medical_procedures: ElementsType[str] = MEDICAL_PROCEDURES
    insurance_plans: ElementsType[str] = INSURANCE_PLANS
    vital_signs: ElementsType[str] = VITAL_SIGNS
