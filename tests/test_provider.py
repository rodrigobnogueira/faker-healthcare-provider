import pytest
from faker import Faker

from faker_healthcare import HealthcareProvider


@pytest.fixture
def faker() -> Faker:
    fake = Faker()
    fake.add_provider(HealthcareProvider)
    return fake


class TestHealthcareProvider:
    def test_disease(self, faker: Faker) -> None:
        for _ in range(100):
            result: str = faker.disease()
            assert isinstance(result, str)
            assert len(result) > 0

    def test_icd10_code(self, faker: Faker) -> None:
        for _ in range(100):
            result: str = faker.icd10_code()
            assert isinstance(result, str)
            assert len(result) > 0

    def test_disease_medical_specialty(self, faker: Faker) -> None:
        for _ in range(100):
            result: str = faker.disease_medical_specialty()
            assert isinstance(result, str)
            assert len(result) > 0

    def test_hospital_department(self, faker: Faker) -> None:
        for _ in range(100):
            result: str = faker.hospital_department()
            assert isinstance(result, str)
            assert result in HealthcareProvider.hospital_departments

    def test_generic_drug(self, faker: Faker) -> None:
        for _ in range(100):
            result: str = faker.generic_drug()
            assert isinstance(result, str)
            assert len(result) > 0

    def test_brand_drug(self, faker: Faker) -> None:
        for _ in range(100):
            result: str = faker.brand_drug()
            assert isinstance(result, str)
            assert result in HealthcareProvider.brand_drugs

    def test_symptom(self, faker: Faker) -> None:
        for _ in range(100):
            result: str = faker.symptom()
            assert isinstance(result, str)
            assert len(result) > 0

    def test_blood_type(self, faker: Faker) -> None:
        for _ in range(100):
            result: str = faker.blood_type()
            assert isinstance(result, str)
            assert result in HealthcareProvider.blood_types

    def test_allergy(self, faker: Faker) -> None:
        for _ in range(100):
            result: str = faker.allergy()
            assert isinstance(result, str)
            assert result in HealthcareProvider.allergies

    def test_medical_procedure(self, faker: Faker) -> None:
        for _ in range(100):
            result: str = faker.medical_procedure()
            assert isinstance(result, str)
            assert result in HealthcareProvider.medical_procedures

    def test_insurance_plan(self, faker: Faker) -> None:
        for _ in range(100):
            result: str = faker.insurance_plan()
            assert isinstance(result, str)
            assert result in HealthcareProvider.insurance_plans

    def test_vital_sign(self, faker: Faker) -> None:
        for _ in range(100):
            result: str = faker.vital_sign()
            assert isinstance(result, str)
            assert result in HealthcareProvider.vital_signs

    def test_diagnosis(self, faker: Faker) -> None:
        for _ in range(100):
            result: str = faker.diagnosis()
            assert isinstance(result, str)
            assert "(" in result
            assert ")" in result
