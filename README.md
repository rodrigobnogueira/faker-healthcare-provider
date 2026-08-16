# faker-healthcare-provider

Generate realistic, **medically accurate, and correlated** healthcare/medical test data in **6 languages**: English, Spanish, Portuguese, Chinese, French, and German.

This provider generates **correlated clinical data** based on the **WHO ICD-10 and ICD-10-CM (CDC/NCHS) classifications**, ensuring that symptoms, medications, specialties, and diagnostic codes match the generated disease.

## Installation

```bash
pip install faker-healthcare-provider
```

## Quick Start

```python
from faker import Faker
from faker_healthcare import HealthcareProvider
from faker_healthcare.es_ES import Provider as SpanishProvider

# English (default)
fake = Faker()
fake.add_provider(HealthcareProvider)

# Generate a complete patient scenario
scenario = fake.patient_scenario()
print(scenario)
# {
#   'disease': 'Type 2 Diabetes',
#   'icd10': 'E11.9',
#   'symptoms': ['Fatigue', 'Blurred Vision', 'Frequent Urination'],
#   'medications': ['Metformin', 'Insulin Glargine'],
#   'medical_specialty': 'Endocrinology'
# }

# Or generate individual data
fake.disease()                    # 'Essential Hypertension'
fake.diagnosis()                  # 'Type 2 Diabetes (E11.9)'
fake.disease_medical_specialty()  # 'Cardiology'

# Use a different language: add that locale's Provider, not the base one
fake_es = Faker('es_ES')
fake_es.add_provider(SpanishProvider)
fake_es.disease()                 # 'Diabetes mellitus tipo 2'
fake_es.diagnosis()               # 'Diabetes mellitus tipo 2 (E11.9)'
```

> **The locale `Provider` is what loads the translated catalogue.** Adding the base
> `HealthcareProvider` to a `Faker('es_ES')` gives you Spanish names and addresses from
> Faker itself, but **English** clinical data from this package. Import
> `faker_healthcare.<locale>` and add its `Provider` instead. Every example below does.

💡 **Tip**: Run `python showcase.py` to see all available features and examples!

## Supported Locales

- 🇺🇸 **English** (`en_US`) - Default
- 🇪🇸 **Spanish** (`es_ES`)
- 🇧🇷 **Portuguese** (`pt_BR` - Brazil)
- 🇨🇳 **Chinese** (`zh_CN` - Simplified)
- 🇫🇷 **French** (`fr_FR`)
- 🇩🇪 **German** (`de_DE`)

## Usage

### Basic Usage (English)

```python
from faker import Faker
from faker_healthcare import HealthcareProvider

fake = Faker()
fake.add_provider(HealthcareProvider)

fake.diagnosis()                  # 'Type 2 Diabetes (E11.9)'
fake.disease()                    # 'Essential Hypertension'
fake.icd10_code()                 # 'I10'
fake.generic_drug()               # 'Metformin'
fake.intervention()               # 'Pelvic Floor Exercises'
fake.disease_medical_specialty()  # 'Cardiology'
fake.blood_type()                 # 'O+'
```

### Multi-Language Support

Each locale ships its own `Provider`. Import it from `faker_healthcare.<locale>` and add
**that** provider — the base `HealthcareProvider` always carries the English catalogue.

```python
from faker import Faker
from faker_healthcare.de_DE import Provider as GermanProvider
from faker_healthcare.es_ES import Provider as SpanishProvider
from faker_healthcare.fr_FR import Provider as FrenchProvider
from faker_healthcare.pt_BR import Provider as PortugueseProvider
from faker_healthcare.zh_CN import Provider as ChineseProvider

# Spanish
fake_es = Faker('es_ES')
fake_es.add_provider(SpanishProvider)
fake_es.disease()  # 'Diabetes mellitus tipo 2'

# Portuguese (Brazil)
fake_pt = Faker('pt_BR')
fake_pt.add_provider(PortugueseProvider)
fake_pt.disease()  # 'Diabetes mellitus tipo 2'

# Chinese (Simplified)
fake_zh = Faker('zh_CN')
fake_zh.add_provider(ChineseProvider)
fake_zh.disease()  # '非胰岛素依赖型糖尿病'

# French
fake_fr = Faker('fr_FR')
fake_fr.add_provider(FrenchProvider)
fake_fr.disease()  # 'Diabète sucré de type 2'

# German
fake_de = Faker('de_DE')
fake_de.add_provider(GermanProvider)
fake_de.disease()  # 'Diabetes mellitus Typ 2'
```

Every example in this README is executed by `tests/test_readme.py`, so a broken snippet
fails CI.

