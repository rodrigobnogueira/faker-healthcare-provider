"""Tests for the measurement API: numbers, their flags, and their correlations.

Everything this suite protects is an internal-consistency property, because that is
what the package is for. A random number in a `value` field is easy; a number that
agrees with its own flag, with the reference interval printed beside it, with the other
half of the same blood pressure, with the height and weight it was computed from, and
with the diagnosis on the record, is the part a consumer cannot generate themselves.
"""

import re

import pytest
from faker import Faker

from faker_healthcare import HealthcareProvider
from faker_healthcare.clinical_labels import CLINICAL_LABELS
from faker_healthcare.clinical_values import (
    ALCOHOL_CATEGORY_THRESHOLDS,
    ALCOHOL_HIGHEST_CATEGORY,
    CONDITION_LAB_EFFECTS,
    CONDITION_VITAL_EFFECTS,
    FLAG_LABEL_KEYS,
    LAB_DEFINITIONS,
    MIN_PULSE_PRESSURE_MMHG,
    PULSE_PRESSURE_RANGE_MMHG,
    VITAL_DEFINITIONS,
    measurement_band,
)
from faker_healthcare.disease_correlations import DISEASE_CORRELATIONS


ICD10_RE = re.compile(r"^[A-Z]\d{2}(\.\d{1,3})?$")

# Every code in the shipped English catalogue, which is the same multiset as every other
# locale's (tests/test_locales.py enforces that), mapped to a disease name that carries
# it. Effects are keyed by code precisely so one table serves all six locales.
DISEASE_FOR_CODE = {data["icd10"]: name for name, data in DISEASE_CORRELATIONS.items()}

FLAG_FOR_LABEL = {CLINICAL_LABELS[key]: flag for flag, key in FLAG_LABEL_KEYS.items()}


@pytest.fixture
def faker() -> Faker:
    fake = Faker()
    fake.add_provider(HealthcareProvider)
    return fake


def _seeded(seed: int = 4242) -> Faker:
    fake = Faker()
    fake.add_provider(HealthcareProvider)
    fake.seed_instance(seed)
    return fake


class TestDefinitionIntegrity:
    """The tables themselves, before anything draws from them."""

    @pytest.mark.parametrize("name,definition", sorted(VITAL_DEFINITIONS.items()))
    def test_vital_bounds_are_ordered(self, name: str, definition: dict) -> None:
        assert definition["min_value"] <= definition["low"] < definition["high"] <= definition["max_value"], name
        assert definition["decimals"] >= 0, name
        assert definition["unit"], name

    @pytest.mark.parametrize("analyte,definition", sorted(LAB_DEFINITIONS.items()))
    def test_lab_bounds_are_ordered(self, analyte: str, definition: dict) -> None:
        assert definition["min_value"] <= definition["ref_low"] < definition["ref_high"] <= definition["max_value"], analyte
        assert definition["decimals"] >= 0, analyte
        assert definition["unit"], analyte

    def test_the_catalogue_covers_the_promised_ground(self) -> None:
        """A panel that cannot show renal, liver, thyroid, lipid and inflammatory work is not a panel."""
        expected = (
            # haematology
            ("haemoglobin", "wbc", "platelets", "ferritin", "inr"),
            # renal
            ("sodium", "potassium", "urea", "creatinine", "egfr"),
            # liver
            ("alt", "ast", "bilirubin_total", "albumin"),
            # metabolic and thyroid
            ("fasting_glucose", "hba1c", "tsh", "free_t4"),
            # lipids and inflammatory
            ("total_cholesterol", "ldl", "hdl", "triglycerides", "crp"),
        )
        assert len(LAB_DEFINITIONS) >= 18
        for group in expected:
            for analyte in group:
                assert analyte in LAB_DEFINITIONS, analyte

    def test_correlations_are_worth_shipping(self) -> None:
        """An uncorrelated lab table is what a consumer already has; this is the product."""
        assert len(CONDITION_LAB_EFFECTS) >= 20

    def test_the_drawn_pulse_pressure_cannot_cross_the_guaranteed_floor(self) -> None:
        """The documented invariant and the range actually drawn from must not diverge."""
        assert PULSE_PRESSURE_RANGE_MMHG[0] >= MIN_PULSE_PRESSURE_MMHG
        assert PULSE_PRESSURE_RANGE_MMHG[0] <= PULSE_PRESSURE_RANGE_MMHG[1]


