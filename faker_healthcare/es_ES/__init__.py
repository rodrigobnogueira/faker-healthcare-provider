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
    """Proveedor de Faker para generar datos médicos/sanitarios falsos (es_ES)."""

    hospital_departments = HOSPITAL_DEPARTMENTS
    brand_drugs = BRAND_DRUGS
    blood_types = BLOOD_TYPES
    allergies = ALLERGIES
    medical_procedures = MEDICAL_PROCEDURES
    insurance_plans = INSURANCE_PLANS
    vital_signs = VITAL_SIGNS