## Available Methods

| Method | Example |
|--------|---------|
| `diagnosis()` | Type 2 Diabetes (E11.9) |
| `disease()` | Essential Hypertension, Asthma |
| `icd10_code()` | E11.9, I10, J45.909 |
| `patient_scenario()` | A correlated disease / code / symptoms / medications record |
| `disease_medical_specialty()` | Cardiology, Neurology |
| `hospital_department()` | Emergency, ICU, Radiology |
| `generic_drug()` | Metformin, Lisinopril |
| `intervention()` | Surgery, Pelvic Floor Exercises, Hearing Aids |
| `brand_drug()` | Zolpraxen, Vyrativa, Trovadex *(fictitious, from a screened list)* |
| `symptom()` | Fever, Headache, Fatigue |
| `blood_type()` | A+, O-, AB+ |
| `allergy()` | Penicillin, Peanuts |
| `medical_procedure()` | MRI Scan, Blood Test |
| `insurance_plan()` | PPO, HMO, Medicare |
| `vital_sign()` | Blood Pressure, Heart Rate *(the name of a sign)* |
| `blood_pressure()` | {'systolic': 118, 'diastolic': 76, 'unit': 'mmHg'} |
| `vital_sign_measurement()` | {'name': 'Heart Rate', 'value': 72, 'unit': 'bpm'} |
| `vital_sign_measurements()` | All six vital signs at once, with a coherent blood pressure |
| `body_measurements()` | {'height_cm': 176.0, 'weight_kg': 84.2, 'bmi': 27.2} |
| `alcohol_units_per_week()` | 0, 6, 21 *(UK units; 0 is a common, valid answer)* |
| `alcohol_intake_category()` | Non-drinker, Low risk, Increasing risk, Higher risk |
| `lab_result()` | One flagged result with the reference interval beside it |
| `lab_panel()` | 4-8 distinct results, correlated when `disease=` is given |

`generic_drug()` draws only from drug substances. Treatments that are not drugs —
surgery, devices, diets, "No Medications" — come from `intervention()`. A condition's
own treatment list (`medication(disease=...)`, `medications(...)`, `patient_scenario()`)
still contains both, because that is what makes the record realistic.

Accessors that take a `disease=` argument (`icd10_code`, `symptom`, `medication`,
`disease_symptoms`, `medications`, `patient_scenario`, `blood_pressure`,
`vital_sign_measurement`, `vital_sign_measurements`, `lab_result`, `lab_panel`) raise
`ValueError` for a disease that is not in the catalogue; they never fall back to an
unrelated condition's data.

## Measurements and Lab Results

Numbers, not just the names of measurements — and correlated with the diagnosis the same
way symptoms and medications are.

```python
from faker import Faker
from faker_healthcare import HealthcareProvider

fake = Faker()
fake.add_provider(HealthcareProvider)

fake.blood_pressure()                         # {'systolic': 118, 'diastolic': 76, 'unit': 'mmHg'}
fake.body_measurements(sex='female', age=54)  # {'height_cm': 163.2, 'weight_kg': 71.4, 'bmi': 26.8}
fake.alcohol_units_per_week()                 # 6
fake.alcohol_intake_category(units=21)        # 'Increasing risk'

# A panel for a condition always carries the analytes that condition moves.
for result in fake.lab_panel(disease='Type 2 Diabetes'):
    print(result)
# {'analyte': 'Hemoglobin A1c (HbA1c)', 'value': 58, 'unit': 'mmol/mol',
#  'reference_low': 20, 'reference_high': 41, 'flag': 'High'}
# {'analyte': 'Fasting Glucose', 'value': 8.1, 'unit': 'mmol/L',
#  'reference_low': 3.9, 'reference_high': 5.5, 'flag': 'High'}
# {'analyte': 'Sodium', 'value': 139, 'unit': 'mmol/L',
#  'reference_low': 135, 'reference_high': 145, 'flag': 'Normal'}
```

What the correlation guarantees, for the 40-odd conditions that have an entry — type 2
diabetes, CKD, hypothyroidism, cirrhosis, iron-deficiency anaemia, sepsis and the rest:

- an analyte that condition moves lands **outside** the reference interval, on the side
  the condition pushes it, with a `flag` that agrees with the value;
- every other analyte lands **inside** it;
- a condition with no entry produces in-range values — an honest "nothing specific
  here" rather than an invented finding;
- `systolic` is always greater than `diastolic`, by a plausible pulse pressure;
- `bmi` is computed from the `height_cm` and `weight_kg` returned beside it, never drawn
  separately.