class TestEffectTables:
    """The correlations are only useful if they point at things that exist."""

    @pytest.mark.parametrize("code", sorted({*CONDITION_LAB_EFFECTS, *CONDITION_VITAL_EFFECTS}))
    def test_every_code_is_a_shipped_condition(self, code: str) -> None:
        """Effects are keyed by ICD-10 code; an invented code correlates with nothing."""
        assert ICD10_RE.match(code), code
        assert code in DISEASE_FOR_CODE, f"{code} is not the code of any condition in the catalogue"

    @pytest.mark.parametrize("code,effects", sorted(CONDITION_LAB_EFFECTS.items()))
    def test_lab_effects_name_defined_analytes_and_directions(self, code: str, effects: dict) -> None:
        assert effects, f"{code}: an empty entry should be left out entirely"
        for analyte, direction in effects.items():
            assert analyte in LAB_DEFINITIONS, f"{code}: unknown analyte '{analyte}'"
            assert direction in ("low", "high"), f"{code}: unknown direction '{direction}'"

    @pytest.mark.parametrize("code,effects", sorted(CONDITION_VITAL_EFFECTS.items()))
    def test_vital_effects_name_defined_signs_and_directions(self, code: str, effects: dict) -> None:
        assert effects, f"{code}: an empty entry should be left out entirely"
        for name, direction in effects.items():
            assert name in VITAL_DEFINITIONS, f"{code}: unknown vital sign '{name}'"
            assert direction in ("low", "high"), f"{code}: unknown direction '{direction}'"

    def test_every_effect_has_a_band_to_land_in(self) -> None:
        """A direction with nowhere to go would produce an in-range value flagged abnormal.

        Oxygen saturation is the live example: its reference ceiling of 100% is also the
        physiological ceiling, so "oxygen saturation high" can never be honoured and
        must never be asked for.
        """
        for effects in CONDITION_LAB_EFFECTS.values():
            for analyte, direction in effects.items():
                lab = LAB_DEFINITIONS[analyte]
                measurement_band(lab["ref_low"], lab["ref_high"], lab["min_value"], lab["max_value"], lab["decimals"], direction)
        for effects in CONDITION_VITAL_EFFECTS.values():
            for name, direction in effects.items():
                vital = VITAL_DEFINITIONS[name]
                measurement_band(vital["low"], vital["high"], vital["min_value"], vital["max_value"], vital["decimals"], direction)

    def test_impossible_band_raises_rather_than_lying(self) -> None:
        definition = VITAL_DEFINITIONS["oxygen_saturation"]
        with pytest.raises(ValueError, match="No 'high' band"):
            measurement_band(definition["low"], definition["high"], definition["min_value"], definition["max_value"], definition["decimals"], "high")


