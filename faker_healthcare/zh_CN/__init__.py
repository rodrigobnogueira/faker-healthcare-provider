from faker.providers import ElementsType

from .. import HealthcareProvider as BaseHealthcareProvider
from ..types import DiseaseData
from .constants import (
    ALLERGIES,
    BLOOD_TYPES,
    HOSPITAL_DEPARTMENTS,
    INSURANCE_PLANS,
    MEDICAL_PROCEDURES,
    VITAL_SIGNS,
    ZH_BRAND_CHARS,
)


class Provider(BaseHealthcareProvider):
    """Faker provider for generating healthcare/medical fake data (zh_CN)."""

    def _load_disease_correlations(self) -> dict[str, DiseaseData]:
        from .disease_correlations import DISEASE_CORRELATIONS

        return DISEASE_CORRELATIONS

    hospital_departments: ElementsType[str] = HOSPITAL_DEPARTMENTS
    blood_types: ElementsType[str] = BLOOD_TYPES
    allergies: ElementsType[str] = ALLERGIES
    medical_procedures: ElementsType[str] = MEDICAL_PROCEDURES
    insurance_plans: ElementsType[str] = INSURANCE_PLANS
    vital_signs: ElementsType[str] = VITAL_SIGNS

    def brand_drug(self) -> str:
        """Return a fictitious Chinese-style brand name paired with a Latin one.

        The Chinese characters are drawn from a pool of generic pharmaceutical
        characters and combined into an invented name (never a real trademark);
        the Latin part reuses the base generator. Any resemblance is coincidental.
        """
        chars = "".join(self.random_elements(ZH_BRAND_CHARS, length=self.random_int(2, 3), unique=True))
        return f"{chars} ({super().brand_drug()})"
