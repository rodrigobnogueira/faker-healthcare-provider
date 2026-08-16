"""The README is executable documentation, and this test is what keeps it honest.

Two defects shipped in every release up to 2.3.2 because nothing ever ran the README:

1. Its whole multi-locale path taught `Faker('es_ES')` plus the **base**
   `HealthcareProvider`, which loads the ENGLISH catalogue — the working pattern
   (`from faker_healthcare.es_ES import Provider`) appeared nowhere in it.
2. It documented `medical_specialty()` twice; the real method is
   `disease_medical_specialty()`.

So: every ```python block in the README is executed, every Faker built by one of those
blocks must carry the catalogue for its own locale, and every method the README's table
documents must exist and be callable.
"""

import importlib
import re
from pathlib import Path
from typing import Any

import pytest
from faker import Faker

from faker_healthcare import HealthcareProvider


README_PATH = Path(__file__).resolve().parent.parent / "README.md"
README_TEXT = README_PATH.read_text(encoding="utf-8")

PYTHON_BLOCK_RE = re.compile(r"^```python\n(.*?)^```", re.MULTILINE | re.DOTALL)
METHOD_ROW_RE = re.compile(r"^\| `([a-z_0-9]+)\(\)` \|", re.MULTILINE)

PYTHON_BLOCKS = PYTHON_BLOCK_RE.findall(README_TEXT)
BLOCK_IDS = [f"block{index}" for index, _ in enumerate(PYTHON_BLOCKS, start=1)]

NON_ENGLISH_LOCALES = ["pt_BR", "es_ES", "zh_CN", "fr_FR", "de_DE"]

# Present in the English catalogue only; if a locale provider exposes it, the base
# (English) provider was loaded instead of the locale's own.
ENGLISH_ONLY_DISEASE = "Type 2 Diabetes"


def _run_block(source: str) -> dict[str, Any]:
    namespace: dict[str, Any] = {}
    exec(compile(source, str(README_PATH), "exec"), namespace)  # noqa: S102 - the README is our own file
    return namespace


def _healthcare_provider(fake: Faker) -> HealthcareProvider | None:
    return next((p for p in fake.providers if isinstance(p, HealthcareProvider)), None)


def test_readme_has_python_examples() -> None:
    """Guard the regex itself: a README whose examples stopped matching proves nothing."""
    assert len(PYTHON_BLOCKS) >= 3, "no fenced python examples found in README.md"


@pytest.mark.parametrize("source", PYTHON_BLOCKS, ids=BLOCK_IDS)
def test_readme_example_runs(source: str) -> None:
    """Every documented snippet must run as written."""
    _run_block(source)


@pytest.mark.parametrize("source", PYTHON_BLOCKS, ids=BLOCK_IDS)
def test_readme_example_loads_the_right_catalog(source: str) -> None:
    """A non-English example must not end up generating English clinical data."""
    for name, value in _run_block(source).items():
        if not isinstance(value, Faker):
            continue
        provider = _healthcare_provider(value)
        if provider is None:
            continue
        locale = value.locales[0]
        if locale.startswith("en"):
            continue
        assert ENGLISH_ONLY_DISEASE not in provider.diseases, f"README example variable '{name}' uses locale {locale} but loaded the English catalog"


@pytest.mark.parametrize("locale", NON_ENGLISH_LOCALES)
def test_readme_documents_the_working_locale_import(locale: str) -> None:
    """The only pattern that loads a locale's catalogue is importing its Provider."""
    assert f"from faker_healthcare.{locale} import Provider" in README_TEXT, f"README never shows how to load the {locale} catalog"


@pytest.mark.parametrize("locale", NON_ENGLISH_LOCALES)
def test_documented_locale_pattern_returns_localized_data(locale: str) -> None:
    provider_class = importlib.import_module(f"faker_healthcare.{locale}").Provider
    fake = Faker(locale)
    fake.add_provider(provider_class)
    provider = _healthcare_provider(fake)
    assert provider is not None
    assert ENGLISH_ONLY_DISEASE not in provider.diseases
    assert isinstance(fake.disease(), str)


def test_readme_documents_only_real_methods() -> None:
    """Every method in the "Available Methods" table must exist and be callable."""
    documented = METHOD_ROW_RE.findall(README_TEXT)
    assert documented, "no method table rows found in README.md"

    fake = Faker()
    fake.add_provider(HealthcareProvider)
    missing = [name for name in documented if not hasattr(fake, name)]
    assert not missing, f"README documents methods that do not exist: {missing}"
    for name in documented:
        assert getattr(fake, name)(), f"README method '{name}' returned nothing"
