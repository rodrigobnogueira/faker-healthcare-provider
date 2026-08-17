# Agent Guidance

This repository contains a Faker provider for generating **correlated** healthcare/medical
test data in six languages (English, Spanish, Portuguese, Chinese, French, German). Keep
changes small, data-focused, and easy to verify.

> MEDICAL DISCLAIMER: All data here is for TESTING AND DEVELOPMENT ONLY. It must never be
> presented as usable for real diagnosis, treatment, or any clinical decision.

## Project Layout

- `faker_healthcare/provider.py` — the base `HealthcareProvider` and its public API.
- `faker_healthcare/disease_correlations.py` — the English `DISEASE_CORRELATIONS` catalog.
- `faker_healthcare/constants.py` — static English tuples (departments, allergies, the
  brand-name morpheme pools, etc.), and the re-export of `BRAND_DRUG_NAMES`.
- `faker_healthcare/brand_names.py` and `faker_healthcare/zh_CN/brand_names.py` —
  **generated**; the screened brand-name catalogues. Never edit them by hand.
- `scripts/generate_brand_names.py` — the screens and the review record that produce those
  two modules. This is the file you edit when a brand name has to change.
- `faker_healthcare/clinical_values.py` — the **locale-neutral** numeric tables: vital-sign
  and lab-analyte definitions (units, reference intervals, bounds, precision) and the
  ICD-10-keyed `CONDITION_LAB_EFFECTS` / `CONDITION_VITAL_EFFECTS` correlations. No
  translated text lives here, and it is never duplicated per locale.
- `faker_healthcare/prescribing.py` — the **locale-neutral** dose ladders: per substance
  ID, the dispensed strengths, the unit, the route and the plausible frequencies, plus the
  route/frequency/order-status IDs. Never duplicated per locale.
- `faker_healthcare/assessments.py` — the **locale-neutral** definitions of the six scored
  instruments (maximum, severity bands, cut-off, which conditions use which). Read its
  docstring before touching it: it carries the copyright boundary that forbids item text.
- `faker_healthcare/identifiers.py` — generated patient identifiers and their check-digit
  arithmetic (currently the NHS Number, Modulus 11), and the reserved-test-range rule.
