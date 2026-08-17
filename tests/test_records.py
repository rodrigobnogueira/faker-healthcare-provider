"""Tests for the records half: medication orders, assessments, demographics, identifiers.

The theme is the same as `test_clinical_values.py`: a record is only worth generating if
its parts agree with each other. A dose has to be a dose of the drug beside it, a
severity band has to be the band the score falls in, a patient's sex and age have to be
possible for the condition on the record, and an identifier has to pass the checksum the
software under test will run on it.
"""

import re
import subprocess
import sys
from datetime import date

import pytest
from faker import Faker

from faker_healthcare import HealthcareProvider
from faker_healthcare.assessments import (
    ASSESSMENT_INSTRUMENTS,
    CONDITION_ASSESSMENTS,
    PSYCHIATRIC_ICD10_CHAPTER,
    band_label_key,
    is_clinically_significant,
)
from faker_healthcare.clinical_labels import CLINICAL_LABELS, MEDICATION_NAMES
from faker_healthcare.clinical_values import (
    ADULT_AGE_RANGE,
    AGE_BAND_RESOLUTION,
    BODY_PROFILES,
    DEMOGRAPHIC_CONSTRAINTS,
    PATIENT_AGE_RANGE,
    SEXES,
    age_bands_for,
    declared_age_range,
    is_paediatric_only,
    satisfies_demographics,
)
from faker_healthcare.constants import NON_DRUG_INTERVENTIONS
from faker_healthcare.disease_correlations import DISEASE_CORRELATIONS
from faker_healthcare.identifiers import (
    NHS_NUMBER_LENGTH,
    NHS_TEST_RANGE_PREFIX,
    format_nhs_number,
    nhs_check_digit,
    nhs_number_digits,
    nhs_number_is_valid,
)
from faker_healthcare.prescribing import (
    DOSE_LADDERS,
    FREQUENCY_IDS,
    MEDICATION_STATUS_BANDS,
    MEDICATION_STATUS_IDS,
    ROUTE_IDS,
    frequency_label_key,
    route_label_key,
    status_label_key,
)
from faker_healthcare.types import DemographicConstraint


DISEASE_FOR_CODE = {data["icd10"]: name for name, data in DISEASE_CORRELATIONS.items()}

# The conditions that state a skew rather than an absolute: a share of female patients,
# or a shape for the ages. Both are asserted against the configured figure below, over
# thousands of seeded draws, because a weighting nobody measures is a comment.
SEX_WEIGHTED = sorted((code, constraint["female_probability"]) for code, constraint in DEMOGRAPHIC_CONSTRAINTS.items() if "female_probability" in constraint)
AGE_BANDED = sorted((code, constraint["age_bands"]) for code, constraint in DEMOGRAPHIC_CONSTRAINTS.items() if "age_bands" in constraint)

# Enough draws that the sampling error on any share here is well under a percentage
# point, so the tolerance is a statement about the data and not about luck. The seeds are
# fixed, so a failure is reproducible rather than intermittent.
DEMOGRAPHIC_DRAWS = 4000
DEMOGRAPHIC_TOLERANCE = 0.03

STATUS_LABELS = {CLINICAL_LABELS[status_label_key(status)] for status in MEDICATION_STATUS_IDS}

# Every drug the English catalogue prescribes, which is what an order may name.
DRUG_POOL = {medication for data in DISEASE_CORRELATIONS.values() for medication in data["medications"]} - set(NON_DRUG_INTERVENTIONS)

# The one condition in the catalogue whose entire treatment list is non-drug: surgery,
# glasses, anti-glare lenses, magnifiers. It is the case that decides what an "order" for
# a condition with nothing to order looks like.
NO_DRUG_DISEASE = "Cataracts"


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


