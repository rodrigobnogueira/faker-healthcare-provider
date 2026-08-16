import importlib.util
from pathlib import Path
from types import ModuleType


def load_brand_name_generator() -> ModuleType:
    """Import scripts/generate_brand_names.py, which is a script and not an installed module.

    The brand-name tests re-run the screens the script defines rather than restating
    them, so a screen can only be loosened in one place — and loosening it there also
    changes the catalogue the script regenerates, which the same tests compare against
    the committed files.
    """
    path = Path(__file__).resolve().parent.parent / "scripts" / "generate_brand_names.py"
    spec = importlib.util.spec_from_file_location("generate_brand_names", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module