- `faker_healthcare/clinical_labels.py` and `faker_healthcare/<locale>/clinical_labels.py` —
  the display words for those IDs: `CLINICAL_LABELS` (analyte and vital names, the
  low/normal/high flags, the alcohol categories, the administration routes, the dosing
  frequencies, the medication-order statuses, the assessment severity bands) and
  `MEDICATION_NAMES` (substance ID → the spelling that locale's catalogue uses). Every
  locale defines the same key set for both.
- `faker_healthcare/types.py` — `DiseaseData` / `PatientScenario` / `Patient` /
  `PatientRecord` / measurement, order and assessment TypedDicts (the data shapes).
  Optional keys use the two-class TypedDict form, not `typing.NotRequired`, because the
  package supports Python 3.10.
- `faker_healthcare/<locale>/` — one package per locale (`pt_BR`, `es_ES`, `zh_CN`, `fr_FR`,
  `de_DE`), each with its own `__init__.py` (a `Provider` subclass), `constants.py`,
  `clinical_labels.py`, and `disease_correlations.py`.
- `tests/` — `test_provider.py`, `test_correlations.py`, `test_locales.py`,
  `test_clinical_values.py`, `test_records.py`, `test_performance.py`, `test_readme.py`,
  `conftest.py`
  (which loads the generator script so the tests re-run its screens instead of restating
  them), and `zh_cn_equivalents.py` — the committed English→Simplified Chinese equivalent
  of every medication and symptom, which `TestZhTranslationEquivalence` holds the zh_CN
  catalogue to slot by slot.
- `README.md` — its examples are **executable**: `tests/test_readme.py` runs every fenced
  `python` block and calls every method the "Available Methods" table lists. Change a public
  method and the README changes with it, in the same PR.
- `CONTRIBUTING.md` — the human-facing summary of these rules; when a rule here changes,
  update it in the same change so the two cannot drift.

## Data Shapes (do not drift)

Every entry in every `DISEASE_CORRELATIONS` dict is a `DiseaseData`:

```python
"Disease Name": {
    "icd10": "E11.9",                       # str, WHO ICD-10 format: ^[A-Z]\d{2}(\.\d{1,3})?$
    "symptoms": ["...", "..."],             # non-empty list[str]
    "medications": ["...", "..."],          # non-empty list[str]
    "medical_specialty": "Endocrinology",   # str
},
```

- All four keys are required and must be non-empty; tests enforce this (`TestDataIntegrity`,
  `TestLocaleParity`).
- The base provider **derives** `diseases`, `icd10_codes`, `symptoms`, `generic_drugs`,
  `interventions`, and `medical_specialties` from `DISEASE_CORRELATIONS`. Do not add these as
  redundant class attributes on locale providers — `test_performance.py` asserts they stay
  derived properties. What a locale *does* declare is its static tuples
  (`hospital_departments`, `blood_types`, `allergies`, `medical_procedures`,
  `insurance_plans`, `vital_signs`, `non_drug_interventions`), which the same test requires.
- `icd10` is universal (same code across all locales). Symptoms, medications, disease names,
  and specialties are translated per locale. Two distinct disease names may legitimately share
  one ICD-10 code (e.g. `Epilepsy` and `Seizure Disorder` → `G40.909`); the code is deduped
  via a set in `icd10_codes`.

## Correlation Consistency (the core invariant)

The whole point of the library is that generated clinical data is internally consistent.
When you add or edit a disease:

- The `icd10` must be the correct WHO ICD-10 code for that condition. Check it is the code for
  the condition you named, not a neighbouring one: rheumatoid arthritis shipped as `M79.1`
  (*Myalgia*, non-billable) for several releases before it was corrected to `M06.9`.
- `symptoms` must be symptoms that condition actually causes, and **each entry must be a
  self-contained clinical term**. Never split one sentence across slots: stress incontinence
  once read `["Urine Leakage with Coughing", "Sneezing", "Exercise", "Lifting", "Laughing"]`,
  so `symptom()` returned "Laughing" as a symptom and the fragments leaked into the global
  symptom pool. Each slot must still read correctly on its own, out of context.
- `medications` must be treatments actually used for that condition, and **must name
  substances, not drug classes**. `["Risperidone", "Aripiprazole", "SSRIs", "Stimulants",
  "Anticonvulsants"]` is three substances plus two categories padding out the list; name the
  substances or shorten the list. (Some older entries still carry class names such as
  `Antibiotics` or `Statins`; fix them when you touch that condition, and never add a new one.)
- Use real **generic** names, **never brand/trademark names** — brand names are produced
  separately by `brand_drug()`. Prefer the **INN** (WHO places it in the public domain),
  **except where a locale has a different adopted name in clinical use**, in which case use
  the locale's adopted name: the `en` catalog says `Albuterol` (INN salbutamol) and
  `Acetaminophen` (INN paracetamol) because those are the US-adopted names, and `de_DE` says
  `Paracetamol`. Match the locale, do not "correct" a locale's adopted name to the INN.
- A treatment that is **not a drug** — a procedure, a device, a diet, `Surgery`, `IV Fluids`,
  `Wrist Splint`, `No Medications` — is legitimate inside `medications`, but it must also be
  listed in that locale's `NON_DRUG_INTERVENTIONS` tuple in `constants.py`, at the same index
  as its counterpart in every other locale. That tuple is what keeps `generic_drug()` a pool of
  drugs; `intervention()` and the `interventions` property expose the rest.
  `tests/test_locales.py` fails if a declared intervention is not prescribed by any condition.
- `medical_specialty` must be the specialty that manages the condition, and should reuse an
  existing specialty string already present in the catalog.

`patient_scenario()`, `icd10_code(disease=...)`, `symptom(disease=...)`, and
`medication(disease=...)` all read straight from this data, so any inconsistency becomes a
visible, wrong-looking record.

**An accessor that takes a `disease=` argument must RAISE `ValueError` for a disease it does
not know** — `icd10_code`, `symptom`, `medication`, `disease_symptoms`, `medications`,
`patient_scenario`, `blood_pressure`, `vital_sign_measurement`, `vital_sign_measurements`,
`lab_result`, `lab_panel`, `medication_order`, `medication_orders`, `assessment_score`,
`patient` and `patient_record` all do. Never fall back to an uncorrelated random draw: the
caller asked about one condition and would silently receive another condition's data, which
is precisely the failure this library exists to prevent. The same applies to an unknown
measurement or instrument ID (`lab_result(analyte=...)`,
`vital_sign_measurement(name=...)`, `assessment_score(instrument=...)`).

## Measurements (the locale-neutral half)

`vital_sign()` returns the NAME of a vital sign; the measurement API returns numbers —
`blood_pressure()`, `vital_sign_measurement()`, `vital_sign_measurements()`,
`body_measurements()`, `alcohol_units_per_week()`, `alcohol_intake_category()`,
`lab_result()`, `lab_panel()`. All of it is additive: the string API is unchanged.

- **Reference ranges, units and numeric bounds are locale-invariant, so they live in ONE
  module.** `faker_healthcare/clinical_values.py` keys them by stable IDs (`heart_rate`,
  `hba1c`); each locale translates **labels only**, in its own `clinical_labels.py`. Do not
  copy a range into a locale package: six copies of one number are six chances to disagree
  about a value that cannot legitimately differ, and the first correction leaves five stale.
  `tests/test_locales.py::TestClinicalLabelParity` enforces both halves — every locale must
  define every label key, no locale may ship a `clinical_values.py` or redeclare
  `vital_definitions` / `lab_definitions`, and the base label key set must equal the union
  of the numeric tables (so a new analyte cannot ship unnamed).
- **Units are SI** (mmol/L, µmol/L, g/L, IFCC mmol/mol), stated in the module docstring with
  the conversions to US conventional units. Do not mix systems: an analyte in the wrong one
  is indistinguishable from a wrong number.
- **`CONDITION_LAB_EFFECTS` / `CONDITION_VITAL_EFFECTS` are keyed by ICD-10 code**, not by
  disease name, because the code is the one field identical in all six locales — that is
  what makes one table correlate in French and Chinese. A code that is not in the catalogue
  correlates with nothing; a test iterates every key to prove it exists.
- **Only add an effect you are confident about.** The bar is the same as for a condition's
  symptoms: textbook and unambiguous for the *unqualified* condition, not "can occur in
  severe cases". An empty entry is better than a wrong one — a condition with no entry
  simply produces in-range values, which is an honest "nothing specific here". The module
  keeps worked examples of the bar (haemophilia prolongs the APTT, not the INR).
- **A direction must have somewhere to go.** `measurement_band()` raises rather than
  returning an in-range value for an impossible direction (nothing can push oxygen
  saturation above 100%), and a test asserts no shipped effect asks for one.
- **The generated numbers must agree with each other.** These are invariants, asserted over
  thousands of seeded draws in `tests/test_clinical_values.py`, not spot-checked:
  `systolic > diastolic` by at least a plausible pulse pressure (they are one measurement:
  diastolic is drawn and systolic derived from it); `flag` is derived from the same
  comparison the caller can make against `reference_low`/`reference_high`; `bmi` is computed
  from the `height_cm` and `weight_kg` returned beside it.
- **Model direction, not severity.** An abnormal value is placed by severity tier (mild most
  of the time, marked rarely) so a diabetic HbA1c reads like a diabetic HbA1c, but nothing
  here knows how advanced a condition is, and no method should claim to.
- **Adult data only.** `body_measurements()` refuses a paediatric age rather than
  extrapolating an adult curve; real growth references (WHO/CDC charts) are a data import,
  with the licence review that implies. `patient_record()` is bound by the same limit and
  refuses a paediatric-only condition; `patient()`, which returns no measurements, is not.

## Records (orders, assessments, demographics, identifiers)

`medication_order()`, `medication_orders()`, `assessment_score()`, `nhs_number()`,
`patient()` and `patient_record()` are the second half of the same design, and the same
split applies: **numeric tables are locale-neutral, only words are translated.**

- **Dose ladders live once**, in `prescribing.py`, keyed by substance ID. A ladder carries
  the dispensed strengths, the unit, the **route** and the plausible **frequencies**,
  because all three belong to the substance: insulin is subcutaneous whatever it treats,
  methotrexate is weekly. Three independent draws produce "Insulin 500 mg orally four
  times daily".
- **Never emit an invented dose.** A substance with no verified adult ladder returns
  `None` for dose, unit, route and frequency. Cytotoxic chemotherapy is deliberately
  absent (real doses are body-surface-area based), and so are drug *class* names, which
  have no dose at all. Adding a ladder means naming an adult dose you can source (BNF or
  the SmPC), in the same PR as the six `MEDICATION_NAMES` entries for it.
- **`MEDICATION_NAMES` is the bridge between the two halves.** It maps the substance ID to
  the exact string that locale's catalogue ships, and `tests/test_locales.py::TestMedicationNameParity`
  fails if a name is not a medication that locale actually prescribes — which is what makes
  it checkable rather than a promise. If a locale spells a drug two ways, pick the correct
  one and accept that the other occurrence goes undosed; do not add a wrong name to widen
  coverage.
- **Assessment instruments: the score, never the items.** See below — this one is a legal
  boundary, not a style preference.
- **Demographic constraints live once**, in `clinical_values.DEMOGRAPHIC_CONSTRAINTS`, keyed
  by ICD-10 code. Sex and age are facts about a condition, not words about it, so they are
  never copied into six catalogues. Constrain only what is unambiguous, and record the
  reasoning for a condition you deliberately did NOT constrain (haemophilia's shipped code
  is *acquired* haemophilia, which has no sex skew; sickle cell disease skews by ancestry,
  which this package does not model).
- **A skew is weighted and sourced; it is never asserted as an absolute unless it is one.**
  The table offers three strengths and choosing the wrong one generates a false fact:
  - `sex` is an **absolute lock** — preeclampsia is female, full stop. Use it only where
    the condition genuinely cannot occur in the other sex;
  - `female_probability` is a **weighting**, the share of patients who are female, for a
    condition that is strongly skewed but not locked;
  - `min_age`/`max_age` bound a uniform age draw, `age_bands` (`(share, lowest, highest)`
    triples, contiguous, summing to 100) replace them with a shape, and an absent key means
    "anyone". `age_bands` and `min_age`/`max_age` are mutually exclusive: the bands already
    carry the bounds, and restating them is two places to disagree.
- **Cite the figure inline, next to the entry.** The same bar as `CONDITION_LAB_EFFECTS`:
  the number and where it comes from, in the comment above the entry — "male breast cancer
  is under 1% of breast cancers (ACS)", not "mostly women". **A skew you cannot source is
  not added**, and a sourced skew is written at the strength the source supports.
- **"Free" is a claim too.** For one release this table was binary — locked or free — and
  three conditions were correctly refused a lock on medical grounds, which left them free.
  Breast cancer then generated 49% male patients against a real figure under 1% (a fiftyfold
  error, worse than the male-preeclampsia bug the table was built to fix) and cystic
  fibrosis drew ages uniformly to 100. Reaching for `sex: "female"` would have been wrong in
  the other direction: men with breast cancer are a real patient group and must remain
  generatable. If neither absolute is true, weight it and cite the weight.
- **Assert the weighting, do not just declare it.** `tests/test_records.py::TestDemographicConstraints`
  draws thousands of seeded patients per weighted condition and fails if the observed split
  or age shape drifts from the configured one, if a weighting silently becomes a lock, or if
  a constrained code is not a real catalogue code. A weighting nobody measures is a comment.

## Assessment Instruments: scores only, never item text

**This is a copyright boundary and it is not negotiable.** `faker_healthcare/assessments.py`
may contain an instrument's name, its maximum score, its severity bands and its published
cut-off, and nothing else. It must never contain the items, the questions, the response
options, the answer wording or the scoring instructions — and neither may a locale package,
a docstring, a test fixture, the README, or an example.

Most of these instruments are under active copyright; several are licensed commercially and
their translations are separately licensed works. Reproducing the items would redistribute
someone else's literary property under a licence its owner never granted, in six languages,
to everyone who installs the package. A **score** is different in kind: "PHQ-9 = 14" is a
number about a fictional patient, and it is also exactly what a medical record, a research
extract or a de-identification test rig actually holds.

- Ship only the six agreed instruments: PHQ-9, GAD-7, MMSE, MADRS, AUDIT-C, CAGE. A seventh
  is a maintainer decision.
- The MMSE is **inverted** — a low score is the abnormal one. Anything that places a score
  by severity must read `higher_is_worse` rather than assuming.
- Classify conditions by **ICD-10 only**. Do not reference any other diagnostic manual in
  data, API names, comments or docs.
- `tests/test_records.py::TestAssessmentBoundary` enforces the shape from both ends: the
  definition may carry only the five allowed keys and the result only the four. A PR that
  adds item text fails there, and would be closed anyway.

## Locale Mechanism

- Each locale package's `Provider` subclasses the base and overrides `_load_disease_correlations`
  to import that locale's `DISEASE_CORRELATIONS` lazily (import happens inside the method, not at
  module top level — this keeps per-locale data out of memory until used; `test_performance.py`
  `test_locale_memory_isolation` enforces it via subprocesses).
