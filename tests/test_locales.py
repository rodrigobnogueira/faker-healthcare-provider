import importlib
import re
from collections import Counter, defaultdict
from pathlib import Path
from types import ModuleType

import pytest
from conftest import load_brand_name_generator
from faker import Faker

from faker_healthcare import HealthcareProvider
from faker_healthcare.clinical_values import (
    ALCOHOL_CATEGORY_THRESHOLDS,
    ALCOHOL_HIGHEST_CATEGORY,
    FLAG_LABEL_KEYS,
    LAB_DEFINITIONS,
    VITAL_DEFINITIONS,
)


SUPPORTED_LOCALES = ["en_US", "pt_BR", "es_ES", "zh_CN", "fr_FR", "de_DE"]
NON_ENGLISH_LOCALES = [locale for locale in SUPPORTED_LOCALES if locale != "en_US"]

# ICD-10 codes are universal, so they are the reliable way to check that a condition
# exists in every locale regardless of how its name is translated.
NEW_CONDITION_ICD10_CODES = {"B02.9", "L03.90", "A69.20", "A90", "B27.90", "A08.4", "K76.0", "G56.00"}

# Constants that are the same catalog in every language and must therefore hold the same
# number of entries everywhere. A locale that is short an entry can never generate it.
SHARED_CONSTANTS = [
    "HOSPITAL_DEPARTMENTS",
    "BLOOD_TYPES",
    "ALLERGIES",
    "MEDICAL_PROCEDURES",
    "VITAL_SIGNS",
    "NON_DRUG_INTERVENTIONS",
]

# INSURANCE_PLANS is deliberately country-specific — US plan types, Brazilian plan
# structures, Spanish mutualidades, German GKV/PKV funds — so its size legitimately
# differs per locale and it is EXEMPT from cardinality parity by design.
LOCALE_SPECIFIC_CONSTANTS = ["INSURANCE_PLANS"]

# The brand-name catalogue is shared, not translated: locale providers inherit
# brand_drug() from the base, so it and the morphemes it was screened out of live only
# in the base constants module (zh_CN adds ZH_BRAND_CHARS and ZH_BRAND_NAMES on top).
BASE_ONLY_CONSTANTS = [
    "BRAND_DRUG_NAMES",
    "BRAND_PREFIXES",
    "BRAND_INFIXES",
    "BRAND_SUFFIXES",
    "BRAND_FORBIDDEN_ENDINGS",
]

# Hiragana and katakana. Simplified Chinese data must contain neither; a katakana drug
# name (リオチロニン) shipped in zh_CN for several releases.
JAPANESE_KANA_RE = re.compile(r"[぀-ヿ]")


def _load_correlations(locale: str) -> dict:
    """Load the DISEASE_CORRELATIONS mapping for a given locale."""
    if locale == "en_US":
        module = importlib.import_module("faker_healthcare.disease_correlations")
    else:
        module = importlib.import_module(f"faker_healthcare.{locale}.disease_correlations")
    return module.DISEASE_CORRELATIONS


def _load_constants(locale: str) -> ModuleType:
    """Load the constants module for a given locale."""
    if locale == "en_US":
        return importlib.import_module("faker_healthcare.constants")
    return importlib.import_module(f"faker_healthcare.{locale}.constants")


def _load_clinical_labels(locale: str) -> dict[str, str]:
    """Load the clinical display labels for a given locale."""
    if locale == "en_US":
        module = importlib.import_module("faker_healthcare.clinical_labels")
    else:
        module = importlib.import_module(f"faker_healthcare.{locale}.clinical_labels")
    labels: dict[str, str] = module.CLINICAL_LABELS
    return labels


def _disease_named_by_code(locale: str, code: str) -> str:
    """Return this locale's own name for the condition carrying an ICD-10 code."""
    return next(name for name, data in _load_correlations(locale).items() if data["icd10"] == code)


def _icd10_counter(locale: str) -> Counter:
    """Multiset of ICD-10 codes; a multiset, because two conditions may share a code."""
    return Counter(data["icd10"] for data in _load_correlations(locale).values())


def _length_profile(locale: str) -> dict[str, list[tuple[int, int]]]:
    """Per ICD-10 code, the sorted (symptom count, medication count) pairs of its conditions.

    Keyed by code rather than by position, so the catalogs may legitimately be ordered
    differently, and grouped, because two conditions may share one code.
    """
    profile: defaultdict[str, list[tuple[int, int]]] = defaultdict(list)
    for data in _load_correlations(locale).values():
        profile[data["icd10"]].append((len(data["symptoms"]), len(data["medications"])))
    return {code: sorted(pairs) for code, pairs in profile.items()}


