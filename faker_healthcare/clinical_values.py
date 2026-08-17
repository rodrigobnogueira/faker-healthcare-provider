"""Locale-neutral numeric reference data for vital signs, body measurements and labs.

MEDICAL DISCLAIMER: everything here exists to make **synthetic test data** look
plausible. These are not clinical reference intervals for any real laboratory. Real
intervals vary by assay, analyser, population, sex, age and pregnancy, and every real
report carries its own. Never use these numbers for anything but generating fake data.

Why this module is not per-locale
---------------------------------
A millimole is a millimole in every language. Reference intervals, units and numeric
bounds are therefore defined **once, here**, keyed by stable IDs (`heart_rate`,
`hba1c`), and the six locale packages translate **labels only**
(`faker_healthcare/<locale>/clinical_labels.py`). Copying these tables into the locale
packages would multiply one number by six, put six copies out of step the first time a
range was corrected, and hand the locale-parity suite six chances to disagree about a
value that cannot legitimately differ. `tests/test_locales.py` enforces the split from
both sides: every locale must define every label key, and no locale may ship its own
copy of these tables.

Units: SI
---------
Analytes use the SI units in which laboratories in the UK, Ireland, most of Europe,
Australia and New Zealand report, which is also what the requester's use case (CRATE,
University of Cambridge) reads: mmol/L, µmol/L, g/L, and IFCC mmol/mol for HbA1c. To
convert to US conventional units, divide/multiply by the usual factors — glucose and
lipids mg/dL = mmol/L x 18 (glucose) or x 38.67 (cholesterol) and x 88.57
(triglycerides); creatinine mg/dL = µmol/L / 88.4; bilirubin mg/dL = µmol/L / 17.1;
haemoglobin g/dL = g/L / 10; HbA1c % (DCCT/NGSP) = mmol/mol / 10.929 + 2.15.

Where the numbers come from
---------------------------
Adult values, sex-combined, chosen to match the ranges published in widely used
references rather than any single laboratory:

- Blood pressure categories: 2017 ACC/AHA hypertension guideline (normal < 120/80).
- Resting heart rate 60-100/min, respiratory rate 12-20/min, oral temperature
  36.1-37.2 °C, SpO2 95-100%: standard adult vital-sign ranges as published by
  MedlinePlus and Johns Hopkins Medicine patient references.
- Haematology, renal, liver, thyroid and inflammatory intervals: the SI adult ranges
  published by the Association for Clinical Biochemistry and Laboratory Medicine and in
  standard UK laboratory handbooks.
- Haemoglobin thresholds for anaemia: WHO haemoglobin concentrations for the diagnosis
  of anaemia (2011).
- eGFR: KDIGO 2012 CKD categories (G1 >= 90 mL/min/1.73m^2).
- HbA1c: IFCC units, with the WHO/IDF diabetes threshold at 48 mmol/mol and the
  non-diabetic range below 42 mmol/mol.
- Lipid targets: NICE CG181 / the JBS3 desirable values (total cholesterol < 5.0,
  LDL < 3.0, triglycerides < 1.7 mmol/L).

`min_value`/`max_value` are the outermost values the generator will produce — plausible
clinical extremes, not physiological limits, so that a condition-driven abnormal value
is still a number a laboratory could print.

Known simplifications (stated rather than hidden)
-------------------------------------------------
- **Reference intervals are sex- and age-combined.** Haemoglobin, creatinine, ferritin
  and urate all have separate male and female intervals in practice; one interval per
  analyte keeps `lab_result()` free of a demographic argument it would then have to be
  given consistently across a whole record.
- **Analytes are drawn independently of each other.** Each one is correlated with the
  *diagnosis*, not with its neighbours in the panel, so pairs that are arithmetically
  related in reality are only directionally consistent here: eGFR is not computed from
  the creatinine beside it (the equations need age, sex and ethnicity), and the lipids
  do not satisfy the Friedewald relationship between total cholesterol, LDL, HDL and
  triglycerides. Correlating analytes with each other, rather than only with the
  condition, is the obvious next step for this module.
- **Direction, not severity** — see SEVERITY_TIERS below.
"""

from .types import DemographicConstraint, Direction, Flag, LabDefinition, Sex, VitalDefinition


__all__ = [
    "ADULT_AGE_RANGE",
    "AGE_BAND_RESOLUTION",
    "ALCOHOL_CATEGORY_THRESHOLDS",
    "ALCOHOL_HIGHEST_CATEGORY",
    "ALCOHOL_UNIT_GRAMS",
    "ALCOHOL_WEEKLY_BANDS",
    "BMI_DRIFT_AGE_RANGE",
    "BMI_DRIFT_PER_YEAR",
    "BMI_LIMITS",
    "BMI_MEAN",
    "BMI_SD",
    "BODY_PROFILES",
    "CONDITION_LAB_EFFECTS",
    "CONDITION_VITAL_EFFECTS",
    "DEMOGRAPHIC_CONSTRAINTS",
    "FLAG_LABEL_KEYS",
    "HEIGHT_LOSS_CM_PER_YEAR_AFTER",
    "LAB_DEFINITIONS",
    "MIN_PULSE_PRESSURE_MMHG",
    "PATIENT_AGE_RANGE",
    "PULSE_PRESSURE_RANGE_MMHG",
    "SEVERITY_RESOLUTION",
    "SEVERITY_TIERS",
    "SEXES",
    "SEX_PROBABILITY_RESOLUTION",
    "VITAL_DEFINITIONS",
    "age_bands_for",
    "age_range_for",
    "alcohol_category_key",
    "declared_age_range",
    "flag_for",
    "from_steps",
    "is_paediatric_only",
    "measurement_band",
    "satisfies_demographics",
    "to_steps",
]