- Keep the catalogs at **parity**, and parity means **content** parity, not equal counts.
  Equal counts alone are worthless: zh_CN shipped for several releases missing the `G40.909`
  condition the other five locales had and carrying an `H25.9` condition none of them had, and
  the counts matched perfectly. `test_locales.py::TestLocaleParity` now enforces all of:
  - the **multiset of ICD-10 codes** per locale equals the base's (a multiset, because two
    conditions may legitimately share a code);
  - per ICD-10 code, the **(symptom count, medication count) pairs** equal the base's, so a
    translation cannot quietly drop a symptom;
  - every **shared constant tuple** (`HOSPITAL_DEPARTMENTS`, `BLOOD_TYPES`, `ALLERGIES`,
    `MEDICAL_PROCEDURES`, `VITAL_SIGNS`, `NON_DRUG_INTERVENTIONS`) has the same cardinality in
    all six locales. `INSURANCE_PLANS` is the one deliberate exemption — plan types are
    country-specific. A **new** constant must be added to one of the classification lists in
    `test_locales.py` or the suite fails;
  - every locale's `CLINICAL_LABELS` has the **same key set** as the base's, none of them
    empty, none of them duplicated within a locale, and not simply copied from English. The
    numeric tables behind those labels are the other deliberate exemption: they are
    locale-neutral by design and a test fails if a locale starts duplicating them;
  - `zh_CN` contains no Japanese kana (U+3040–U+30FF) — that is how a katakana drug name
    (リオチロニン) reached the Simplified Chinese catalog.