def _healthcare_provider(fake: Faker) -> HealthcareProvider:
    """Return the HealthcareProvider instance backing a Faker, for its derived pools."""
    return next(p for p in fake.providers if isinstance(p, HealthcareProvider))


def _get_provider_for_locale(locale: str) -> type[HealthcareProvider]:
    """Get the appropriate provider class for a given locale."""
    if locale == "en_US":
        return HealthcareProvider
    if locale not in SUPPORTED_LOCALES:
        raise ValueError(f"Unsupported locale: {locale}")
    # Imported lazily, one locale at a time, so the test never pulls every
    # locale package into sys.modules at import time.
    module = importlib.import_module(f"faker_healthcare.{locale}")
    return module.Provider


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

    def test_zh_brand_drug_has_chinese_latin_shape(self) -> None:
        from faker_healthcare.zh_CN import Provider

        fake = Faker("zh_CN")
        fake.add_provider(Provider)
        for _ in range(50):
            drug = fake.brand_drug()
            assert re.fullmatch(r"[一-鿿]{2,3} \([A-Z][a-z]{4,13}\)", drug), drug

    def test_zh_brand_drug_draws_only_from_the_screened_lists(self) -> None:
        """Both halves must come from a shipped list, not be composed at runtime.

        The zh_CN override used to pick 2-3 characters out of ZH_BRAND_CHARS on every
        call, which is 30,752 identifiers nobody could screen. It now draws the Chinese
        half from ZH_BRAND_NAMES and the Latin half from the base catalogue.
        """
        from faker_healthcare.constants import BRAND_DRUG_NAMES
        from faker_healthcare.zh_CN import Provider
        from faker_healthcare.zh_CN.constants import ZH_BRAND_NAMES

        fake = Faker("zh_CN")
        fake.add_provider(Provider)
        for _ in range(500):
            chinese, latin = fake.brand_drug().split(" ", 1)
            assert chinese in ZH_BRAND_NAMES, chinese
            assert latin.strip("()") in BRAND_DRUG_NAMES, latin

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

    def test_intervention_returns_string(self, fake_locale: tuple[Faker, str]) -> None:
        fake, locale = fake_locale
        intervention = fake.intervention()
        assert isinstance(intervention, str)
        assert len(intervention) > 0

    def test_drug_pool_and_intervention_pool_are_disjoint(self, fake_locale: tuple[Faker, str]) -> None:
        """generic_drug() must never return a procedure, device, or diet in any locale."""
        fake, locale = fake_locale
        provider = _healthcare_provider(fake)
        interventions = set(provider.interventions)
        assert interventions, f"{locale}: no interventions derived from the catalog"
        assert interventions.isdisjoint(provider.generic_drugs), locale

    def test_declared_interventions_all_appear_in_the_catalog(self, fake_locale: tuple[Faker, str]) -> None:
        """A declared intervention that no condition prescribes is a translation left behind."""
        fake, locale = fake_locale
        provider = _healthcare_provider(fake)
        prescribed: set[str] = set()
        for data in provider.disease_correlations.values():
            prescribed.update(data["medications"])
        missing = set(provider.non_drug_interventions) - prescribed
        assert not missing, f"{locale}: declared interventions not used by any condition: {sorted(missing)}"

    def test_unknown_disease_raises_in_every_locale(self, fake_locale: tuple[Faker, str]) -> None:
        """No locale may fall back to an uncorrelated draw for an unknown disease."""
        fake, locale = fake_locale
        unknown = "Not A Disease"
        for call in (
            lambda: fake.icd10_code(disease=unknown),
            lambda: fake.symptom(disease=unknown),
            lambda: fake.medication(disease=unknown),
            lambda: fake.disease_symptoms(unknown),
            lambda: fake.medications(unknown),
            lambda: fake.patient_scenario(disease=unknown),
            lambda: fake.blood_pressure(disease=unknown),
            lambda: fake.vital_sign_measurement(disease=unknown),
            lambda: fake.vital_sign_measurements(disease=unknown),
            lambda: fake.lab_result(disease=unknown),
            lambda: fake.lab_panel(disease=unknown),
        ):
            with pytest.raises(ValueError, match=unknown):
                call()

    def test_blood_pressure_invariant_holds_in_every_locale(self, fake_locale: tuple[Faker, str]) -> None:
        fake, locale = fake_locale
        fake.seed_instance(2026)
        for _ in range(500):
            pressure = fake.blood_pressure()
            assert pressure["systolic"] > pressure["diastolic"], (locale, pressure)

    def test_measurements_are_numbers_with_localized_names(self, fake_locale: tuple[Faker, str]) -> None:
        """vital_sign() still returns a NAME; vital_sign_measurement() returns a number."""
        fake, locale = fake_locale
        labels = _load_clinical_labels(locale)
        assert isinstance(fake.vital_sign(), str)
        measurement = fake.vital_sign_measurement(name="heart_rate")
        assert measurement["name"] == labels["heart_rate"], locale
        assert isinstance(measurement["value"], (int, float)), locale

    def test_lab_result_flag_agrees_with_the_value_in_every_locale(self, fake_locale: tuple[Faker, str]) -> None:
        """The flag word is translated; the comparison behind it is not."""
        fake, locale = fake_locale
        labels = _load_clinical_labels(locale)
        flag_for_label = {labels[key]: flag for flag, key in FLAG_LABEL_KEYS.items()}
        fake.seed_instance(31)
        diabetes = _disease_named_by_code(locale, "E11.9")
        for disease in (None, diabetes):
            for _ in range(200):
                result = fake.lab_result(disease=disease)
                expected = "low" if result["value"] < result["reference_low"] else "high" if result["value"] > result["reference_high"] else "normal"
                assert flag_for_label[result["flag"]] == expected, (locale, result)

    def test_correlation_reaches_every_locale_through_the_icd10_code(self, fake_locale: tuple[Faker, str]) -> None:
        """One numeric table, six languages: the diabetic HbA1c is high in all of them."""
        fake, locale = fake_locale
        labels = _load_clinical_labels(locale)
        fake.seed_instance(32)
        diabetes = _disease_named_by_code(locale, "E11.9")
        panel = fake.lab_panel(disease=diabetes)
        hba1c = next(result for result in panel if result["analyte"] == labels["hba1c"])
        assert hba1c["value"] > hba1c["reference_high"], (locale, hba1c)
        assert hba1c["flag"] == labels["flag_high"], (locale, hba1c)
        assert hba1c["unit"] == "mmol/mol", locale

    def test_body_measurements_are_self_consistent_in_every_locale(self, fake_locale: tuple[Faker, str]) -> None:
        fake, locale = fake_locale
        fake.seed_instance(33)
        for _ in range(200):
            body = fake.body_measurements()
            assert body["bmi"] == round(body["weight_kg"] / (body["height_cm"] / 100) ** 2, 1), (locale, body)

    def test_unknown_measurement_ids_raise_in_every_locale(self, fake_locale: tuple[Faker, str]) -> None:
        fake, locale = fake_locale
        with pytest.raises(ValueError, match="Unknown analyte"):
            fake.lab_result(analyte="not_an_analyte")
        with pytest.raises(ValueError, match="Unknown vital sign"):
            fake.vital_sign_measurement(name="not_a_vital_sign")


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


