# faker-healthcare-provider

Generate realistic, **medically accurate, and correlated** healthcare/medical test data in **6 languages**: English, Spanish, Portuguese, Chinese, French, and German.

This provider generates **correlated clinical data** based on the **World Health Organization (WHO) ICD-10 classification**, ensuring that symptoms, medications, specialties, and diagnostic codes match the generated disease.

## Installation

```bash
pip install faker-healthcare-provider
```

## Supported Languages

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

fake.diagnosis()          # 'Type 2 Diabetes (E11.9)'
fake.disease()            # 'Essential Hypertension'
fake.icd10_code()         # 'I10'
fake.generic_drug()       # 'Metformin'
fake.medical_specialty()  # 'Cardiology'
fake.blood_type()         # 'O+'
```

### Multi-Language Support

```python
from faker import Faker
from faker_healthcare import HealthcareProvider

# Spanish
fake_es = Faker('es_ES')
fake_es.add_provider(HealthcareProvider)
fake_es.disease()  # 'Diabetes Tipo 2'

# Portuguese (Brazil)
fake_pt = Faker('pt_BR')
fake_pt.add_provider(HealthcareProvider)
fake_pt.disease()  # 'Diabetes Tipo 2'

# Chinese (Simplified)
fake_zh = Faker('zh_CN')
fake_zh.add_provider(HealthcareProvider)
fake_zh.disease()  # '2型糖尿病'

# French
fake_fr = Faker('fr_FR')
fake_fr.add_provider(HealthcareProvider)
fake_fr.disease()  # 'Diabète de Type 2'

# German
fake_de = Faker('de_DE')
fake_de.add_provider(HealthcareProvider)
fake_de.disease()  # 'Typ-2-Diabetes'
```

## Available Methods

| Method | Example |
|--------|---------|
| `diagnosis()` | Type 2 Diabetes (E11.9) |
| `disease()` | Essential Hypertension, Asthma |
| `icd10_code()` | E11.9, I10, J45.909 |
| `medical_specialty()` | Cardiology, Neurology |
| `hospital_department()` | Emergency, ICU, Radiology |
| `generic_drug()` | Metformin, Lisinopril |
| `brand_drug()` | Lipitor, Prozac, Ozempic |
| `symptom()` | Fever, Headache, Fatigue |
| `blood_type()` | A+, O-, AB+ |
| `allergy()` | Penicillin, Peanuts |
| `medical_procedure()` | MRI Scan, Blood Test |
| `insurance_plan()` | PPO, HMO, Medicare |
| `vital_sign()` | Blood Pressure, Heart Rate |

## Locale-Specific Features

Each locale includes:
- **Translated medical terminology** (diseases, symptoms, procedures)
- **Locale-specific insurance systems**:
  - 🇺🇸 US: Medicare, PPO, HMO
  - 🇪🇸 Spain: Sistema Nacional de Salud, Sanitas, Adeslas
  - 🇧🇷 Brazil: SUS, Unimed, Amil
  - 🇨🇳 China: 城镇职工基本医疗保险, 商业医疗保险
  - 🇫🇷 France: Sécurité Sociale, Mutuelle
  - 🇩🇪 Germany: GKV, PKV

**Universal data** (same across all languages):
- ICD-10 codes (international standard)
- Blood types (universal notation)

## License

MIT
