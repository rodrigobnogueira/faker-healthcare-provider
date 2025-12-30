"""Tests for correlated clinical data generation."""

import pytest
from faker import Faker

from faker_healthcare import HealthcareProvider
from faker_healthcare.disease_correlations import DISEASE_CORRELATIONS


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
