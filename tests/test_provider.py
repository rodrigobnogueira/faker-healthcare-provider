import re

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
            assert re.fullmatch(r"[A-Z][a-z]{4,13}", result), result

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


# Real brands kept ONLY here for collision QA — never shipped in the package.
_FAMOUS_REAL_BRANDS = {
    "lipitor",
    "prozac",
    "ozempic",
    "humira",
    "keytruda",
    "wegovy",
    "jardiance",
    "eliquis",
    "xanax",
    "zoloft",
    "mounjaro",
    "norvasc",
    "synthroid",
    "glucophage",
    "prilosec",
    "zocor",
    "plavix",
    "skyrizi",
    "entyvio",
    "taltz",
    "cosentyx",
    "dupixent",
    "xolair",
    "ventolin",
    "advil",
    "tylenol",
    "augmentin",
    "nexium",
    "lantus",
    "januvia",
}

# WHO INN class stems a generated brand must never end with.
_INN_STEMS = (
    "mab",
    "nib",
    "pril",
    "sartan",
    "statin",
    "vir",
    "prazole",
    "dipine",
    "olol",
    "cillin",
    "mycin",
    "gliptin",
    "floxacin",
    "caine",
    "profen",
    "parin",
)


class TestBrandGenerator:
    def test_pattern_uniqueness_and_no_real_brands(self, faker: Faker) -> None:
        names = [faker.brand_drug() for _ in range(1000)]
        for name in names:
            assert re.fullmatch(r"[A-Z][a-z]{4,13}", name), name
            assert name.lower() not in _FAMOUS_REAL_BRANDS
            assert not any(name.lower().endswith(stem) for stem in _INN_STEMS), name
        assert len(set(names)) > 300

    def test_reproducible_under_seed(self) -> None:
        first = Faker()
        first.add_provider(HealthcareProvider)
        first.seed_instance(4242)
        second = Faker()
        second.add_provider(HealthcareProvider)
        second.seed_instance(4242)
        assert [first.brand_drug() for _ in range(25)] == [second.brand_drug() for _ in range(25)]