# --------------------------------------------------------------------------------------
# Vital signs
# --------------------------------------------------------------------------------------

# IDs are locale-neutral and stable; the display name for each one lives under the same
# key in every locale's CLINICAL_LABELS.
VITAL_DEFINITIONS: dict[str, VitalDefinition] = {
    "systolic_bp": {"unit": "mmHg", "low": 90, "high": 120, "decimals": 0, "min_value": 70, "max_value": 220},
    "diastolic_bp": {"unit": "mmHg", "low": 60, "high": 80, "decimals": 0, "min_value": 40, "max_value": 130},
    "heart_rate": {"unit": "bpm", "low": 60, "high": 100, "decimals": 0, "min_value": 35, "max_value": 180},
    "respiratory_rate": {"unit": "breaths/min", "low": 12, "high": 20, "decimals": 0, "min_value": 8, "max_value": 40},
    "temperature_c": {"unit": "°C", "low": 36.1, "high": 37.2, "decimals": 1, "min_value": 34.0, "max_value": 41.0},
    # 100% is both the reference ceiling and the physiological ceiling, so no condition
    # can push oxygen saturation "high" — `measurement_band` refuses to invent a band
    # that does not exist, and a test asserts no shipped effect asks for one.
    "oxygen_saturation": {"unit": "%", "low": 95, "high": 100, "decimals": 0, "min_value": 80, "max_value": 100},
}

# A blood pressure is one measurement, not two independent draws: the systolic pressure
# is derived from the diastolic one through a pulse pressure, which is what keeps
# systolic > diastolic by a plausible margin for EVERY seed rather than for most of
# them. Normal adult pulse pressure is 30-50 mmHg, so that is the range drawn from;
# MIN_PULSE_PRESSURE_MMHG is the weaker floor `blood_pressure()` guarantees as a
# contract, which a future range may narrow towards but must never cross.
PULSE_PRESSURE_RANGE_MMHG = (30, 55)
MIN_PULSE_PRESSURE_MMHG = 25


# --------------------------------------------------------------------------------------
# Laboratory analytes (SI units — see the module docstring)
# --------------------------------------------------------------------------------------

LAB_DEFINITIONS: dict[str, LabDefinition] = {
    # Haematology
    "haemoglobin": {"unit": "g/L", "ref_low": 120, "ref_high": 170, "decimals": 0, "min_value": 50, "max_value": 200},
    "wbc": {"unit": "x10^9/L", "ref_low": 4.0, "ref_high": 11.0, "decimals": 1, "min_value": 0.5, "max_value": 40.0},
    "platelets": {"unit": "x10^9/L", "ref_low": 150, "ref_high": 400, "decimals": 0, "min_value": 5, "max_value": 900},
    "ferritin": {"unit": "µg/L", "ref_low": 15, "ref_high": 300, "decimals": 0, "min_value": 2, "max_value": 1200},
    "inr": {"unit": "ratio", "ref_low": 0.8, "ref_high": 1.2, "decimals": 1, "min_value": 0.7, "max_value": 6.0},
    # Renal
    "sodium": {"unit": "mmol/L", "ref_low": 135, "ref_high": 145, "decimals": 0, "min_value": 115, "max_value": 165},
    "potassium": {"unit": "mmol/L", "ref_low": 3.5, "ref_high": 5.3, "decimals": 1, "min_value": 2.2, "max_value": 7.5},
    "urea": {"unit": "mmol/L", "ref_low": 2.5, "ref_high": 7.8, "decimals": 1, "min_value": 1.0, "max_value": 45.0},
    "creatinine": {"unit": "µmol/L", "ref_low": 45, "ref_high": 110, "decimals": 0, "min_value": 25, "max_value": 700},
    "egfr": {"unit": "mL/min/1.73m^2", "ref_low": 90, "ref_high": 120, "decimals": 0, "min_value": 5, "max_value": 140},
    # Liver
    "alt": {"unit": "U/L", "ref_low": 10, "ref_high": 45, "decimals": 0, "min_value": 3, "max_value": 500},
    "ast": {"unit": "U/L", "ref_low": 10, "ref_high": 40, "decimals": 0, "min_value": 3, "max_value": 400},
    "alkaline_phosphatase": {"unit": "U/L", "ref_low": 30, "ref_high": 130, "decimals": 0, "min_value": 15, "max_value": 800},
    "bilirubin_total": {"unit": "µmol/L", "ref_low": 3, "ref_high": 21, "decimals": 0, "min_value": 1, "max_value": 300},
    "albumin": {"unit": "g/L", "ref_low": 35, "ref_high": 50, "decimals": 0, "min_value": 12, "max_value": 60},
    # Metabolic
    "fasting_glucose": {"unit": "mmol/L", "ref_low": 3.9, "ref_high": 5.5, "decimals": 1, "min_value": 1.5, "max_value": 30.0},
    "hba1c": {"unit": "mmol/mol", "ref_low": 20, "ref_high": 41, "decimals": 0, "min_value": 15, "max_value": 140},
    # Thyroid
    "tsh": {"unit": "mIU/L", "ref_low": 0.4, "ref_high": 4.0, "decimals": 2, "min_value": 0.01, "max_value": 100.0},
    "free_t4": {"unit": "pmol/L", "ref_low": 12.0, "ref_high": 22.0, "decimals": 1, "min_value": 1.0, "max_value": 60.0},
    # Lipids
    "total_cholesterol": {"unit": "mmol/L", "ref_low": 3.0, "ref_high": 5.0, "decimals": 1, "min_value": 1.5, "max_value": 15.0},
    "ldl": {"unit": "mmol/L", "ref_low": 1.5, "ref_high": 3.0, "decimals": 1, "min_value": 0.4, "max_value": 10.0},
    "hdl": {"unit": "mmol/L", "ref_low": 1.0, "ref_high": 2.2, "decimals": 1, "min_value": 0.3, "max_value": 4.0},
    "triglycerides": {"unit": "mmol/L", "ref_low": 0.5, "ref_high": 1.7, "decimals": 1, "min_value": 0.2, "max_value": 20.0},
    # Inflammatory
    # ref_low is 0: "CRP low" is not a finding, and no effect entry may ask for one.
    "crp": {"unit": "mg/L", "ref_low": 0, "ref_high": 5, "decimals": 0, "min_value": 0, "max_value": 350},
}


