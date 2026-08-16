"""Tests for correlated clinical data generation."""

import re
from collections.abc import Callable

import pytest
from faker import Faker

from faker_healthcare import HealthcareProvider
from faker_healthcare.disease_correlations import DISEASE_CORRELATIONS


# ICD-10 codes follow a letter + two digits, optionally a dot and 1-3 more chars (e.g. E11.9, I10, C50.919).
ICD10_PATTERN = re.compile(r"^[A-Z]\d{2}(\.\d{1,3})?$")

# Conditions added in 2.2.0, keyed by their (universal) ICD-10 code.
NEW_CONDITIONS_2_2_0 = {
    "Shingles": "B02.9",
    "Cellulitis": "L03.90",
    "Lyme Disease": "A69.20",
    "Dengue Fever": "A90",
    "Infectious Mononucleosis": "B27.90",
    "Viral Gastroenteritis": "A08.4",
    "Nonalcoholic Fatty Liver Disease": "K76.0",
    "Carpal Tunnel Syndrome": "G56.00",
}


@pytest.fixture
def faker() -> Faker:
    fake = Faker()
    fake.add_provider(HealthcareProvider)
    return fake


class TestCorrelatedData:
    """Tests for correlated clinical data generation methods."""

    def test_icd10_code_with_disease(self, faker: Faker) -> None:
        """Test that icd10_code returns correct code for a specific disease."""
        disease = "Pneumonia"
        result = faker.icd10_code(disease=disease)
        assert result == DISEASE_CORRELATIONS[disease]["icd10"]

    def test_symptom_with_disease(self, faker: Faker) -> None:
        """Test that symptom returns a symptom from the disease's symptom list."""
        disease = "Type 2 Diabetes"
        result = faker.symptom(disease=disease)
        assert result in DISEASE_CORRELATIONS[disease]["symptoms"]

    def test_disease_symptoms(self, faker: Faker) -> None:
        """Test that disease_symptoms returns multiple symptoms for a disease."""
        disease = "Asthma"
        result = faker.disease_symptoms(disease, count=3)
        assert isinstance(result, list)
        assert len(result) == 3
        for symptom in result:
            assert symptom in DISEASE_CORRELATIONS[disease]["symptoms"]

    def test_medication_with_disease(self, faker: Faker) -> None:
        """Test that medication returns a medication from the disease's medication list."""
        disease = "Essential Hypertension"
        result = faker.medication(disease=disease)
        assert result in DISEASE_CORRELATIONS[disease]["medications"]

    def test_medications(self, faker: Faker) -> None:
        """Test that medications returns multiple medications for a disease."""
        disease = "Depression"
        result = faker.medications(disease, count=2)
        assert isinstance(result, list)
        assert len(result) == 2
        for medication in result:
            assert medication in DISEASE_CORRELATIONS[disease]["medications"]

    def test_diseases_by_symptom(self, faker: Faker) -> None:
        """Test that diseases_by_symptom returns diseases with a specific symptom."""
        symptom = "Fever"
        result = faker.diseases_by_symptom(symptom)
        assert isinstance(result, list)
        assert len(result) > 0
        # Verify all returned diseases actually have the symptom
        for disease in result:
            assert symptom in DISEASE_CORRELATIONS[disease]["symptoms"]

    def test_patient_scenario_random(self, faker: Faker) -> None:
        """Test generating a random patient scenario."""
        result = faker.patient_scenario()
        assert isinstance(result, dict)
        assert "disease" in result
        assert "icd10" in result
        assert "symptoms" in result
        assert "medications" in result
        assert "medical_specialty" in result

        disease = result["disease"]
        assert result["icd10"] == DISEASE_CORRELATIONS[disease]["icd10"]
        assert result["medical_specialty"] == DISEASE_CORRELATIONS[disease]["medical_specialty"]
        assert all(s in DISEASE_CORRELATIONS[disease]["symptoms"] for s in result["symptoms"])
        assert all(m in DISEASE_CORRELATIONS[disease]["medications"] for m in result["medications"])

    def test_patient_scenario_specific_disease(self, faker: Faker) -> None:
        """Test generating a patient scenario for a specific disease."""
        disease = "COVID-19"
        result = faker.patient_scenario(disease=disease)
        assert result["disease"] == disease
        assert result["icd10"] == DISEASE_CORRELATIONS[disease]["icd10"]
        assert result["medical_specialty"] == DISEASE_CORRELATIONS[disease]["medical_specialty"]

    def test_diagnosis_correlated(self, faker: Faker) -> None:
        """Test that diagnosis returns correctly correlated disease and ICD-10 code."""
        for _ in range(10):
            result = faker.diagnosis()
            # Extract disease and code
            assert "(" in result and ")" in result
            parts = result.split(" (")
            disease = parts[0]
            code = parts[1].rstrip(")")

            # Verify they're correlated
            if disease in DISEASE_CORRELATIONS:
                assert code == DISEASE_CORRELATIONS[disease]["icd10"]