- **A localized medication must name the SAME SUBSTANCE as the base entry, and a test
  says so.** This is the most dangerous defect this data can carry, because it is
  invisible: a real drug, plausible for the condition, in one locale only. zh_CN shipped
  four — `地西泮` (diazepam) for Disulfiram, `可乐定` (clonidine) for Clonazepam,
  `铝碳酸镁` (hydrotalcite) for Sucralfate, `布林佐胺` (brinzolamide) for Brimonidine —
  and every parity count was correct throughout, because a substitution and an index shift
  both preserve the counts.
  - `tests/zh_cn_equivalents.py` pins the correspondence: the exact Chinese string for
    every English medication and symptom in the base catalogue.
    `test_locales.py::TestZhTranslationEquivalence` walks the two catalogues together, by
    ICD-10 code and by position within it, and fails by name on a slot that disagrees.
    Correcting or adding a translation means editing that table in the same commit.
  - The medication mapping is **one-to-one in both directions**: one Chinese name may not
    stand for two substances (that is exactly what `可乐定` was doing). Symptoms are
    exempt from injectivity only because the base catalogue writes the same symptom two
    ways (`Headache`/`Headaches`, `Frequency`/`Frequent Urination`).
  - Where a substance has a dose ladder, this table and `MEDICATION_NAMES` must agree; a
    test asserts it, so the two mappings cannot drift.
  - The other five locales have no such table yet. Adding one is a locale-review task, not
    a mechanical one — write the table as the *record* of a term-by-term review, never by
    transcribing what the catalogue happens to say today.

  If you add a condition, add it to **all six** `disease_correlations.py` files (English base
  plus five locales), with the same number of symptoms and medications in each. If you add,
  remove, or translate a shared constant entry, do it in all six `constants.py` files.