# --------------------------------------------------------------------------------------
# Condition -> measurement correlations, keyed by ICD-10 code
# --------------------------------------------------------------------------------------
#
# THIS is the part that is worth shipping. A random lab table with no relationship to the
# diagnosis is something every consumer can already generate; a haemoglobin that is low
# *because the record says iron-deficiency anaemia* is not.
#
# Keyed by ICD-10 code, not by disease name, because the code is the one field this
# package guarantees is identical in all six locales — so `lab_result(disease=...)`
# correlates in French and Chinese without a line of per-locale data.
#
# Rules for adding an entry (the same bar as DISEASE_CORRELATIONS, see AGENTS.md):
#   * only associations that are textbook and unambiguous for the *unqualified*
#     condition. Not "can occur in severe cases", not "in the subgroup that also has X";
#   * every code must already exist in the shipped catalogue (a test iterates them);
#   * an empty entry is better than a wrong one — a condition with no entry simply
#     produces in-range values, which is an honest "nothing specific to see here".
#
# Deliberately absent, as worked examples of the bar:
#   * D68.311 (haemophilia): the abnormal clotting test is the APTT, not the INR, which
#     is normal. An "INR high" entry here would teach the wrong thing;
#   * I21.9 (myocardial infarction), I26.99 (pulmonary embolism): the diagnostic
#     analytes are troponin and D-dimer, which this panel does not carry;
#   * M81.0 (osteoporosis): routine biochemistry is characteristically normal, and that
#     is exactly what an unlisted condition already produces.

CONDITION_VITAL_EFFECTS: dict[str, dict[str, Direction]] = {
    "I10": {"systolic_bp": "high", "diastolic_bp": "high"},  # Essential hypertension
    "I11.9": {"systolic_bp": "high", "diastolic_bp": "high"},  # Hypertensive heart disease
    "O14.90": {"systolic_bp": "high", "diastolic_bp": "high"},  # Pre-eclampsia
    "I48.91": {"heart_rate": "high"},  # Atrial fibrillation (fast ventricular response)
    "I50.9": {"heart_rate": "high", "respiratory_rate": "high"},  # Congestive heart failure
    "I26.99": {"heart_rate": "high", "respiratory_rate": "high", "oxygen_saturation": "low"},  # Pulmonary embolism
    "E05.90": {"heart_rate": "high"},  # Hyperthyroidism
    "E03.9": {"heart_rate": "low"},  # Hypothyroidism (bradycardia)
    "J44.9": {"respiratory_rate": "high", "oxygen_saturation": "low"},  # COPD
    "J45.909": {"respiratory_rate": "high", "heart_rate": "high"},  # Asthma
    "J18.9": {"temperature_c": "high", "respiratory_rate": "high", "oxygen_saturation": "low"},  # Pneumonia
    "U07.1": {"temperature_c": "high", "oxygen_saturation": "low"},  # COVID-19
    "J11.1": {"temperature_c": "high"},  # Influenza
    "A41.9": {"temperature_c": "high", "heart_rate": "high", "respiratory_rate": "high"},  # Sepsis
    "A15.0": {"temperature_c": "high"},  # Pulmonary tuberculosis
    "A90": {"temperature_c": "high"},  # Dengue fever
    "B27.90": {"temperature_c": "high"},  # Infectious mononucleosis
    "N10": {"temperature_c": "high"},  # Acute pyelonephritis
    "K35.80": {"temperature_c": "high"},  # Appendicitis
}