class TestBloodPressure:
    def test_systolic_always_exceeds_diastolic(self, faker: Faker) -> None:
        """The invariant, over thousands of seeded draws rather than a handful of samples."""
        faker.seed_instance(20260816)
        for _ in range(5000):
            pressure = faker.blood_pressure()
            assert pressure["systolic"] - pressure["diastolic"] >= MIN_PULSE_PRESSURE_MMHG, pressure
            assert pressure["unit"] == "mmHg"

    @pytest.mark.parametrize("code", sorted(code for code, effects in CONDITION_VITAL_EFFECTS.items() if "systolic_bp" in effects))
    def test_the_invariant_survives_a_condition_that_moves_it(self, faker: Faker, code: str) -> None:
        disease = DISEASE_FOR_CODE[code]
        faker.seed_instance(7)
        for _ in range(2000):
            pressure = faker.blood_pressure(disease=disease)
            assert pressure["systolic"] - pressure["diastolic"] >= MIN_PULSE_PRESSURE_MMHG, pressure
            assert pressure["systolic"] > VITAL_DEFINITIONS["systolic_bp"]["high"], pressure

    def test_hypertension_actually_raises_the_pressure(self, faker: Faker) -> None:
        """The correlation has to bite: a hypertensive record must not read 112/70."""
        faker.seed_instance(11)
        normal = [faker.blood_pressure()["systolic"] for _ in range(500)]
        raised = [faker.blood_pressure(disease="Essential Hypertension")["systolic"] for _ in range(500)]
        assert max(normal) <= VITAL_DEFINITIONS["systolic_bp"]["high"]
        assert min(raised) > VITAL_DEFINITIONS["systolic_bp"]["high"]

    def test_unknown_disease_raises(self, faker: Faker) -> None:
        with pytest.raises(ValueError, match="Not A Disease"):
            faker.blood_pressure(disease="Not A Disease")


class TestVitalSignMeasurements:
    def test_measurement_has_a_localized_name_and_a_number(self, faker: Faker) -> None:
        for _ in range(200):
            measurement = faker.vital_sign_measurement()
            assert measurement["name"] in CLINICAL_LABELS.values()
            assert isinstance(measurement["value"], (int, float))
            assert measurement["unit"]

    @pytest.mark.parametrize("name", sorted(VITAL_DEFINITIONS))
    def test_a_named_sign_lands_in_its_reference_range(self, faker: Faker, name: str) -> None:
        definition = VITAL_DEFINITIONS[name]
        faker.seed_instance(3)
        for _ in range(300):
            value = faker.vital_sign_measurement(name=name)["value"]
            assert definition["low"] <= value <= definition["high"], (name, value)

    def test_the_full_set_covers_every_sign_and_keeps_the_bp_pair_coherent(self, faker: Faker) -> None:
        measurements = faker.vital_sign_measurements()
        assert len(measurements) == len(VITAL_DEFINITIONS)
        assert [m["name"] for m in measurements] == [CLINICAL_LABELS[name] for name in ("systolic_bp", "diastolic_bp", "heart_rate", "respiratory_rate", "temperature_c", "oxygen_saturation")]
        systolic, diastolic = measurements[0]["value"], measurements[1]["value"]
        assert systolic - diastolic >= MIN_PULSE_PRESSURE_MMHG

    @pytest.mark.parametrize("code,effects", sorted(CONDITION_VITAL_EFFECTS.items()))
    def test_a_condition_moves_exactly_the_signs_it_claims(self, faker: Faker, code: str, effects: dict) -> None:
        disease = DISEASE_FOR_CODE[code]
        faker.seed_instance(99)
        for _ in range(50):
            for name, definition in VITAL_DEFINITIONS.items():
                value = faker.vital_sign_measurement(name=name, disease=disease)["value"]
                direction = effects.get(name)
                if direction == "high":
                    assert value > definition["high"], (disease, name, value)
                elif direction == "low":
                    assert value < definition["low"], (disease, name, value)
                else:
                    assert definition["low"] <= value <= definition["high"], (disease, name, value)

    def test_unknown_vital_sign_raises(self, faker: Faker) -> None:
        with pytest.raises(ValueError, match="Unknown vital sign"):
            faker.vital_sign_measurement(name="blood_pressure")

    def test_unknown_disease_raises(self, faker: Faker) -> None:
        for call in (lambda: faker.vital_sign_measurement(disease="Not A Disease"), lambda: faker.vital_sign_measurements(disease="Not A Disease")):
            with pytest.raises(ValueError, match="Not A Disease"):
                call()

    def test_vital_sign_still_returns_the_label(self, faker: Faker) -> None:
        """The pre-existing string API is untouched: this feature is additive."""
        assert faker.vital_sign() in HealthcareProvider.vital_signs


