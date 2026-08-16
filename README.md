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
| `vital_sign()` | Blood Pressure, Heart Rate |

`generic_drug()` draws only from drug substances. Treatments that are not drugs —
surgery, devices, diets, "No Medications" — come from `intervention()`. A condition's
own treatment list (`medication(disease=...)`, `medications(...)`, `patient_scenario()`)
still contains both, because that is what makes the record realistic.

Accessors that take a `disease=` argument (`icd10_code`, `symptom`, `medication`,
`disease_symptoms`, `medications`, `patient_scenario`) raise `ValueError` for a disease
that is not in the catalogue; they never fall back to an unrelated condition's data.

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
