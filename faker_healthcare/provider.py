from collections.abc import Mapping
from typing import TypedDict

from faker.providers import BaseProvider, ElementsType

from .clinical_labels import CLINICAL_LABELS
from .clinical_values import (
    ADULT_AGE_RANGE,
    ALCOHOL_WEEKLY_BANDS,
    BMI_DRIFT_AGE_RANGE,
    BMI_DRIFT_PER_YEAR,
    BMI_LIMITS,
    BMI_MEAN,
    BMI_SD,
    BODY_PROFILES,
    CONDITION_LAB_EFFECTS,
    CONDITION_VITAL_EFFECTS,
    FLAG_LABEL_KEYS,
    HEIGHT_LOSS_CM_PER_YEAR_AFTER,
    LAB_DEFINITIONS,
    PULSE_PRESSURE_RANGE_MMHG,
    SEVERITY_RESOLUTION,
    SEVERITY_TIERS,
    VITAL_DEFINITIONS,
    alcohol_category_key,
    flag_for,
    from_steps,
    measurement_band,
    to_steps,
)
from .constants import (
    ALLERGIES,
    BLOOD_TYPES,
    BRAND_DRUG_NAMES,
    HOSPITAL_DEPARTMENTS,
    INSURANCE_PLANS,
    MEDICAL_PROCEDURES,
    NON_DRUG_INTERVENTIONS,
    VITAL_SIGNS,
)
from .types import (
    BloodPressure,
    BodyMeasurements,
    Direction,
    DiseaseData,
    LabDefinition,
    LabResult,
    VitalDefinition,
    VitalMeasurement,
)


class PatientScenario(TypedDict):
    disease: str
    icd10: str
    symptoms: list[str]
    medications: list[str]
    medical_specialty: str


