# Contributing

Thanks for helping improve `faker-healthcare-provider`. This library generates
**correlated** healthcare test data — a generated record's ICD-10 code, symptoms,
medications, and specialty all belong to the same condition — in six languages.
Most contributions are data contributions, so most of this guide is about how the
data has to look and what has to be proven before it lands.

> **MEDICAL DISCLAIMER — read before contributing data.** Everything in this
> repository is **synthetic test data for development and testing only**. It is not
> clinical guidance and must never be presented as usable for diagnosis, treatment,
> or any healthcare decision. Contributions are reviewed with that framing: the goal
> is records that *look* realistic to software under test, never a clinical resource.
> Never contribute real patient data, or anything derived from it, in any form.

This file is the human-facing summary of the repository's working rules. The full
rulebook, including the conventions that automated agents must follow, lives in
[AGENTS.md](AGENTS.md); when the two disagree, AGENTS.md wins and this file should be
corrected in the same PR.

## Supported versions

- **Python 3.10 – 3.14** (see the `Programming Language` classifiers in
  `pyproject.toml`; the `Tests` workflow runs the suite on every one of them).
  Code must stay valid on 3.10 — no syntax or stdlib API newer than that.
- **Faker >= 18.0.0** (`dependencies` in `pyproject.toml`). Stick to long-standing
  `BaseProvider` API (`self.random_element`, `self.generator.random`); do not rely on
  behaviour introduced in a newer Faker without raising the floor deliberately.

## Local setup

```bash
python3 -m venv .venv
.venv/bin/pip install -e ".[dev]"
```

Run the same four gates CI runs, from the repository root:

```bash
.venv/bin/python -m pytest
.venv/bin/python -m ruff check .
.venv/bin/python -m ruff format --check .
.venv/bin/python -m mypy --ignore-missing-imports --no-strict-optional .
```

Optionally install the hooks so the same checks run on commit — the pinned hook
versions are also executed by CI:

```bash
.venv/bin/pre-commit install
.venv/bin/pre-commit run --all-files
```

`python showcase.py` prints every public method with sample output; it is a quick way
to eyeball a change end to end.

Leave version bumps, tags, and releases to the maintainer — `pyproject.toml` and
`faker_healthcare/__init__.py` must always carry the same version, and the release
workflow checks the tag against it.

## The data shape

Every entry of every `DISEASE_CORRELATIONS` dict is a `DiseaseData`
(`faker_healthcare/types.py`):

```python
"Disease Name": {
    "icd10": "E11.9",                       # str, ICD-10 format: ^[A-Z]\d{2}(\.\d{1,3})?$
    "symptoms": ["...", "..."],             # non-empty list[str]
    "medications": ["...", "..."],          # non-empty list[str]
    "medical_specialty": "Endocrinology",   # str
},
```

All four keys are **required and non-empty** — `tests/test_correlations.py::TestDataIntegrity`
and `tests/test_locales.py::TestLocaleParity` fail otherwise.

The provider **derives** `diseases`, `icd10_codes`, `symptoms`, `generic_drugs`,
`interventions`, and `medical_specialties` from this dict. Never re-declare them as class
attributes on a locale provider — a locale declares only its static tuples, including
`non_drug_interventions`. `tests/test_performance.py` asserts they stay derived properties, and
that importing one locale does not drag another locale's modules into `sys.modules`
(hence the lazy import inside `_load_disease_correlations`).

## Six-locale parity

The catalogues live in:

| Locale | File |
| --- | --- |
| English (base) | `faker_healthcare/disease_correlations.py` |
| Portuguese (Brazil) | `faker_healthcare/pt_BR/disease_correlations.py` |
| Spanish | `faker_healthcare/es_ES/disease_correlations.py` |
| Chinese (Simplified) | `faker_healthcare/zh_CN/disease_correlations.py` |
| French | `faker_healthcare/fr_FR/disease_correlations.py` |
| German | `faker_healthcare/de_DE/disease_correlations.py` |