CONDITION_LAB_EFFECTS: dict[str, dict[str, Direction]] = {
    # Metabolic / endocrine
    "E11.9": {"hba1c": "high", "fasting_glucose": "high"},  # Type 2 diabetes
    "E10.9": {"hba1c": "high", "fasting_glucose": "high"},  # Type 1 diabetes
    "E11.319": {"hba1c": "high", "fasting_glucose": "high"},  # Diabetic retinopathy
    "O24.419": {"fasting_glucose": "high"},  # Gestational diabetes
    "E03.9": {"tsh": "high", "free_t4": "low"},  # Hypothyroidism
    "E05.90": {"tsh": "low", "free_t4": "high"},  # Hyperthyroidism
    "E78.5": {"total_cholesterol": "high", "ldl": "high", "triglycerides": "high"},  # Hyperlipidaemia
    "E66.9": {"triglycerides": "high", "hdl": "low"},  # Obesity
    # Renal
    "N18.9": {"creatinine": "high", "urea": "high", "egfr": "low"},  # Chronic kidney disease
    "N17.9": {"creatinine": "high", "urea": "high", "egfr": "low"},  # Acute kidney injury
    "N04.9": {"albumin": "low", "total_cholesterol": "high"},  # Nephrotic syndrome
    # Haematology
    "D50.9": {"haemoglobin": "low", "ferritin": "low"},  # Iron deficiency anaemia
    "D64.9": {"haemoglobin": "low"},  # Anaemia, unspecified
    "D51.0": {"haemoglobin": "low"},  # Pernicious anaemia
    "D57.1": {"haemoglobin": "low", "bilirubin_total": "high"},  # Sickle-cell disease (haemolysis)
    "D69.6": {"platelets": "low"},  # Thrombocytopenia
    "D72.819": {"wbc": "low"},  # Leukopenia
    "C95.90": {"wbc": "high"},  # Leukaemia
    "C90.00": {"haemoglobin": "low"},  # Myeloma (the "A" of CRAB)
    # Liver / GI
    "K74.60": {"albumin": "low", "bilirubin_total": "high", "inr": "high", "platelets": "low"},  # Cirrhosis
    "K76.9": {"alt": "high", "ast": "high"},  # Chronic liver disease
    "K76.0": {"alt": "high"},  # Non-alcoholic fatty liver disease
    "B18.2": {"alt": "high", "ast": "high"},  # Chronic hepatitis C
    "B27.90": {"wbc": "high", "alt": "high"},  # Infectious mononucleosis
    "C25.9": {"bilirubin_total": "high", "alkaline_phosphatase": "high"},  # Pancreatic cancer (obstructive jaundice)
    "C18.9": {"haemoglobin": "low", "ferritin": "low"},  # Colon cancer (occult blood loss)
    "K90.0": {"haemoglobin": "low", "ferritin": "low"},  # Coeliac disease (malabsorption)
    "K50.90": {"crp": "high", "haemoglobin": "low"},  # Crohn's disease
    "K51.90": {"haemoglobin": "low"},  # Ulcerative colitis
    # Infection / inflammation
    "A41.9": {"wbc": "high", "crp": "high"},  # Sepsis
    "J18.9": {"wbc": "high", "crp": "high"},  # Pneumonia
    "N10": {"wbc": "high", "crp": "high"},  # Acute pyelonephritis
    "K35.80": {"wbc": "high", "crp": "high"},  # Appendicitis
    "K81.0": {"wbc": "high", "crp": "high"},  # Acute cholecystitis
    "K57.92": {"wbc": "high", "crp": "high"},  # Diverticulitis
    "K85.90": {"crp": "high"},  # Acute pancreatitis
    "A15.0": {"crp": "high"},  # Pulmonary tuberculosis
    "U07.1": {"crp": "high"},  # COVID-19
    "A90": {"platelets": "low", "wbc": "low"},  # Dengue fever
    "M06.9": {"crp": "high"},  # Rheumatoid arthritis
    "M32.9": {"wbc": "low"},  # Systemic lupus erythematosus (leukopenia)
}


# --------------------------------------------------------------------------------------
# Body measurements
# --------------------------------------------------------------------------------------
#
# Anthropometric profiles for the two reference classes clinical growth and body-
# composition references are published for. This is a data simplification for synthetic
# records, not a statement about anyone's identity, and the numbers are round adult
# averages (NCD-RisC pooled adult heights for Western populations, and an adult BMI
# distribution centred slightly above the "overweight" threshold, which is where the
# adult populations of most high-income countries now sit).
BODY_PROFILES: dict[str, dict[str, float]] = {
    "male": {"height_mean_cm": 175.0, "height_sd_cm": 7.0, "height_min_cm": 150.0, "height_max_cm": 205.0},
    "female": {"height_mean_cm": 162.0, "height_sd_cm": 6.5, "height_min_cm": 140.0, "height_max_cm": 190.0},
}

# The same two keys as BODY_PROFILES, as an ordered tuple: `patient()` draws a sex from
# it, and a tuple (not a dict view) is what keeps that draw stable and typed. A test
# asserts the two stay the same set.
SEXES: tuple[Sex, ...] = ("male", "female")

BMI_MEAN = 26.5
BMI_SD = 4.5
BMI_LIMITS = (15.0, 55.0)

# Adults lose stature from about the sixth decade — roughly a centimetre per decade.
HEIGHT_LOSS_CM_PER_YEAR_AFTER = (50, 0.1)

# Middle-aged adults are heavier than young ones: the mean BMI is shifted by this much
# per year of age away from 40, and stops moving at 60.
BMI_DRIFT_PER_YEAR = 0.05
BMI_DRIFT_AGE_RANGE = (18, 60)

