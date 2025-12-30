"""
Performance tests to verify memory optimization and data loading behavior.

These tests verify:
1. Constants files don't trigger disease data loading
2. No redundant data is stored in locale provider classes
3. Properties are accessible from the base class

Note: Full locale-specific disease data isolation would require dynamic locale-based
DISEASE_CORRELATIONS loading, which is beyond the current refactoring scope.
"""

import importlib

from faker_healthcare import HealthcareProvider


class TestOptimization:
    """Test memory optimization and module loading behavior."""

    def test_no_redundant_data_in_locale_providers(self) -> None:
        """Verify that locale providers don't have redundant disease-derived data as class attributes."""
        from faker_healthcare.de_DE import Provider as DEProvider
        from faker_healthcare.es_ES import Provider as ESProvider
        from faker_healthcare.fr_FR import Provider as FRProvider
        from faker_healthcare.pt_BR import Provider as PTProvider
        from faker_healthcare.zh_CN import Provider as ZHProvider

        locale_providers = {
            "de_DE": DEProvider,
            "es_ES": ESProvider,
            "fr_FR": FRProvider,
            "pt_BR": PTProvider,
            "zh_CN": ZHProvider,
        }

        redundant_attrs = ["diseases", "icd10_codes", "symptoms", "generic_drugs", "medical_specialties"]

        for locale, provider_class in locale_providers.items():
            for attr in redundant_attrs:
                assert attr not in provider_class.__dict__, f"{locale} provider has redundant '{attr}' attribute"

        for attr in redundant_attrs:
            assert attr in HealthcareProvider.__dict__, f"Base provider missing '{attr}' property"
            assert isinstance(getattr(HealthcareProvider, attr), property), f"Base provider '{attr}' is not a property"

        expected_attrs = [
            "hospital_departments",
            "brand_drugs",
            "blood_types",
            "allergies",
            "medical_procedures",
            "insurance_plans",
            "vital_signs",
        ]

        all_providers = {**{"en (base)": HealthcareProvider}, **locale_providers}
        for locale, provider_class in all_providers.items():
            for attr in expected_attrs:
                assert attr in provider_class.__dict__, f"{locale} provider missing '{attr}' attribute"

    def test_locale_providers_inherit_from_base(self) -> None:
        """Verify that locale providers properly inherit from the base HealthcareProvider."""
        from faker_healthcare.de_DE import Provider as DEProvider
        from faker_healthcare.es_ES import Provider as ESProvider
        from faker_healthcare.fr_FR import Provider as FRProvider
        from faker_healthcare.pt_BR import Provider as PTProvider
        from faker_healthcare.zh_CN import Provider as ZHProvider

        all_providers = [HealthcareProvider, DEProvider, ESProvider, FRProvider, PTProvider, ZHProvider]

        for provider_class in all_providers:
            assert issubclass(provider_class, HealthcareProvider)

    def test_locale_constants_have_correct_types(self) -> None:
        """Verify that locale constants are tuples."""

        locales = ["en (base)", "de_DE", "es_ES", "fr_FR", "pt_BR", "zh_CN"]
        constant_names = [
            "HOSPITAL_DEPARTMENTS",
            "BRAND_DRUGS",
            "BLOOD_TYPES",
            "ALLERGIES",
            "MEDICAL_PROCEDURES",
            "INSURANCE_PLANS",
            "VITAL_SIGNS",
        ]

        for locale in locales:
            if locale == "en (base)":
                constants_module = importlib.import_module("faker_healthcare.constants")
            else:
                constants_module = importlib.import_module(f"faker_healthcare.{locale}.constants")
            for const_name in constant_names:
                const = getattr(constants_module, const_name)
                assert isinstance(const, tuple), f"{locale}.{const_name} is not a tuple"
                assert len(const) > 0, f"{locale}.{const_name} is empty"

    def test_locale_memory_isolation(self) -> None:
        """Verify that importing one locale doesn't load other locales' data into memory."""
        import subprocess
        import sys

        test_script = """
import sys
import importlib

target_locale = sys.argv[1]

if target_locale == "en":
    provider_module = importlib.import_module("faker_healthcare.provider")
else:
    provider_module = importlib.import_module(f"faker_healthcare.{target_locale}")

all_locales = ["en", "de_DE", "es_ES", "fr_FR", "pt_BR", "zh_CN"]
other_locales = [loc for loc in all_locales if loc != target_locale]

for other_locale in other_locales:
    if other_locale == "en":
        # Check if English disease_correlations was loaded when importing non-English locale
        if target_locale != "en" and "faker_healthcare.disease_correlations" in sys.modules:
            print(f"FAIL: English disease_correlations module loaded when importing {target_locale}")
            sys.exit(1)
        continue

    other_constants_module = f"faker_healthcare.{other_locale}.constants"
    other_disease_correlations_module = f"faker_healthcare.{other_locale}.disease_correlations"

    if other_constants_module in sys.modules:
        print(f"FAIL: {other_locale} constants module loaded when importing {target_locale}")
        sys.exit(1)

    if other_disease_correlations_module in sys.modules:
        print(f"FAIL: {other_locale} disease_correlations module loaded when importing {target_locale}")
        sys.exit(1)

print("OK")
"""

        all_locales = ["en", "de_DE", "es_ES", "fr_FR", "pt_BR", "zh_CN"]

        for target_locale in all_locales:
            result = subprocess.run(
                [sys.executable, "-c", test_script, target_locale],
                capture_output=True,
                text=True,
            )

            assert result.returncode == 0, f"Loading {target_locale} caused other locale data to load:\nstdout: {result.stdout}\nstderr: {result.stderr}"
            assert "OK" in result.stdout, f"Unexpected output for {target_locale}: {result.stdout}"