**A condition must exist in all six**, and parity means **content** parity, not equal
counts. Equal counts alone let real divergence through: zh_CN shipped for several
releases missing the `G40.909` condition the other five locales had and carrying an
`H25.9` condition none of them had, and every count matched.
`tests/test_locales.py::TestLocaleParity` therefore checks

- the **multiset of ICD-10 codes** per locale against the base (a multiset, because two
  conditions may legitimately share a code — `Epilepsy` and `Seizure Disorder`);
- per ICD-10 code, the **(symptom count, medication count) pairs** against the base, so a
  translation cannot quietly drop a symptom;
- the **cardinality of every shared constant tuple** (`HOSPITAL_DEPARTMENTS`,
  `BLOOD_TYPES`, `ALLERGIES`, `MEDICAL_PROCEDURES`, `VITAL_SIGNS`,
  `NON_DRUG_INTERVENTIONS`) across all six locales. `INSURANCE_PLANS` is the single
  deliberate exemption, because plan types are country-specific; a **new** constant has
  to be classified in `test_locales.py` or the suite fails;
- the **key set of every locale's `CLINICAL_LABELS`** against the base's, with no empty
  and no duplicated labels, and not simply copied from English. The numeric tables those
  labels name are the other deliberate exemption — they are locale-neutral by design (see
  *Measurements and lab values* below), and a test fails if a locale duplicates them;
- the **key set of every locale's `MEDICATION_NAMES`** against the base's and against the
  dose ladders, with every value checked to be a medication that locale's catalogue
  actually prescribes;
- that `zh_CN` contains no Japanese kana (U+3040–U+30FF) — that is how a katakana drug
  name reached the Simplified Chinese catalogue;
- that every zh_CN medication and symptom is the **committed equivalent** of the English
  term in the same slot (see below).

**A localized drug name must name the same substance as the base entry.** This is the
defect the count-based checks above cannot see, and the worst one this data can carry: a
real drug, plausible for the condition, wrong, in one locale only. zh_CN shipped `地西泮`
(diazepam) where the base says Disulfiram, `可乐定` (clonidine) where it says Clonazepam,
`铝碳酸镁` (hydrotalcite) where it says Sucralfate, and `布林佐胺` (brinzolamide) where it
says Brimonidine — with every count matching, because a substitution and an index shift
both preserve counts.

So the correspondence is pinned in `tests/zh_cn_equivalents.py`: the exact Chinese string
for every English medication and symptom. `TestZhTranslationEquivalence` walks the two
catalogues together — by ICD-10 code, then by position within it — and fails, naming the
slot, on any disagreement. Two consequences for a contributor:

- **changing or adding a zh_CN medication or symptom means editing that table in the same
  commit**, which is the point: the change becomes deliberate and reviewable instead of a
  string edit nobody can check;
- **one Chinese name may not stand for two substances.** `可乐定` was serving as both
  Clonidine and Clonazepam, and that ambiguity is exactly what let the wrong one ship.

The other five locales have no such table yet; adding one is a genuinely valuable
contribution, but it has to be the *record of a term-by-term review*, not a transcription
of what the catalogue currently says.

An English-only addition, or one with four symptoms in one locale and five in another,
will fail CI. If you cannot produce all six translations, open an issue describing the
addition rather than sending a partial catalogue.

Follow the translation conventions already in the data:

- `pt_BR`, `es_ES`: medication names localized (`Amoxicillin` → `Amoxicilina`).
- `de_DE`: medication names germanized (`Doxycycline` → `Doxycyclin`); use the German
  clinical term where it differs (bacterial cellulitis is `Phlegmone`, not `Cellulite`).
- `fr_FR`: medications are deliberately kept **in English**; only disease names,
  symptoms, and the specialty are translated.
- `zh_CN`: names, symptoms, medications, and specialties are all Simplified Chinese.
- `medical_specialty` strings: reuse the exact spelling already used in that locale
  instead of inventing a new one.