ADULT_AGE_RANGE = (18, 110)


# --------------------------------------------------------------------------------------
# Who a condition can occur in, keyed by ICD-10 code
# --------------------------------------------------------------------------------------
#
# Without this, generating a patient beside a diagnosis produces male preeclampsia and
# eighty-year-old bronchiolitis — the demographic version of a diagnosis whose ICD-10
# code belongs to another condition, and something every consumer of this package has to
# work around by hand.
#
# Keyed by ICD-10 code and living HERE, once, for the same reason as the effect tables
# above and stated once more because it is the rule that matters most in this file: sex
# and age are not translatable. "Female" is a fact about the condition, not a word about
# it, so it cannot live in six catalogues where five copies could fall behind the sixth.
#
# Each entry states only what it knows (`DemographicConstraint` has no required keys),
# and it states it at the strength the evidence supports:
#   * `sex` — an absolute lock: the condition occurs only in that anthropometric class;
#   * `female_probability` — a weighting: the share of patients who are female, for a
#     condition that is skewed but not locked. Mutually exclusive with `sex`, because a
#     weight of 0 or 1 IS a lock and belongs in `sex`;
#   * `min_age` / `max_age` — inclusive bounds on a plausible patient's age, not on the
#     age at diagnosis and not a hard clinical limit. The draw inside them is uniform;
#   * `age_bands` — `(share, lowest, highest)` triples replacing those bounds with a
#     shape, for a condition whose real age distribution is nothing like uniform. Shares
#     are percentages summing to 100, the bands are contiguous and ascending, and the
#     draw is uniform within the band that wins.
#
# The bar is the same as everywhere else: constrain only what is unambiguous, and SOURCE
# whatever you skew. Every weight and every band below names the figure it came from; a
# skew nobody can cite does not belong here. A condition with no entry can occur in
# anyone at any age, which is an honest default and is still what most of the catalogue
# gets. The published figures used here are mostly US national statistics — that is where
# this kind of number is reported most consistently — and they are not claims about the
# age or sex structure of any particular country's clinic population.
#
# Why the middle strength exists at all. For one release this table was binary: a
# condition was either locked or free, and three conditions were correctly refused a lock
# on medical grounds — which left them free, and free was measurably wrong. Breast cancer
# generated 49% male patients against a real figure under 1%, a fifty-fold error and a
# worse defect than the male-preeclampsia bug the table was built to fix. "Female, full
# stop" would have been wrong in the other direction: men with breast cancer are a real
# patient group who need to appear in test data. A sourced weight is the answer to both,
# and the same argument applies to age: cystic fibrosis drawing uniformly to 100 was not
# a neutral default, it was a claim, and a wrong one.
#
# Deliberately absent or deliberately unweighted, as worked examples of the bar:
#   * D68.311 (haemophilia): the code shipped here is *acquired* haemophilia — an
#     autoimmune inhibitor disorder, mostly of older adults, affecting both sexes — so
#     the near-total male skew of X-linked haemophilia would be a wrong fact under this
#     code. The catalogue's medications for the condition (factor VIII, factor IX,
#     emicizumab) read like congenital haemophilia A/B, which is D66/D67. That
#     contradiction has to be settled in the catalogue before any sex weight here can be
#     sourced, and asserting one now would silently pick a side;
#   * D57.1 (sickle cell disease): its strong skew is by ancestry, which this package
#     does not model at all, and not by sex or age;
#   * I21.9 (myocardial infarction), I63.9 (stroke), C34.90 (lung cancer): each skews
#     male, old, or both, but by ratios that move so much between populations and decades
#     that no single number would be honest;
#   * every other condition keeps the uniform 0-100 draw, including adult-onset ones
#     where an age floor would be reasonable. Adding one means sourcing it.
DEMOGRAPHIC_CONSTRAINTS: dict[str, DemographicConstraint] = {
    # ---- Locked: the condition occurs in one sex, full stop. ----
    # Female-only. The four with an upper bound are bounded by reproductive age rather
    # than by the condition: an endometriosis diagnosis can persist past the menopause,
    # but a *new* patient generated for it is of reproductive age.
    "O14.90": {"sex": "female", "min_age": 15, "max_age": 50},  # Preeclampsia (pregnancy)
    "O24.419": {"sex": "female", "min_age": 15, "max_age": 50},  # Gestational diabetes (pregnancy)
    "E28.2": {"sex": "female", "min_age": 15, "max_age": 50},  # Polycystic ovary syndrome
    "N80.9": {"sex": "female", "min_age": 15, "max_age": 55},  # Endometriosis
    "D25.9": {"sex": "female", "min_age": 20, "max_age": 55},  # Uterine fibroids
    "C56.9": {"sex": "female"},  # Ovarian cancer (germ-cell tumours occur in teenagers)
    "C54.1": {"sex": "female", "min_age": 40},  # Endometrial cancer (rare before 40)
    # Male-only.
    "C61": {"sex": "male", "min_age": 40},  # Prostate cancer
    "N40.0": {"sex": "male", "min_age": 45},  # Benign prostatic hyperplasia
    "N52.9": {"sex": "male", "min_age": 18},  # Erectile dysfunction
    # Paediatric-only. Both are conditions of early childhood, and both are why
    # `patient_record()` refuses to build an adult record around them.
    "J05.0": {"max_age": 5},  # Croup (typically 6 months to 3 years)
    "J21.9": {"max_age": 2},  # Bronchiolitis (under 2 by definition)
    # ---- Weighted: strongly skewed, but a lock would be a false absolute. ----
    # Male breast cancer is under 1% of all breast cancers (American Cancer Society, Key
    # Statistics for Breast Cancer in Men), so 0.99 female rather than female-only. The
    # age shape uses the two figures ACS publishes for the female disease — about 10% of
    # cases diagnosed before 45, and half of women 62 or younger at diagnosis — which
    # puts the generated median on 62 instead of on the midpoint of a uniform draw. The
    # floor is 20 because SEER's age-at-diagnosis table starts there and rounds the
    # under-20 share to zero.
    "C50.919": {"female_probability": 0.99, "age_bands": ((10, 20, 44), (40, 45, 62), (50, 63, 100))},  # Breast cancer
    # About 8 of the 10 million Americans with osteoporosis are women (Bone Health &
    # Osteoporosis Foundation, Osteoporosis Fast Facts). M81.0 is *age-related*
    # osteoporosis specifically, and the densitometric criterion it is diagnosed by is
    # defined for postmenopausal women and for men aged 50 and over — hence the floor.
    "M81.0": {"female_probability": 0.80, "min_age": 50},  # Age-related osteoporosis
    # NHANES 2015-2016 found gout in 5.2% of men and 2.7% of women (Chen-Xu et al.,
    # Arthritis Rheumatol 2019), leaving women about a third of prevalent cases. Gout
    # under 30 is rare enough that it usually points at an inherited enzyme defect or
    # renal disease rather than at ordinary gout.
    "M10.9": {"female_probability": 0.35, "min_age": 30},  # Gout
    # About 9 in 10 people with lupus are women (CDC's national lupus registries; US
    # Office on Women's Health). Childhood-onset lupus is real, so there is no floor.
    "M32.9": {"female_probability": 0.90},  # Systemic lupus erythematosus
    # Sjögren's runs about 9:1 female across population-based studies, and higher in
    # several of them.
    "M35.00": {"female_probability": 0.90},  # Sjögren's syndrome
    # The USPSTF screening review puts aneurysm prevalence over 50 at 3.9-7.2% in men
    # against 1.0-1.3% in women, and screening is offered to men only. I71.9 is
    # *unspecified site*, so it also covers thoracic aneurysm, whose sex ratio is
    # flatter; 0.2 follows the abdominal figures, which dominate the counts.
    "I71.9": {"female_probability": 0.20, "min_age": 50},  # Aortic aneurysm
    # Almost two-thirds of Americans with Alzheimer's are women (Alzheimer's Association,
    # Alzheimer's Disease Facts and Figures). The same source puts younger-onset dementia
    # at roughly 200,000 Americans aged 30-64 against about 7 million aged 65 and over
    # with Alzheimer's dementia, so the under-65 band is a few percent — rounded up to 5,
    # generously. Early-onset disease is defined by onset before 65 and is vanishingly
    # rare below the mid-forties, which is where the floor comes from.
    "G30.9": {"female_probability": 0.65, "age_bands": ((5, 45, 64), (95, 65, 100))},  # Alzheimer's disease
    # Women are 5-8 times likelier than men to develop thyroid disease (American Thyroid
    # Association) — a statement about thyroid disease as a whole, used here as the best
    # published figure for hypothyroidism on its own.
    "E03.9": {"female_probability": 0.85},  # Hypothyroidism
    # Rheumatoid arthritis runs about 3:1 female overall and closer to 2:1 after 60
    # (Alamanos & Drosos, Autoimmun Rev 2005, and the reviews since); 0.70 sits at the
    # conservative end of "two to three times more common in women".
    "M06.9": {"female_probability": 0.70},  # Rheumatoid arthritis
    # Multiple sclerosis is about 3:1 female in contemporary cohorts, up from 2:1 in the
    # 1980s and 1:1 in the 1940s — the ratio is still moving, so this one will date.
    "G35": {"female_probability": 0.75},  # Multiple sclerosis
    # CDC's ADDM network identified autism in 4.9% of boys and 1.4% of girls aged 8 in
    # 2022 (MMWR Surveill Summ 2025;74(2)). That is the *diagnosed* ratio: girls are
    # widely held to be under-diagnosed, so the underlying ratio is probably narrower —
    # but a fixture built from health and education records should look like the records.
    "F84.0": {"female_probability": 0.22},  # Autism spectrum disorder
    # 15% of boys and 8% of girls aged 3-17 had ever been diagnosed with ADHD in the 2022
    # National Survey of Children's Health (CDC). Diagnosed, with the same caveat.
    "F90.9": {"female_probability": 0.35},  # Attention deficit hyperactivity disorder
    # ---- Lifelong, but not spread evenly across a lifetime. ----
    # Adults are two-thirds of the people living with congenital heart disease: 66% (95%
    # CI 64-68) in 2010, up from 49% in 2000 (Marelli et al., Circulation
    # 2014;130:749-756). A ceiling would still be wrong — Q24.9 is unspecified, and it
    # covers lesions compatible with a normal lifespan — and the draw stays uniform
    # *within* each group, because the child/adult split is the part with a source. That
    # alone moves the median generated age from 50 to about 38.
    "Q24.9": {"age_bands": ((34, 0, 17), (66, 18, 100))},  # Congenital heart disease
    # Cystic fibrosis is lifelong, and the CF Foundation Patient Registry gives its
    # shape: about 60% of people with CF in the US are 18 or over, 27% of those adults
    # are 40 or over, and 22% of the 40-and-overs are 60 or over. Median predicted
    # survival for a child born in 2020-2024 is 65 years, so 80 is the outermost age this
    # generator will produce, not a limit on the disease — the same sense in which
    # `max_value` bounds an analyte.
    "E84.9": {"age_bands": ((40, 0, 17), (44, 18, 39), (12, 40, 59), (4, 60, 80))},  # Cystic fibrosis
}

