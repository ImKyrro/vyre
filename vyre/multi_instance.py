import sys

_handles = []
_NAMES = ["ROBLOX_singletonEvent", "ROBLOX_singletonMutex"]


def is_supported() -> bool:
    return sys.platform == "win32"


def is_enabled() -> bool:
    return bool(_handles)


def enable() -> bool:
    if not is_supported() or _handles:
        return _handles != []
    import ctypes

    kernel32 = ctypes.windll.kernel32
    try:
        event = kernel32.CreateEventW(None, True, False, _NAMES[0])
        mutex = kernel32.CreateMutexW(None, True, _NAMES[1])
        for handle in (event, mutex):
            if handle:
                _handles.append(handle)
        return bool(_handles)
    except OSError:
        return False


def disable() -> None:
    if not is_supported():
        return
    import ctypes

    kernel32 = ctypes.windll.kernel32
    while _handles:
        handle = _handles.pop()
        try:
            kernel32.CloseHandle(handle)
        except OSError:
            pass
