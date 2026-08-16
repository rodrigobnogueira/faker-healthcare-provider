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
    ZH_BRAND_NAMES,
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
    non_drug_interventions: ElementsType[str] = NON_DRUG_INTERVENTIONS

    # Words only. The units, reference intervals, dose ladders and assessment ranges
    # behind the measurement, prescribing and assessment APIs are locale-neutral and stay
    # in faker_healthcare/clinical_values.py, prescribing.py and assessments.py.
    clinical_labels: Mapping[str, str] = CLINICAL_LABELS
    medication_names: Mapping[str, str] = MEDICATION_NAMES

    zh_brand_names: ElementsType[str] = ZH_BRAND_NAMES

    def brand_drug(self) -> str:
        """Return a fictitious Chinese-style brand name paired with a Latin one.

        Both halves come from screened static lists — `zh_brand_names` here and
        `brand_drug_names` from the base provider — rather than being combined at
        runtime, which previously put 30,752 unscreened Chinese names in the API.

        The Chinese list carries a weaker guarantee than the Latin one and says so in
        its own module: it has passed the automated screens and a Simplified-Chinese
        reading pass (which rejected 58 of the 64 names that used to ship here), but no
        trademark register was searched and no fluent native speaker's sign-off is
        recorded. Corrections are welcome and land in ZH_REAL_PRODUCT_DENYLIST.
        """
        return f"{self.random_element(self.zh_brand_names)} ({super().brand_drug()})"