class TestBodyMeasurements:
    def test_bmi_matches_the_height_and_weight_returned(self, faker: Faker) -> None:
        """The BMI is computed from these two numbers, never drawn beside them."""
        faker.seed_instance(2026)
        for _ in range(2000):
            body = faker.body_measurements()
            assert body["bmi"] == round(body["weight_kg"] / (body["height_cm"] / 100) ** 2, 1), body

    @pytest.mark.parametrize("sex", ["male", "female", "MALE", "Female"])
    def test_sex_is_accepted_case_insensitively_and_bounds_the_height(self, faker: Faker, sex: str) -> None:
        for _ in range(200):
            body = faker.body_measurements(sex=sex)
            assert 140.0 <= body["height_cm"] <= 205.0, body
            # The widest weight the clamps allow: BMI 15-55 over height 1.40-2.05 m.
            assert 29.0 <= body["weight_kg"] <= 232.0, body

    def test_ages_shift_the_numbers_without_breaking_them(self, faker: Faker) -> None:
        for age in (18, 40, 65, 90, 110):
            body = faker.body_measurements(age=age)
            assert body["bmi"] == round(body["weight_kg"] / (body["height_cm"] / 100) ** 2, 1)

    def test_unknown_sex_raises(self, faker: Faker) -> None:
        with pytest.raises(ValueError, match="Unknown sex"):
            faker.body_measurements(sex="unspecified")

    @pytest.mark.parametrize("age", [0, 12, 17, 130])
    def test_non_adult_age_raises_rather_than_extrapolating(self, faker: Faker, age: int) -> None:
        """Paediatric anthropometry needs growth references, not a stretched adult curve."""
        with pytest.raises(ValueError, match="outside the adult range"):
            faker.body_measurements(age=age)


class TestAlcohol:
    def test_distribution_is_skewed_the_way_survey_data_is(self, faker: Faker) -> None:
        faker.seed_instance(5)
        units = [faker.alcohol_units_per_week() for _ in range(5000)]
        assert all(isinstance(value, int) and 0 <= value <= 90 for value in units)
        assert units.count(0) > 500, "no abstainers at all"
        assert sum(1 for value in units if value <= 14) > len(units) * 0.5, "most people should be inside the guideline"
        assert max(units) > 35, "the tail is the point"

    @pytest.mark.parametrize(
        "units,expected_key",
        [
            (0, "alcohol_none"),
            (1, "alcohol_low_risk"),
            (14, "alcohol_low_risk"),
            (15, "alcohol_increasing_risk"),
            (35, "alcohol_increasing_risk"),
            (36, ALCOHOL_HIGHEST_CATEGORY),
            (200, ALCOHOL_HIGHEST_CATEGORY),
        ],
    )
    def test_categories_follow_the_documented_bands(self, faker: Faker, units: int, expected_key: str) -> None:
        assert faker.alcohol_intake_category(units=units) == CLINICAL_LABELS[expected_key]

    def test_category_of_a_drawn_intake_is_consistent(self, faker: Faker) -> None:
        faker.seed_instance(6)
        for _ in range(500):
            units = faker.alcohol_units_per_week()
            expected = next((key for bound, key in ALCOHOL_CATEGORY_THRESHOLDS if units <= bound), ALCOHOL_HIGHEST_CATEGORY)
            assert faker.alcohol_intake_category(units=units) == CLINICAL_LABELS[expected]

    def test_negative_intake_raises(self, faker: Faker) -> None:
        with pytest.raises(ValueError, match="cannot be negative"):
            faker.alcohol_intake_category(units=-1)


