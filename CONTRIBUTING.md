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

The provider **derives** `diseases`, `icd10_codes`, `symptoms`, `generic_drugs`, and
`medical_specialties` from this dict. Never re-declare them as class attributes on a
locale provider; `tests/test_performance.py` asserts they stay derived properties, and
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

**A condition must exist in all six.** `tests/test_locales.py::TestLocaleParity`
enforces equal condition counts across locales and matches conditions by their
ICD-10 code, which is universal — the disease *name* is translated, the code is not.
An English-only addition will fail CI. If you cannot produce all six translations,
open an issue describing the addition rather than sending a partial catalogue.

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
  causes, `medications` must be treatments actually used for it (drugs, or
  interventions following the existing pattern such as `Surgery`, `IV Fluids`,
  `No Medications`), and `medical_specialty` must be the specialty that manages it.
  Two conditions may legitimately share an ICD-10 code (`Epilepsy` and
  `Seizure Disorder` → `G40.909`).
- **Generic names only.** Use real **INN generic** names, which WHO places in the
  public domain. Never put a brand or trademark name in `medications`.

### Brand drug names are fictitious — keep it that way

`brand_drug()` *generates* names from invented morphemes (`BRAND_PREFIXES`,
`BRAND_INFIXES`, `BRAND_SUFFIXES`, with `BRAND_FORBIDDEN_ENDINGS` rejecting anything
that would read like a generic; `zh_CN` has an equivalent Chinese-character path).

**Never add a real trademark anywhere** — not to `medications`, not to the morpheme
pools. This repository previously shipped real brand names and had to remove them;
the current generator and its tests are the fix. `tests/test_provider.py::TestBrandGenerator`
asserts the output pattern, that no famous real brand is ever produced, that no name
ends in a WHO INN class stem (`-mab`, `-pril`, `-statin`, …), and that 1000 draws
yield more than 300 distinct names. Do not weaken or delete those assertions; if a new
morpheme makes the suite fail, the morpheme is wrong, not the test. New morphemes must
also be checked for offensive or trademark-like substrings when concatenated with the
existing pools.

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
  test in `tests/test_locales.py` so it is exercised in all six locales, and a
  seeded-reproducibility assertion if it draws randomness.
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
