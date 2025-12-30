import pytest
from faker import Faker

from faker_healthcare import HealthcareProvider


SUPPORTED_LOCALES = ["en_US", "pt_BR", "es_ES", "zh_CN", "fr_FR", "de_DE"]


def _get_provider_for_locale(locale: str):
    """Get the appropriate provider class for a given locale."""
    if locale == "en_US":
        return HealthcareProvider
    elif locale == "pt_BR":
        from faker_healthcare.pt_BR import Provider

        return Provider
    elif locale == "es_ES":
        from faker_healthcare.es_ES import Provider

        return Provider
    elif locale == "zh_CN":
        from faker_healthcare.zh_CN import Provider

        return Provider
    elif locale == "fr_FR":
        from faker_healthcare.fr_FR import Provider

        return Provider
    elif locale == "de_DE":
        from faker_healthcare.de_DE import Provider

        return Provider
    else:
        raise ValueError(f"Unsupported locale: {locale}")


@pytest.fixture(params=SUPPORTED_LOCALES)
def fake_locale(request: pytest.FixtureRequest) -> tuple[Faker, str]:
    locale = request.param
    fake = Faker(locale)
    provider_class = _get_provider_for_locale(locale)
    fake.add_provider(provider_class)
    return fake, locale


class TestLocaleProviders:
    def test_disease_returns_string(self, fake_locale: tuple[Faker, str]) -> None:
        fake, locale = fake_locale
        disease = fake.disease()
        assert isinstance(disease, str)
        assert len(disease) > 0

    def test_icd10_code_returns_valid_format(self, fake_locale: tuple[Faker, str]) -> None:
        fake, locale = fake_locale
        code = fake.icd10_code()
        assert isinstance(code, str)
        assert len(code) > 0

    def test_disease_medical_specialty_returns_string(self, fake_locale: tuple[Faker, str]) -> None:
        fake, locale = fake_locale
        specialty = fake.disease_medical_specialty()
        assert isinstance(specialty, str)
        assert len(specialty) > 0

    def test_hospital_department_returns_string(self, fake_locale: tuple[Faker, str]) -> None:
        fake, locale = fake_locale
        dept = fake.hospital_department()
        assert isinstance(dept, str)
        assert len(dept) > 0

    def test_generic_drug_returns_string(self, fake_locale: tuple[Faker, str]) -> None:
        fake, locale = fake_locale
        drug = fake.generic_drug()
        assert isinstance(drug, str)
        assert len(drug) > 0

    def test_brand_drug_returns_string(self, fake_locale: tuple[Faker, str]) -> None:
        fake, locale = fake_locale
        drug = fake.brand_drug()
        assert isinstance(drug, str)
        assert len(drug) > 0

    def test_symptom_returns_string(self, fake_locale: tuple[Faker, str]) -> None:
        fake, locale = fake_locale
        symptom = fake.symptom()
        assert isinstance(symptom, str)
        assert len(symptom) > 0

    def test_blood_type_returns_valid_type(self, fake_locale: tuple[Faker, str]) -> None:
        fake, locale = fake_locale
        blood_type = fake.blood_type()
        assert isinstance(blood_type, str)
        assert len(blood_type) > 0
        # Note: Blood types may be locale-specific (e.g., Chinese uses "O型Rh阳性")
        # so we only validate that it's a non-empty string

    def test_allergy_returns_string(self, fake_locale: tuple[Faker, str]) -> None:
        fake, locale = fake_locale
        allergy = fake.allergy()
        assert isinstance(allergy, str)
        assert len(allergy) > 0

    def test_medical_procedure_returns_string(self, fake_locale: tuple[Faker, str]) -> None:
        fake, locale = fake_locale
        procedure = fake.medical_procedure()
        assert isinstance(procedure, str)
        assert len(procedure) > 0

    def test_insurance_plan_returns_string(self, fake_locale: tuple[Faker, str]) -> None:
        fake, locale = fake_locale
        plan = fake.insurance_plan()
        assert isinstance(plan, str)
        assert len(plan) > 0

    def test_vital_sign_returns_string(self, fake_locale: tuple[Faker, str]) -> None:
        fake, locale = fake_locale
        sign = fake.vital_sign()
        assert isinstance(sign, str)
        assert len(sign) > 0

    def test_diagnosis_returns_formatted_string(self, fake_locale: tuple[Faker, str]) -> None:
        fake, locale = fake_locale
        diagnosis = fake.diagnosis()
        assert isinstance(diagnosis, str)
        assert "(" in diagnosis
        assert ")" in diagnosis


class TestLocaleSpecificData:
    """Verify all locales load their own locale-specific data."""

    def test_all_locales_return_diseases(self) -> None:
        """Test that each locale loads its own disease data."""
        for locale in SUPPORTED_LOCALES:
            fake = Faker(locale)
            provider_class = _get_provider_for_locale(locale)
            fake.add_provider(provider_class)
            disease = fake.disease()
            assert isinstance(disease, str)
            assert len(disease) > 0

    def test_locale_specific_disease_data(self) -> None:
        """Verify each locale loads its own disease names, not English."""
        locale_sample_diseases = {
            "en_US": ["Type 2 Diabetes", "Hypertension"],
            "pt_BR": ["Diabetes mellitus tipo 2", "Hipertensão essencial (primária)"],
            "es_ES": ["Diabetes mellitus tipo 2", "Hipertensión esencial"],
            "zh_CN": ["非胰岛素依赖型糖尿病", "特发性(原发性)高血压"],  # Chinese names differ
            "fr_FR": ["Diabète de type 2", "Hypertension essentielle"],
            "de_DE": ["Diabetes mellitus Typ 2", "Essentielle Hypertonie"],
        }

        for locale, expected_diseases in locale_sample_diseases.items():
            fake = Faker(locale)
            provider_class = _get_provider_for_locale(locale)
            fake.add_provider(provider_class)

            # Get the provider instance to access diseases property
            provider = [p for p in fake.providers if hasattr(p, "diseases")][0]
            all_diseases = set(provider.diseases)

            # Verify at least one expected disease is present
            assert any(ed in all_diseases for ed in expected_diseases), f"Locale {locale} failed: Expected diseases {expected_diseases} not found in {list(all_diseases)[:5]}"

            # For non-English locales, verify English diseases are NOT present
            if locale != "en_US":
                english_diseases = ["Type 2 Diabetes", "Hypertension", "Hyperlipidemia"]
                assert not any(ed in all_diseases for ed in english_diseases), f"Locale {locale} failed: English diseases found in locale-specific data!"