class TestLabResults:
    def test_flag_always_agrees_with_the_value(self, faker: Faker) -> None:
        """The flag is derived from the comparison, so it cannot drift from it."""
        faker.seed_instance(1234)
        diseases = [None, *(DISEASE_FOR_CODE[code] for code in CONDITION_LAB_EFFECTS)]
        for disease in diseases:
            for analyte in LAB_DEFINITIONS:
                for _ in range(20):
                    result = faker.lab_result(analyte=analyte, disease=disease)
                    flag = FLAG_FOR_LABEL[result["flag"]]
                    if result["value"] < result["reference_low"]:
                        assert flag == "low", result
                    elif result["value"] > result["reference_high"]:
                        assert flag == "high", result
                    else:
                        assert flag == "normal", result

    def test_reference_interval_is_the_analytes_own(self, faker: Faker) -> None:
        for analyte, definition in LAB_DEFINITIONS.items():
            result = faker.lab_result(analyte=analyte)
            assert result["reference_low"] == definition["ref_low"], analyte
            assert result["reference_high"] == definition["ref_high"], analyte
            assert result["unit"] == definition["unit"], analyte
            assert result["analyte"] == CLINICAL_LABELS[analyte], analyte

    def test_an_unaffected_analyte_stays_in_range(self, faker: Faker) -> None:
        faker.seed_instance(8)
        for _ in range(2000):
            result = faker.lab_result(analyte="sodium")
            assert result["reference_low"] <= result["value"] <= result["reference_high"], result
            assert FLAG_FOR_LABEL[result["flag"]] == "normal"

    @pytest.mark.parametrize("code,effects", sorted(CONDITION_LAB_EFFECTS.items()))
    def test_every_correlation_actually_bites(self, faker: Faker, code: str, effects: dict) -> None:
        """For each condition: the analytes it claims to move are outside the interval,
        in the stated direction, with a flag that says so — and nothing else is."""
        disease = DISEASE_FOR_CODE[code]
        faker.seed_instance(4242)
        for _ in range(20):
            for analyte, definition in LAB_DEFINITIONS.items():
                result = faker.lab_result(analyte=analyte, disease=disease)
                direction = effects.get(analyte)
                flag = FLAG_FOR_LABEL[result["flag"]]
                if direction == "high":
                    assert result["value"] > definition["ref_high"] and flag == "high", (disease, analyte, result)
                elif direction == "low":
                    assert result["value"] < definition["ref_low"] and flag == "low", (disease, analyte, result)
                else:
                    assert definition["ref_low"] <= result["value"] <= definition["ref_high"] and flag == "normal", (disease, analyte, result)

    def test_a_diabetic_record_reads_like_one(self, faker: Faker) -> None:
        """The worked example from the issue, spelled out rather than parametrized away."""
        faker.seed_instance(2)
        for _ in range(100):
            result = faker.lab_result(analyte="hba1c", disease="Type 2 Diabetes")
            assert result["value"] > 41
            assert result["unit"] == "mmol/mol"
            assert result["flag"] == CLINICAL_LABELS["flag_high"]

    def test_a_disease_without_effects_produces_in_range_values(self, faker: Faker) -> None:
        """An unlisted condition is an honest 'nothing specific here', not a silent lie."""
        assert "M17.9" not in CONDITION_LAB_EFFECTS
        faker.seed_instance(9)
        for _ in range(200):
            result = faker.lab_result(disease="Osteoarthritis")
            assert result["reference_low"] <= result["value"] <= result["reference_high"], result

    def test_a_random_analyte_for_a_correlated_disease_is_one_it_moves(self, faker: Faker) -> None:
        faker.seed_instance(10)
        affected = {CLINICAL_LABELS[analyte] for analyte in CONDITION_LAB_EFFECTS["N18.9"]}
        for _ in range(200):
            assert faker.lab_result(disease="Chronic Kidney Disease")["analyte"] in affected

    def test_unknown_analyte_raises(self, faker: Faker) -> None:
        with pytest.raises(ValueError, match="Unknown analyte"):
            faker.lab_result(analyte="cholesterol")

    def test_unknown_disease_raises(self, faker: Faker) -> None:
        with pytest.raises(ValueError, match="Not A Disease"):
            faker.lab_result(disease="Not A Disease")


