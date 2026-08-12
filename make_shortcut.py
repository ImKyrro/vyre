import os
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).parent.resolve()


def _pythonw() -> str:
    candidate = Path(sys.executable).with_name("pythonw.exe")
    return str(candidate if candidate.exists() else sys.executable)


def _create(shortcut: Path) -> None:
    target = _pythonw()
    script = ROOT / "Vyre.pyw"
    icon = ROOT / "vyre" / "assets" / "icon.ico"
    ps = (
        "$ws = New-Object -ComObject WScript.Shell; "
        f"$s = $ws.CreateShortcut('{shortcut}'); "
        f"$s.TargetPath = '{target}'; "
        f"$s.Arguments = '\"{script}\"'; "
        f"$s.WorkingDirectory = '{ROOT}'; "
        f"$s.IconLocation = '{icon}'; "
        "$s.Description = 'Vyre - Roblox Alt Account Manager'; "
        "$s.Save()"
    )
    subprocess.run(["powershell", "-NoProfile", "-Command", ps], check=True)


def main() -> None:
    desktop = Path(os.environ["USERPROFILE"]) / "Desktop"
    start_menu = (
        Path(os.environ["APPDATA"])
        / "Microsoft" / "Windows" / "Start Menu" / "Programs"
    )
    for folder in (desktop, start_menu):
        folder.mkdir(parents=True, exist_ok=True)
        _create(folder / "Vyre.lnk")

    print("Created shortcuts on the Desktop and in the Start Menu.")
    print("To pin to the taskbar: launch Vyre, right-click its taskbar icon,")
    print("then choose 'Pin to taskbar'. (Windows blocks silent pinning.)")


if __name__ == "__main__":
    main()