class TestBackwardCompatibility:
    """Tests to ensure backward compatibility with existing API."""

    def test_disease_no_param_works(self, faker: Faker) -> None:
        """Test that disease() with no parameters still works."""
        result = faker.disease()
        assert isinstance(result, str)
        assert len(result) > 0

    def test_icd10_code_no_param_works(self, faker: Faker) -> None:
        """Test that icd10_code() with no parameters still works."""
        result = faker.icd10_code()
        assert isinstance(result, str)
        assert len(result) > 0

    def test_symptom_no_param_works(self, faker: Faker) -> None:
        """Test that symptom() with no parameters still works."""
        result = faker.symptom()
        assert isinstance(result, str)
        assert len(result) > 0

    def test_medication_no_param_works(self, faker: Faker) -> None:
        """Test that medication() with no parameters still works."""
        result = faker.medication()
        assert isinstance(result, str)
        assert len(result) > 0


class TestUnknownDiseaseRaises:
    """Every accessor that takes a disease must reject an unknown one.

    Falling back to an uncorrelated random draw is worse than failing: the caller
    asked for data about a specific condition and would silently get data about
    some other one.
    """

    ACCESSORS: dict[str, Callable[[Faker, str], object]] = {
        "icd10_code": lambda f, d: f.icd10_code(disease=d),
        "symptom": lambda f, d: f.symptom(disease=d),
        "medication": lambda f, d: f.medication(disease=d),
        "disease_symptoms": lambda f, d: f.disease_symptoms(d),
        "medications": lambda f, d: f.medications(d),
        "patient_scenario": lambda f, d: f.patient_scenario(disease=d),
    }

    @pytest.mark.parametrize("name", sorted(ACCESSORS))
    def test_unknown_disease_raises(self, faker: Faker, name: str) -> None:
        with pytest.raises(ValueError, match="Not A Disease"):
            self.ACCESSORS[name](faker, "Not A Disease")

    @pytest.mark.parametrize("name", sorted(ACCESSORS))
    def test_known_disease_still_works(self, faker: Faker, name: str) -> None:
        assert self.ACCESSORS[name](faker, "Type 2 Diabetes")


class TestDataIntegrity:
    """Tests to ensure data structure integrity."""

    def test_all_diseases_have_required_fields(self) -> None:
        """Test that all diseases in DISEASE_CORRELATIONS have required fields."""
        required_fields = ["icd10", "symptoms", "medications", "medical_specialty"]
        for disease, data in DISEASE_CORRELATIONS.items():
            for field in required_fields:
                assert field in data, f"Disease '{disease}' missing field '{field}'"

    def test_all_diseases_have_symptoms(self) -> None:
        """Test that all diseases have at least one symptom."""
        for disease, data in DISEASE_CORRELATIONS.items():
            assert len(data["symptoms"]) >= 1, f"Disease '{disease}' has no symptoms"

    def test_all_diseases_have_medications(self) -> None:
        """Test that all diseases have at least one medication."""
        for disease, data in DISEASE_CORRELATIONS.items():
            assert len(data["medications"]) >= 1, f"Disease '{disease}' has no medications"

    def test_all_icd10_codes_well_formed(self) -> None:
        """Test that every ICD-10 code matches the expected WHO ICD-10 format."""
        for disease, data in DISEASE_CORRELATIONS.items():
            assert ICD10_PATTERN.match(data["icd10"]), f"Disease '{disease}' has malformed ICD-10 code '{data['icd10']}'"


class TestNewConditions:
    """Tests for the conditions added in 2.2.0."""

    def test_new_conditions_present_with_correct_codes(self) -> None:
        """Each new condition is registered with its verified ICD-10 code."""
        for disease, icd10 in NEW_CONDITIONS_2_2_0.items():
            assert disease in DISEASE_CORRELATIONS, f"New condition '{disease}' missing from correlations"
            assert DISEASE_CORRELATIONS[disease]["icd10"] == icd10, f"'{disease}' has unexpected ICD-10 code"

    @pytest.mark.parametrize("disease", sorted(NEW_CONDITIONS_2_2_0))
    def test_new_condition_patient_scenario_is_correlated(self, faker: Faker, disease: str) -> None:
        """patient_scenario for each new condition returns internally consistent, correlated data."""
        scenario = faker.patient_scenario(disease=disease)
        data = DISEASE_CORRELATIONS[disease]
        assert scenario["disease"] == disease
        assert scenario["icd10"] == data["icd10"]
        assert scenario["medical_specialty"] == data["medical_specialty"]
        assert scenario["symptoms"], f"'{disease}' scenario produced no symptoms"
        assert scenario["medications"], f"'{disease}' scenario produced no medications"
        assert all(s in data["symptoms"] for s in scenario["symptoms"])
        assert all(m in data["medications"] for m in scenario["medications"])
