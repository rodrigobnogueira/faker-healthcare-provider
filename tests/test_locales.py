import importlib
import re
from collections import Counter, defaultdict
from pathlib import Path
from types import ModuleType

import pytest
from conftest import load_brand_name_generator
from faker import Faker
from zh_cn_equivalents import ZH_MEDICATIONS, ZH_SYMPTOMS

from faker_healthcare import HealthcareProvider
from faker_healthcare.assessments import ASSESSMENT_INSTRUMENTS
from faker_healthcare.clinical_values import (
    ALCOHOL_CATEGORY_THRESHOLDS,
    ALCOHOL_HIGHEST_CATEGORY,
    FLAG_LABEL_KEYS,
    LAB_DEFINITIONS,
    VITAL_DEFINITIONS,
)
from faker_healthcare.prescribing import (
    DOSE_LADDERS,
    FREQUENCY_IDS,
    MEDICATION_STATUS_IDS,
    ROUTE_IDS,
    frequency_label_key,
    route_label_key,
    status_label_key,
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


def _by_icd10(locale: str) -> dict[str, list[tuple[str, dict]]]:
    """Conditions grouped by ICD-10 code, in catalogue order within a code.

    Two conditions may share a code (`Epilepsy` and `Seizure Disorder` → `G40.909`), so
    the pairing between two locales is by code *and* position. Position is what makes an
    index shift visible; reordering the entries under one code in one locale only is a
    real divergence and is meant to fail.
    """
    grouped: defaultdict[str, list[tuple[str, dict]]] = defaultdict(list)
    for name, data in _load_correlations(locale).items():
        grouped[data["icd10"]].append((name, data))
    return dict(grouped)


def _load_constants(locale: str) -> ModuleType:
    """Load the constants module for a given locale."""
    if locale == "en_US":
        return importlib.import_module("faker_healthcare.constants")
    return importlib.import_module(f"faker_healthcare.{locale}.constants")


def _load_labels_module(locale: str) -> ModuleType:
    if locale == "en_US":
        return importlib.import_module("faker_healthcare.clinical_labels")
    return importlib.import_module(f"faker_healthcare.{locale}.clinical_labels")


def _load_clinical_labels(locale: str) -> dict[str, str]:
    """Load the clinical display labels for a given locale."""
    labels: dict[str, str] = _load_labels_module(locale).CLINICAL_LABELS
    return labels


def _load_medication_names(locale: str) -> dict[str, str]:
    """Load the substance ID -> catalogue spelling map for a given locale."""
    names: dict[str, str] = _load_labels_module(locale).MEDICATION_NAMES
    return names


def _drug_pool(locale: str) -> set[str]:
    """Every medication some condition in this locale prescribes."""
    return {medication for data in _load_correlations(locale).values() for medication in data["medications"]}


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
            lambda: fake.medication_order(disease=unknown),
            lambda: fake.medication_orders(disease=unknown),
            lambda: fake.assessment_score(disease=unknown),
            lambda: fake.patient(disease=unknown),
            lambda: fake.patient_record(disease=unknown),
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
        with pytest.raises(ValueError, match="Unknown assessment instrument"):
            fake.assessment_score(instrument="not_an_instrument")

    def test_medication_orders_are_dosed_and_localized_in_every_locale(self, fake_locale: tuple[Faker, str]) -> None:
        """One locale-neutral dose ladder, six languages: the substance name, the route,
        the frequency and the status are this locale's words; the number is not."""
        fake, locale = fake_locale
        labels = _load_clinical_labels(locale)
        names = _load_medication_names(locale)
        routes = {labels[route_label_key(route)] for route in ROUTE_IDS}
        frequencies = {labels[frequency_label_key(frequency)] for frequency in FREQUENCY_IDS}
        statuses = {labels[status_label_key(status)] for status in MEDICATION_STATUS_IDS}
        by_name = {name: substance for substance, name in names.items()}

        fake.seed_instance(41)
        for _ in range(200):
            order = fake.medication_order()
            ladder = DOSE_LADDERS[by_name[order["medication"]]]
            assert order["dose"] in ladder["doses"], (locale, order)
            assert order["unit"] == ladder["unit"], (locale, order)
            assert order["route"] in routes and order["frequency"] in frequencies, (locale, order)
            assert order["status"] in statuses, (locale, order)

    def test_the_dose_ladder_reaches_every_locale_through_the_substance_id(self, fake_locale: tuple[Faker, str]) -> None:
        """Metformin is 500/850/1000 mg in Chinese too — the ladder is not duplicated."""
        fake, locale = fake_locale
        names = _load_medication_names(locale)
        fake.seed_instance(42)
        diabetes = _disease_named_by_code(locale, "E11.9")
        orders = [fake.medication_order(disease=diabetes) for _ in range(50)]
        metformin = [order for order in orders if order["medication"] == names["metformin"]]
        assert metformin, f"{locale}: metformin never ordered for diabetes"
        assert all(order["dose"] in (500, 850, 1000) and order["unit"] == "mg" for order in metformin), (locale, metformin[0])

    def test_assessment_bands_are_localized_in_every_locale(self, fake_locale: tuple[Faker, str]) -> None:
        fake, locale = fake_locale
        labels = _load_clinical_labels(locale)
        band_labels = {labels[key] for definition in ASSESSMENT_INSTRUMENTS.values() for _, key in definition["bands"]}
        fake.seed_instance(43)
        for _ in range(100):
            result = fake.assessment_score()
            # The instrument's NAME is a proper noun and is not translated; the band is.
            assert result["instrument"] in {definition["name"] for definition in ASSESSMENT_INSTRUMENTS.values()}, locale
            assert result["severity"] in band_labels, (locale, result)

    def test_patients_and_records_are_correlated_in_every_locale(self, fake_locale: tuple[Faker, str]) -> None:
        """Demographic constraints are keyed by ICD-10 code, so they hold in Chinese too."""
        fake, locale = fake_locale
        fake.seed_instance(44)
        preeclampsia = _disease_named_by_code(locale, "O14.90")
        for _ in range(50):
            patient = fake.patient(disease=preeclampsia)
            assert patient["sex"] == "female", (locale, patient)
            assert 15 <= patient["age"] <= 50, (locale, patient)

        record = fake.patient_record(disease=_disease_named_by_code(locale, "E11.9"))
        assert record["age"] >= 18
        assert len(record["vital_signs"]) == len(VITAL_DEFINITIONS)
        assert record["lab_panel"] and record["medication_orders"]

    def test_nhs_number_is_available_and_valid_in_every_locale(self, fake_locale: tuple[Faker, str]) -> None:
        """The provider class is shared, so the identifier is too; the default stays the
        reserved test range whichever catalogue is loaded."""
        fake, locale = fake_locale
        for _ in range(50):
            number = fake.nhs_number()
            assert re.fullmatch(r"999 \d{3} \d{4}", number), (locale, number)


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
        expected = {
            *VITAL_DEFINITIONS,
            *LAB_DEFINITIONS,
            *FLAG_LABEL_KEYS.values(),
            *(key for _, key in ALCOHOL_CATEGORY_THRESHOLDS),
            ALCOHOL_HIGHEST_CATEGORY,
            # The prescribing and assessment vocabularies are IDs in exactly the same
            # way, so a new route, frequency, status or severity band cannot ship unnamed
            # either.
            *(route_label_key(route) for route in ROUTE_IDS),
            *(frequency_label_key(frequency) for frequency in FREQUENCY_IDS),
            *(status_label_key(status) for status in MEDICATION_STATUS_IDS),
            *(key for definition in ASSESSMENT_INSTRUMENTS.values() for _, key in definition["bands"]),
        }
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
        for module in ("clinical_values.py", "prescribing.py", "assessments.py"):
            assert not (package / module).exists(), f"{locale} ships its own copy of {module}"

        provider = _get_provider_for_locale(locale)
        for attribute in ("vital_definitions", "lab_definitions", "dose_ladders", "assessment_instruments"):
            assert attribute not in provider.__dict__, f"{locale} provider redeclares '{attribute}'"
            assert getattr(provider, attribute) is getattr(HealthcareProvider, attribute), f"{locale} provider does not share the base '{attribute}'"

    @pytest.mark.parametrize("locale", SUPPORTED_LOCALES)
    def test_every_locale_provider_declares_its_own_labels(self, locale: str) -> None:
        provider = _get_provider_for_locale(locale)
        for attribute, expected in (("clinical_labels", _load_clinical_labels(locale)), ("medication_names", _load_medication_names(locale))):
            assert attribute in provider.__dict__, f"{locale} provider does not declare {attribute}"
            assert getattr(provider, attribute) == expected


class TestMedicationNameParity:
    """The other half of the prescribing split: one ladder, six spellings.

    `prescribing.DOSE_LADDERS` is keyed by a locale-neutral substance ID and is never
    duplicated; each locale's `MEDICATION_NAMES` says what that substance is called in
    ITS catalogue. Both halves have to hold for a dose to reach a French record: a
    missing key means an unreachable ladder, and a name that is a fine translation but is
    not the string the catalogue actually ships would simply never match.
    """

    @pytest.mark.parametrize("locale", NON_ENGLISH_LOCALES)
    def test_every_locale_names_every_dosed_substance(self, locale: str) -> None:
        base = set(_load_medication_names("en_US"))
        actual = set(_load_medication_names(locale))
        assert not base - actual, f"{locale} is missing medication names: {sorted(base - actual)}"
        assert not actual - base, f"{locale} names substances no other locale has: {sorted(actual - base)}"

    def test_the_base_names_and_the_ladders_are_the_same_set(self) -> None:
        assert set(_load_medication_names("en_US")) == set(DOSE_LADDERS)

    @pytest.mark.parametrize("locale", SUPPORTED_LOCALES)
    def test_every_name_is_a_medication_that_locale_actually_prescribes(self, locale: str) -> None:
        """The check that makes the mapping verifiable rather than a promise."""
        pool = _drug_pool(locale)
        missing = {substance: name for substance, name in _load_medication_names(locale).items() if name not in pool}
        assert not missing, f"{locale} names medications its catalogue does not contain: {missing}"

    @pytest.mark.parametrize("locale", SUPPORTED_LOCALES)
    def test_names_are_distinct_within_a_locale(self, locale: str) -> None:
        """Two substances sharing one spelling would make the reverse lookup ambiguous,
        and one of the two ladders unreachable."""
        names = list(_load_medication_names(locale).values())
        duplicates = {name for name in names if names.count(name) > 1}
        assert not duplicates, f"{locale} uses one name for more than one substance: {sorted(duplicates)}"

    @pytest.mark.parametrize("locale", ["pt_BR", "es_ES", "zh_CN"])
    def test_names_are_actually_localized(self, locale: str) -> None:
        """Two locales are deliberately absent from this list, for opposite reasons.

        `fr_FR` keeps drug names in English by catalogue convention (see AGENTS.md), so
        its map IS the English one on purpose. `de_DE` germanizes many names
        (`Amitriptylin`, `Doxycyclin`) but shares the English spelling for many more,
        because both are the INN — `Metformin`, `Ibuprofen`, `Warfarin` are simply the
        same word, and asserting otherwise would demand a wrong translation. What catches
        a copied file in both is the test above: a name from the wrong language is not in
        that locale's catalogue at all.
        """
        base = _load_medication_names("en_US")
        names = _load_medication_names(locale)
        untranslated = [substance for substance, name in names.items() if name == base[substance]]
        assert len(untranslated) <= len(base) // 3, f"{locale} looks copied from English: {sorted(untranslated)}"

    def test_zh_cn_medication_names_contain_no_japanese_kana(self) -> None:
        offenders = [name for name in _load_medication_names("zh_CN").values() if JAPANESE_KANA_RE.search(name)]
        assert not offenders, f"zh_CN medication names contain Japanese kana: {offenders}"


class TestZhTranslationEquivalence:
    """A localized drug must name the SAME substance as the base entry, and it is checked.

    `TestLocaleParity` counts symptoms and medications per ICD-10 code, which is blind to
    the worst defect this data can carry: a plausible, real, *different* drug in one
    locale. zh_CN shipped four of them — `地西泮` (diazepam) for Disulfiram, `可乐定`
    (clonidine) for Clonazepam, `铝碳酸镁` (hydrotalcite) for Sucralfate, `布林佐胺`
    (brinzolamide) for Brimonidine — with every count correct.

    So the correspondence itself is pinned, in `tests/zh_cn_equivalents.py`: walking the
    two catalogues together, slot by slot, each Chinese string must be the one recorded
    for the English string beside it. That fails on a substituted drug, on an index shift
    (which is how three of the four are believed to have arrived), and on a second
    spelling of a drug that already has one.
    """

    @staticmethod
    def _slots(field: str) -> list[tuple[str, str, str, str]]:
        """Every (ICD-10 code, base condition name, English term, Chinese term) slot."""
        base = _by_icd10("en_US")
        chinese = _by_icd10("zh_CN")
        slots: list[tuple[str, str, str, str]] = []
        for code, entries in base.items():
            for position, (name, data) in enumerate(entries):
                _, zh_data = chinese[code][position]
                slots.extend((code, name, term, zh_data[field][index]) for index, term in enumerate(data[field]))
        return slots

    def test_every_base_medication_has_a_committed_chinese_equivalent(self) -> None:
        missing = sorted({term for _, _, term, _ in self._slots("medications")} - set(ZH_MEDICATIONS))
        assert not missing, f"medications with no entry in tests/zh_cn_equivalents.py: {missing}"

    def test_every_base_symptom_has_a_committed_chinese_equivalent(self) -> None:
        missing = sorted({term for _, _, term, _ in self._slots("symptoms")} - set(ZH_SYMPTOMS))
        assert not missing, f"symptoms with no entry in tests/zh_cn_equivalents.py: {missing}"

    def test_the_tables_carry_nothing_the_catalogue_dropped(self) -> None:
        """Otherwise a removed condition leaves its translations behind to rot."""
        for table, field, name in ((ZH_MEDICATIONS, "medications", "ZH_MEDICATIONS"), (ZH_SYMPTOMS, "symptoms", "ZH_SYMPTOMS")):
            stale = sorted(set(table) - {term for _, _, term, _ in self._slots(field)})
            assert not stale, f"{name} has entries the base catalogue no longer contains: {stale}"

    def test_every_zh_medication_is_the_committed_equivalent_of_the_base_medication(self) -> None:
        wrong = {
            f"{code} ({condition}): {term}": f"{chinese} (expected {ZH_MEDICATIONS[term]})"
            for code, condition, term, chinese in self._slots("medications")
            if term in ZH_MEDICATIONS and chinese != ZH_MEDICATIONS[term]
        }
        assert not wrong, f"zh_CN names a different substance than the base entry: {wrong}"

    def test_every_zh_symptom_is_the_committed_equivalent_of_the_base_symptom(self) -> None:
        wrong = {
            f"{code} ({condition}): {term}": f"{chinese} (expected {ZH_SYMPTOMS[term]})"
            for code, condition, term, chinese in self._slots("symptoms")
            if term in ZH_SYMPTOMS and chinese != ZH_SYMPTOMS[term]
        }
        assert not wrong, f"zh_CN describes a different symptom than the base entry: {wrong}"

    def test_two_substances_never_share_one_chinese_name(self) -> None:
        """The medication mapping is one-to-one in both directions.

        One Chinese string standing for two English drugs is the signature of the defect:
        `可乐定` was the shipped translation of both Clonidine and Clonazepam. (Symptoms
        are deliberately exempt: `Headache`/`Headaches` and `Frequency`/`Frequent
        Urination` are the same symptom written twice in the base catalogue.)
        """
        collisions = {chinese: sorted(term for term, name in ZH_MEDICATIONS.items() if name == chinese) for chinese in ZH_MEDICATIONS.values() if list(ZH_MEDICATIONS.values()).count(chinese) > 1}
        assert not collisions, f"one Chinese name for more than one substance: {collisions}"

    def test_the_table_agrees_with_the_substance_id_map(self) -> None:
        """The bridge to `MEDICATION_NAMES`, so the two mappings cannot drift apart.

        `MEDICATION_NAMES` maps a substance ID to each catalogue's spelling for the ~130
        substances with a dose ladder; this table covers all of them plus every undosed
        one, keyed by the base spelling. Where they overlap they must agree, or a dose
        would print beside a name this table says belongs to another drug.
        """
        base_names = _load_medication_names("en_US")
        zh_names = _load_medication_names("zh_CN")
        disagreements = {substance: (ZH_MEDICATIONS.get(base_names[substance]), zh_names[substance]) for substance in base_names if ZH_MEDICATIONS.get(base_names[substance]) != zh_names[substance]}
        assert not disagreements, f"MEDICATION_NAMES and ZH_MEDICATIONS disagree (table, MEDICATION_NAMES): {disagreements}"


class TestDiseaseEntityCoherence:
    """A condition's ICD-10 code and its medications must name the SAME disease entity.

    The catalogue shipped `"Hemophilia": {"icd10": "D68.311", "medications": ["Factor
    VIII", "Factor IX", "Desmopressin", "Antifibrinolytics", "Emicizumab"]}` for several
    releases. D68.311 is *acquired* haemophilia — an autoimmune factor VIII inhibitor,
    treated with immunosuppression and bypassing agents — while factor replacement,
    desmopressin and emicizumab all treat the congenital disease, and emicizumab's FDA
    label says so in as many words ("hemophilia A (congenital factor VIII deficiency)").
    Every other check in this file passed on it: the code is well formed, the drugs are
    real, the specialty is right, the counts match in all six locales, and the Chinese
    names are the committed equivalents of the English ones. What nothing looked at was
    whether the code and the drugs were about the same disease.

    So this is the generalised form rather than a pin on one entry: a table of codes that
    name one specific molecular entity, and the therapies that belong to a *different*
    one. It already covers the two haemophilia codes the catalogue does not yet carry, so
    a future D67 entry treated with factor VIII fails before it is reviewed.
    """

    # Therapies are matched by pattern, not by exact string, because one substance is
    # spelled six ways (Factor/Fator/Faktor/因子) and a table of exact strings would go
    # stale the moment a locale is added. The patterns are deliberately loose about
    # spelling and strict about the entity: `VIII` and `IX` are the whole point.
    THERAPY_PATTERNS = {
        "factor VIII replacement": re.compile(r"(fa[ck]?tor|因子)\s*VIII", re.IGNORECASE),
        "factor IX replacement": re.compile(r"(fa[ck]?tor|因子)\s*IX", re.IGNORECASE),
        "desmopressin": re.compile(r"desmopres|去氨加压素", re.IGNORECASE),
        "emicizumab": re.compile(r"emicizumab|艾美赛珠单抗", re.IGNORECASE),
    }

    # Per ICD-10 code: what the code means, and the therapies that must never appear
    # beside it because they treat another entity. Sources are in the base catalogue's
    # comment on "Hemophilia A" and in the FDA labels it cites.
    INCOMPATIBLE = {
        # Acquired haemophilia. The patient's own genes make factor VIII normally; an
        # autoantibody neutralises it. Routine replacement of a protein that is not
        # missing, and emicizumab, which is licensed for the congenital disease, both
        # describe a different patient. This is the pairing that shipped.
        "D68.311": ("acquired haemophilia", ("factor VIII replacement", "factor IX replacement", "desmopressin", "emicizumab")),
        # Hereditary factor VIII deficiency (haemophilia A). Factor IX replacement is
        # haemophilia B therapy, and naming it here is what made the old entry read as
        # two diseases at once.
        "D66": ("hereditary factor VIII deficiency (haemophilia A)", ("factor IX replacement",)),
        # Hereditary factor IX deficiency (haemophilia B). Not in the catalogue today;
        # the rule is here so that adding it wrong is a failure rather than a review
        # comment. Desmopressin is explicitly *not* indicated in haemophilia B (FDA DDAVP
        # Injection label) and emicizumab is licensed for haemophilia A only.
        "D67": ("hereditary factor IX deficiency (haemophilia B)", ("factor VIII replacement", "desmopressin", "emicizumab")),
    }

    # The therapy a deficiency code must prescribe. Without this half, an entry could
    # satisfy the rule above by prescribing nothing specific at all.
    REQUIRED = {"D66": "factor VIII replacement", "D67": "factor IX replacement"}

    # The entry exactly as it shipped, kept as the fixture the check is proved against so
    # the assertion cannot go quietly vacuous now that the catalogue is clean.
    SHIPPED_DEFECT = {
        "Hemophilia": {
            "icd10": "D68.311",
            "symptoms": ["Prolonged Bleeding", "Joint Pain", "Bruising", "Hemarthrosis", "Nosebleeds"],
            "medications": ["Factor VIII", "Factor IX", "Desmopressin", "Antifibrinolytics", "Emicizumab"],
            "medical_specialty": "Hematology",
        },
    }

    @classmethod
    def _violations(cls, catalogue: dict) -> list[str]:
        """Every (condition, therapy) pair whose therapy belongs to another entity."""
        found: list[str] = []
        for name, data in catalogue.items():
            if data["icd10"] not in cls.INCOMPATIBLE:
                continue
            entity, forbidden = cls.INCOMPATIBLE[data["icd10"]]
            for therapy in forbidden:
                pattern = cls.THERAPY_PATTERNS[therapy]
                found.extend(f"{data['icd10']} ({name}) is {entity} but prescribes {therapy}: {medication}" for medication in data["medications"] if pattern.search(medication))
        return found

    @pytest.mark.parametrize("locale", SUPPORTED_LOCALES)
    def test_no_condition_prescribes_another_entitys_therapy(self, locale: str) -> None:
        violations = self._violations(_load_correlations(locale))
        assert not violations, f"{locale}: {violations}"

    @pytest.mark.parametrize("locale", SUPPORTED_LOCALES)
    def test_a_deficiency_code_prescribes_replacement_of_the_factor_it_names(self, locale: str) -> None:
        """The positive half, and the thing that keeps the negative half honest: it runs
        the patterns against the real catalogue in every locale, so a pattern that does
        not recognise `Faktor VIII` fails here instead of silently excusing German."""
        catalogue = _load_correlations(locale)
        for code, therapy in self.REQUIRED.items():
            for name, data in catalogue.items():
                if data["icd10"] != code:
                    continue
                pattern = self.THERAPY_PATTERNS[therapy]
                assert any(pattern.search(medication) for medication in data["medications"]), f"{locale}: {code} ({name}) names a factor deficiency but prescribes no {therapy}: {data['medications']}"

    def test_the_check_catches_the_pairing_it_was_written_for(self) -> None:
        """Four of the shipped entry's five medications were another disease's."""
        violations = self._violations(self.SHIPPED_DEFECT)
        assert len(violations) == 4, violations
        assert all("D68.311 (Hemophilia) is acquired haemophilia" in violation for violation in violations)

    def test_the_patterns_recognise_the_spelling_every_locale_uses(self) -> None:
        """Including the spellings no catalogue entry currently carries — `Fator IX` has
        to stay recognisable, or removing the last factor IX entry would also remove the
        check that stops it coming back under the wrong code."""
        spellings = {
            "factor VIII replacement": ("Factor VIII", "Fator VIII", "Faktor VIII", "因子VIII"),
            "factor IX replacement": ("Factor IX", "Fator IX", "Faktor IX", "因子IX"),
            "desmopressin": ("Desmopressin", "Desmopressina", "Desmopresina", "去氨加压素"),
            "emicizumab": ("Emicizumab", "Emicizumabe", "艾美赛珠单抗"),
        }
        assert set(spellings) == set(self.THERAPY_PATTERNS), "every pattern needs its locale spellings listed"
        unmatched = {therapy: [name for name in names if not self.THERAPY_PATTERNS[therapy].search(name)] for therapy, names in spellings.items()}
        assert not any(unmatched.values()), f"patterns that miss a locale's spelling: { {k: v for k, v in unmatched.items() if v} }"

    def test_factor_viii_and_factor_ix_are_never_the_same_match(self) -> None:
        """The two patterns are one roman numeral apart, and a pattern that matched both
        would make every haemophilia rule above simultaneously true and useless."""
        assert not self.THERAPY_PATTERNS["factor IX replacement"].search("Factor VIII")
        assert not self.THERAPY_PATTERNS["factor VIII replacement"].search("Factor IX")

    def test_every_code_the_rules_name_is_accounted_for(self) -> None:
        """Same bar as the correlation tables: a rule keyed by a typo protects nothing.
        A code here is either shipped or a known gap — D67 and D68.311 are exactly the
        entries this table exists to catch *before* somebody writes them."""
        shipped = set(_icd10_counter("en_US"))
        assert set(self.REQUIRED) <= set(self.INCOMPATIBLE)
        assert set(self.INCOMPATIBLE) - shipped == {"D67", "D68.311"}, "a rule names a code that is neither shipped nor a recorded gap"
        assert "D66" in shipped, "the haemophilia recode landed differently than these rules assume"


class TestZhBrandCatalogue:
    """Same guarantee as the base catalogue, asserted over the whole shipped tuple.

    The Chinese list is the weaker of the two and its module says exactly how — it has had
    a Simplified-Chinese reading pass but no trademark search and no recorded native
    speaker's sign-off — which is not a licence to skip the screens that can be automated.
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

    def test_no_shipped_name_is_on_the_denylist(self) -> None:
        """The screen already covers this; asserting it separately says why it matters.

        `screen_zh` rejects a denylisted name, so a shipped name can only appear on the
        denylist if somebody hand-edited the generated module — which the `--check` test
        would also catch, but with a diff instead of a name.
        """
        from faker_healthcare.zh_CN.constants import ZH_BRAND_NAMES

        generator = load_brand_name_generator()
        denied = set(generator.ZH_REAL_PRODUCT_DENYLIST)
        assert [name for name in ZH_BRAND_NAMES if name in denied] == []

    def test_every_denylist_entry_is_reachable_from_the_character_pool(self) -> None:
        """A denylisted name the pool cannot produce screens nothing.

        It is not harmful, but it is almost always a typo — a character that looks like a
        pool character and is not — and the entry then silently stops protecting the name
        it was added for.
        """
        from faker_healthcare.zh_CN.constants import ZH_BRAND_CHARS

        generator = load_brand_name_generator()
        pool = set(ZH_BRAND_CHARS)
        offenders = [name for name in generator.ZH_REAL_PRODUCT_DENYLIST if not set(name) <= pool]
        assert offenders == []

    def test_every_denylist_entry_has_a_recorded_reason(self) -> None:
        """The reasons are the durable half of a reading pass, so they are enforced.

        A bare entry keeps one name out; an entry with a reason tells the next reviewer
        what the pattern was, which is what stopped 58 names in 2026-08-16 and 337 more in
        2026-08-17 from having to be re-derived.
        """
        source = (Path(__file__).resolve().parent.parent / "scripts" / "generate_brand_names.py").read_text(encoding="utf-8")
        block = source.split("ZH_REAL_PRODUCT_DENYLIST: tuple[str, ...] = (", 1)[1].split("\n)", 1)[0]
        unexplained = [line.strip() for line in block.splitlines() if line.strip().startswith('"') and "#" not in line]
        assert unexplained == []

    def test_the_2026_08_16_rejections_are_still_rejected(self) -> None:
        """The reading passes only compound if their verdicts cannot be undone.

        These are the 64 names the module shipped before the 2026-08-16 reading pass, taken
        from that commit. Fifty-eight were rejected then and one more (复安) in 2026-08-17,
        so every name here is either still shipped or still refused by a screen — a pool or
        denylist edit that re-admitted one would fail here rather than in a release.
        """
        candidates = (
            "乐佳 乐欣 佳元 佳欣 元力 元泰 力华 力泽 华可 华益 博可 博清 可复 可益 和复 和素 "
            "复安 复维 宁定 宁舒 安元 安欣 定尔 定诗 尔平 尔达 平施 平迪 康可 康益 恩乐 恩欣 "
            "施力 施泽 欣元 欣泽 泰定 泰舒 泽力 泽清 清可 清益 特可 特益 瑞施 瑞通 益宁 益维 "
            "素复 素维 维宁 维舒 舒康 舒迪 诗平 诗达 诺恩 诺通 达恩 达通 迪元 迪欣 通元 通欣"
        ).split()
        assert len(candidates) == 64

        from faker_healthcare.zh_CN.constants import ZH_BRAND_NAMES

        generator = load_brand_name_generator()
        catalogue = generator.catalogue_terms(("zh_CN",))
        still_shipped = [name for name in candidates if name in ZH_BRAND_NAMES]
        assert sorted(still_shipped) == sorted(["宁舒", "恩欣", "舒迪", "达恩", "迪欣"])

        readmitted = [name for name in candidates if name not in ZH_BRAND_NAMES and not generator.screen_zh(name, catalogue)]
        assert readmitted == []

    def test_the_shipped_list_is_wide_enough_to_be_worth_generating(self) -> None:
        """zh_CN composites are (Chinese half) x (Latin half), and only the halves are pinned.

        The Latin half has always had 245 entries, so the composite count looks large however
        thin the Chinese half is: with six Chinese names it was 1,470 composites drawn from
        six Chinese pairs, and a user generating Chinese data saw the same six over and over.
        This pins the number that actually varies. It is a floor, not the current count, so
        adding reviewed names does not fail it — but withdrawing one silently will.
        """
        from faker_healthcare.zh_CN.constants import ZH_BRAND_NAMES

        assert len(ZH_BRAND_NAMES) >= 25

    def test_draws_cover_every_shipped_chinese_half(self) -> None:
        """No shipped Chinese name may be unreachable through the provider.

        Asserted over the whole tuple rather than a coverage fraction: the list is small
        enough that 2,000 draws exhaust it, so anything missing is unreachable, not unlucky.
        """
        from faker_healthcare.zh_CN import Provider
        from faker_healthcare.zh_CN.constants import ZH_BRAND_NAMES

        fake = Faker("zh_CN")
        fake.add_provider(Provider)
        fake.seed_instance(20260817)
        halves = {fake.brand_drug().split(" ", 1)[0] for _ in range(2000)}
        assert halves == set(ZH_BRAND_NAMES)
