import ctypes.wintypes
import typing
import winreg

from pyxivdata.installation.game_locator import GameInstallation

CommandLineToArgvW = ctypes.windll.shell32.CommandLineToArgvW
CommandLineToArgvW.argtypes = ctypes.wintypes.LPWSTR, ctypes.POINTER(ctypes.c_int)
CommandLineToArgvW.restype = ctypes.POINTER(ctypes.wintypes.LPWSTR)
LocalFree = ctypes.windll.kernel32.LocalFree
LocalFree.argtypes = ctypes.c_void_p,
LocalFree.restype = ctypes.c_void_p


def _read_registry_str(key: typing.Union[int, winreg.HKEYType], sub_key: str,
                       value_name: typing.Optional[str] = None) -> typing.Optional[str]:
    import winreg
    try:
        with winreg.OpenKey(key=key, sub_key=sub_key, access=winreg.KEY_WOW64_32KEY | winreg.KEY_READ) as key:
            return winreg.QueryValueEx(key, value_name)[0]
    except FileNotFoundError:
        pass
    try:
        with winreg.OpenKey(key=key, sub_key=sub_key, access=winreg.KEY_WOW64_64KEY | winreg.KEY_READ) as key:
            return winreg.QueryValueEx(key, value_name)[0]
    except FileNotFoundError:
        pass
    return None


def _split_arguments(command_line: str):
    argc = ctypes.c_int(0)
    argv_arr = CommandLineToArgvW(command_line, ctypes.byref(argc))
    if not argv_arr:
        raise ctypes.WinError()
    res = [argv_arr[i] for i in range(argc.value)]
    argv_arr = LocalFree(argv_arr)
    if argv_arr:
        raise ctypes.WinError()
    return res


def find_game_installations() -> typing.List[GameInstallation]:
    result = []

    if val := _read_registry_str(
            winreg.HKEY_LOCAL_MACHINE,
            r"SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall\{2B41E132-07DF-4925-A3D3-F2D1765CCDFE}",
            "DisplayIcon"):
        result.append(GameInstallation.from_root_path(val))

    for steam_app_id in (
            39210,  # paid version
            312060,  # trial version
    ):
        if val := _read_registry_str(
                winreg.HKEY_LOCAL_MACHINE,
                rf"SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall\Steam App {steam_app_id}",
                "InstallLocation"):
            result.append(GameInstallation.from_root_path(val))

    if val := _read_registry_str(
            winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\Classes\ff14kr\shell\open\command",
            ""):
        result.append(GameInstallation.from_root_path(_split_arguments(val)[0]))

    if val := _read_registry_str(
            winreg.HKEY_LOCAL_MACHINE,
            r"SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall\FFXIV",
            "DisplayIcon"):
        result.append(GameInstallation.from_root_path(val))

    return result