class TestLabPanel:
    def test_panel_has_no_duplicate_analytes(self, faker: Faker) -> None:
        faker.seed_instance(13)
        for _ in range(500):
            panel = faker.lab_panel()
            analytes = [result["analyte"] for result in panel]
            assert len(analytes) == len(set(analytes)), analytes
            assert 4 <= len(panel) <= 8

    @pytest.mark.parametrize("code,effects", sorted(CONDITION_LAB_EFFECTS.items()))
    def test_a_diseased_panel_always_carries_that_diseases_analytes(self, faker: Faker, code: str, effects: dict) -> None:
        disease = DISEASE_FOR_CODE[code]
        faker.seed_instance(17)
        for _ in range(20):
            panel = faker.lab_panel(disease=disease)
            by_label = {result["analyte"]: result for result in panel}
            assert len(by_label) == len(panel), "duplicate analytes"
            for analyte, direction in effects.items():
                result = by_label[CLINICAL_LABELS[analyte]]
                assert FLAG_FOR_LABEL[result["flag"]] == direction, (disease, analyte, result)

    def test_size_is_honoured(self, faker: Faker) -> None:
        for size in (1, 5, len(LAB_DEFINITIONS)):
            assert len(faker.lab_panel(size=size)) == size

    def test_size_too_small_for_the_condition_raises(self, faker: Faker) -> None:
        """Truncating the pinned analytes would hand back a panel contradicting the diagnosis."""
        with pytest.raises(ValueError, match="must be at least"):
            faker.lab_panel(disease="Cirrhosis", size=2)

    @pytest.mark.parametrize("size", [0, -1, 99])
    def test_out_of_range_size_raises(self, faker: Faker, size: int) -> None:
        with pytest.raises(ValueError, match="size must be between"):
            faker.lab_panel(size=size)

    def test_unknown_disease_raises(self, faker: Faker) -> None:
        with pytest.raises(ValueError, match="Not A Disease"):
            faker.lab_panel(disease="Not A Disease")


class TestSeededDeterminism:
    """Two providers seeded alike must produce identical records, forever, per version."""

    def test_every_measurement_method_is_reproducible(self) -> None:
        first, second = _seeded(), _seeded()

        def draws(fake: Faker) -> list:
            return [
                [fake.blood_pressure() for _ in range(10)],
                [fake.blood_pressure(disease="Essential Hypertension") for _ in range(10)],
                [fake.vital_sign_measurement() for _ in range(10)],
                [fake.vital_sign_measurements(disease="Pneumonia") for _ in range(5)],
                [fake.body_measurements() for _ in range(10)],
                [fake.body_measurements(sex="female", age=55) for _ in range(10)],
                [fake.alcohol_units_per_week() for _ in range(25)],
                [fake.alcohol_intake_category() for _ in range(10)],
                [fake.lab_result() for _ in range(25)],
                [fake.lab_result(disease="Type 2 Diabetes") for _ in range(10)],
                [fake.lab_panel(disease="Chronic Kidney Disease") for _ in range(5)],
            ]

        assert draws(first) == draws(second)

    def test_panels_are_stable_across_processes(self) -> None:
        """Pools are iterated in definition order, never in set order.

        A panel assembled by iterating a set would vary with PYTHONHASHSEED, so the same
        seed would produce different records in two runs of the same test suite.
        """
        import subprocess
        import sys

        script = "\n".join(
            [
                "from faker import Faker",
                "from faker_healthcare import HealthcareProvider",
                "fake = Faker()",
                "fake.add_provider(HealthcareProvider)",
                "fake.seed_instance(4242)",
                "print([result['analyte'] for result in fake.lab_panel(disease='Cirrhosis', size=10)])",
            ]
        )
        outputs = set()
        for hash_seed in ("0", "1", "2"):
            completed = subprocess.run([sys.executable, "-c", script], capture_output=True, text=True, check=True, env={"PYTHONHASHSEED": hash_seed, "PATH": ""})
            outputs.add(completed.stdout)
        assert len(outputs) == 1, outputs