class TestLocaleParity:
    """Verify every locale exposes the same *content*, not merely the same counts.

    Equal condition counts alone let real divergence through: zh_CN shipped for several
    releases without the G40.909 condition every other locale had, carrying an H25.9
    condition no other locale had, and the counts matched perfectly. Parity here means
    the ICD-10 multiset, the per-condition list lengths, and the size of every shared
    constant tuple.
    """

    def test_all_locales_have_equal_disease_count(self) -> None:
        """Every locale must define the same number of diseases so no locale falls behind on additions."""
        counts = {locale: len(_load_correlations(locale)) for locale in SUPPORTED_LOCALES}
        assert len(set(counts.values())) == 1, f"Locale disease counts differ: {counts}"

    @pytest.mark.parametrize("locale", NON_ENGLISH_LOCALES)
    def test_icd10_multiset_matches_the_base(self, locale: str) -> None:
        """Same codes, same number of times — the check equal counts cannot make."""
        base = _icd10_counter("en_US")
        actual = _icd10_counter(locale)
        missing = base - actual
        extra = actual - base
        assert not missing and not extra, f"{locale} diverges from the base catalog: missing={dict(missing)}, unexpected={dict(extra)}"

    @pytest.mark.parametrize("locale", NON_ENGLISH_LOCALES)
    def test_per_condition_list_lengths_match_the_base(self, locale: str) -> None:
        """A translated condition must carry as many symptoms and medications as the base one."""
        base = _length_profile("en_US")
        actual = _length_profile(locale)
        differing = {code: (base[code], actual[code]) for code in base if code in actual and base[code] != actual[code]}
        assert not differing, f"{locale}: (symptoms, medications) counts differ from the base for {differing}"

    @pytest.mark.parametrize("constant_name", SHARED_CONSTANTS)
    def test_shared_constants_have_equal_cardinality(self, constant_name: str) -> None:
        """A locale short one procedure or one allergy can never generate it."""
        sizes = {locale: len(getattr(_load_constants(locale), constant_name)) for locale in SUPPORTED_LOCALES}
        assert len(set(sizes.values())) == 1, f"{constant_name} differs across locales: {sizes}"

    def test_every_base_constant_is_classified(self) -> None:
        """A new constant must be declared shared or locale-specific, not silently unchecked."""
        base = _load_constants("en_US")
        declared = {name for name in vars(base) if name.isupper() and isinstance(getattr(base, name), tuple)}
        classified = set(SHARED_CONSTANTS) | set(LOCALE_SPECIFIC_CONSTANTS) | set(BASE_ONLY_CONSTANTS)
        buckets = "SHARED_CONSTANTS, LOCALE_SPECIFIC_CONSTANTS, or BASE_ONLY_CONSTANTS"
        assert declared == classified, f"unclassified constants in faker_healthcare/constants.py: {sorted(declared - classified)} (add them to {buckets})"

    def test_zh_cn_contains_no_japanese_kana(self) -> None:
        """zh_CN is Simplified Chinese; kana means a Japanese term slipped in."""
        offenders: list[str] = []
        for disease, data in _load_correlations("zh_CN").items():
            values = [disease, data["icd10"], data["medical_specialty"], *data["symptoms"], *data["medications"]]
            offenders.extend(value for value in values if JAPANESE_KANA_RE.search(value))

        constants_module = _load_constants("zh_CN")
        for name in vars(constants_module):
            if name.isupper() and isinstance(getattr(constants_module, name), tuple):
                offenders.extend(value for value in getattr(constants_module, name) if JAPANESE_KANA_RE.search(value))

        assert not offenders, f"zh_CN contains Japanese kana: {offenders}"

    @pytest.mark.parametrize("locale", SUPPORTED_LOCALES)
    def test_new_conditions_present_in_locale(self, locale: str) -> None:
        """Each locale must include the 2.2.0 conditions, identified by their shared ICD-10 codes."""
        codes = {data["icd10"] for data in _load_correlations(locale).values()}
        missing = NEW_CONDITION_ICD10_CODES - codes
        assert not missing, f"Locale {locale} is missing conditions with ICD-10 codes: {missing}"

    @pytest.mark.parametrize("locale", SUPPORTED_LOCALES)
    def test_locale_entries_are_structurally_complete(self, locale: str) -> None:
        """Every locale entry must carry non-empty symptoms, medications, and a specialty."""
        for disease, data in _load_correlations(locale).items():
            assert data["icd10"], f"{locale}: '{disease}' has empty ICD-10 code"
            assert data["symptoms"], f"{locale}: '{disease}' has no symptoms"
            assert data["medications"], f"{locale}: '{disease}' has no medications"
            assert data["medical_specialty"], f"{locale}: '{disease}' has no specialty"


