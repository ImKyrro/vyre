import sys

TARGET = "robloxplayerbeta.exe"

_SW_MINIMIZE = 6
_SW_RESTORE = 9
_WM_CLOSE = 0x0010
_SWP_NOZORDER = 0x0004
_SWP_NOACTIVATE = 0x0010
_BELOW_NORMAL = 0x00004000
_NORMAL_PRIORITY = 0x00000020
_PROCESS_SET_INFORMATION = 0x0200
_PROCESS_QUERY_LIMITED = 0x1000

_configured = False


def is_supported() -> bool:
    return sys.platform == "win32"


def _api():
    global _configured
    import ctypes
    from ctypes import wintypes

    user32 = ctypes.windll.user32
    kernel32 = ctypes.windll.kernel32
    if _configured:
        return user32, kernel32, wintypes

    user32.IsWindowVisible.argtypes = [wintypes.HWND]
    user32.IsWindowVisible.restype = wintypes.BOOL
    user32.GetWindowTextLengthW.argtypes = [wintypes.HWND]
    user32.GetWindowTextLengthW.restype = ctypes.c_int
    user32.GetWindowThreadProcessId.argtypes = [wintypes.HWND, ctypes.POINTER(wintypes.DWORD)]
    user32.GetWindowThreadProcessId.restype = wintypes.DWORD
    user32.ShowWindow.argtypes = [wintypes.HWND, ctypes.c_int]
    user32.ShowWindow.restype = wintypes.BOOL
    user32.SetForegroundWindow.argtypes = [wintypes.HWND]
    user32.SetForegroundWindow.restype = wintypes.BOOL
    user32.PostMessageW.argtypes = [wintypes.HWND, wintypes.UINT, wintypes.WPARAM, wintypes.LPARAM]
    user32.PostMessageW.restype = wintypes.BOOL
    user32.SetWindowPos.argtypes = [
        wintypes.HWND, wintypes.HWND, ctypes.c_int, ctypes.c_int,
        ctypes.c_int, ctypes.c_int, wintypes.UINT,
    ]
    user32.SetWindowPos.restype = wintypes.BOOL
    user32.SystemParametersInfoW.argtypes = [
        wintypes.UINT, wintypes.UINT, ctypes.c_void_p, wintypes.UINT,
    ]
    user32.SystemParametersInfoW.restype = wintypes.BOOL
    kernel32.OpenProcess.argtypes = [wintypes.DWORD, wintypes.BOOL, wintypes.DWORD]
    kernel32.OpenProcess.restype = wintypes.HANDLE
    kernel32.QueryFullProcessImageNameW.argtypes = [
        wintypes.HANDLE, wintypes.DWORD, wintypes.LPWSTR, ctypes.POINTER(wintypes.DWORD),
    ]
    kernel32.QueryFullProcessImageNameW.restype = wintypes.BOOL
    kernel32.CloseHandle.argtypes = [wintypes.HANDLE]
    kernel32.CloseHandle.restype = wintypes.BOOL
    kernel32.SetPriorityClass.argtypes = [wintypes.HANDLE, wintypes.DWORD]
    kernel32.SetPriorityClass.restype = wintypes.BOOL
    _configured = True
    return user32, kernel32, wintypes


def _process_name(pid: int) -> str:
    import ctypes

    user32, kernel32, wintypes = _api()
    handle = kernel32.OpenProcess(_PROCESS_QUERY_LIMITED, False, pid)
    if not handle:
        return ""
    try:
        size = wintypes.DWORD(260)
        buffer = ctypes.create_unicode_buffer(size.value)
        if kernel32.QueryFullProcessImageNameW(handle, 0, buffer, ctypes.byref(size)):
            return buffer.value.split("\\")[-1].lower()
        return ""
    finally:
        kernel32.CloseHandle(handle)