Append new conditions at the end of each file (order is not significant) and update
the "N diseases" count in each module docstring.

## Data rules

- **Additive by default.** Do not remove or rename an existing condition unless it is
  a verified duplicate, typo, or invalid entry — say which in the PR description.
- **Verify medical facts; do not invent them.** Condition names, ICD-10 codes, and
  medications must be checked against reputable sources (WHO ICD-10 / ICD-10-CM
  references, CDC, FDA, or the relevant specialty guideline) and the sources named in
  the PR. A drug or code newer than you expect may well be real — confirm it, don't
  assume it is fake.
- **Correlation is the product.** `symptoms` must be symptoms that condition actually
  causes, `medications` must be treatments actually used for it, and
  `medical_specialty` must be the specialty that manages it. Two conditions may
  legitimately share an ICD-10 code (`Epilepsy` and `Seizure Disorder` → `G40.909`).
- **Every symptom is a self-contained clinical term.** Never split one sentence across
  slots. Stress incontinence once read `["Urine Leakage with Coughing", "Sneezing",
  "Exercise", "Lifting", "Laughing"]`, so `symptom()` could return "Laughing" as a
  clinical symptom and the fragments leaked into the global symptom pool. Read each slot
  on its own; if it does not stand up alone, rewrite it.
- **Medications name substances, not drug classes.** `["Risperidone", "Aripiprazole",
  "SSRIs", "Stimulants", "Anticonvulsants"]` is three substances plus two categories used
  as filler. Name the substances, or make the list shorter. (Older entries still carry
  some class names; fix them when you touch that condition, and do not add new ones.)
- **Generic names only, matching the locale.** Never put a brand or trademark name in
  `medications`. Prefer the **INN**, which WHO places in the public domain, **except
  where a locale has a different adopted name in clinical use** — then use the locale's
  adopted name. That is why the English catalogue says `Albuterol` (INN salbutamol) and
  `Acetaminophen` (INN paracetamol) while `es_ES` says `Salbutamol` and `de_DE` says
  `Paracetamol`. Do not "correct" a locale's adopted name to the INN.
- **Non-drug treatments must be declared.** A procedure, device, diet, or
  `No Medications` is legitimate inside a condition's `medications`, but it must also
  appear in that locale's `NON_DRUG_INTERVENTIONS` tuple, at the same index as its
  counterpart in the other locales. That tuple is what keeps `generic_drug()` a pool of
  actual drugs; `intervention()` returns the rest. A declared intervention that no
  condition prescribes fails `tests/test_locales.py`.
- **`disease=` accessors raise on an unknown disease.** `icd10_code`, `symptom`,
  `medication`, `disease_symptoms`, `medications`, `patient_scenario`, `blood_pressure`,
  `vital_sign_measurement`, `vital_sign_measurements`, `lab_result`, `lab_panel`,
  `medication_order`, `medication_orders`, `assessment_score`, `patient` and
  `patient_record` all raise `ValueError`, as do `lab_result(analyte=...)`,
  `vital_sign_measurement(name=...)` and `assessment_score(instrument=...)` for an unknown
  ID. Never make one fall back to a random draw: the caller asked about one condition and
  would silently receive another's data.

### Measurements and lab values

`vital_sign()` returns the *name* of a vital sign. The measurement API returns numbers:
`blood_pressure()`, `vital_sign_measurement()`, `vital_sign_measurements()`,
`body_measurements()`, `alcohol_units_per_week()`, `alcohol_intake_category()`,
`lab_result()` and `lab_panel()`.

**The numbers are locale-neutral and live in exactly one place.** Units, reference
intervals, bounds and the condition correlations are in
`faker_healthcare/clinical_values.py`, keyed by stable IDs (`heart_rate`, `hba1c`); each
locale's `clinical_labels.py` translates the **words only** — analyte and vital-sign
names, the low/normal/high flags, the alcohol categories. Do not copy a reference range
into a locale package. Six copies of one number are six chances to disagree about a value
that cannot legitimately differ, and the first correction leaves five of them stale.
`tests/test_locales.py::TestClinicalLabelParity` enforces it from both ends: every locale
must define every label key, the base key set must equal the union of the numeric tables,
and no locale may ship its own `clinical_values.py` or redeclare `vital_definitions` /
`lab_definitions`.