class TestDoseLadderIntegrity:
    """The tables themselves, before anything draws from them."""

    @pytest.mark.parametrize("substance,ladder", sorted(DOSE_LADDERS.items()))
    def test_ladder_is_well_formed(self, substance: str, ladder: dict) -> None:
        assert ladder["unit"], substance
        assert ladder["doses"], substance
        assert all(dose > 0 for dose in ladder["doses"]), substance
        assert list(ladder["doses"]) == sorted(ladder["doses"]), f"{substance}: doses are listed low to high"
        assert len(set(ladder["doses"])) == len(ladder["doses"]), substance
        assert ladder["route"] in ROUTE_IDS, substance
        assert ladder["frequencies"], substance
        assert set(ladder["frequencies"]) <= set(FREQUENCY_IDS), substance

    @pytest.mark.parametrize("substance", sorted(DOSE_LADDERS))
    def test_every_ladder_names_a_drug_the_catalogue_prescribes(self, substance: str) -> None:
        """A ladder for a substance no condition prescribes could never be reached."""
        assert substance in MEDICATION_NAMES, f"{substance} has no name in the base catalogue"
        assert MEDICATION_NAMES[substance] in DRUG_POOL, f"{MEDICATION_NAMES[substance]} is not prescribed by any condition"

    def test_ladders_and_names_are_the_same_set(self) -> None:
        """Neither half may grow without the other: an unnamed ladder is unreachable,
        and a named substance with no ladder would silently produce a doseless order."""
        assert set(DOSE_LADDERS) == set(MEDICATION_NAMES)

    def test_no_intervention_has_a_ladder(self) -> None:
        """Surgery has no dose; a ladder for one would put a milligram figure on it."""
        assert not {MEDICATION_NAMES[substance] for substance in DOSE_LADDERS} & set(NON_DRUG_INTERVENTIONS)

    def test_every_route_and_frequency_id_is_used_and_labelled(self) -> None:
        """An ID nothing uses is dead weight; an ID nothing names would raise at runtime."""
        used_routes = {ladder["route"] for ladder in DOSE_LADDERS.values()}
        used_frequencies = {frequency for ladder in DOSE_LADDERS.values() for frequency in ladder["frequencies"]}
        assert used_routes == set(ROUTE_IDS)
        assert used_frequencies == set(FREQUENCY_IDS)
        for route in ROUTE_IDS:
            assert route_label_key(route) in CLINICAL_LABELS
        for frequency in FREQUENCY_IDS:
            assert frequency_label_key(frequency) in CLINICAL_LABELS

    def test_status_bands_cover_every_roll_and_every_status(self) -> None:
        assert MEDICATION_STATUS_BANDS[-1][0] == 100
        assert [band[0] for band in MEDICATION_STATUS_BANDS] == sorted(band[0] for band in MEDICATION_STATUS_BANDS)
        assert {band[1] for band in MEDICATION_STATUS_BANDS} == set(MEDICATION_STATUS_IDS)

    def test_the_ladders_reach_most_of_the_catalogue(self) -> None:
        """Coverage is the difference between a dosed record and a doseless one."""
        dosed = {MEDICATION_NAMES[substance] for substance in DOSE_LADDERS}
        covered = [name for name, data in DISEASE_CORRELATIONS.items() if set(data["medications"]) & dosed]
        assert len(covered) > 0.7 * len(DISEASE_CORRELATIONS)


