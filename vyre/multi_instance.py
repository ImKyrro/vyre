import sys

_handles = []
_EVENT_NAME = "ROBLOX_singletonEvent"
_MUTEX_NAME = "ROBLOX_singletonMutex"
_ERROR_ALREADY_EXISTS = 183


def is_supported() -> bool:
    return sys.platform == "win32"


def is_enabled() -> bool:
    return bool(_handles)


def _kernel32():
    import ctypes
    from ctypes import wintypes

    k = ctypes.windll.kernel32
    k.CreateEventW.restype = wintypes.HANDLE
    k.CreateEventW.argtypes = [wintypes.LPVOID, wintypes.BOOL, wintypes.BOOL, wintypes.LPCWSTR]
    k.CreateMutexW.restype = wintypes.HANDLE
    k.CreateMutexW.argtypes = [wintypes.LPVOID, wintypes.BOOL, wintypes.LPCWSTR]
    k.CloseHandle.restype = wintypes.BOOL
    k.CloseHandle.argtypes = [wintypes.HANDLE]
    return k


def enable() -> bool:
    if not is_supported() or _handles:
        return bool(_handles)
    import ctypes

    k = _kernel32()
    event = k.CreateEventW(None, True, False, _EVENT_NAME)
    if event:
        _handles.append(event)
    mutex = k.CreateMutexW(None, True, _MUTEX_NAME)
    if mutex:
        _handles.append(mutex)
    return bool(_handles)


def disable() -> None:
    if not is_supported() or not _handles:
        return
    k = _kernel32()
    while _handles:
        k.CloseHandle(_handles.pop())


def status() -> str:
    if not is_supported():
        return "Only available on Windows."
    if not _handles:
        return "Off"
    from ctypes import wintypes

    k = _kernel32()
    k.GetLastError.restype = wintypes.DWORD
    k.GetLastError.argtypes = []
    probe = k.CreateMutexW(None, False, _MUTEX_NAME)
    already = k.GetLastError() == _ERROR_ALREADY_EXISTS
    if probe:
        k.CloseHandle(probe)
    return "Active (holding singleton)" if already else "Active (created)"
