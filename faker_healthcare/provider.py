from typing import Any

from faker.providers import BaseProvider, ElementsType

from .constants import (
    ALLERGIES,
    BLOOD_TYPES,
    BRAND_DRUGS,
    HOSPITAL_DEPARTMENTS,
    INSURANCE_PLANS,
    MEDICAL_PROCEDURES,
    MEDICAL_SPECIALTIES,
    VITAL_SIGNS,
)
from .disease_correlations import DISEASE_CORRELATIONS


class HealthcareProvider(BaseProvider):
    """Faker provider for generating healthcare/medical fake data.

    This provider generates correlated clinical data based on medical relationships
    between diseases, symptoms, medications, and ICD-10 codes.

    MEDICAL DISCLAIMER: This data is for TESTING AND DEVELOPMENT PURPOSES ONLY.
    It should NOT be used for actual medical diagnosis, treatment, or healthcare decisions.
    """

    @property
    def diseases(self) -> tuple[str, ...]:
        """All disease names (derived from DISEASE_CORRELATIONS)."""
        return tuple(DISEASE_CORRELATIONS.keys())

    @property
    def icd10_codes(self) -> tuple[str, ...]:
        """All ICD-10 codes (derived from DISEASE_CORRELATIONS)."""
        codes = {data["icd10"] for data in DISEASE_CORRELATIONS.values()}
        return tuple(sorted(codes))

    @property
    def symptoms(self) -> tuple[str, ...]:
        """All unique symptoms across all diseases (derived from DISEASE_CORRELATIONS)."""
        all_symptoms = set()
        for data in DISEASE_CORRELATIONS.values():
            all_symptoms.update(data["symptoms"])
        return tuple(sorted(all_symptoms))

    @property
    def generic_drugs(self) -> tuple[str, ...]:
        """All unique medications (derived from DISEASE_CORRELATIONS)."""
        all_meds = set()
        for data in DISEASE_CORRELATIONS.values():
            all_meds.update(data["medications"])
        return tuple(sorted(all_meds))

    medical_specialties: ElementsType[str] = MEDICAL_SPECIALTIES

    hospital_departments: ElementsType[str] = HOSPITAL_DEPARTMENTS

    brand_drugs: ElementsType[str] = BRAND_DRUGS

    blood_types: ElementsType[str] = BLOOD_TYPES

    allergies: ElementsType[str] = ALLERGIES

    medical_procedures: ElementsType[str] = MEDICAL_PROCEDURES

    insurance_plans: ElementsType[str] = INSURANCE_PLANS

    vital_signs: ElementsType[str] = VITAL_SIGNS

    def disease(self) -> str:
        """Return a random disease name."""
        return self.random_element(self.diseases)

    def icd10_code(self, disease: str | None = None) -> str:
        """Return an ICD-10 code.

        Args:
            disease: Optional disease name. If provided, returns the correct ICD-10 code for that disease.
                    If None, returns a random ICD-10 code.
        """
        if disease and disease in DISEASE_CORRELATIONS:
            return DISEASE_CORRELATIONS[disease]["icd10"]
        return self.random_element(self.icd10_codes)

    def medical_specialty(self) -> str:
        return self.random_element(self.medical_specialties)

    def hospital_department(self) -> str:
        return self.random_element(self.hospital_departments)

    def generic_drug(self) -> str:
        return self.random_element(self.generic_drugs)

    def brand_drug(self) -> str:
        return self.random_element(self.brand_drugs)

    def symptom(self, disease: str | None = None) -> str:
        """Return a symptom.

        Args:
            disease: Optional disease name. If provided, returns a symptom associated with that disease.
                    If None, returns a random symptom.
        """
        if disease and disease in DISEASE_CORRELATIONS:
            return self.random_element(DISEASE_CORRELATIONS[disease]["symptoms"])
        return self.random_element(self.symptoms)

    def disease_symptoms(self, disease: str, count: int = 3) -> list[str]:
        """Return multiple symptoms for a specific disease.

        Args:
            disease: Disease name to get symptoms for.
            count: Number of symptoms to return (1-5). Defaults to 3.
                  Will be capped at the number of available symptoms for the disease.

        Returns:
            List of symptom strings for the disease.

        Raises:
            ValueError: If disease is not found in correlations.
        """
        if disease not in DISEASE_CORRELATIONS:
            raise ValueError(f"Disease '{disease}' not found in disease correlations")

        disease_symptoms = DISEASE_CORRELATIONS[disease]["symptoms"]
        actual_count = min(count, len(disease_symptoms))
        return self.random_elements(disease_symptoms, length=actual_count, unique=True)

    def medication(self, disease: str | None = None) -> str:
        """Return a medication.

        Args:
            disease: Optional disease name. If provided, returns a medication for that disease.
                    If None, returns a random medication.
        """
        if disease and disease in DISEASE_CORRELATIONS:
            return self.random_element(DISEASE_CORRELATIONS[disease]["medications"])
        return self.random_element(self.generic_drugs)

    def medications(self, disease: str, count: int = 2) -> list[str]:
        """Return multiple medications for a specific disease.

        Args:
            disease: Disease name to get medications for.
            count: Number of medications to return. Defaults to 2.
                  Will be capped at the number of available medications for the disease.

        Returns:
            List of medication strings for the disease.

        Raises:
            ValueError: If disease is not found in correlations.
        """
        if disease not in DISEASE_CORRELATIONS:
            raise ValueError(f"Disease '{disease}' not found in disease correlations")

        disease_meds = DISEASE_CORRELATIONS[disease]["medications"]
        actual_count = min(count, len(disease_meds))
        return self.random_elements(disease_meds, length=actual_count, unique=True)

    def diseases_by_symptom(self, symptom: str) -> list[str]:
        """Return all diseases that have a specific symptom.

        Args:
            symptom: Symptom to search for.

        Returns:
            List of disease names that include this symptom.
        """
        return [disease_name for disease_name, data in DISEASE_CORRELATIONS.items() if symptom in data["symptoms"]]

    def patient_scenario(self, disease: str | None = None) -> dict[str, Any]:
        """Generate a complete patient scenario with correlated clinical data.

        Args:
            disease: Optional specific disease. If None, a random disease is selected.

        Returns:
            Dictionary containing:
                - disease: The disease name
                - icd10: The correct ICD-10 code
                - symptoms: List of 3-5 correlated symptoms
                - medications: List of 2-3 correlated medications
                - specialty: The primary medical specialty
        """
        if disease is None:
            disease = self.disease()
        elif disease not in DISEASE_CORRELATIONS:
            raise ValueError(f"Disease '{disease}' not found in diseases list")

        disease_data = DISEASE_CORRELATIONS[disease]
        num_symptoms = self.random_int(min=1, max=min(5, len(disease_data["symptoms"])))
        num_meds = self.random_int(min=2, max=min(3, len(disease_data["medications"])))

        return {
            "disease": disease,
            "icd10": disease_data["icd10"],
            "symptoms": self.disease_symptoms(disease, count=num_symptoms),
            "medications": self.medications(disease, count=num_meds),
            "specialty": disease_data["specialty"],
        }

    def blood_type(self) -> str:
        return self.random_element(self.blood_types)

    def allergy(self) -> str:
        return self.random_element(self.allergies)

    def medical_procedure(self) -> str:
        return self.random_element(self.medical_procedures)

    def insurance_plan(self) -> str:
        return self.random_element(self.insurance_plans)

    def vital_sign(self) -> str:
        return self.random_element(self.vital_signs)

    def diagnosis(self) -> str:
        """Return a diagnosis with correlated disease and ICD-10 code."""
        disease = self.disease()
        icd10 = self.icd10_code(disease=disease)
        return f"{disease} ({icd10})"
