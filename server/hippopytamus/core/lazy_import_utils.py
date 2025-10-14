import importlib.util
import sys


def module_exists(name: str) -> bool:
    full_name = f"hippopytamus.{name}"
    return importlib.util.find_spec(full_name) is not None


def module_is_loaded(name: str) -> bool:
    full_name = f"hippopytamus.{name}"
    return full_name in sys.modules