- Per-locale translation conventions already in the data (follow them exactly):
  - `pt_BR`, `es_ES`: medication names localized (e.g. `Amoxicillin` → `Amoxicilina`).
  - `de_DE`: medication names germanized (e.g. `Doxycycline` → `Doxycyclin`, `Cefuroxime` →
    `Cefuroxim`); use the German medical term where it differs (e.g. bacterial cellulitis is
    `Phlegmone`, not `Cellulite`).
  - `fr_FR`: the `medications` list is kept in **English** (only disease names, symptoms, and
    specialty are translated). Match this — do not translate French medications.
  - `zh_CN`: disease names, symptoms, medications, and specialties are all in Simplified Chinese.
  - `medical_specialty` strings are already translated per locale — reuse the exact existing
    spelling for that locale rather than inventing a new one.

## Data Update Rules

- Catalog updates are **additive by default**. Do not remove or rename an existing condition
  unless the user asks, or unless it is a verified duplicate/typo/invalid entry.
- **Verify medical facts before adding them.** Do not invent clinical data. Check condition
  names, ICD-10 codes, and medication names against reputable sources (WHO ICD-10 / ICD-10-CM
  references, CDC, FDA, IDSA/AASLD or equivalent specialty guidelines) and prefer official
  documentation. Newer-than-your-training drugs/codes can be real — confirm, don't assume fake.
