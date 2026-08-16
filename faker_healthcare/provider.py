from typing import TypedDict

from faker.providers import BaseProvider, ElementsType

from .constants import (
    ALLERGIES,
    BLOOD_TYPES,
    BRAND_FORBIDDEN_ENDINGS,
    BRAND_INFIXES,
    BRAND_PREFIXES,
    BRAND_SUFFIXES,
    HOSPITAL_DEPARTMENTS,
    INSURANCE_PLANS,
    MEDICAL_PROCEDURES,
    NON_DRUG_INTERVENTIONS,
    VITAL_SIGNS,
)
from .types import DiseaseData


class PatientScenario(TypedDict):
    disease: str
    icd10: str
    symptoms: list[str]
    medications: list[str]
    medical_specialty: str


class HealthcareProvider(BaseProvider):
    """Faker provider for generating healthcare/medical fake data.

    This provider generates correlated clinical data based on medical relationships
    between diseases, symptoms, medications, and ICD-10 codes.

    MEDICAL DISCLAIMER: This data is for TESTING AND DEVELOPMENT PURPOSES ONLY.
    It should NOT be used for actual medical diagnosis, treatment, or healthcare decisions.
    """

    _disease_correlations: dict[str, DiseaseData] | None = None

    @property
    def disease_correlations(self) -> dict[str, DiseaseData]:
        """Lazy-loaded disease correlations data (locale-specific)."""
        if self._disease_correlations is None:
            self._disease_correlations = self._load_disease_correlations()
        return self._disease_correlations

    def _load_disease_correlations(self) -> dict[str, DiseaseData]:
        """Load disease correlations. Override in locale providers."""
        from .disease_correlations import DISEASE_CORRELATIONS

        return DISEASE_CORRELATIONS

    @property
    def diseases(self) -> tuple[str, ...]:
        """All disease names (derived from DISEASE_CORRELATIONS)."""
        return tuple(self.disease_correlations.keys())

    @property
    def icd10_codes(self) -> tuple[str, ...]:
        """All ICD-10 codes (derived from DISEASE_CORRELATIONS)."""
        codes = {data["icd10"] for data in self.disease_correlations.values()}
        return tuple(sorted(codes))

    @property
    def symptoms(self) -> tuple[str, ...]:
        """All unique symptoms across all diseases (derived from DISEASE_CORRELATIONS)."""
        all_symptoms: set[str] = set()
        for data in self.disease_correlations.values():
            all_symptoms.update(data["symptoms"])
        return tuple(sorted(all_symptoms))

    @property
    def generic_drugs(self) -> tuple[str, ...]:
        """All unique drugs (derived from DISEASE_CORRELATIONS).

        Non-drug interventions (surgery, devices, diets) are excluded: they belong in a
        condition's treatment list but not in the flat pool a consumer draws a medication
        column from. They are available separately via `interventions`.
        """
        interventions = set(self.non_drug_interventions)
        all_meds: set[str] = set()
        for data in self.disease_correlations.values():
            all_meds.update(data["medications"])
        return tuple(sorted(all_meds - interventions))

    @property
    def interventions(self) -> tuple[str, ...]:
        """All non-drug interventions this locale's catalog actually prescribes.

        Derived from DISEASE_CORRELATIONS by intersecting it with
        `non_drug_interventions`, so a declared intervention that no condition uses
        never shows up here.
        """
        declared = set(self.non_drug_interventions)
        present: set[str] = set()
        for data in self.disease_correlations.values():
            present.update(med for med in data["medications"] if med in declared)
        return tuple(sorted(present))

    @property
    def medical_specialties(self) -> tuple[str, ...]:
        """All unique medical specialties (derived from DISEASE_CORRELATIONS)."""
        specialties = {data["medical_specialty"] for data in self.disease_correlations.values()}
        return tuple(sorted(specialties))

    hospital_departments: ElementsType[str] = HOSPITAL_DEPARTMENTS

    blood_types: ElementsType[str] = BLOOD_TYPES

    allergies: ElementsType[str] = ALLERGIES

    medical_procedures: ElementsType[str] = MEDICAL_PROCEDURES

    insurance_plans: ElementsType[str] = INSURANCE_PLANS

    vital_signs: ElementsType[str] = VITAL_SIGNS

    non_drug_interventions: ElementsType[str] = NON_DRUG_INTERVENTIONS

    def disease(self) -> str:
        """Return a random disease name."""
        return self.random_element(self.diseases)

    def icd10_code(self, disease: str | None = None) -> str:
        """Return an ICD-10 code.

        Args:
            disease: Optional disease name. If provided, returns the correct ICD-10 code for that disease.
                    If None, returns a random ICD-10 code.

        Raises:
            ValueError: If disease is given but not found in correlations.
        """
        if disease is None:
            return self.random_element(self.icd10_codes)
        if disease not in self.disease_correlations:
            raise ValueError(f"Disease '{disease}' not found in disease correlations")
        return self.disease_correlations[disease]["icd10"]

    def disease_medical_specialty(self) -> str:
        return self.random_element(self.medical_specialties)

    def hospital_department(self) -> str:
        return self.random_element(self.hospital_departments)

    def generic_drug(self) -> str:
        """Return a random generic drug name (never a non-drug intervention)."""
        return self.random_element(self.generic_drugs)

    def intervention(self) -> str:
        """Return a random non-drug intervention (a procedure, device, or lifestyle measure)."""
        return self.random_element(self.interventions)

    def brand_drug(self) -> str:
        """Return a fictitious brand-style drug name.

        The name is generated from invented morphemes (never a real trademark)
        and deliberately avoids WHO INN stems, so it cannot be mistaken for a
        generic substance name. Any resemblance to a real brand is coincidental.
        """
        name = ""
        for _ in range(12):
            parts = [self.random_element(BRAND_PREFIXES)]
            if self.generator.random.random() < 0.4:
                parts.append(self.random_element(BRAND_INFIXES))
            parts.append(self.random_element(BRAND_SUFFIXES))
            name = "".join(parts)
            if not name.lower().endswith(BRAND_FORBIDDEN_ENDINGS):
                break
        return name

    def symptom(self, disease: str | None = None) -> str:
        """Return a symptom.

        Args:
            disease: Optional disease name. If provided, returns a symptom associated with that disease.
                    If None, returns a random symptom.

        Raises:
            ValueError: If disease is given but not found in correlations.
        """
        if disease is None:
            return self.random_element(self.symptoms)
        if disease not in self.disease_correlations:
            raise ValueError(f"Disease '{disease}' not found in disease correlations")
        return self.random_element(self.disease_correlations[disease]["symptoms"])

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
        if disease not in self.disease_correlations:
            raise ValueError(f"Disease '{disease}' not found in disease correlations")

        disease_symptoms = self.disease_correlations[disease]["symptoms"]
        actual_count = min(count, len(disease_symptoms))
        return list(self.random_elements(disease_symptoms, length=actual_count, unique=True))

    def medication(self, disease: str | None = None) -> str:
        """Return a medication.

        Args:
            disease: Optional disease name. If provided, returns a treatment for that disease,
                    which may be a non-drug intervention if the condition prescribes one.
                    If None, returns a random drug (never a non-drug intervention).

        Raises:
            ValueError: If disease is given but not found in correlations.
        """
        if disease is None:
            return self.random_element(self.generic_drugs)
        if disease not in self.disease_correlations:
            raise ValueError(f"Disease '{disease}' not found in disease correlations")
        return self.random_element(self.disease_correlations[disease]["medications"])

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
        if disease not in self.disease_correlations:
            raise ValueError(f"Disease '{disease}' not found in disease correlations")

        disease_meds = self.disease_correlations[disease]["medications"]
        actual_count = min(count, len(disease_meds))
        return list(self.random_elements(disease_meds, length=actual_count, unique=True))

    def diseases_by_symptom(self, symptom: str) -> list[str]:
        """Return all diseases that have a specific symptom.

        Args:
            symptom: Symptom to search for.

        Returns:
            List of disease names that include this symptom.
        """
        return [disease_name for disease_name, data in self.disease_correlations.items() if symptom in data["symptoms"]]

    def patient_scenario(self, disease: str | None = None) -> PatientScenario:
        """Generate a complete patient scenario with correlated clinical data.

        Args:
            disease: Optional specific disease. If None, a random disease is selected.

        Returns:
            Dictionary containing:
                - disease: The disease name
                - icd10: The correct ICD-10 code
                - symptoms: List of 3-5 correlated symptoms (fewer only if the condition has fewer)
                - medications: List of 2-3 correlated medications (fewer only if the condition has fewer)
                - medical_specialty: The primary medical specialty

        Raises:
            ValueError: If disease is given but not found in correlations.
        """
        if disease is None:
            disease = self.disease()
        elif disease not in self.disease_correlations:
            raise ValueError(f"Disease '{disease}' not found in diseases list")

        disease_data = self.disease_correlations[disease]
        # Both ranges are clamped to what the condition actually has, so a condition with
        # fewer than three symptoms or a single medication cannot produce an empty randrange.
        available_symptoms = len(disease_data["symptoms"])
        available_meds = len(disease_data["medications"])
        num_symptoms = self.random_int(min=min(3, available_symptoms), max=min(5, available_symptoms))
        num_meds = self.random_int(min=min(2, available_meds), max=min(3, available_meds))

        return {
            "disease": disease,
            "icd10": disease_data["icd10"],
            "symptoms": self.disease_symptoms(disease, count=num_symptoms),
            "medications": self.medications(disease, count=num_meds),
            "medical_specialty": disease_data["medical_specialty"],
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