Units are **SI** (mmol/L, µmol/L, g/L, IFCC mmol/mol for HbA1c), with the conversions to
US conventional units in the module docstring. Do not mix systems.

The correlations (`CONDITION_LAB_EFFECTS`, `CONDITION_VITAL_EFFECTS`) are keyed by
**ICD-10 code**, because the code is the one field identical in all six locales — that is
what makes one table correlate in French and Chinese. To add one:

- the code must already be in the catalogue (a test iterates every key and checks);
- the association must be **textbook and unambiguous for the unqualified condition**, the
  same bar as a condition's symptoms. Not "can occur in severe cases", not "in the
  subgroup that also has X". An empty entry is better than a wrong one: a condition with
  no entry produces in-range values, an honest "nothing specific here";
- name your source in the PR, as for any other medical fact;
- the direction must be reachable — nothing can push oxygen saturation above 100%, and
  `measurement_band()` raises rather than returning an in-range value flagged abnormal.

Generated numbers must agree with each other, and the tests assert it over thousands of
seeded draws rather than a few samples: `systolic > diastolic` by a plausible pulse
pressure (they are one measurement, not two draws), `flag` matches the value against the
reference interval printed beside it, `bmi` is computed from the height and weight
returned with it. The API models **direction, not severity** — a diabetic HbA1c is high,
but nothing here knows how well controlled that diabetes is — and `body_measurements()`
covers adults only, refusing a paediatric age rather than extrapolating an adult curve.

### Medication orders, assessments and patients

The records half — `medication_order()`, `medication_orders()`, `assessment_score()`,
`nhs_number()`, `patient()`, `patient_record()` — is split exactly the same way. The
numbers live once, in `faker_healthcare/prescribing.py` (dose ladders, routes,
frequencies, order statuses), `faker_healthcare/assessments.py` (instrument ranges and
severity bands) and `faker_healthcare/clinical_values.py` (`DEMOGRAPHIC_CONSTRAINTS`).
The words live in the six `clinical_labels.py` files.

- **A dose ladder belongs to a substance, and so do its route and its frequencies.**
  Insulin is subcutaneous whatever it is prescribed for; methotrexate is weekly. Drawing
  the three independently produced "Insulin 500 mg orally four times daily", which is why
  they are one table entry. Doses are the strengths actually dispensed, not a range to
  draw a random integer from — 637 mg of metformin is not a thing.
