"""
Showcase for faker-healthcare-provider library.

This script demonstrates the capabilities of the Healthcare Provider
for generating realistic medical test data.
"""

from faker import Faker

from faker_healthcare import HealthcareProvider


fake = Faker()
fake.add_provider(HealthcareProvider)


def print_header(title: str) -> None:
    """Print a formatted section header."""
    print(f"\n{'=' * 70}")
    print(f"  {title}")
    print(f"{'=' * 70}")


def print_subheader(title: str) -> None:
    """Print a formatted subsection header."""
    print(f"\n{title}")
    print("-" * 70)


def showcase_basic_data() -> None:
    """Demonstrate basic medical data generation."""
    print_header("Basic Medical Data")

    print_subheader("Medical Specialties")
    for _ in range(3):
        print(f"  • {fake.medical_specialty()}")

    print_subheader("Hospital Departments")
    for _ in range(3):
        print(f"  • {fake.hospital_department()}")

    print_subheader("Blood Types")
    for _ in range(4):
        print(f"  • {fake.blood_type()}")

    print_subheader("Insurance Plans")
    for _ in range(3):
        print(f"  • {fake.insurance_plan()}")


def showcase_diseases_and_codes() -> None:
    """Demonstrate disease and ICD-10 code generation."""
    print_header("Diseases & ICD-10 Codes")

    print_subheader("Random Diseases with ICD-10 Codes")
    for _ in range(5):
        disease = fake.disease()
        icd10 = fake.icd10_code(disease=disease)
        print(f"  • {disease:<40} [{icd10}]")

    print_subheader("Formatted Diagnosis")
    for _ in range(3):
        print(f"  • {fake.diagnosis()}")


def showcase_medications() -> None:
    """Demonstrate medication generation."""
    print_header("Medications")

    print_subheader("Brand Name Drugs")
    for _ in range(5):
        print(f"  • {fake.brand_drug()}")

    print_subheader("Generic Drugs")
    for _ in range(5):
        print(f"  • {fake.generic_drug()}")


def showcase_symptoms_and_procedures() -> None:
    """Demonstrate symptoms and procedures."""
    print_header("Symptoms, Allergies & Procedures")

    print_subheader("Common Symptoms")
    for _ in range(5):
        print(f"  • {fake.symptom()}")

    print_subheader("Allergies")
    for _ in range(5):
        print(f"  • {fake.allergy()}")

    print_subheader("Medical Procedures")
    for _ in range(5):
        print(f"  • {fake.medical_procedure()}")

    print_subheader("Vital Signs")
    for _ in range(5):
        print(f"  • {fake.vital_sign()}")


def showcase_correlated_data() -> None:
    """Demonstrate correlated clinical data generation."""
    print_header("Correlated Clinical Data")

    print_subheader("Disease-Specific Symptoms")
    disease = "Type 2 Diabetes"
    print(f"\nDisease: {disease}")
    symptoms = fake.disease_symptoms(disease, count=4)
    print("Symptoms:")
    for symptom in symptoms:
        print(f"  • {symptom}")

    print_subheader("Disease-Specific Medications")
    medications = fake.medications(disease, count=3)
    print(f"\nDisease: {disease}")
    print("Medications:")
    for med in medications:
        print(f"  • {med}")


def showcase_patient_scenarios() -> None:
    """Demonstrate complete patient scenario generation."""
    print_header("Complete Patient Scenarios")

    for i in range(3):
        print_subheader(f"Patient #{i + 1}")
        scenario = fake.patient_scenario()

        print(f"\nDisease:      {scenario['disease']}")
        print(f"ICD-10 Code:  {scenario['icd10']}")
        print(f"Specialty:    {scenario['specialty']}")

        print("\nSymptoms:")
        for symptom in scenario["symptoms"]:
            print(f"  • {symptom}")

        print("\nMedications:")
        for med in scenario["medications"]:
            print(f"  • {med}")


def showcase_multi_language() -> None:
    """Demonstrate multi-language support."""
    print_header("Multi-Language Support")

    languages = [
        ("es_ES", "Spanish", "🇪🇸"),
        ("pt_BR", "Portuguese", "🇧🇷"),
        ("zh_CN", "Chinese", "🇨🇳"),
        ("fr_FR", "French", "🇫🇷"),
        ("de_DE", "German", "🇩🇪"),
    ]

    for locale, lang_name, flag in languages:
        print_subheader(f"{flag} {lang_name} ({locale})")
        fake_lang = Faker(locale)
        fake_lang.add_provider(HealthcareProvider)

        print(f"\nDisease:    {fake_lang.disease()}")
        print(f"Diagnosis:  {fake_lang.diagnosis()}")
        print(f"Specialty:  {fake_lang.medical_specialty()}")
        print(f"Insurance:  {fake_lang.insurance_plan()}")


def main() -> None:
    """Run all showcase demonstrations."""
    print("\n" + "=" * 70)
    print("  FAKER HEALTHCARE PROVIDER - CAPABILITIES SHOWCASE")
    print("=" * 70)
    print("\n⚕️  Generating realistic medical test data for development...")
    print("⚠️  DISCLAIMER: For testing purposes only - not for medical use!\n")

    showcase_basic_data()
    showcase_diseases_and_codes()
    showcase_medications()
    showcase_symptoms_and_procedures()
    showcase_correlated_data()
    showcase_patient_scenarios()
    showcase_multi_language()

    print("\n" + "=" * 70)
    print("  End of Showcase")
    print("=" * 70 + "\n")


if __name__ == "__main__":
    main()