- When you add a condition, append it to the end of each `disease_correlations.py` (order is not
  significant) and update the "N diseases" count in each module docstring.
- **Brand names are fictitious and come from a screened, committed list.** `brand_drug()` returns
  `random_element(BRAND_DRUG_NAMES)` — 245 names in the generated `faker_healthcare/brand_names.py`
  — and zh_CN pairs one with a name from the generated `ZH_BRAND_NAMES`. **Never add a real
  trademark anywhere**, not to `medications` and not to the morpheme pools.
  - Both generated modules are written by `scripts/generate_brand_names.py`. Edit that script, not
    the modules; `tests/test_provider.py` re-runs it in `--check` mode and fails if the committed
    files differ. The morpheme tuples (`BRAND_PREFIXES` / `BRAND_INFIXES` / `BRAND_SUFFIXES`) and
    `ZH_BRAND_CHARS` are its **input**, so editing one changes nothing until you re-run it.
  - The script screens every candidate four ways: no `BRAND_FORBIDDEN_ENDINGS` WHO INN class stem,
    not in `REAL_PRODUCT_DENYLIST`, no `OFFENSIVE_SUBSTRINGS` term, and no collision with a drug in
    any locale's catalogue. Adding a name means adding it to `REVIEWED_LATIN_NAMES` **after reading
    it**; `--propose N` prints screened candidates spread evenly across prefixes to review.
  - **The Chinese list works exactly the same way** — `REVIEWED_ZH_NAMES` is its
    `REVIEWED_LATIN_NAMES`, `--propose-zh N` is its `--propose`, and `ZH_REAL_PRODUCT_DENYLIST` and
    `ZH_GENERIC_MORPHEMES` are its screens. A locale that invents identifiers does not get a weaker
    process because the reviewer is harder to find; it gets the same one, and the module says what
    the review did and did not cover. `ZH_GENERIC_MORPHEMES` is the Chinese `BRAND_FORBIDDEN_ENDINGS`:
    a name containing 素/维/尔/平/定 reads as a substance (维生素, 美托洛尔, 氨氯地平, 安定), not as a brand.
  - `REAL_PRODUCT_DENYLIST`, `ZH_REAL_PRODUCT_DENYLIST` and `OFFENSIVE_SUBSTRINGS` are
    **append-only**. A name is never removed once added, whatever the reason it went in: removing
    one silently re-admits a name a reviewer already rejected. Discontinued products and marginal
    collisions stay. Write the reason beside each entry — a 2026-08-16 reading pass rejected 58 of
    the 64 Chinese names then shipping, and the value of that pass is in the 58 recorded reasons,
    not in the 6 survivors.
  - Do not restore the old design. `brand_drug()` used to concatenate morphemes at call time (31,500
    names, 30,752 more in zh_CN), retry 12 times against the INN stems, and **return the last
    attempt anyway** when every retry failed. Nothing screened those names for real products, and
    the same morphemes ported to faker-js produced five that shadow real products — two of them FDA
    veterinary drugs. A number that large cannot be screened; that is the whole reason for the list.
