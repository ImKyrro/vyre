import sys

TARGET = "robloxplayerbeta.exe"

_SW_MINIMIZE = 6
_SW_RESTORE = 9
_WM_CLOSE = 0x0010
_SWP_NOZORDER = 0x0004
_IDLE_PRIORITY = 0x00000040
_BELOW_NORMAL = 0x00004000
_NORMAL_PRIORITY = 0x00000020
_PROCESS_SET_INFORMATION = 0x0200
_PROCESS_QUERY_LIMITED = 0x1000


def is_supported() -> bool:
    return sys.platform == "win32"


def _process_name(pid: int) -> str:
    import ctypes
    from ctypes import wintypes

    kernel32 = ctypes.windll.kernel32
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
    from ctypes import wintypes

    user32 = ctypes.windll.user32
    results = []
    pid_cache = {}

    WNDENUMPROC = ctypes.WINFUNCTYPE(wintypes.BOOL, wintypes.HWND, wintypes.LPARAM)

    def callback(hwnd, _):
        if not user32.IsWindowVisible(hwnd):
            return True
        length = user32.GetWindowTextLengthW(hwnd)
        if length == 0:
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
    import ctypes

    user32 = ctypes.windll.user32
    windows = list_windows()
    for hwnd, _ in windows:
        user32.ShowWindow(hwnd, _SW_MINIMIZE)
    return len(windows)


def restore_all() -> int:
    import ctypes

    user32 = ctypes.windll.user32
    windows = list_windows()
    for hwnd, _ in windows:
        user32.ShowWindow(hwnd, _SW_RESTORE)
        user32.SetForegroundWindow(hwnd)
    return len(windows)


def close_all() -> int:
    import ctypes

    user32 = ctypes.windll.user32
    windows = list_windows()
    for hwnd, _ in windows:
        user32.PostMessageW(hwnd, _WM_CLOSE, 0, 0)
    return len(windows)


def tile_grid() -> int:
    import ctypes
    from ctypes import wintypes

    user32 = ctypes.windll.user32
    windows = list_windows()
    if not windows:
        return 0

    rect = wintypes.RECT()
    user32.SystemParametersInfoW(0x0030, 0, ctypes.byref(rect), 0)
    work_w = rect.right - rect.left
    work_h = rect.bottom - rect.top

    total = len(windows)
    cols = int(total ** 0.5)
    cols = max(1, cols if cols * cols >= total else cols + 1)
    rows = (total + cols - 1) // cols
    cell_w = work_w // cols
    cell_h = work_h // rows

    for index, (hwnd, _) in enumerate(windows):
        user32.ShowWindow(hwnd, _SW_RESTORE)
        col = index % cols
        row = index // cols
        x = rect.left + col * cell_w
        y = rect.top + row * cell_h
        user32.SetWindowPos(hwnd, 0, x, y, cell_w, cell_h, _SWP_NOZORDER)
    return total


def set_low_priority(low: bool = True) -> int:
    import ctypes

    kernel32 = ctypes.windll.kernel32
    seen = set()
    changed = 0
    for _, pid in list_windows():
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