class TestMedicationOrders:
    def test_order_shape_and_labels(self, faker: Faker) -> None:
        faker.seed_instance(101)
        for _ in range(500):
            order = faker.medication_order()
            assert set(order) == {"medication", "dose", "unit", "route", "frequency", "status"}
            assert order["medication"] in DRUG_POOL
            assert order["status"] in STATUS_LABELS

    def test_a_drawn_order_is_always_dosed(self, faker: Faker) -> None:
        """Without a disease the pool IS the substances with a ladder, so every order
        drawn at random carries a real dose rather than a None."""
        faker.seed_instance(102)
        by_name = {name: substance for substance, name in MEDICATION_NAMES.items()}
        for _ in range(500):
            order = faker.medication_order()
            ladder = DOSE_LADDERS[by_name[order["medication"]]]
            assert order["dose"] in ladder["doses"], order
            assert order["unit"] == ladder["unit"], order
            assert order["route"] == CLINICAL_LABELS[route_label_key(ladder["route"])], order
            assert order["frequency"] in {CLINICAL_LABELS[frequency_label_key(frequency)] for frequency in ladder["frequencies"]}, order

    def test_every_status_is_reachable(self, faker: Faker) -> None:
        """past / current / future is the split the requester asked for; all three must
        actually occur, and 'current' must be the common one."""
        faker.seed_instance(103)
        statuses = [faker.medication_order()["status"] for _ in range(2000)]
        assert set(statuses) == STATUS_LABELS
        current = CLINICAL_LABELS[status_label_key("current")]
        assert statuses.count(current) > len(statuses) * 0.4

    def test_a_condition_orders_its_own_medications(self, faker: Faker) -> None:
        faker.seed_instance(104)
        interventions = set(NON_DRUG_INTERVENTIONS)
        for disease, data in DISEASE_CORRELATIONS.items():
            if disease == NO_DRUG_DISEASE:
                continue
            expected = set(data["medications"]) - interventions
            for _ in range(5):
                assert faker.medication_order(disease=disease)["medication"] in expected, disease

    def test_a_condition_prefers_the_medications_it_can_dose(self, faker: Faker) -> None:
        """Same shape as lab_result(disease=...) preferring the analytes it moves."""
        faker.seed_instance(105)
        dosed = {MEDICATION_NAMES[substance] for substance in DOSE_LADDERS}
        prescribed = set(DISEASE_CORRELATIONS["Type 2 Diabetes"]["medications"]) & dosed
        assert prescribed
        for _ in range(200):
            order = faker.medication_order(disease="Type 2 Diabetes")
            assert order["medication"] in prescribed
            assert order["dose"] is not None

    def test_an_undosed_substance_returns_none_rather_than_a_number(self, faker: Faker) -> None:
        """Tuberculosis is treated with four drugs this package has no ladder for. The
        honest answer is no dose, not a plausible-looking milligram figure."""
        faker.seed_instance(106)
        for _ in range(50):
            order = faker.medication_order(disease="Tuberculosis")
            assert order["medication"] in set(DISEASE_CORRELATIONS["Tuberculosis"]["medications"])
            assert order["dose"] is None and order["unit"] is None
            assert order["route"] is None and order["frequency"] is None
            assert order["status"] in STATUS_LABELS

    def test_orders_never_include_a_non_drug_intervention(self, faker: Faker) -> None:
        faker.seed_instance(107)
        interventions = set(NON_DRUG_INTERVENTIONS)
        for disease in ("Chronic Kidney Disease", "Celiac Disease", "Hearing Loss", "Iron Deficiency Anemia"):
            for order in faker.medication_orders(disease=disease, count=4):
                assert order["medication"] not in interventions, (disease, order)

    def test_orders_are_distinct_and_honour_count(self, faker: Faker) -> None:
        faker.seed_instance(108)
        for _ in range(200):
            orders = faker.medication_orders()
            names = [order["medication"] for order in orders]
            assert len(names) == len(set(names))
            assert 1 <= len(orders) <= 4
        assert len(faker.medication_orders(count=6)) == 6
        assert len(faker.medication_orders(disease="Asthma", count=99)) == len(set(DISEASE_CORRELATIONS["Asthma"]["medications"]) - set(NON_DRUG_INTERVENTIONS))

    def test_a_condition_with_no_drug_at_all(self, faker: Faker) -> None:
        """Cataracts prescribes surgery, glasses and magnifiers. `medication_orders`
        returns an empty list; a single order cannot be produced and says so."""
        assert faker.medication_orders(disease=NO_DRUG_DISEASE) == []
        with pytest.raises(ValueError, match="prescribes no drug"):
            faker.medication_order(disease=NO_DRUG_DISEASE)

    def test_unknown_disease_and_bad_count_raise(self, faker: Faker) -> None:
        for call in (lambda: faker.medication_order(disease="Not A Disease"), lambda: faker.medication_orders(disease="Not A Disease")):
            with pytest.raises(ValueError, match="Not A Disease"):
                call()
        with pytest.raises(ValueError, match="count must be at least 1"):
            faker.medication_orders(count=0)


class TestAssessmentBoundary:
    """The legal boundary, asserted rather than only documented.

    A generated assessment carries an instrument name, a score, a maximum and a band.
    Never the items, the questions, the response options or the scoring instructions —
    most of these instruments are under active copyright, and reproducing their text
    inside an MIT-licensed package would redistribute someone else's work under a licence
    they never granted. These tests fail if a future change starts adding that content.
    """

    ALLOWED_DEFINITION_KEYS = {"name", "max_score", "higher_is_worse", "bands", "significant_from"}
    ALLOWED_RESULT_KEYS = {"instrument", "score", "max_score", "severity"}

    @pytest.mark.parametrize("instrument,definition", sorted(ASSESSMENT_INSTRUMENTS.items()))
    def test_definition_carries_nothing_but_the_scored_range(self, instrument: str, definition: dict) -> None:
        assert set(definition) == self.ALLOWED_DEFINITION_KEYS, f"{instrument}: only the scored range belongs here, never item content"

    def test_result_carries_nothing_but_the_four_fields(self, faker: Faker) -> None:
        for instrument in ASSESSMENT_INSTRUMENTS:
            assert set(faker.assessment_score(instrument=instrument)) == self.ALLOWED_RESULT_KEYS

    def test_only_the_six_agreed_instruments_ship(self) -> None:
        """A seventh needs a maintainer decision, not a table entry."""
        assert set(ASSESSMENT_INSTRUMENTS) == {"phq9", "gad7", "mmse", "madrs", "audit_c", "cage"}

    def test_no_shipped_string_looks_like_item_content(self) -> None:
        """Instrument names are short identifiers; a sentence here would be item text."""
        for definition in ASSESSMENT_INSTRUMENTS.values():
            assert len(definition["name"]) <= 10, definition["name"]
            assert "?" not in definition["name"]