class HealthcareProvider(BaseProvider):
    """Faker provider for generating healthcare/medical fake data.

    This provider generates correlated clinical data based on medical relationships
    between diseases, symptoms, medications, and ICD-10 codes.

    MEDICAL DISCLAIMER: This data is for TESTING AND DEVELOPMENT PURPOSES ONLY.
    It should NOT be used for actual medical diagnosis, treatment, or healthcare decisions.
    """

    _disease_correlations: dict[str, DiseaseData] | None = None

    @property
    def disease_correlations(self) -> dict[str, DiseaseData]:
        """Lazy-loaded disease correlations data (locale-specific)."""
        if self._disease_correlations is None:
            self._disease_correlations = self._load_disease_correlations()
        return self._disease_correlations

    def _load_disease_correlations(self) -> dict[str, DiseaseData]:
        """Load disease correlations. Override in locale providers."""
        from .disease_correlations import DISEASE_CORRELATIONS

        return DISEASE_CORRELATIONS

    @property
    def diseases(self) -> tuple[str, ...]:
        """All disease names (derived from DISEASE_CORRELATIONS)."""
        return tuple(self.disease_correlations.keys())

    @property
    def icd10_codes(self) -> tuple[str, ...]:
        """All ICD-10 codes (derived from DISEASE_CORRELATIONS)."""
        codes = {data["icd10"] for data in self.disease_correlations.values()}
        return tuple(sorted(codes))

    @property
    def symptoms(self) -> tuple[str, ...]:
        """All unique symptoms across all diseases (derived from DISEASE_CORRELATIONS)."""
        all_symptoms: set[str] = set()
        for data in self.disease_correlations.values():
            all_symptoms.update(data["symptoms"])
        return tuple(sorted(all_symptoms))

    @property
    def generic_drugs(self) -> tuple[str, ...]:
        """All unique drugs (derived from DISEASE_CORRELATIONS).

        Non-drug interventions (surgery, devices, diets) are excluded: they belong in a
        condition's treatment list but not in the flat pool a consumer draws a medication
        column from. They are available separately via `interventions`.
        """
        interventions = set(self.non_drug_interventions)
        all_meds: set[str] = set()
        for data in self.disease_correlations.values():
            all_meds.update(data["medications"])
        return tuple(sorted(all_meds - interventions))

    @property
    def interventions(self) -> tuple[str, ...]:
        """All non-drug interventions this locale's catalog actually prescribes.

        Derived from DISEASE_CORRELATIONS by intersecting it with
        `non_drug_interventions`, so a declared intervention that no condition uses
        never shows up here.
        """
        declared = set(self.non_drug_interventions)
        present: set[str] = set()
        for data in self.disease_correlations.values():
            present.update(med for med in data["medications"] if med in declared)
        return tuple(sorted(present))

    @property
    def medical_specialties(self) -> tuple[str, ...]:
        """All unique medical specialties (derived from DISEASE_CORRELATIONS)."""
        specialties = {data["medical_specialty"] for data in self.disease_correlations.values()}
        return tuple(sorted(specialties))

    hospital_departments: ElementsType[str] = HOSPITAL_DEPARTMENTS

    blood_types: ElementsType[str] = BLOOD_TYPES

    allergies: ElementsType[str] = ALLERGIES

    medical_procedures: ElementsType[str] = MEDICAL_PROCEDURES

    insurance_plans: ElementsType[str] = INSURANCE_PLANS

    vital_signs: ElementsType[str] = VITAL_SIGNS

    non_drug_interventions: ElementsType[str] = NON_DRUG_INTERVENTIONS

    brand_drug_names: ElementsType[str] = BRAND_DRUG_NAMES

    # The display words for the measurement API — the ONE part of it that is translated.
    # Each locale provider overrides this with its own CLINICAL_LABELS.
    clinical_labels: Mapping[str, str] = CLINICAL_LABELS

    # ...and the numbers are not. Units, reference intervals and bounds are the same in
    # every language, so they are declared once in `faker_healthcare/clinical_values.py`
    # and deliberately NOT redeclared per locale; see that module's docstring.
    vital_definitions: Mapping[str, VitalDefinition] = VITAL_DEFINITIONS
    lab_definitions: Mapping[str, LabDefinition] = LAB_DEFINITIONS

    def disease(self) -> str:
        """Return a random disease name."""
        return self.random_element(self.diseases)

    def icd10_code(self, disease: str | None = None) -> str:
        """Return an ICD-10 code.

        Args:
            disease: Optional disease name. If provided, returns the correct ICD-10 code for that disease.
                    If None, returns a random ICD-10 code.

        Raises:
            ValueError: If disease is given but not found in correlations.
        """
        if disease is None:
            return self.random_element(self.icd10_codes)
        if disease not in self.disease_correlations:
            raise ValueError(f"Disease '{disease}' not found in disease correlations")
        return self.disease_correlations[disease]["icd10"]

    def disease_medical_specialty(self) -> str:
        return self.random_element(self.medical_specialties)

    def hospital_department(self) -> str:
        return self.random_element(self.hospital_departments)

    def generic_drug(self) -> str:
        """Return a random generic drug name (never a non-drug intervention)."""
        return self.random_element(self.generic_drugs)

    def intervention(self) -> str:
        """Return a random non-drug intervention (a procedure, device, or lifestyle measure)."""
        return self.random_element(self.interventions)

    def brand_drug(self) -> str:
        """Return a fictitious brand-style drug name from the screened catalogue.

        The names in `brand_drug_names` are invented, built from the morphemes in
        `constants.py` by `scripts/generate_brand_names.py`, screened against WHO INN
        class stems, a real-product denylist, an offensive-substring list, and this
        package's own generic-drug catalogue, and then read by a human. That last step
        is only possible because the shipped set is ~250 names; it is not a trademark
        search, and it is accurate as of the date recorded in README.md.
        """
        return self.random_element(self.brand_drug_names)

    def symptom(self, disease: str | None = None) -> str:
        """Return a symptom.

        Args:
            disease: Optional disease name. If provided, returns a symptom associated with that disease.
                    If None, returns a random symptom.

        Raises:
            ValueError: If disease is given but not found in correlations.
        """
        if disease is None:
            return self.random_element(self.symptoms)
        if disease not in self.disease_correlations:
            raise ValueError(f"Disease '{disease}' not found in disease correlations")
        return self.random_element(self.disease_correlations[disease]["symptoms"])

    def disease_symptoms(self, disease: str, count: int = 3) -> list[str]:
        """Return multiple symptoms for a specific disease.

        Args:
            disease: Disease name to get symptoms for.
            count: Number of symptoms to return (1-5). Defaults to 3.
                  Will be capped at the number of available symptoms for the disease.

        Returns:
            List of symptom strings for the disease.

        Raises:
            ValueError: If disease is not found in correlations.
        """
        if disease not in self.disease_correlations:
            raise ValueError(f"Disease '{disease}' not found in disease correlations")

        disease_symptoms = self.disease_correlations[disease]["symptoms"]
        actual_count = min(count, len(disease_symptoms))
        return list(self.random_elements(disease_symptoms, length=actual_count, unique=True))

    def medication(self, disease: str | None = None) -> str:
        """Return a medication.

        Args:
            disease: Optional disease name. If provided, returns a treatment for that disease,
                    which may be a non-drug intervention if the condition prescribes one.
                    If None, returns a random drug (never a non-drug intervention).

        Raises:
            ValueError: If disease is given but not found in correlations.
        """
        if disease is None:
            return self.random_element(self.generic_drugs)
        if disease not in self.disease_correlations:
            raise ValueError(f"Disease '{disease}' not found in disease correlations")
        return self.random_element(self.disease_correlations[disease]["medications"])

    def medications(self, disease: str, count: int = 2) -> list[str]:
        """Return multiple medications for a specific disease.

        Args:
            disease: Disease name to get medications for.
            count: Number of medications to return. Defaults to 2.
                  Will be capped at the number of available medications for the disease.

        Returns:
            List of medication strings for the disease.

        Raises:
            ValueError: If disease is not found in correlations.
        """
        if disease not in self.disease_correlations:
            raise ValueError(f"Disease '{disease}' not found in disease correlations")

        disease_meds = self.disease_correlations[disease]["medications"]
        actual_count = min(count, len(disease_meds))
        return list(self.random_elements(disease_meds, length=actual_count, unique=True))

    def diseases_by_symptom(self, symptom: str) -> list[str]:
        """Return all diseases that have a specific symptom.

        Args:
            symptom: Symptom to search for.

        Returns:
            List of disease names that include this symptom.
        """
        return [disease_name for disease_name, data in self.disease_correlations.items() if symptom in data["symptoms"]]

    def patient_scenario(self, disease: str | None = None) -> PatientScenario:
        """Generate a complete patient scenario with correlated clinical data.

        Args:
            disease: Optional specific disease. If None, a random disease is selected.

        Returns:
            Dictionary containing:
                - disease: The disease name
                - icd10: The correct ICD-10 code
                - symptoms: List of 3-5 correlated symptoms (fewer only if the condition has fewer)
                - medications: List of 2-3 correlated medications (fewer only if the condition has fewer)
                - medical_specialty: The primary medical specialty

        Raises:
            ValueError: If disease is given but not found in correlations.
        """
        if disease is None:
            disease = self.disease()
        elif disease not in self.disease_correlations:
            raise ValueError(f"Disease '{disease}' not found in diseases list")

        disease_data = self.disease_correlations[disease]
        # Both ranges are clamped to what the condition actually has, so a condition with
        # fewer than three symptoms or a single medication cannot produce an empty randrange.
        available_symptoms = len(disease_data["symptoms"])
        available_meds = len(disease_data["medications"])
        num_symptoms = self.random_int(min=min(3, available_symptoms), max=min(5, available_symptoms))
        num_meds = self.random_int(min=min(2, available_meds), max=min(3, available_meds))

        return {
            "disease": disease,
            "icd10": disease_data["icd10"],
            "symptoms": self.disease_symptoms(disease, count=num_symptoms),
            "medications": self.medications(disease, count=num_meds),
            "medical_specialty": disease_data["medical_specialty"],
        }

    def blood_type(self) -> str:
        return self.random_element(self.blood_types)

    def allergy(self) -> str:
        return self.random_element(self.allergies)

    def medical_procedure(self) -> str:
        return self.random_element(self.medical_procedures)

    def insurance_plan(self) -> str:
        return self.random_element(self.insurance_plans)

    def vital_sign(self) -> str:
        """Return the NAME of a vital sign ('Heart Rate').

        For a name with a number attached, see `vital_sign_measurement()`.
        """
        return self.random_element(self.vital_signs)

    def diagnosis(self) -> str:
        """Return a diagnosis with correlated disease and ICD-10 code."""
        disease = self.disease()
        icd10 = self.icd10_code(disease=disease)
        return f"{disease} ({icd10})"

    # ----------------------------------------------------------------------------------
    # Measurements
    #
    # Everything below returns numbers rather than the name of a measurement, and every
    # number comes from this provider's own RNG (`random_int`, `generator.random`), so
    # two providers seeded alike produce identical records. The numeric tables are
    # locale-neutral (`clinical_values.py`); only the labels are translated.
    # ----------------------------------------------------------------------------------

    def _label(self, key: str) -> str:
        """Return this locale's display label for a locale-neutral clinical ID."""
        try:
            return self.clinical_labels[key]
        except KeyError:
            raise ValueError(f"No clinical label defined for '{key}' in this locale") from None

    def _disease_effects(self, disease: str | None, effects: Mapping[str, Mapping[str, Direction]]) -> Mapping[str, Direction]:
        """Return the measurement effects a condition has, keyed by measurement ID.

        Effects are keyed by ICD-10 code rather than by disease name, so one table
        correlates in all six locales.

        Raises:
            ValueError: If disease is given but not found in correlations. A condition
                that IS in the catalogue but has no entry in the effects table simply
                has no effects, and its measurements come out in range.
        """
        if disease is None:
            return {}
        if disease not in self.disease_correlations:
            raise ValueError(f"Disease '{disease}' not found in disease correlations")
        return effects.get(self.disease_correlations[disease]["icd10"], {})

    def _draw_steps(self, band: tuple[int, int], direction: Direction | None) -> int:
        """Draw a value, in quantisation steps, from a band of allowed values.

        In-range values are uniform across the reference interval. Abnormal ones are
        weighted towards the boundary they crossed — see SEVERITY_TIERS in
        `clinical_values.py` for why a flat draw is the wrong shape.
        """
        low, high = band
        if direction is None:
            return self.random_int(low, high)
        roll = self.random_int(1, 100)
        _, mildest, harshest = next((tier for tier in SEVERITY_TIERS if roll <= tier[0]), SEVERITY_TIERS[-1])
        severity = mildest + (harshest - mildest) * (self.random_int(0, SEVERITY_RESOLUTION) / SEVERITY_RESOLUTION)
        offset = round((high - low) * severity)
        return low + offset if direction == "high" else high - offset

    def _vital_definition(self, name: str) -> VitalDefinition:
        if name not in self.vital_definitions:
            raise ValueError(f"Unknown vital sign '{name}'; expected one of: {', '.join(self.vital_definitions)}")
        return self.vital_definitions[name]

    def blood_pressure(self, disease: str | None = None) -> BloodPressure:
        """Return a blood-pressure reading in mmHg.

        Systolic is ALWAYS greater than diastolic, by at least the minimum plausible
        pulse pressure, because the two are not drawn independently: the diastolic
        pressure is drawn first and the systolic derived from it through a pulse
        pressure of 30-55 mmHg. Two independent draws from two overlapping ranges hand
        you a systolic of 92 under a diastolic of 95 on some seed, which is the sort of
        value that only shows up in a consumer's test suite months later.

        Args:
            disease: Optional disease name. A condition that raises blood pressure
                (hypertension, pre-eclampsia) puts both numbers above the reference
                range; the invariant still holds.

        Raises:
            ValueError: If disease is given but not found in correlations.
        """
        effects = self._disease_effects(disease, CONDITION_VITAL_EFFECTS)
        diastolic_definition = self._vital_definition("diastolic_bp")
        systolic_definition = self._vital_definition("systolic_bp")
        decimals = diastolic_definition["decimals"]

        diastolic_band = measurement_band(
            diastolic_definition["low"],
            diastolic_definition["high"],
            diastolic_definition["min_value"],
            diastolic_definition["max_value"],
            decimals,
            effects.get("diastolic_bp"),
        )
        systolic_band = measurement_band(
            systolic_definition["low"],
            systolic_definition["high"],
            systolic_definition["min_value"],
            systolic_definition["max_value"],
            decimals,
            effects.get("systolic_bp"),
        )

        diastolic = self._draw_steps(diastolic_band, effects.get("diastolic_bp"))
        # The pulse pressure is widened only as far as it must be to reach the systolic
        # band. Where the two cannot both be satisfied the pulse pressure wins, because
        # a physiologically impossible pair is a worse record than a systolic a few mmHg
        # outside its band.
        minimum = max(PULSE_PRESSURE_RANGE_MMHG[0], systolic_band[0] - diastolic)
        maximum = max(minimum, min(PULSE_PRESSURE_RANGE_MMHG[1], systolic_band[1] - diastolic))
        systolic = diastolic + self.random_int(minimum, maximum)

        return {"systolic": int(from_steps(systolic, decimals)), "diastolic": int(from_steps(diastolic, decimals)), "unit": systolic_definition["unit"]}

    def vital_sign_measurement(self, name: str | None = None, disease: str | None = None) -> VitalMeasurement:
        """Return one measured vital sign: a localized name, a number, and its unit.

        Args:
            name: Optional vital-sign ID — a locale-neutral key of `vital_definitions`
                such as `'heart_rate'`, NOT a display label. If None, one is chosen at
                random, preferring the signs the given disease actually affects.
            disease: Optional disease name. A sign this condition is known to move lands
                outside its reference range in that direction; every other sign lands
                inside it.

        Raises:
            ValueError: If the vital sign ID or the disease is unknown.
        """
        effects = self._disease_effects(disease, CONDITION_VITAL_EFFECTS)
        if name is None:
            name = self.random_element(tuple(effects) if effects else tuple(self.vital_definitions))
        definition = self._vital_definition(name)
        direction = effects.get(name)
        decimals = definition["decimals"]
        band = measurement_band(definition["low"], definition["high"], definition["min_value"], definition["max_value"], decimals, direction)
        return {"name": self._label(name), "value": from_steps(self._draw_steps(band, direction), decimals), "unit": definition["unit"]}

    def vital_sign_measurements(self, disease: str | None = None) -> list[VitalMeasurement]:
        """Return one measurement for every vital sign, as a set of observations.

        Named `vital_sign_measurements` and not `vital_signs` because `vital_signs` is
        already the tuple of vital-sign NAMES that `vital_sign()` draws from, and that
        API predates this one.

        The blood pressure comes from `blood_pressure()`, so the systolic and diastolic
        entries in the returned list are a coherent pair rather than two loose numbers.

        Args:
            disease: Optional disease name; the signs that condition affects land
                outside their reference ranges.

        Raises:
            ValueError: If disease is given but not found in correlations.
        """
        pressure = self.blood_pressure(disease=disease)
        measurements: list[VitalMeasurement] = [
            {"name": self._label("systolic_bp"), "value": pressure["systolic"], "unit": pressure["unit"]},
            {"name": self._label("diastolic_bp"), "value": pressure["diastolic"], "unit": pressure["unit"]},
        ]
        measurements.extend(self.vital_sign_measurement(name=name, disease=disease) for name in self.vital_definitions if name not in ("systolic_bp", "diastolic_bp"))
        return measurements

    def body_measurements(self, sex: str | None = None, age: int | None = None) -> BodyMeasurements:
        """Return an adult's height, weight, and the BMI computed from the two.

        The BMI is never drawn independently: a height, a weight and a BMI that
        disagree is the same class of defect as a diagnosis whose ICD-10 code belongs to
        another condition. Weight is derived from a drawn BMI and the drawn height, then
        the returned BMI is recomputed from the rounded numbers actually returned.

        Args:
            sex: `'male'` or `'female'` (case-insensitive), selecting which
                anthropometric profile to draw from; random if None.
            age: Adult age in years, used to shift the height and BMI means slightly;
                random if None.

        Raises:
            ValueError: If sex is not one of the profiles, or age is outside the adult
                range. Paediatric anthropometry needs real growth references
                (WHO/CDC growth charts) rather than an extrapolated adult curve, so this
                method refuses the age rather than inventing a child.
        """
        if sex is None:
            sex = self.random_element(tuple(BODY_PROFILES))
        else:
            sex = sex.lower()
            if sex not in BODY_PROFILES:
                raise ValueError(f"Unknown sex '{sex}'; expected one of: {', '.join(BODY_PROFILES)}")
        minimum_age, maximum_age = ADULT_AGE_RANGE
        if age is None:
            age = self.random_int(minimum_age, maximum_age)
        elif not minimum_age <= age <= maximum_age:
            raise ValueError(f"Age {age} is outside the adult range {minimum_age}-{maximum_age} this method models")

        profile = BODY_PROFILES[sex]
        from_age, cm_per_year = HEIGHT_LOSS_CM_PER_YEAR_AFTER
        height = self.generator.random.gauss(profile["height_mean_cm"], profile["height_sd_cm"]) - max(0, age - from_age) * cm_per_year
        height_cm = round(min(max(height, profile["height_min_cm"]), profile["height_max_cm"]), 1)

        youngest, oldest = BMI_DRIFT_AGE_RANGE
        mean_bmi = BMI_MEAN + (min(max(age, youngest), oldest) - 40) * BMI_DRIFT_PER_YEAR
        bmi = min(max(self.generator.random.gauss(mean_bmi, BMI_SD), BMI_LIMITS[0]), BMI_LIMITS[1])

        metres = height_cm / 100
        weight_kg = round(bmi * metres**2, 1)
        return {"height_cm": height_cm, "weight_kg": weight_kg, "bmi": round(weight_kg / metres**2, 1)}

    def alcohol_units_per_week(self) -> int:
        """Return self-reported weekly alcohol consumption in UK units.

        One UK unit is 10 mL (8 g) of pure ethanol — a US standard drink is 1.75 of
        them. The distribution is deliberately skewed the way survey data is: about a
        fifth of adults report none at all, most drinkers stay inside the 14-unit UK
        low-risk guideline, and a long tail runs well past it. `0` is a legitimate,
        common return value.
        """
        roll = self.random_int(1, 100)
        _, low, high = next((band for band in ALCOHOL_WEEKLY_BANDS if roll <= band[0]), ALCOHOL_WEEKLY_BANDS[-1])
        return self.random_int(low, high)

    def alcohol_intake_category(self, units: int | None = None) -> str:
        """Return the localized risk category for a weekly alcohol intake.

        Bands follow the UK Chief Medical Officers' 2016 guidelines: none, low risk
        (1-14 units), increasing risk (15-35), higher risk (above 35).

        Args:
            units: Weekly units to categorize; drawn from
                `alcohol_units_per_week()` if None.

        Raises:
            ValueError: If units is negative.
        """
        if units is None:
            units = self.alcohol_units_per_week()
        return self._label(alcohol_category_key(units))

    def lab_result(self, analyte: str | None = None, disease: str | None = None) -> LabResult:
        """Return one laboratory result, flagged against its reference interval.

        `flag` always agrees with `value`: it is derived from the same comparison, not
        drawn separately.

        Args:
            analyte: Optional analyte ID — a locale-neutral key of `lab_definitions`
                such as `'hba1c'`, NOT a display label. If None, one is chosen at
                random, preferring the analytes the given disease actually moves (as
                `symptom(disease=...)` returns a symptom OF that disease).
            disease: Optional disease name. An analyte this condition is known to move
                lands outside the reference interval in that direction, with the flag to
                match; every other analyte lands inside it.

        Raises:
            ValueError: If the analyte or the disease is unknown. Neither falls back to
                an uncorrelated draw — a caller who asked about one condition would
                silently receive another's numbers.
        """
        effects = self._disease_effects(disease, CONDITION_LAB_EFFECTS)
        if analyte is None:
            analyte = self.random_element(tuple(effects) if effects else tuple(self.lab_definitions))
        elif analyte not in self.lab_definitions:
            raise ValueError(f"Unknown analyte '{analyte}'; expected one of: {', '.join(self.lab_definitions)}")

        definition = self.lab_definitions[analyte]
        direction = effects.get(analyte)
        decimals = definition["decimals"]
        reference_low = to_steps(definition["ref_low"], decimals)
        reference_high = to_steps(definition["ref_high"], decimals)
        band = measurement_band(definition["ref_low"], definition["ref_high"], definition["min_value"], definition["max_value"], decimals, direction)
        value = self._draw_steps(band, direction)

        return {
            "analyte": self._label(analyte),
            "value": from_steps(value, decimals),
            "unit": definition["unit"],
            "reference_low": from_steps(reference_low, decimals),
            "reference_high": from_steps(reference_high, decimals),
            "flag": self._label(FLAG_LABEL_KEYS[flag_for(value, reference_low, reference_high)]),
        }

    def lab_panel(self, disease: str | None = None, size: int | None = None) -> list[LabResult]:
        """Return a panel of distinct laboratory results, in report order.

        Every analyte the condition moves is included, so the correlation is visible in
        the panel rather than left to chance, and the rest of the panel is filled with
        analytes that come back in range.

        Args:
            disease: Optional disease name; its affected analytes are always present and
                always flagged.
            size: Number of results (4-8 if None). Must be at least the number of
                analytes the condition pins, and no more than the number defined.

        Raises:
            ValueError: If disease is unknown, or size is out of range or too small to
                carry the condition's own analytes — truncating those would hand back a
                panel that quietly contradicts the diagnosis.
        """
        effects = self._disease_effects(disease, CONDITION_LAB_EFFECTS)
        pinned = tuple(effects)
        if size is None:
            size = max(len(pinned), self.random_int(4, 8))
        elif not 1 <= size <= len(self.lab_definitions):
            raise ValueError(f"size must be between 1 and {len(self.lab_definitions)}, got {size}")
        elif size < len(pinned):
            raise ValueError(f"Disease '{disease}' correlates with {len(pinned)} analytes; size must be at least {len(pinned)}, got {size}")

        unaffected = [analyte for analyte in self.lab_definitions if analyte not in effects]
        filler = self.random_elements(unaffected, length=size - len(pinned), unique=True) if size > len(pinned) else []
        chosen = {*pinned, *filler}
        # Iterated in definition order, never in set order, so the panel is stable under
        # PYTHONHASHSEED and a seeded run is reproducible.
        return [self.lab_result(analyte=analyte, disease=disease) for analyte in self.lab_definitions if analyte in chosen]