- **Diagnostic codes are kept as reference data.** ICD-10-CM codes come from CDC/NCHS (distributed free
  by the U.S. government); base WHO ICD-10 codes are used under **CC BY-ND 3.0 IGO** — reproduce codes
  verbatim, keep the WHO attribution in the module docstrings and README, and never modify a code.
- Add focused tests that extend the existing patterns (`TestNewConditions` in
  `test_correlations.py`, `TestLocaleParity` in `test_locales.py`).
- **A new public method must reach the README and `showcase.py`.** `tests/test_readme.py`
  executes every fenced `python` block in the README and calls every method its
  "Available Methods" table lists, so a documented method that does not exist — the README
  claimed `medical_specialty()` for several releases, the real name being
  `disease_medical_specialty()` — fails CI. The same test asserts every non-English example
  imports that locale's own `Provider`; adding the base `HealthcareProvider` to a
  `Faker('es_ES')` loads the **English** catalog, which is what the README used to teach.
  It checks each documented method returned something — `None` or an empty container fails,
  **falsiness does not**: `0` is a correct answer from `alcohol_units_per_week()`, and a
  truthiness check would have failed on it about one run in five.

## Generated Identifiers (the reserved-range rule)

Applies to every **numbered identifier a real authority issues to a real person** — an NHS
Number today, and whatever comes next.

- **Default to the range the issuing authority reserves for testing.** `nhs_number()`
  returns a number in the 999 range NHS England never allocates, so a generated identifier
  cannot be a living patient's. The whole hazard is that a *valid* identifier is by
  construction one that could belong to someone real, and a synthetic record carrying one
  can be matched against, or mistaken for, a real record.
- **Make the unreserved mode explicit at the call site and say why**:
  `nhs_number(official_test_range=False)`, documented as capable of colliding with a real
  person's number. Never make it the default, and never make it the only mode.
- **Implement the check digit from the published specification and cite it** in the module
  docstring, with the URL. Get the invalid-remainder case right — an NHS stem whose
  Modulus 11 check digit works out to 10 is never issued and must be redrawn, not
  truncated into something a validator would reject.
- **Test against published examples** the code was not written around, and test that a
  single-digit change stops validating. That is what proves the checksum is the real one
  rather than an arithmetic look-alike.
- If an authority publishes **no** reserved range, say so in the docstring and in the PR,
  and give the caller a way to supply a prefix. Do not quietly generate live-space
  identifiers by default.

## Generated Names (the screened-set rule)

Applies to every **user-visible identifier this package invents** — a brand name, a product
name, a facility or plan name, anything a consumer could mistake for a real named thing.
Clinical data drawn from real catalogues (ICD-10 codes, INN drug names) is reference data
and is governed by the rules above instead.

- **Draw it from a screened, enumerable, committed set. Never assemble it at runtime from a
  space too large to screen.** `random_element(SOME_TUPLE)`, not a loop over morpheme pools.
  The size of the set is the point: a set you can print is a set someone can read, and
  reading it is the only step that catches "this invented name is somebody's product".
- **Generate the set with a committed script, not by hand.** Deterministic, no RNG, sorted
  output, idempotent — re-running it must reproduce the committed file byte for byte, and a
  test must assert that (`--check`). Otherwise the shipped list and the screens drift apart
  and nobody notices.
- **Screen lists are append-only.** Once a name is denied it stays denied, with the reason in
  a comment. Removing an entry re-admits a name a reviewer rejected, and does it invisibly.
- **Assert the safety property by iterating the whole shipped set**, in a test that fails on
  the offending entries by name. Sampling the *generator* — "1000 draws, none of them bad" —
  proves nothing about the entry it did not draw, and neither does a distinctness count.
- **State the claim you can actually support.** "Screened against <these corpora> on <date>"
  is checkable. "Not a real trademark" and "any resemblance is coincidental" are not, and
  this repository shipped both while five reachable names shadowed real products.
