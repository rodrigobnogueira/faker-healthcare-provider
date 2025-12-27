# faker-healthcare

Faker provider for generating healthcare/medical fake data.

## Installation

```bash
pip install faker-healthcare-provider
```

## Usage

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

## License

MIT
