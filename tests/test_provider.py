import re

import pytest
from conftest import load_brand_name_generator
from faker import Faker

from faker_healthcare import HealthcareProvider
from faker_healthcare.constants import BRAND_DRUG_NAMES


_generator = load_brand_name_generator()


@pytest.fixture
def faker() -> Faker:
    fake = Faker()
    fake.add_provider(HealthcareProvider)
    return fake


def _healthcare_provider(fake: Faker) -> HealthcareProvider:
    """Return the HealthcareProvider instance backing a Faker, for its derived pools."""
    return next(p for p in fake.providers if isinstance(p, HealthcareProvider))


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

    def test_intervention(self, faker: Faker) -> None:
        provider = _healthcare_provider(faker)
        for _ in range(100):
            result: str = faker.intervention()
            assert isinstance(result, str)
            assert result in provider.interventions

    def test_generic_drug_never_returns_an_intervention(self, faker: Faker) -> None:
        """The flat drug pool is what a consumer fills a medication column from."""
        provider = _healthcare_provider(faker)
        interventions = set(provider.interventions)
        assert interventions, "no interventions derived from the catalog"
        assert interventions.isdisjoint(provider.generic_drugs)
        for _ in range(200):
            assert faker.generic_drug() not in interventions

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


# Real products a screen of this catalogue has already rejected. Two of them are FDA
# veterinary products, which is how the first screen missed them: it covered human
# brands only. Kept as a literal here, separate from the generator's denylist, so that
# re-adding one is a test failure and not a silent regression.
_KNOWN_REAL_PRODUCT_COLLISIONS = (
    "Revalor",
    "Orbax",
    "Orbaex",
    "Lumemox",
    "Nuvizen",
    "Sonadex",
)


class TestBrandCatalogue:
    """The shipped catalogue is the guarantee, so every assertion iterates all of it.

    A sampled check would pass on a catalogue with one bad name in it, which is exactly
    the failure mode this replaced: the old brand_drug() screened each generated name
    against INN stems, kept the last attempt anyway when 12 tries all failed, and never
    screened for real product names at all.
    """

    def test_catalogue_is_non_empty_sorted_and_deduplicated(self) -> None:
        assert BRAND_DRUG_NAMES
        assert list(BRAND_DRUG_NAMES) == sorted(BRAND_DRUG_NAMES)
        assert len(set(BRAND_DRUG_NAMES)) == len(BRAND_DRUG_NAMES)

    def test_no_shipped_name_fails_any_screen(self) -> None:
        catalogue = _generator.catalogue_terms(_generator.LOCALES)
        offenders = {name: _generator.screen_latin(name, catalogue) for name in BRAND_DRUG_NAMES}
        assert {name: reasons for name, reasons in offenders.items() if reasons} == {}

    def test_no_shipped_name_ends_in_an_inn_stem(self) -> None:
        offenders = [name for name in BRAND_DRUG_NAMES if name.lower().endswith(_INN_STEMS)]
        assert offenders == []

    def test_no_shipped_name_is_a_famous_real_brand(self) -> None:
        offenders = [name for name in BRAND_DRUG_NAMES if name.lower() in _FAMOUS_REAL_BRANDS]
        assert offenders == []

    @pytest.mark.parametrize("product", _KNOWN_REAL_PRODUCT_COLLISIONS)
    def test_known_real_product_is_absent(self, product: str) -> None:
        assert product.lower() not in {name.lower() for name in BRAND_DRUG_NAMES}

    def test_every_shipped_name_matches_the_brand_pattern(self) -> None:
        offenders = [name for name in BRAND_DRUG_NAMES if not re.fullmatch(r"[A-Z][a-z]{4,13}", name)]
        assert offenders == []

    def test_every_shipped_name_is_reachable_from_the_morphemes(self) -> None:
        """The catalogue is a screened subset of the morpheme space, not a free list."""
        offenders = [name for name in BRAND_DRUG_NAMES if name not in set(_generator.latin_space())]
        assert offenders == []

    def test_generator_reproduces_the_committed_files(self) -> None:
        """Re-running the script must produce the committed files byte for byte."""
        assert _generator.main(["--check"]) == 0


class TestBrandGenerator:
    def test_brand_drug_only_returns_catalogue_names(self, faker: Faker) -> None:
        names = [faker.brand_drug() for _ in range(1000)]
        assert set(names) <= set(BRAND_DRUG_NAMES)

    def test_draws_cover_most_of_the_catalogue(self, faker: Faker) -> None:
        """A pool this size should be nearly exhausted in 1000 draws.

        The old test asserted 300+ distinct names, which only proved the *space* was
        big; it says nothing about safety, and a screened catalogue is deliberately
        smaller than the space. What matters now is that no part of the catalogue is
        unreachable, so this asserts coverage of the pool instead.
        """
        names = {faker.brand_drug() for _ in range(1000)}
        assert len(names) > 0.9 * len(BRAND_DRUG_NAMES)

    def test_reproducible_under_seed(self) -> None:
        first = Faker()
        first.add_provider(HealthcareProvider)
        first.seed_instance(4242)
        second = Faker()
        second.add_provider(HealthcareProvider)
        second.seed_instance(4242)
        assert [first.brand_drug() for _ in range(25)] == [second.brand_drug() for _ in range(25)]
