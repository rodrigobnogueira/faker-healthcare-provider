# Agent Guidance

This repository contains a Faker provider for generating **correlated** healthcare/medical
test data in six languages (English, Spanish, Portuguese, Chinese, French, German). Keep
changes small, data-focused, and easy to verify.

> MEDICAL DISCLAIMER: All data here is for TESTING AND DEVELOPMENT ONLY. It must never be
> presented as usable for real diagnosis, treatment, or any clinical decision.

## Project Layout

- `faker_healthcare/provider.py` — the base `HealthcareProvider` and its public API.
- `faker_healthcare/disease_correlations.py` — the English `DISEASE_CORRELATIONS` catalog.
- `faker_healthcare/constants.py` — static English tuples (departments, brand drugs, etc.).
- `faker_healthcare/types.py` — `DiseaseData` / `PatientScenario` TypedDicts (the data shapes).
- `faker_healthcare/<locale>/` — one package per locale (`pt_BR`, `es_ES`, `zh_CN`, `fr_FR`,
  `de_DE`), each with its own `__init__.py` (a `Provider` subclass), `constants.py`, and
  `disease_correlations.py`.
- `tests/` — `test_provider.py`, `test_correlations.py`, `test_locales.py`, `test_performance.py`.

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
- The base provider **derives** `diseases`, `icd10_codes`, `symptoms`, `generic_drugs`, and
  `medical_specialties` from `DISEASE_CORRELATIONS`. Do not add these as redundant class
  attributes on locale providers — `test_performance.py` asserts they stay derived properties.
- `icd10` is universal (same code across all locales). Symptoms, medications, disease names,
  and specialties are translated per locale. Two distinct disease names may legitimately share
  one ICD-10 code (e.g. `Epilepsy` and `Seizure Disorder` → `G40.909`); the code is deduped
  via a set in `icd10_codes`.

## Correlation Consistency (the core invariant)

The whole point of the library is that generated clinical data is internally consistent.
When you add or edit a disease:

- The `icd10` must be the correct WHO ICD-10 code for that condition.
- `symptoms` must be symptoms that condition actually causes.
- `medications` must be treatments actually used for that condition (drugs or, following the
  existing pattern, interventions like `Surgery`, `IV Fluids`, `Wrist Splint`, `No Medications`).
  Use real **generic INN** names (public domain), **never brand/trademark names** — brand names are
  produced separately by `brand_drug()`.
- `medical_specialty` must be the specialty that manages the condition, and should reuse an
  existing specialty string already present in the catalog.

`patient_scenario()`, `icd10_code(disease=...)`, `symptom(disease=...)`, and
`medication(disease=...)` all read straight from this data, so any inconsistency becomes a
visible, wrong-looking record.

## Locale Mechanism

- Each locale package's `Provider` subclasses the base and overrides `_load_disease_correlations`
  to import that locale's `DISEASE_CORRELATIONS` lazily (import happens inside the method, not at
  module top level — this keeps per-locale data out of memory until used; `test_performance.py`
  `test_locale_memory_isolation` enforces it via subprocesses).
- Keep the catalogs at **parity**: every locale defines the same number of conditions, matched by
  their shared ICD-10 codes. `test_locales.py::TestLocaleParity` checks equal counts and that a
  new condition (identified by ICD-10) exists in all six locales. If you add a condition, add it
  to **all six** `disease_correlations.py` files (English base + five locales).
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
- **Brand names are fictitious and generated.** `brand_drug()` builds names from invented morphemes
  (`BRAND_PREFIXES` / `BRAND_INFIXES` / `BRAND_SUFFIXES`, refusing endings in `BRAND_FORBIDDEN_ENDINGS`
  so they can't look like a generic; zh_CN adds a Chinese-character path). **Never add a real trademark**
  anywhere — not to the morpheme pools, not to `medications`.
- **Diagnostic codes are kept as reference data.** ICD-10-CM codes come from CDC/NCHS (distributed free
  by the U.S. government); base WHO ICD-10 codes are used under **CC BY-ND 3.0 IGO** — reproduce codes
  verbatim, keep the WHO attribution in the module docstrings and README, and never modify a code.
- Add focused tests that extend the existing patterns (`TestNewConditions` in
  `test_correlations.py`, `TestLocaleParity` in `test_locales.py`).

## Performance Test Expectations

`test_performance.py` guards the memory design: locale providers must not carry derived data as
class attributes, must inherit from `HealthcareProvider`, locale constants must be non-empty
tuples, and importing one locale must not pull another locale's modules into `sys.modules`.
Keep the lazy `_load_disease_correlations` pattern intact.

## Running Tests

Create a venv and run the full suite (including the performance suite) before opening a PR:

```bash
python3 -m venv .venv
.venv/bin/pip install -e . pytest faker
.venv/bin/python -m pytest
```

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