class TestClinicalLabelParity:
    """Labels are per-locale; the numbers behind them deliberately are NOT.

    The measurement API is split down the middle. Units, reference intervals, bounds and
    the condition -> analyte correlations live once in
    `faker_healthcare/clinical_values.py`, because a millimole is a millimole in every
    language; only the words live in `faker_healthcare/<locale>/clinical_labels.py`.

    That makes the numeric tables a DELIBERATE, EXPLICIT EXEMPTION from the six-locale
    parity rule that governs `disease_correlations.py` and the constant tuples: they are
    not duplicated per locale, and `test_no_locale_ships_its_own_numeric_tables` fails
    if a future change starts duplicating them. The labels get the full parity
    treatment instead, since they are the half that can legitimately differ and
    therefore the half that can legitimately fall behind.
    """

    def test_base_label_keys_cover_the_numeric_tables_exactly(self) -> None:
        """Adding an analyte or a vital sign forces a label for it — in all six locales.

        Without this the tables and the labels drift: a new analyte would generate a
        number no locale could name, and `_label()` would raise at call time instead of
        at test time.
        """
        expected = {*VITAL_DEFINITIONS, *LAB_DEFINITIONS, *FLAG_LABEL_KEYS.values(), *(key for _, key in ALCOHOL_CATEGORY_THRESHOLDS), ALCOHOL_HIGHEST_CATEGORY}
        assert set(_load_clinical_labels("en_US")) == expected

    @pytest.mark.parametrize("locale", NON_ENGLISH_LOCALES)
    def test_every_locale_defines_every_label_key(self, locale: str) -> None:
        base = set(_load_clinical_labels("en_US"))
        actual = set(_load_clinical_labels(locale))
        assert not base - actual, f"{locale} is missing labels: {sorted(base - actual)}"
        assert not actual - base, f"{locale} defines labels no other locale has: {sorted(actual - base)}"

    @pytest.mark.parametrize("locale", SUPPORTED_LOCALES)
    def test_labels_are_non_empty_and_distinct(self, locale: str) -> None:
        """Two keys sharing one label is how a copy-paste translation goes unnoticed."""
        labels = _load_clinical_labels(locale)
        assert all(value.strip() for value in labels.values()), locale
        duplicates = {value for value in labels.values() if list(labels.values()).count(value) > 1}
        assert not duplicates, f"{locale} uses the same label for more than one key: {sorted(duplicates)}"

    @pytest.mark.parametrize("locale", NON_ENGLISH_LOCALES)
    def test_labels_are_actually_translated(self, locale: str) -> None:
        """A handful of terms are the same word in two languages; a whole file is not."""
        base = _load_clinical_labels("en_US")
        labels = _load_clinical_labels(locale)
        untranslated = [key for key, value in labels.items() if value == base[key]]
        assert len(untranslated) <= len(base) // 4, f"{locale} looks copied from English: {sorted(untranslated)}"

    def test_zh_cn_labels_contain_no_japanese_kana(self) -> None:
        offenders = [value for value in _load_clinical_labels("zh_CN").values() if JAPANESE_KANA_RE.search(value)]
        assert not offenders, f"zh_CN clinical labels contain Japanese kana: {offenders}"

    @pytest.mark.parametrize("locale", NON_ENGLISH_LOCALES)
    def test_no_locale_ships_its_own_numeric_tables(self, locale: str) -> None:
        """The exemption, enforced: reference ranges are never duplicated per locale.

        Six copies of one reference interval is six chances to disagree about a value
        that cannot legitimately differ, and the first correction would leave five of
        them stale.
        """
        package = Path(importlib.import_module(f"faker_healthcare.{locale}").__file__).parent
        assert not (package / "clinical_values.py").exists(), f"{locale} ships its own copy of the numeric tables"

        provider = _get_provider_for_locale(locale)
        for attribute in ("vital_definitions", "lab_definitions"):
            assert attribute not in provider.__dict__, f"{locale} provider redeclares '{attribute}'"
            assert getattr(provider, attribute) is getattr(HealthcareProvider, attribute), f"{locale} provider does not share the base '{attribute}'"

    @pytest.mark.parametrize("locale", SUPPORTED_LOCALES)
    def test_every_locale_provider_declares_its_own_labels(self, locale: str) -> None:
        provider = _get_provider_for_locale(locale)
        assert "clinical_labels" in provider.__dict__, f"{locale} provider does not declare clinical_labels"
        assert provider.clinical_labels == _load_clinical_labels(locale)


