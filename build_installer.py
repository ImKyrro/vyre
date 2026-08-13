import subprocess
import sys
from pathlib import Path

from vyre import __version__

ROOT = Path(__file__).parent.resolve()
ICON = ROOT / "vyre" / "assets" / "icon.ico"
ENTRY = ROOT / "installer" / "vyre_installer.py"
OUT = ROOT / "build_out"


def main() -> None:
    file_version = ".".join((__version__.split(".") + ["0", "0", "0"])[:4])
    command = [
        sys.executable,
        "-m",
        "nuitka",
        "--standalone",
        "--onefile",
        "--assume-yes-for-downloads",
        "--enable-plugin=pyside6",
        "--include-module=vyre.theme",
        "--include-module=vyre.ui.widgets",
        "--windows-console-mode=disable",
        f"--windows-icon-from-ico={ICON}",
        "--company-name=Kyrro",
        "--product-name=Vyre Setup",
        f"--file-version={file_version}",
        f"--product-version={file_version}",
        "--file-description=Vyre Setup",
        "--copyright=Kyrro",
        f"--output-dir={OUT}",
        "--output-filename=VyreSetup.exe",
        "--remove-output",
        str(ENTRY),
    ]
    print("Building VyreSetup.exe with Nuitka...")
    raise SystemExit(subprocess.call(command))


if __name__ == "__main__":
    main()
