import json
import os
from pathlib import Path

_MARKER = "_vyrePerformance"


def _versions_dir() -> Path:
    root = os.environ.get("LOCALAPPDATA", os.path.expanduser("~"))
    return Path(root) / "Roblox" / "Versions"


def version_dirs() -> list:
    base = _versions_dir()
    if not base.exists():
        return []
    result = []
    for child in base.iterdir():
        if child.is_dir() and (child / "RobloxPlayerBeta.exe").exists():
            result.append(child)
    return result


def is_installed() -> bool:
    return bool(version_dirs())


def _settings_path(version_dir: Path) -> Path:
    return version_dir / "ClientSettings" / "ClientAppSettings.json"


def _performance_flags(fps_cap: int) -> dict:
    return {
        _MARKER: "true",
        "DFIntTaskSchedulerTargetFps": str(max(1, fps_cap)),
        "FFlagDisablePostFx": "True",
        "FIntRenderShadowIntensity": "0",
        "DFFlagDebugPauseVoxelizer": "True",
        "FIntDebugTextureManagerSkipMips": "8",
        "DFFlagTextureQualityOverrideEnabled": "True",
        "DFIntTextureQualityOverride": "0",
    }


def apply(fps_cap: int = 30) -> int:
    flags = _performance_flags(fps_cap)
    count = 0
    for version_dir in version_dirs():
        path = _settings_path(version_dir)
        path.parent.mkdir(parents=True, exist_ok=True)
        try:
            path.write_text(json.dumps(flags, indent=2), encoding="utf-8")
            count += 1
        except OSError:
            pass
    return count


def restore() -> int:
    count = 0
    for version_dir in version_dirs():
        path = _settings_path(version_dir)
        try:
            path.write_text("{}", encoding="utf-8")
            count += 1
        except OSError:
            pass
    return count


def is_applied() -> bool:
    for version_dir in version_dirs():
        path = _settings_path(version_dir)
        if not path.exists():
            continue
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
            if isinstance(data, dict) and data.get(_MARKER):
                return True
        except (ValueError, OSError):
            continue
    return False