class TestZhBrandCatalogue:
    """Same guarantee as the base catalogue, asserted over the whole shipped tuple.

    The Chinese list carries the weaker claim of the two — see the TODO in
    faker_healthcare/zh_CN/brand_names.py — but "not reviewed by a fluent speaker" is
    not a licence to skip the screens that can be automated.
    """

    def test_catalogue_is_non_empty_sorted_and_deduplicated(self) -> None:
        from faker_healthcare.zh_CN.constants import ZH_BRAND_NAMES

        assert ZH_BRAND_NAMES
        assert list(ZH_BRAND_NAMES) == sorted(ZH_BRAND_NAMES)
        assert len(set(ZH_BRAND_NAMES)) == len(ZH_BRAND_NAMES)

    def test_no_shipped_name_fails_any_screen(self) -> None:
        from faker_healthcare.zh_CN.constants import ZH_BRAND_NAMES

        generator = load_brand_name_generator()
        catalogue = generator.catalogue_terms(("zh_CN",))
        offenders = {name: generator.screen_zh(name, catalogue) for name in ZH_BRAND_NAMES}
        assert {name: reasons for name, reasons in offenders.items() if reasons} == {}

    def test_every_shipped_name_is_reachable_from_the_character_pool(self) -> None:
        from faker_healthcare.zh_CN.constants import ZH_BRAND_CHARS, ZH_BRAND_NAMES

        offenders = [name for name in ZH_BRAND_NAMES if not set(name) <= set(ZH_BRAND_CHARS)]
        assert offenders == []