class TestAssessmentScores:
    @pytest.mark.parametrize("instrument,definition", sorted(ASSESSMENT_INSTRUMENTS.items()))
    def test_bands_cover_the_whole_scale_exactly_once(self, instrument: str, definition: dict) -> None:
        bounds = [upper for upper, _ in definition["bands"]]
        assert bounds == sorted(bounds), instrument
        assert bounds[-1] == definition["max_score"], instrument
        assert all(band_label_key(instrument, score) for score in range(definition["max_score"] + 1)), instrument
        assert all(key in CLINICAL_LABELS for _, key in definition["bands"]), instrument

    @pytest.mark.parametrize("instrument", sorted(ASSESSMENT_INSTRUMENTS))
    def test_score_stays_in_range_and_matches_its_band(self, faker: Faker, instrument: str) -> None:
        faker.seed_instance(201)
        definition = ASSESSMENT_INSTRUMENTS[instrument]
        for _ in range(500):
            result = faker.assessment_score(instrument=instrument)
            assert result["instrument"] == definition["name"]
            assert result["max_score"] == definition["max_score"]
            assert 0 <= result["score"] <= result["max_score"]
            assert result["severity"] == CLINICAL_LABELS[band_label_key(instrument, result["score"])], result

    def test_scores_cluster_at_the_healthy_end_of_each_scale(self, faker: Faker) -> None:
        """Including the inverted one. A flat draw would make the average PHQ-9 in a
        screening population moderately depressed and the average MMSE demented."""
        faker.seed_instance(202)
        phq9 = [faker.assessment_score(instrument="phq9")["score"] for _ in range(2000)]
        mmse = [faker.assessment_score(instrument="mmse")["score"] for _ in range(2000)]
        assert sum(phq9) / len(phq9) < 27 * 0.35, "PHQ-9 scores should sit low"
        assert sum(mmse) / len(mmse) > 30 * 0.65, "MMSE scores should sit HIGH — on this one a low score is the abnormal one"
        assert max(phq9) > 20 and min(mmse) < 15, "the abnormal end must still be reachable"

    @pytest.mark.parametrize("code,instruments", sorted(CONDITION_ASSESSMENTS.items()))
    def test_a_correlated_condition_scores_past_the_cut_off(self, faker: Faker, code: str, instruments: tuple) -> None:
        """A depression record must not come back with a PHQ-9 of 2, and a dementia
        record must not come back with an MMSE of 30."""
        disease = DISEASE_FOR_CODE[code]
        faker.seed_instance(203)
        for instrument in instruments:
            for _ in range(200):
                result = faker.assessment_score(instrument=instrument, disease=disease)
                assert is_clinically_significant(instrument, result["score"]), (disease, instrument, result)

    def test_a_random_instrument_for_a_correlated_condition_is_one_it_uses(self, faker: Faker) -> None:
        faker.seed_instance(204)
        expected = {ASSESSMENT_INSTRUMENTS[instrument]["name"] for instrument in CONDITION_ASSESSMENTS["F32.9"]}
        for _ in range(200):
            assert faker.assessment_score(disease="Depression")["instrument"] in expected

    def test_an_uncorrelated_condition_still_scores(self, faker: Faker) -> None:
        """Schizophrenia is rated with instruments this package does not ship, so it has
        no entry — it gets an instrument, not a wrong correlation."""
        assert "F20.9" not in CONDITION_ASSESSMENTS
        faker.seed_instance(205)
        for _ in range(100):
            result = faker.assessment_score(disease="Schizophrenia")
            assert result["instrument"] in {definition["name"] for definition in ASSESSMENT_INSTRUMENTS.values()}

    def test_unknown_instrument_and_disease_raise(self, faker: Faker) -> None:
        with pytest.raises(ValueError, match="Unknown assessment instrument"):
            faker.assessment_score(instrument="hamd")
        with pytest.raises(ValueError, match="Not A Disease"):
            faker.assessment_score(disease="Not A Disease")

    def test_band_helper_rejects_an_impossible_score(self) -> None:
        with pytest.raises(ValueError, match="outside the range"):
            band_label_key("gad7", 22)


