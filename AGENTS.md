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
- `faker_healthcare/types.py` — `DiseaseData` / `PatientScenario` TypedDicts (the data shapes).
- `faker_healthcare/<locale>/` — one package per locale (`pt_BR`, `es_ES`, `zh_CN`, `fr_FR`,
  `de_DE`), each with its own `__init__.py` (a `Provider` subclass), `constants.py`, and
  `disease_correlations.py`.
- `tests/` — `test_provider.py`, `test_correlations.py`, `test_locales.py`,
  `test_performance.py`, `test_readme.py`, and `conftest.py` (which loads the generator
  script so the tests re-run its screens instead of restating them).
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
not know** — `icd10_code`, `symptom`, `medication`, `disease_symptoms`, `medications` and
`patient_scenario` all do. Never fall back to an uncorrelated random draw: the caller asked
about one condition and would silently receive another condition's data, which is precisely
the failure this library exists to prevent.

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
  - `zh_CN` contains no Japanese kana (U+3040–U+30FF) — that is how a katakana drug name
    (リオチロニン) reached the Simplified Chinese catalog.

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
  - `REAL_PRODUCT_DENYLIST`, `ZH_REAL_PRODUCT_DENYLIST` and `OFFENSIVE_SUBSTRINGS` are
    **append-only**. A name is never removed once added, whatever the reason it went in: removing
    one silently re-admits a name a reviewer already rejected. Discontinued products and marginal
    collisions stay.
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

## Generated Identifiers (the screened-set rule)

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