- **If a set cannot be responsibly screened** — for instance because it needs a reviewer with
  a language you do not have — ship it anyway as a static list, say plainly in the module and
  the PR that it is unscreened, and leave a marked TODO. A short unreviewed list is auditable
  and fixable; a runtime generator is neither. Do not describe it as screened.
- **A locale-specific generated identifier gets the same machinery as the Latin one**, in the
  same script: its own append-only denylist with a reason per entry, its own equivalent of the
  INN-stem screen (for Chinese, `ZH_GENERIC_MORPHEMES` — a name that reads as a substance is
  not a brand), its own reviewed list, its own `--propose`, and the same whole-set test. The
  TODO above is where such a list *starts*, not where it is allowed to stay: the 64 unreviewed
  Chinese names carried that TODO for one release, a reading pass then rejected 58 of them, and
  the six survivors are what "screened" honestly means here.
- **When the TODO is discharged, replace it with what was actually done — including what was
  not.** "Read one by one in Simplified Chinese on <date> against <these criteria>; not a
  trademark search; no native speaker's sign-off recorded" is checkable and is the whole
  claim. Do not upgrade a reading pass into a sign-off, do not name a reviewer who did not
  review, and keep inviting the report that lands in the denylist.
- **Expect the plausible names to be the dangerous ones.** Chinese pharmaceutical brands recycle
  康/泰/瑞/舒/益/欣 so heavily that the candidates which sound most like a real brand are the ones
  most likely to be one, while the rest fail plausibility instead. A generator over a saturated
  morpheme space has no safe middle, which is why the shipped set is small and why growing it
  means reading candidates one at a time rather than raising a target size.

## Performance Test Expectations

`test_performance.py` guards the memory design: locale providers must not carry derived data as
class attributes, must inherit from `HealthcareProvider`, locale constants must be non-empty
tuples, and importing one locale must not pull another locale's modules into `sys.modules`.
Keep the lazy `_load_disease_correlations` pattern intact.

## Running Tests

Create a venv and run the full suite (including the performance suite) before opening a PR:

```bash
python3 -m venv .venv
.venv/bin/pip install -e ".[dev]"
.venv/bin/python -m pytest
.venv/bin/python -m ruff check .
.venv/bin/python -m ruff format --check .
.venv/bin/python -m mypy --ignore-missing-imports --no-strict-optional .
```

- **CI must run every tool the `dev` extra declares.** A declared-but-unenforced tool is
  how lint drift lands on `main` — either wire it into `.github/workflows/tests.yml` or
  remove it from the extra. Keep the arguments identical to `.pre-commit-config.yaml` so
  the hooks and CI cannot disagree about what "clean" means.

## Publishing a Release

The primary path is automated. Pushing a `vX.Y.Z` tag triggers `.github/workflows/release.yml`,
which runs the tests, builds fresh distributions, runs `twine check`, verifies the tag matches
the `pyproject.toml` version, and publishes to PyPI via **Trusted Publishing** (OIDC — no token
or secret; the publisher is registered on PyPI under project → Settings → Publishing for
`release.yml`, environment `pypi`, owner `rodrigobnogueira`, repository
`faker-healthcare-provider`). The workflow also supports `workflow_dispatch` to (re)run a release
for an already-pushed tag.

Release checklist (the workflow automates build/upload, not the judgment steps):

- Publish only from an up-to-date `main` after all intended PRs are merged.
- Check PyPI for the latest published `faker-healthcare-provider` version before choosing the next.
- Bump the version in **both** `pyproject.toml` and `faker_healthcare/__init__.py`
  (`__version__`) to the same value; keep the `Programming Language :: Python` classifiers in
  sync with the tested matrix.
- Run `python -m pytest`, `python -m build`, and `python -m twine check dist/*` locally first.
- Commit the version bump, then create and push the matching `vX.Y.Z` tag.
- After publishing, verify the new version on PyPI and smoke-test an install from a clean env.
- **After a repo or package rename, fix every metadata surface in the same change** —
  `pyproject.toml` `[project.urls]`, README badges and links, the GitHub About/description,
  and the docs. PyPI only refreshes project metadata when a release is published, so pair the
  URL fix with a patch release; otherwise the registry keeps serving the old, dead links.
