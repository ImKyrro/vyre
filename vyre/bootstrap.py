import importlib
import subprocess
import sys

_REQUIRED = [
    ("PySide6", "PySide6>=6.7"),
    ("cryptography", "cryptography>=42"),
    ("mcp", "mcp>=2.0"),
]

_OPTIONAL = {"mcp"}


def _missing() -> list:
    missing = []
    for module, spec in _REQUIRED:
        try:
            importlib.import_module(module)
        except ImportError:
            missing.append((module, spec))
    return missing


def _install(specs: list, on_message=None) -> bool:
    def say(text):
        if on_message:
            on_message(text)
        else:
            print(text)

    say("Installing required components: " + ", ".join(specs))
    try:
        subprocess.check_call(
            [sys.executable, "-m", "pip", "install", "--disable-pip-version-check", *specs]
        )
        return True
    except (subprocess.CalledProcessError, OSError) as error:
        say(f"Automatic install failed: {error}")
        return False


def ensure(on_message=None) -> bool:
    missing = _missing()
    if not missing:
        return True
    required_specs = [spec for module, spec in missing if module not in _OPTIONAL]
    optional_specs = [spec for module, spec in missing if module in _OPTIONAL]

    ok = True
    if required_specs:
        ok = _install(required_specs, on_message)
    if optional_specs:
        _install(optional_specs, on_message)
    return ok