class TestDemographicConstraints:
    """No male preeclampsia patients, no adults with bronchiolitis — and no 49% male
    breast cancer either, which is what "unconstrained" used to mean."""

    @pytest.mark.parametrize("code", sorted(DEMOGRAPHIC_CONSTRAINTS))
    def test_every_constrained_code_is_a_shipped_condition(self, code: str) -> None:
        assert code in DISEASE_FOR_CODE, f"{code} is not the code of any condition in the catalogue"

    def test_the_two_sex_tables_agree(self) -> None:
        """SEXES is what `patient()` draws from and BODY_PROFILES is what
        `body_measurements()` indexes; a sex in one and not the other would be a sex the
        record could carry but the anthropometry could not measure."""
        assert set(SEXES) == set(BODY_PROFILES)

    @pytest.mark.parametrize("code,constraint", sorted(DEMOGRAPHIC_CONSTRAINTS.items()))
    def test_constraints_are_well_formed_and_satisfiable(self, code: str, constraint: DemographicConstraint) -> None:
        assert set(constraint) <= {"sex", "female_probability", "min_age", "max_age", "age_bands"}, code
        assert constraint.get("sex", "male") in SEXES, code
        assert not ("sex" in constraint and "female_probability" in constraint), f"{code} states both a lock and a weight, which contradict each other"
        assert 0 < constraint.get("female_probability", 0.5) < 1, f"{code} weights a sex at 0 or 1, which is a lock and belongs in 'sex'"
        assert not ("age_bands" in constraint and {"min_age", "max_age"} & set(constraint)), f"{code} declares its age bounds twice; the bands already carry them"
        minimum, maximum = declared_age_range(constraint)
        assert PATIENT_AGE_RANGE[0] <= minimum <= maximum <= PATIENT_AGE_RANGE[1], code

    @pytest.mark.parametrize("code,bands", AGE_BANDED)
    def test_age_bands_are_contiguous_and_account_for_every_patient(self, code: str, bands: tuple) -> None:
        """A gap between two bands would be an age range the condition silently never
        generates, and shares that do not sum to 100 would mean the shape was guessed."""
        assert sum(share for share, _, _ in bands) == 100, code
        assert all(share > 0 for share, _, _ in bands), code
        assert all(lowest <= highest for _, lowest, highest in bands), code
        assert all(earlier[2] + 1 == later[1] for earlier, later in zip(bands, bands[1:])), f"{code} has bands that overlap, descend or leave a gap"

    @pytest.mark.parametrize("code", sorted(DEMOGRAPHIC_CONSTRAINTS))
    def test_a_constrained_condition_only_gets_patients_who_could_have_it(self, faker: Faker, code: str) -> None:
        disease = DISEASE_FOR_CODE[code]
        faker.seed_instance(301)
        for _ in range(300):
            patient = faker.patient(disease=disease)
            assert satisfies_demographics(code, patient["sex"], patient["age"]), (disease, patient["sex"], patient["age"])

    def test_no_male_patient_ever_gets_a_female_only_condition(self, faker: Faker) -> None:
        """The failure the constraint table exists for, asserted over the whole catalogue
        rather than only over the conditions that have an entry."""
        female_only = {code for code, constraint in DEMOGRAPHIC_CONSTRAINTS.items() if constraint.get("sex") == "female"}
        male_only = {code for code, constraint in DEMOGRAPHIC_CONSTRAINTS.items() if constraint.get("sex") == "male"}
        assert len(female_only) == 7 and len(male_only) == 3
        faker.seed_instance(302)
        for _ in range(3000):
            patient = faker.patient()
            if patient["sex"] == "male":
                assert patient["icd10"] not in female_only, patient
            else:
                assert patient["icd10"] not in male_only, patient

    def test_no_adult_ever_gets_a_paediatric_only_condition(self, faker: Faker) -> None:
        paediatric = {code for code in DEMOGRAPHIC_CONSTRAINTS if is_paediatric_only(code)}
        assert paediatric, "the paediatric-only set is the point of this test"
        faker.seed_instance(303)
        for _ in range(3000):
            patient = faker.patient()
            if patient["icd10"] in paediatric:
                assert patient["age"] < ADULT_AGE_RANGE[0], patient

    def test_an_unconstrained_condition_can_be_either_sex(self, faker: Faker) -> None:
        """The constraint table must not accidentally pin conditions it says nothing about."""
        faker.seed_instance(304)
        assert {faker.patient(disease="Type 2 Diabetes")["sex"] for _ in range(100)} == {"male", "female"}

    @pytest.mark.parametrize("code,probability", SEX_WEIGHTED)
    def test_a_weighted_condition_lands_on_the_split_it_declares(self, faker: Faker, code: str, probability: float) -> None:
        """The measurement the weighting exists for. Breast cancer generated 49% male
        patients while the table was binary — a fifty-fold error against the real figure
        of under 1%, and one nothing in the suite would have noticed."""
        disease = DISEASE_FOR_CODE[code]
        faker.seed_instance(305)
        patients = [faker.patient(disease=disease) for _ in range(DEMOGRAPHIC_DRAWS)]
        observed = sum(patient["sex"] == "female" for patient in patients) / DEMOGRAPHIC_DRAWS
        assert abs(observed - probability) <= DEMOGRAPHIC_TOLERANCE, f"{disease}: {observed:.3f} female against a configured {probability}"

    @pytest.mark.parametrize("code,probability", SEX_WEIGHTED)
    def test_a_weighting_stays_a_weighting_and_never_becomes_a_lock(self, faker: Faker, code: str, probability: float) -> None:
        """The other half of the same claim: a 0.99 weighting must still produce the 1%,
        because men with breast cancer are a real patient group, not a rounding error."""
        disease = DISEASE_FOR_CODE[code]
        faker.seed_instance(306)
        assert {faker.patient(disease=disease)["sex"] for _ in range(DEMOGRAPHIC_DRAWS)} == {"male", "female"}, disease

    @pytest.mark.parametrize("code,bands", AGE_BANDED)
    def test_a_banded_condition_lands_on_the_age_shape_it_declares(self, faker: Faker, code: str, bands: tuple) -> None:
        disease = DISEASE_FOR_CODE[code]
        faker.seed_instance(307)
        ages = [faker.patient(disease=disease)["age"] for _ in range(DEMOGRAPHIC_DRAWS)]
        assert bands[0][1] <= min(ages) and max(ages) <= bands[-1][2], f"{disease}: ages {min(ages)}-{max(ages)} escape its bands"
        for share, lowest, highest in bands:
            observed = sum(lowest <= age <= highest for age in ages) / DEMOGRAPHIC_DRAWS
            assert abs(observed - share / 100) <= DEMOGRAPHIC_TOLERANCE, f"{disease}: {observed:.3f} of patients aged {lowest}-{highest} against a configured {share}%"

    def test_an_adult_only_draw_drops_the_paediatric_band_and_keeps_the_rest_in_proportion(self) -> None:
        """`patient_record()` asks for adults only. Cystic fibrosis loses its 0-17 band
        entirely, and the three that survive must keep their sizes relative to each other
        rather than being flattened into a uniform adult draw."""
        bands = age_bands_for(DEMOGRAPHIC_CONSTRAINTS["E84.9"], (ADULT_AGE_RANGE[0], PATIENT_AGE_RANGE[1]))
        assert [(lowest, highest) for _, lowest, highest in bands] == [(18, 39), (40, 59), (60, 80)]
        total = sum(weight for weight, _, _ in bands)
        assert [round(weight / total, 2) for weight, _, _ in bands] == [0.73, 0.2, 0.07]

    def test_a_half_clipped_band_carries_half_its_share(self) -> None:
        """Clipping a band in half has to halve its weight, because the draw inside a
        band is uniform — otherwise clipping quietly changes the shape it kept."""
        bands = age_bands_for({"age_bands": ((50, 0, 19), (50, 20, 39))}, (10, 39))
        assert bands == ((25 * AGE_BAND_RESOLUTION, 10, 19), (50 * AGE_BAND_RESOLUTION, 20, 39))

    def test_an_unbanded_condition_is_one_uniform_band(self) -> None:
        """Which is what keeps the common case a single draw from a single range."""
        assert age_bands_for({}, PATIENT_AGE_RANGE) == ((AGE_BAND_RESOLUTION,) + PATIENT_AGE_RANGE,)
        assert age_bands_for({"min_age": 45}, PATIENT_AGE_RANGE) == ((AGE_BAND_RESOLUTION, 45, PATIENT_AGE_RANGE[1]),)

    def test_bands_that_survive_nothing_raise_rather_than_returning_an_impossible_age(self) -> None:
        with pytest.raises(ValueError, match="No age between"):
            age_bands_for({"age_bands": ((100, 0, 2),)}, (ADULT_AGE_RANGE[0], PATIENT_AGE_RANGE[1]))

    def test_unknown_disease_raises(self, faker: Faker) -> None:
        with pytest.raises(ValueError, match="Not A Disease"):
            faker.patient(disease="Not A Disease")