- **Never invent a dose.** A substance with no ladder returns `None` for dose, unit, route
  and frequency, and that is the correct answer for a drug *class* ("Antibiotics") and for
  cytotoxic chemotherapy, whose real doses are body-surface-area based. Adding a ladder
  means an adult dose you can source (the BNF or the manufacturer's SmPC, named in the PR)
  **and** the substance's name in all six `MEDICATION_NAMES` maps, in the same PR.
- **A `MEDICATION_NAMES` value must be a string that locale's catalogue really contains**,
  not merely a good translation — otherwise the lookup silently never matches and the drug
  quietly loses its dose. A test checks every entry against the catalogue. Where a
  catalogue spells one drug two ways, map the correct spelling and leave the other
  occurrence undosed rather than adding a wrong name.
- **Demographic constraints are locale-neutral and keyed by ICD-10 code.** "Female" is a
  fact about preeclampsia, not a word about it. Constrain only what is unambiguous, and
  when you decide *not* to constrain something that looks constrained, write down why:
  breast cancer is not female-only, and congenital heart disease and cystic fibrosis are
  no longer paediatric conditions.
- **`patient_record()` is adults only**, for the same reason `body_measurements()` is: the
  reference intervals, dose ladders and anthropometry here are adult data. It refuses a
  paediatric-only condition instead of ageing the patient up. `patient()` will happily
  generate a two-year-old with bronchiolitis, because it returns no measurements.

### Assessment instruments: ship the score, never the questions

**Do not add an instrument's item text to this repository.** Not the items, not the
questions, not the response options, not the answer wording, not the scoring instructions
— not in `assessments.py`, not in a locale package, not in a docstring, a test fixture, an
example or the README.

Most of these instruments are under **active copyright**; several are licensed
commercially, and their translations are separately licensed works. Putting the items in
an MIT-licensed package would redistribute someone else's literary property under a licence
its owner never granted, in six languages, to everyone who installs it. A **score** is not
that: "PHQ-9 = 14" is a number about a fictional patient, and it is exactly what a medical
record or a de-identification test rig actually holds — which is why the score is the half
worth shipping.

So a generated assessment carries four things: the instrument's name, the score, the
maximum, and the severity band. `tests/test_records.py::TestAssessmentBoundary` asserts
that, and a pull request that adds item content will be closed rather than revised.

Two more rules in the same area:

- **Six instruments** — PHQ-9, GAD-7, MMSE, MADRS, AUDIT-C, CAGE. A seventh is a maintainer
  decision before it is a table entry.
- **Classify with ICD-10 only.** No other diagnostic manual is referenced anywhere in this
  package, in data, API names, comments or docs, and none should be added.

### Generated identifiers default to the reserved test range

`nhs_number()` returns a number from the **999 range NHS England reserves for testing** and
never issues to a patient. That is the default on purpose: a checksum-valid identifier is,
by construction, one that could belong to a real person, and a synthetic record carrying
one can be matched against or mistaken for a real record.
`nhs_number(official_test_range=False)` exists for testing something that rejects the
reserved prefix, and is opt-in.

If you add another issued identifier, follow the same shape: default to whatever range the
issuing authority reserves, make the unreserved mode an explicit argument, implement the
check digit from the published specification and **cite it** in the module docstring, and
test it against published examples the code was not written around (plus a single-digit
change that must stop validating). If the authority publishes no reserved range, say so in
the docstring and the PR rather than quietly generating live-space identifiers.

### Brand drug names come from a screened list

`brand_drug()` returns `random_element(BRAND_DRUG_NAMES)` — 245 invented names in the
generated `faker_healthcare/brand_names.py`. `zh_CN` pairs one of them with a Chinese
name from the generated `ZH_BRAND_NAMES`. **Never add a real trademark anywhere**, not
to `medications` and not to the morpheme pools.

Both generated modules are written by `scripts/generate_brand_names.py`:

```bash
python scripts/generate_brand_names.py            # rewrite the generated modules
python scripts/generate_brand_names.py --check    # fail if they are out of date
python scripts/generate_brand_names.py --propose 20   # candidates to review
```

Edit the script, never the generated modules — `tests/test_provider.py` re-runs it in
`--check` mode and fails if a committed file differs by a byte. The morpheme tuples
(`BRAND_PREFIXES`, `BRAND_INFIXES`, `BRAND_SUFFIXES`) and `ZH_BRAND_CHARS` are the
script's **input**, so changing one has no effect until you re-run it.

Every candidate is screened four ways: it must not end in a `BRAND_FORBIDDEN_ENDINGS`
WHO INN class stem, must not be in `REAL_PRODUCT_DENYLIST`, must contain no term from
`OFFENSIVE_SUBSTRINGS`, and must not collide with a drug in any locale's catalogue.
`tests/test_provider.py::TestBrandCatalogue` re-runs those screens over **every** shipped
name, one by one, and `TestZhBrandCatalogue` does the same for the Chinese list. Do not
weaken those assertions or switch them to sampling: sampling the generator says nothing
about the entry it did not draw.

**Why a list instead of a generator.** `brand_drug()` used to concatenate morphemes on
every call — 31,500 possible names, 30,752 more for the Chinese path — retry 12 times if
the result ended in an INN stem, and then *return the last attempt anyway* if all 12
failed. Nothing in it screened for real product names. When the same morphemes were
ported to faker-js, a human screen of a ~250-name sample found five that shadow real
products (two of them FDA veterinary drugs), and all five were reachable here too. You
cannot screen 31,500 names; you can screen 250. That is the whole trade.

**Adding names.** Run `--propose N`, **read** the candidates, and append the ones that
survive to `REVIEWED_LATIN_NAMES`. Never append a name nobody has read. The three screen
lists — `REAL_PRODUCT_DENYLIST`, `ZH_REAL_PRODUCT_DENYLIST`, `OFFENSIVE_SUBSTRINGS` — are
**append-only**: entries are never removed, whatever the reason they went in, because
removing one silently re-admits a name a reviewer already rejected.

**What the package claims**, in README.md and in the modules themselves: curated fictional
names, screened against a documented corpus on a stated date. Not "never a real trademark"
and not "any resemblance is coincidental" — those are unfalsifiable, this repository
shipped both, and five reachable names contradicted them. Keep the wording checkable.
Reports of a collision are welcome; they land in the denylist.

**The Chinese list is weaker and says so.** `ZH_BRAND_NAMES` passes the automated screens
but has not been reviewed by a fluent Chinese speaker, and `faker_healthcare/zh_CN/brand_names.py`
carries a `TODO(review)` to that effect. If you read Chinese, a review pass is a genuinely
useful contribution: additions go to `ZH_REAL_PRODUCT_DENYLIST` with the reason, then
re-run the script.

### Any other generated identifier follows the same rule

If you add a method that invents a **user-visible name** — a product, a facility, a plan —
it must draw from a screened, enumerable, committed set, produced by a deterministic
committed script, with a test that iterates the whole set and asserts the safety property
on every entry. Do not assemble one at runtime from a space too large to screen, and do not
claim more than the screen supports. If a set cannot be responsibly screened (say, it needs
a language you do not read), ship it as a static list anyway, mark it unscreened in the
module and in the PR, and leave the TODO: a short unreviewed list can be audited and fixed,
a runtime generator cannot.

### Diagnostic codes, provenance, and licensing

Codes are **reference data**, reproduced verbatim:

- Granular codes are **ICD-10-CM** (CDC/NCHS, distributed free by the U.S. government).
- Base codes are **WHO ICD-10**, © World Health Organization, used under
  [CC BY-ND 3.0 IGO](https://creativecommons.org/licenses/by-nd/3.0/igo/) — reproduced
  **verbatim**, with the WHO attribution kept in the module docstrings and README.
  *ND means no derivatives*: never edit, "clean up", or paraphrase a code or an
  official code title.

If you want to import an **external catalogue** (a terminology, a code set, a drug
list, a translated corpus), open an issue first and include:

1. the exact source, edition/version, and a link;
2. its licence, and whether that licence permits redistribution inside an
   MIT-licensed package — attribution-only licences generally can be accommodated,
   licences requiring an affiliate agreement or restricting redistribution (for
   example SNOMED CT) cannot;
3. what attribution text the licence requires, and where it will live (module
   docstring plus README, matching the existing WHO attribution);
4. how the data was extracted, so the provenance can be re-checked later.

Bulk imports are reviewed for licence and provenance **before** any translation work
starts — please don't spend six locales' worth of effort on a catalogue that cannot be
accepted. Data whose licence or origin cannot be established will be declined, however
useful it looks.

## Seeded determinism

The same seed must produce the same sequence, forever, for a given version:

```python
fake = Faker()
fake.add_provider(HealthcareProvider)
fake.seed_instance(4242)
```

(`tests/test_provider.py::TestBrandGenerator::test_reproducible_under_seed` pins this.)

Rules for any code that generates a value:

- Draw randomness **only** from Faker's generator — `self.random_element(...)`,
  `self.random_int(...)`, `self.generator.random`. Never the global `random` module,
  `secrets`, `uuid4`, the clock, or the environment.
- Element pools must have a **stable, hash-independent order**. Anything derived from a
  `set` is sorted before it becomes a pool (see the `icd10_codes`, `symptoms`,
  `generic_drugs`, `medical_specialties` properties) — keep that `sorted()` in place;
  without it, seeded output would vary with `PYTHONHASHSEED` between runs.
- Adding a condition legitimately changes which value a given seed produces — that is
  expected, and is why data lands in additive, appended form rather than by reordering
  or rewriting existing entries.

## Tests to add with your change

- **New condition:** it is covered automatically by the parity and integrity tests, but
  add a correlation assertion in `tests/test_correlations.py::TestNewConditions` — the
  parametrized `patient_scenario()` check that a scenario's symptoms/medications/code
  really come from that condition's entry — and add its ICD-10 code to the shared code
  set in `tests/test_locales.py` when the condition should be pinned across locales.
- **New provider method:** a type/non-emptiness test in `tests/test_provider.py`, a
  test in `tests/test_locales.py` so it is exercised in all six locales, a
  seeded-reproducibility assertion if it draws randomness, and a row in the README's
  "Available Methods" table — `tests/test_readme.py` calls every method that table lists
  and requires a real return value (`None` or an empty container fails; `0` is fine, and
  is a correct answer from `alcohol_units_per_week()`).
- **New analyte, vital sign, or correlation:** an entry in
  `faker_healthcare/clinical_values.py`, a label in **all six** `clinical_labels.py`
  files, and an assertion in `tests/test_clinical_values.py`. The parametrized suites
  there already cover every table entry — each correlation is checked to actually bite,
  and each flag to agree with its value — so a well-formed addition is mostly covered by
  tests that already exist.
- **New dose ladder, route, frequency, severity band, demographic constraint or
  identifier:** the locale-neutral entry (`prescribing.py`, `assessments.py`,
  `clinical_values.py` or `identifiers.py`), its words in **all six** `clinical_labels.py`
  files — plus the six `MEDICATION_NAMES` entries for a new ladder — and an assertion in
  `tests/test_records.py`. Its parametrized suites already iterate every ladder, every
  instrument and every constraint, so a well-formed addition is largely covered; what is
  not covered automatically is the *source* for the dose, which belongs in the PR
  description.
- **README examples are executable.** `tests/test_readme.py` runs every fenced `python`
  block in `README.md` and asserts that a non-English example loads that locale's own
  catalogue. Both defects it now prevents shipped for months: the README documented a
  `medical_specialty()` method that does not exist (it is `disease_medical_specialty()`),
  and its entire multi-locale path used `Faker('es_ES')` with the base
  `HealthcareProvider`, which loads the **English** data. Use
  `from faker_healthcare.es_ES import Provider` in any locale example you write.
- **New condition, or a corrected zh_CN medication or symptom:** add or update its entry
  in `tests/zh_cn_equivalents.py` in the same commit — the table is keyed by the English
  term and holds the exact Chinese string, and `TestZhTranslationEquivalence` fails on a
  base term with no entry, on a stale entry the catalogue no longer uses, and on a slot
  whose Chinese string is not the one recorded. Say in the PR what the Chinese name is,
  the same way you would source any other medical fact.
- **New locale data file or provider:** keep the lazy `_load_disease_correlations`
  pattern and check that `tests/test_performance.py` still passes — it runs the memory
  isolation checks in subprocesses.

Run the full suite (including the performance tests) before opening a PR.

## Pull requests

- Keep PRs focused: one condition set, one feature, or one fix.
- Say where the medical facts came from. "Verified against the ICD-10-CM index" with a
  link beats "looks right".
- All four gates must be green; CI runs them on Python 3.10–3.14.
- Keep mechanical reformatting in its own commit, separate from substantive edits.

If you are unsure whether something fits — especially a large data import — open an
issue before writing code. Discussion is cheaper than six translations.