def list_windows() -> list:
    if not is_supported():
        return []
    import ctypes

    user32, kernel32, wintypes = _api()
    results = []
    pid_cache = {}

    WNDENUMPROC = ctypes.WINFUNCTYPE(wintypes.BOOL, wintypes.HWND, wintypes.LPARAM)

    def callback(hwnd, _):
        if not user32.IsWindowVisible(hwnd):
            return True
        if user32.GetWindowTextLengthW(hwnd) == 0:
            return True
        pid = wintypes.DWORD()
        user32.GetWindowThreadProcessId(hwnd, ctypes.byref(pid))
        name = pid_cache.get(pid.value)
        if name is None:
            name = _process_name(pid.value)
            pid_cache[pid.value] = name
        if name == TARGET:
            results.append((hwnd, pid.value))
        return True

    user32.EnumWindows(WNDENUMPROC(callback), 0)
    return results


def count() -> int:
    return len(list_windows())


def minimize_all() -> int:
    user32, _, _ = _api()
    windows = list_windows()
    for hwnd, _pid in windows:
        user32.ShowWindow(hwnd, _SW_MINIMIZE)
    return len(windows)


def restore_all() -> int:
    user32, _, _ = _api()
    windows = list_windows()
    for hwnd, _pid in windows:
        user32.ShowWindow(hwnd, _SW_RESTORE)
        user32.SetForegroundWindow(hwnd)
    return len(windows)


def close_all() -> int:
    user32, _, _ = _api()
    windows = list_windows()
    for hwnd, _pid in windows:
        user32.PostMessageW(hwnd, _WM_CLOSE, 0, 0)
    return len(windows)


def _work_area():
    import ctypes

    user32, _, wintypes = _api()
    rect = wintypes.RECT()
    user32.SystemParametersInfoW(0x0030, 0, ctypes.byref(rect), 0)
    return rect


def tile_grid() -> int:
    user32, _, _ = _api()
    windows = list_windows()
    if not windows:
        return 0
    rect = _work_area()
    work_w = rect.right - rect.left
    work_h = rect.bottom - rect.top
    total = len(windows)
    cols = max(1, int(total ** 0.5 + 0.999))
    rows = (total + cols - 1) // cols
    cell_w = work_w // cols
    cell_h = work_h // rows
    for index, (hwnd, _pid) in enumerate(windows):
        user32.ShowWindow(hwnd, _SW_RESTORE)
        col = index % cols
        row = index // cols
        x = rect.left + col * cell_w
        y = rect.top + row * cell_h
        user32.SetWindowPos(hwnd, 0, x, y, cell_w, cell_h, _SWP_NOZORDER | _SWP_NOACTIVATE)
    return total


def shrink_titlebars() -> int:
    user32, _, _ = _api()
    windows = list_windows()
    if not windows:
        return 0
    rect = _work_area()
    y = rect.top
    for hwnd, _pid in windows:
        user32.ShowWindow(hwnd, _SW_RESTORE)
        user32.SetWindowPos(hwnd, 0, rect.left, y, 480, 44, _SWP_NOZORDER | _SWP_NOACTIVATE)
        y += 48
    return len(windows)


def restore_sizes() -> int:
    user32, _, _ = _api()
    windows = list_windows()
    rect = _work_area()
    x = rect.left
    for hwnd, _pid in windows:
        user32.ShowWindow(hwnd, _SW_RESTORE)
        user32.SetWindowPos(hwnd, 0, x, rect.top, 1024, 640, _SWP_NOZORDER | _SWP_NOACTIVATE)
        x += 40
    return len(windows)


def set_low_priority(low: bool = True) -> int:
    _, kernel32, _ = _api()
    seen = set()
    changed = 0
    for _hwnd, pid in list_windows():
        if pid in seen:
            continue
        seen.add(pid)
        handle = kernel32.OpenProcess(_PROCESS_SET_INFORMATION, False, pid)
        if not handle:
            continue
        try:
            value = _BELOW_NORMAL if low else _NORMAL_PRIORITY
            if kernel32.SetPriorityClass(handle, value):
                changed += 1
        finally:
            kernel32.CloseHandle(handle)
    return changed