class TestDatesOfBirth:
    @pytest.mark.parametrize("reference", [date(2026, 8, 16), date(2024, 2, 29), date(2025, 1, 1), date(2025, 12, 31)])
    def test_date_of_birth_agrees_with_the_age_beside_it(self, faker: Faker, reference: date) -> None:
        """Including across a leap day, which is where naive year arithmetic breaks."""
        faker.seed_instance(401)
        for _ in range(500):
            patient = faker.patient(reference_date=reference)
            born = patient["date_of_birth"]
            age = reference.year - born.year - ((reference.month, reference.day) < (born.month, born.day))
            assert age == patient["age"], patient

    def test_reference_date_is_the_only_clock_read_and_can_be_pinned(self, faker: Faker) -> None:
        """Two providers seeded alike and given the same reference date agree exactly —
        which is what makes a fixture generated today still reproducible next year."""
        first, second = _seeded(7), _seeded(7)
        reference = date(2020, 6, 15)
        assert [first.patient(reference_date=reference) for _ in range(20)] == [second.patient(reference_date=reference) for _ in range(20)]


class TestNhsNumber:
    # Published examples of valid NHS numbers, used here as an independent check on the
    # Modulus 11 implementation: both are widely documented in NHS material, and both
    # have to come out valid without the code having been written around them.
    PUBLISHED_VALID = ("9434765919", "4010232137")

    @pytest.mark.parametrize("number", PUBLISHED_VALID)
    def test_published_examples_validate(self, number: str) -> None:
        assert nhs_check_digit(number[:-1]) == int(number[-1])
        assert nhs_number_is_valid(number)
        assert nhs_number_is_valid(format_nhs_number(number))

    @pytest.mark.parametrize("number", PUBLISHED_VALID)
    def test_a_transcription_error_is_caught(self, number: str) -> None:
        """The whole point of a check digit: change one digit and it stops validating."""
        broken = [number[:index] + str((int(digit) + 1) % 10) + number[index + 1 :] for index, digit in enumerate(number)]
        assert not any(nhs_number_is_valid(candidate) for candidate in broken)

    def test_generated_numbers_are_valid_and_conventionally_formatted(self, faker: Faker) -> None:
        faker.seed_instance(501)
        for _ in range(2000):
            number = faker.nhs_number()
            assert re.fullmatch(r"\d{3} \d{3} \d{4}", number), number
            assert nhs_number_is_valid(number), number
            assert len(nhs_number_digits(number)) == NHS_NUMBER_LENGTH

    def test_the_default_is_the_reserved_test_range(self, faker: Faker) -> None:
        """A generated identifier must not be able to collide with a real patient's."""
        faker.seed_instance(502)
        for _ in range(2000):
            assert nhs_number_digits(faker.nhs_number()).startswith(NHS_TEST_RANGE_PREFIX)

    def test_the_unreserved_range_is_opt_in_and_reaches_beyond_999(self, faker: Faker) -> None:
        faker.seed_instance(503)
        numbers = [nhs_number_digits(faker.nhs_number(official_test_range=False)) for _ in range(500)]
        assert all(nhs_number_is_valid(number) for number in numbers)
        assert not all(number.startswith(NHS_TEST_RANGE_PREFIX) for number in numbers)
        assert all(not number.startswith("0") for number in numbers)

    def test_generated_numbers_are_not_all_the_same(self, faker: Faker) -> None:
        faker.seed_instance(504)
        assert len({faker.nhs_number() for _ in range(500)}) > 450

    def test_the_helpers_reject_malformed_input(self) -> None:
        with pytest.raises(ValueError, match="stem is exactly"):
            nhs_check_digit("12345")
        with pytest.raises(ValueError, match="is exactly"):
            format_nhs_number("123")
        assert not nhs_number_is_valid("not a number")
        assert not nhs_number_is_valid("123")


