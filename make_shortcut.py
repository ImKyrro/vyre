import os
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).parent.resolve()


def _pythonw() -> str:
    candidate = Path(sys.executable).with_name("pythonw.exe")
    return str(candidate if candidate.exists() else sys.executable)


def main() -> None:
    desktop = Path(os.path.join(os.environ["USERPROFILE"], "Desktop"))
    shortcut = desktop / "Vyre.lnk"
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
    print(f"Created desktop shortcut: {shortcut}")


if __name__ == "__main__":
    main()