# A sex weighting is applied in whole thousandths and an age band in whole ten-thousandths
# of the band's share, so both draws stay integer arithmetic on the provider's own RNG —
# no floats decide a branch, and a seeded run reproduces exactly.
SEX_PROBABILITY_RESOLUTION = 1_000
AGE_BAND_RESOLUTION = 10_000

# The ages `patient()` draws between when a condition constrains neither end. No age
# structure is modelled — a real clinic population is far from uniform — because any
# curve would be a claim about a population this package does not have.
PATIENT_AGE_RANGE = (0, 100)


# --------------------------------------------------------------------------------------
# Alcohol
# --------------------------------------------------------------------------------------
#
# One UK unit = 10 mL = 8 g of pure ethanol (a US "standard drink" is 14 g, i.e. 1.75
# UK units — divide by 1.75 to convert). The bands follow the UK Chief Medical
# Officers' 2016 low-risk drinking guidelines: 14 units a week or fewer is "low risk"
# for both sexes. The 35-unit boundary between increasing and higher risk is a
# sex-neutral simplification of the older 35 (women) / 50 (men) split, because this
# method does not take a sex.
ALCOHOL_UNIT_GRAMS = 8.0

# (cumulative percentile, min units, max units). Roughly the shape of the adult
# distribution reported by the Health Survey for England: about a fifth of adults do not
# drink at all, most drinkers stay inside the guideline, and there is a long right tail.
ALCOHOL_WEEKLY_BANDS: tuple[tuple[int, int, int], ...] = (
    (20, 0, 0),
    (65, 1, 14),
    (88, 15, 35),
    (100, 36, 90),
)