class TestPatientRecord:
    REQUIRED_KEYS = {
        "disease",
        "icd10",
        "symptoms",
        "medications",
        "medical_specialty",
        "sex",
        "age",
        "date_of_birth",
        "vital_signs",
        "lab_panel",
        "medication_orders",
    }

    def test_record_carries_every_part_and_they_agree(self, faker: Faker) -> None:
        faker.seed_instance(601)
        for _ in range(200):
            record = faker.patient_record()
            assert self.REQUIRED_KEYS <= set(record)
            assert set(record) <= self.REQUIRED_KEYS | {"assessment"}
            data = DISEASE_CORRELATIONS[record["disease"]]
            assert record["icd10"] == data["icd10"]
            assert set(record["symptoms"]) <= set(data["symptoms"])
            assert set(record["medications"]) <= set(data["medications"])
            assert len(record["vital_signs"]) == 6
            assert record["lab_panel"]
            assert satisfies_demographics(record["icd10"], record["sex"], record["age"])

    def test_records_are_adults_because_the_reference_data_is(self, faker: Faker) -> None:
        faker.seed_instance(602)
        for _ in range(500):
            assert faker.patient_record()["age"] >= ADULT_AGE_RANGE[0]

    @pytest.mark.parametrize("disease", sorted(DISEASE_FOR_CODE[code] for code in DEMOGRAPHIC_CONSTRAINTS if is_paediatric_only(code)))
    def test_a_paediatric_only_condition_refuses_rather_than_ageing_up(self, faker: Faker, disease: str) -> None:
        with pytest.raises(ValueError, match="occurs only in children"):
            faker.patient_record(disease=disease)

    def test_the_measurements_correlate_with_the_diagnosis(self, faker: Faker) -> None:
        """The record is the whole library in one call, so the correlations must survive
        the trip: a diabetic record's HbA1c is still high inside it."""
        faker.seed_instance(603)
        record = faker.patient_record(disease="Type 2 Diabetes")
        hba1c = next(result for result in record["lab_panel"] if result["analyte"] == CLINICAL_LABELS["hba1c"])
        assert hba1c["value"] > hba1c["reference_high"]
        assert hba1c["flag"] == CLINICAL_LABELS["flag_high"]
        assert {order["medication"] for order in record["medication_orders"]} <= set(DISEASE_CORRELATIONS["Type 2 Diabetes"]["medications"])

    def test_an_assessment_appears_for_psychiatric_conditions_and_only_there(self, faker: Faker) -> None:
        faker.seed_instance(604)
        for _ in range(400):
            record = faker.patient_record()
            expected = record["icd10"].startswith(PSYCHIATRIC_ICD10_CHAPTER) or record["icd10"] in CONDITION_ASSESSMENTS
            assert ("assessment" in record) is expected, record["disease"]

    @pytest.mark.parametrize("disease", ["Depression", "Anxiety Disorder", "Bipolar Disorder", "Alzheimer's Disease"])
    def test_the_psychiatric_record_carries_a_scored_instrument(self, faker: Faker, disease: str) -> None:
        record = faker.patient_record(disease=disease)
        assessment = record["assessment"]
        assert assessment["instrument"] in {definition["name"] for definition in ASSESSMENT_INSTRUMENTS.values()}
        assert 0 <= assessment["score"] <= assessment["max_score"]

    def test_unknown_disease_raises(self, faker: Faker) -> None:
        with pytest.raises(ValueError, match="Not A Disease"):
            faker.patient_record(disease="Not A Disease")


