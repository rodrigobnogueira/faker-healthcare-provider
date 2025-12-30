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
        import importlib

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
        """Verify that importing one locale doesn't load other locales into memory."""
        import sys

        locales_to_test = ["de_DE", "es_ES", "fr_FR", "pt_BR", "zh_CN"]

        for target_locale in locales_to_test:
            loaded_modules_before = set(sys.modules.keys())

            importlib.import_module(f"faker_healthcare.{target_locale}")

            loaded_modules_after = set(sys.modules.keys())
            newly_loaded = loaded_modules_after - loaded_modules_before

            other_locales = [loc for loc in locales_to_test if loc != target_locale]

            for other_locale in other_locales:
                other_locale_modules = [mod for mod in newly_loaded if f"faker_healthcare.{other_locale}" in mod]
                assert not other_locale_modules, f"Loading {target_locale} should not load {other_locale}, but found: {other_locale_modules}"