It models **direction, not severity**: a diabetic HbA1c is high, but nothing here knows
how well controlled that diabetes is. Two further simplifications are stated in
`clinical_values.py`: reference intervals are sex- and age-combined, and analytes are
correlated with the *diagnosis* rather than with each other — so the eGFR is not computed
from the creatinine printed beside it, and the lipids do not satisfy the Friedewald
relationship.

**Units are SI** (mmol/L, µmol/L, g/L, IFCC mmol/mol for HbA1c) — the units UK, Irish,
European, Australian and New Zealand laboratories report in. `clinical_values.py` lists
the conversions to US conventional units.

**Reference ranges, units and bounds are locale-neutral.** They live once in
`faker_healthcare/clinical_values.py`, keyed by stable IDs (`heart_rate`, `hba1c`) that
you pass to `vital_sign_measurement(name=...)` and `lab_result(analyte=...)`. Each locale
translates only the display labels, so `lab_panel(disease='Diabetes mellitus tipo 2')` on
the Spanish provider returns Spanish analyte names and flags with the same numbers.

## Locale-Specific Features

Each locale includes:
- **Translated medical terminology** (diseases, symptoms, procedures)
- **Locale-specific insurance systems**:
  - 🇺🇸 US: Medicare, Medicaid, PPO, HMO, TRICARE, ACA Marketplace
  - 🇪🇸 Spain: Seguridad Social, Seguro Privado (Cuadro Médico / Reembolso), Mutualidades (MUFACE/ISFAS/MUGEJU)
  - 🇧🇷 Brazil: Plano Individual, Familiar, Empresarial, com/sem Coparticipação
  - 🇨🇳 China: 商业保险, 雇主赞助保险, 牙科保险
  - 🇫🇷 France: Assurance Maladie, Mutuelle, Complémentaire santé
  - 🇩🇪 Germany: GKV (AOK, Barmer, TK, …), PKV, Zusatzversicherungen

**Universal data** (same across all languages):
- ICD-10 codes (international standard)
- Blood types (universal notation)

## Disclaimer

All data generated by this provider is **synthetic test data** for development and testing only, and **must not be used for medical diagnosis, treatment, or any clinical or healthcare decision**. The combinations produced are random.

- **Reference intervals are not a laboratory's reference intervals.** The ranges in `clinical_values.py` are round adult values from widely published references, chosen so generated records look plausible. Real intervals vary by assay, analyser, population, sex, age and pregnancy, and every real report carries its own. Never interpret a generated value against them.

- **Diagnoses & ICD-10 codes** are drawn from real classifications so records look realistic. Granular codes are **ICD-10-CM** (produced by CDC/NCHS and distributed free by the U.S. government); base codes are **WHO ICD-10**, © World Health Organization, used under [**CC BY-ND 3.0 IGO**](https://creativecommons.org/licenses/by-nd/3.0/igo/) — reproduced verbatim, with attribution.
- **Generic drug names** are real non-proprietary names: the WHO **International Nonproprietary Name (INN)**, which WHO formally places in the public domain, or the name adopted in that locale's clinical use where it differs (the English catalogue uses *Acetaminophen* and *Albuterol*, the US-adopted names for INN paracetamol and salbutamol).
- **Brand drug names are curated fictional names**, drawn from a fixed list of 245 (`BRAND_DRUG_NAMES`) rather than assembled at random. Each was built from invented morphemes and then screened, on **2026-08-16**, against: WHO INN class stems; an append-only denylist of real products (including two FDA veterinary products that an earlier, human-brands-only screen missed); a list of offensive substrings; and every drug name this package itself ships. The list was then read name by name — which is only possible because it is 245 names and not the 31,500 the morphemes can produce, and is why it is a list at all.

  That is a **documented screen at a point in time, not a guarantee of global trademark non-collision** — no automated screen can give you that, and none was attempted. Brand names exist in every jurisdiction, class, and language, and new ones are registered daily. If one of these names collides with a real product, please [open an issue](https://github.com/rodrigobnogueira/faker-healthcare-provider/issues): it will be added to the denylist, which is append-only, and the list regenerated.

  The zh_CN Chinese names (`ZH_BRAND_NAMES`) are screened the same way but have **not yet been reviewed by a fluent Chinese speaker**; the module says so, and review is welcome.

## Contributing

Bug reports, new conditions, and locale fixes are welcome. [CONTRIBUTING.md](CONTRIBUTING.md)
covers local setup, the six-locale parity rule, how medical facts and data licensing are
reviewed, and what tests a change needs.

## License

MIT
