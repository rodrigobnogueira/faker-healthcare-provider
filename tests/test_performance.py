"""
Performance tests to verify memory optimization and data loading behavior.

These tests verify:
1. Constants files don't trigger disease data loading
2. No redundant data is stored in locale provider classes
3. Properties are accessible from the base class

Note: Full locale-specific disease data isolation would require dynamic locale-based
DISEASE_CORRELATIONS loading, which is beyond the current refactoring scope.
"""

import subprocess
import sys

from faker_healthcare import HealthcareProvider


class TestMemoryOptimization:
    """Test memory optimization and module loading behavior."""

    def test_locale_constants_isolated_from_disease_data(self) -> None:
        """Verify that importing locale constants doesn't load disease correlations."""
        script = """
import sys

# Import Spanish constants
from faker_healthcare.es_ES.constants import HOSPITAL_DEPARTMENTS, BRAND_DRUGS

# Check that Spanish disease correlations are NOT loaded yet
assert 'faker_healthcare.es_ES.disease_correlations' not in sys.modules, \
    "Spanish disease data was loaded when importing constants"

# Portuguese data should also not be loaded
assert 'faker_healthcare.pt_BR.disease_correlations' not in sys.modules, \
    "Portuguese disease data was loaded when importing constants"

# Importing Portuguese constants should also not load disease data
from faker_healthcare.pt_BR.constants import VITAL_SIGNS

assert 'faker_healthcare.pt_BR.disease_correlations' not in sys.modules, \
    "Portuguese disease data was loaded when importing constants"

print("SUCCESS")
"""
        result = subprocess.run(
            [sys.executable, "-c", script],
            capture_output=True,
            text=True,
            cwd=".",
        )
        assert result.returncode == 0, f"stdout: {result.stdout}, stderr: {result.stderr}"
        assert "SUCCESS" in result.stdout

    def test_no_redundant_data_in_locale_providers(self) -> None:
        """Verify that locale providers don't have redundant disease-derived data as class attributes."""
        from faker_healthcare.es_ES import Provider as ESProvider
        from faker_healthcare.pt_BR import Provider as PTProvider

        # These should NOT be class attributes (they're properties in base class)
        redundant_attrs = ["diseases", "icd10_codes", "symptoms", "generic_drugs", "medical_specialties"]

        for attr in redundant_attrs:
            # Check they're not directly defined in the locale class
            assert attr not in ESProvider.__dict__, f"Spanish provider has redundant '{attr}' attribute"
            assert attr not in PTProvider.__dict__, f"Portuguese provider has redundant '{attr}' attribute"

        # The locale classes should only have the 7 non-redundant constants
        expected_attrs = [
            "hospital_departments",
            "brand_drugs",
            "blood_types",
            "allergies",
            "medical_procedures",
            "insurance_plans",
            "vital_signs",
        ]

        for attr in expected_attrs:
            assert attr in ESProvider.__dict__, f"Spanish provider missing '{attr}' attribute"
            assert attr in PTProvider.__dict__, f"Portuguese provider missing '{attr}' attribute"

    def test_locale_providers_inherit_from_base(self) -> None:
        """Verify that locale providers properly inherit from the base HealthcareProvider."""
        from faker_healthcare.es_ES import Provider as ESProvider
        from faker_healthcare.pt_BR import Provider as PTProvider

        assert issubclass(ESProvider, HealthcareProvider)
        assert issubclass(PTProvider, HealthcareProvider)

    def test_locale_constants_have_correct_types(self) -> None:
        """Verify that locale constants are tuples."""
        from faker_healthcare.es_ES.constants import (
            ALLERGIES as ES_ALLERGIES,
        )
        from faker_healthcare.es_ES.constants import (
            BLOOD_TYPES as ES_BLOOD_TYPES,
        )
        from faker_healthcare.es_ES.constants import (
            BRAND_DRUGS as ES_BRAND_DRUGS,
        )
        from faker_healthcare.es_ES.constants import (
            HOSPITAL_DEPARTMENTS as ES_HOSPITAL_DEPARTMENTS,
        )
        from faker_healthcare.es_ES.constants import (
            INSURANCE_PLANS as ES_INSURANCE_PLANS,
        )
        from faker_healthcare.es_ES.constants import (
            MEDICAL_PROCEDURES as ES_MEDICAL_PROCEDURES,
        )
        from faker_healthcare.es_ES.constants import (
            VITAL_SIGNS as ES_VITAL_SIGNS,
        )
        from faker_healthcare.pt_BR.constants import (
            ALLERGIES as PT_ALLERGIES,
        )
        from faker_healthcare.pt_BR.constants import (
            BLOOD_TYPES as PT_BLOOD_TYPES,
        )
        from faker_healthcare.pt_BR.constants import (
            BRAND_DRUGS as PT_BRAND_DRUGS,
        )
        from faker_healthcare.pt_BR.constants import (
            HOSPITAL_DEPARTMENTS as PT_HOSPITAL_DEPARTMENTS,
        )
        from faker_healthcare.pt_BR.constants import (
            INSURANCE_PLANS as PT_INSURANCE_PLANS,
        )
        from faker_healthcare.pt_BR.constants import (
            MEDICAL_PROCEDURES as PT_MEDICAL_PROCEDURES,
        )
        from faker_healthcare.pt_BR.constants import (
            VITAL_SIGNS as PT_VITAL_SIGNS,
        )

        # All should be tuples
        for const in [
            ES_HOSPITAL_DEPARTMENTS,
            ES_BRAND_DRUGS,
            ES_BLOOD_TYPES,
            ES_ALLERGIES,
            ES_MEDICAL_PROCEDURES,
            ES_INSURANCE_PLANS,
            ES_VITAL_SIGNS,
            PT_HOSPITAL_DEPARTMENTS,
            PT_BRAND_DRUGS,
            PT_BLOOD_TYPES,
            PT_ALLERGIES,
            PT_MEDICAL_PROCEDURES,
            PT_INSURANCE_PLANS,
            PT_VITAL_SIGNS,
        ]:
            assert isinstance(const, tuple)
            assert len(const) > 0

    def test_memory_footprint_reduced(self) -> None:
        """Verify that locale files are now much smaller after refactoring."""
        import os

        es_init_path = "faker_healthcare/es_ES/__init__.py"
        pt_init_path = "faker_healthcare/pt_BR/__init__.py"

        # Get file sizes
        es_size = os.path.getsize(es_init_path)
        pt_size = os.path.getsize(pt_init_path)

        # After refactoring, these files should be small (< 1KB)
        # Before refactoring they were ~24KB and ~23KB respectively
        assert es_size < 1024, f"Spanish __init__.py too large: {es_size} bytes"
        assert pt_size < 1024, f"Portuguese __init__.py too large: {pt_size} bytes"

        print(f"Spanish __init__.py: {es_size} bytes")
        print(f"Portuguese __init__.py: {pt_size} bytes")