# (upper bound in units per week, label key). The last entry catches everything above.
ALCOHOL_CATEGORY_THRESHOLDS: tuple[tuple[int, str], ...] = (
    (0, "alcohol_none"),
    (14, "alcohol_low_risk"),
    (35, "alcohol_increasing_risk"),
)
ALCOHOL_HIGHEST_CATEGORY = "alcohol_higher_risk"

# --------------------------------------------------------------------------------------
# How far outside the reference interval an abnormal value lands
# --------------------------------------------------------------------------------------
#
# Drawing uniformly between the reference boundary and `max_value` would make the
# average diabetic HbA1c a diabetic emergency, because the abnormal band is as wide as
# the worst case ever seen and most abnormal results are mild. An abnormal value is
# therefore placed at
#
#     boundary + fraction x (extreme - boundary)
#
# where the fraction comes from one of three severity tiers: mildly abnormal most of the
# time, markedly abnormal rarely. (cumulative percentile, lowest fraction, highest).
#
# The resulting medians land where a clinician would expect them — HbA1c 53 mmol/mol in
# type 2 diabetes with a 90th centile of 84, haemoglobin 112 g/L in iron-deficiency
# anaemia, creatinine 174 µmol/L in CKD, systolic 136 mmHg in hypertension, temperature
# 37.7 °C in pneumonia — while leaving the extremes reachable.
#
# This models DIRECTION, not severity: nothing here knows how advanced a condition is,
# so a panel says "the HbA1c is high because this record says diabetes", never "this
# patient's diabetes is poorly controlled".
SEVERITY_TIERS: tuple[tuple[int, float, float], ...] = (
    (70, 0.0, 0.15),
    (95, 0.15, 0.5),
    (100, 0.5, 1.0),
)
SEVERITY_RESOLUTION = 10_000

# The flag IDs above are locale-neutral; these are the label keys they are shown as.
FLAG_LABEL_KEYS: dict[Flag, str] = {
    "low": "flag_low",
    "normal": "flag_normal",
    "high": "flag_high",
}


# --------------------------------------------------------------------------------------
# Helpers (pure: no randomness lives in this module)
# --------------------------------------------------------------------------------------


def to_steps(value: float, decimals: int) -> int:
    """Convert a value to whole quantisation steps (0.1 mmol/L, 1 mmHg, ...).

    Every draw happens in integer steps, so a generated value is exactly representable
    at the analyte's reporting precision and comparisons against the reference interval
    cannot be decided by a float artefact.
    """
    return round(value * 10**decimals)


def from_steps(steps: int, decimals: int) -> float:
    """Convert whole steps back to a reported value (an int when decimals is 0)."""
    if decimals == 0:
        return int(steps)
    return round(steps / 10**decimals, decimals)