class TestSeededDeterminism:
    """Two providers seeded alike must produce identical records, forever, per version."""

    def test_every_record_method_is_reproducible(self) -> None:
        first, second = _seeded(), _seeded()
        reference = date(2026, 1, 2)

        def draws(fake: Faker) -> list:
            return [
                [fake.medication_order() for _ in range(20)],
                [fake.medication_order(disease="Essential Hypertension") for _ in range(10)],
                [fake.medication_orders(disease="Type 2 Diabetes") for _ in range(10)],
                [fake.assessment_score() for _ in range(20)],
                [fake.assessment_score(disease="Depression") for _ in range(10)],
                [fake.nhs_number() for _ in range(20)],
                [fake.nhs_number(official_test_range=False) for _ in range(20)],
                [fake.patient(reference_date=reference) for _ in range(10)],
                [fake.patient_record(reference_date=reference) for _ in range(5)],
            ]

        assert draws(first) == draws(second)

    def test_records_are_stable_across_processes(self) -> None:
        """Pools are iterated in definition order, never in set order — the same property
        the lab panel needs, and the same subprocess check, because a record assembled
        from a set would vary with PYTHONHASHSEED between runs."""
        script = "\n".join(
            [
                "from datetime import date",
                "from faker import Faker",
                "from faker_healthcare import HealthcareProvider",
                "fake = Faker()",
                "fake.add_provider(HealthcareProvider)",
                "fake.seed_instance(4242)",
                "print([order['medication'] for order in fake.medication_orders(count=4)])",
                "print(fake.patient_record(reference_date=date(2026, 1, 2))['disease'])",
                "print(fake.nhs_number())",
            ]
        )
        outputs = set()
        for hash_seed in ("0", "1", "2"):
            completed = subprocess.run([sys.executable, "-c", script], capture_output=True, text=True, check=True, env={"PYTHONHASHSEED": hash_seed, "PATH": ""})
            outputs.add(completed.stdout)
        assert len(outputs) == 1, outputs