def measurement_band(low: float, high: float, min_value: float, max_value: float, decimals: int, direction: Direction | None = None) -> tuple[int, int]:
    """Return the inclusive band of steps a value may be drawn from.

    `direction=None` gives the reference interval itself. `"high"` gives everything
    above it up to `max_value`, `"low"` everything below it down to `min_value` — so a
    value drawn from the band is guaranteed to be outside the reference interval, on the
    stated side, and still a number that could be printed on a report.

    Raises:
        ValueError: if the requested direction has no band at all (the reference
            interval already touches the outer bound, as for oxygen saturation at 100%),
            rather than quietly returning an in-range value that contradicts the flag.
    """
    low_steps = to_steps(low, decimals)
    high_steps = to_steps(high, decimals)
    if direction is None:
        return low_steps, high_steps
    if direction == "high":
        band = (high_steps + 1, to_steps(max_value, decimals))
    elif direction == "low":
        band = (to_steps(min_value, decimals), low_steps - 1)
    else:
        raise ValueError(f"Unknown direction '{direction}'; expected 'low' or 'high'")
    if band[0] > band[1]:
        raise ValueError(f"No '{direction}' band exists for a reference interval of {low}-{high} bounded by {min_value}-{max_value}")
    return band


def flag_for(value_steps: int, low_steps: int, high_steps: int) -> Flag:
    """Flag a value against its reference interval, comparing in whole steps."""
    if value_steps < low_steps:
        return "low"
    if value_steps > high_steps:
        return "high"
    return "normal"


def declared_age_range(constraint: DemographicConstraint) -> tuple[int, int]:
    """Return the inclusive age range a constraint declares, before any clamping.

    An `age_bands` entry declares its range through its bands — the first band's floor
    and the last band's ceiling — so the bounds are written once rather than restated as
    `min_age`/`max_age` beside them, where the two could drift apart.
    """
    bands = constraint.get("age_bands")
    if bands:
        return bands[0][1], bands[-1][2]
    return constraint.get("min_age", PATIENT_AGE_RANGE[0]), constraint.get("max_age", PATIENT_AGE_RANGE[1])


def age_range_for(constraint: DemographicConstraint, default: tuple[int, int] = PATIENT_AGE_RANGE) -> tuple[int, int]:
    """Return the inclusive age range a constraint allows, within `default`.

    Raises:
        ValueError: if the constraint and the default do not overlap at all — which is
            how `patient_record()` learns that a paediatric-only condition cannot be
            given an adult age, instead of silently returning an impossible one.
    """
    declared_minimum, declared_maximum = declared_age_range(constraint)
    minimum = max(default[0], declared_minimum)
    maximum = min(default[1], declared_maximum)
    if minimum > maximum:
        raise ValueError(f"No age between {default[0]} and {default[1]} satisfies this condition's constraint {dict(constraint)}")
    return minimum, maximum


def age_bands_for(constraint: DemographicConstraint, default: tuple[int, int] = PATIENT_AGE_RANGE) -> tuple[tuple[int, int, int], ...]:
    """Return the `(weight, lowest, highest)` bands an age may be drawn from.

    A constraint with no `age_bands` gives one band spanning its whole allowed range,
    which is the uniform draw. A constraint with bands gives them clipped to `default`
    and reweighted for the clipping: `patient_record()` asks for adults only, so cystic
    fibrosis loses its 0-17 band entirely and congenital heart disease loses a third of
    its population — and the remaining bands keep their proportions to each other rather
    than being silently renormalised into the wrong shape. A band clipped in half carries
    half its share, because the draw inside a band is uniform.

    The weights are integers (`AGE_BAND_RESOLUTION` per share point) and are relative to
    each other, not percentages: the caller draws against their sum.

    Raises:
        ValueError: from `age_range_for`, if nothing at all survives the clipping.
    """
    minimum, maximum = age_range_for(constraint, default)
    bands = constraint.get("age_bands")
    if not bands:
        return ((AGE_BAND_RESOLUTION, minimum, maximum),)
    clipped = []
    for share, lowest, highest in bands:
        first, last = max(lowest, minimum), min(highest, maximum)
        if first > last:
            continue
        weight = share * AGE_BAND_RESOLUTION * (last - first + 1) // (highest - lowest + 1)
        if weight > 0:
            clipped.append((weight, first, last))
    return tuple(clipped)


def is_paediatric_only(code: str, adult_age: int = ADULT_AGE_RANGE[0]) -> bool:
    """Whether a condition's constraint excludes every adult age."""
    return declared_age_range(DEMOGRAPHIC_CONSTRAINTS.get(code, {}))[1] < adult_age


def satisfies_demographics(code: str, sex: Sex, age: int) -> bool:
    """Whether a patient of this sex and age could have the condition with this code.

    A `female_probability` weighting is deliberately not consulted: a weighted condition
    can occur in either sex, and this predicate answers "could", not "how often".
    """
    constraint = DEMOGRAPHIC_CONSTRAINTS.get(code, {})
    if "sex" in constraint and constraint["sex"] != sex:
        return False
    minimum, maximum = declared_age_range(constraint)
    return minimum <= age <= maximum


def alcohol_category_key(units: int) -> str:
    """Return the label key for a weekly consumption in UK units.

    Raises:
        ValueError: if units is negative.
    """
    if units < 0:
        raise ValueError(f"Alcohol units per week cannot be negative: {units}")
    for upper_bound, key in ALCOHOL_CATEGORY_THRESHOLDS:
        if units <= upper_bound:
            return key
    return ALCOHOL_HIGHEST_CATEGORY
