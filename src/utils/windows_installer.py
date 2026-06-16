"""Windows: install to LocalAppData and create desktop shortcut."""

from __future__ import annotations

import os
import shutil
import subprocess
import sys
from pathlib import Path

APP_FOLDER_NAME = 'Сборщик протокола'
EXE_NAME = 'ПротоколСборщик.exe'
SETTINGS_ORG = 'ProtocolBuilder'
SETTINGS_APP = 'Сборщик протокола'


def install_dir() -> Path:
    local_app_data = os.environ.get('LOCALAPPDATA', '')
    return Path(local_app_data) / 'Programs' / APP_FOLDER_NAME


def installed_exe_path() -> Path:
    return install_dir() / EXE_NAME


def is_windows_frozen() -> bool:
    return sys.platform == 'win32' and getattr(sys, 'frozen', False)


def is_running_from_install_dir() -> bool:
    if not is_windows_frozen():
        return True
    try:
        return Path(sys.executable).resolve().parent == install_dir().resolve()
    except OSError:
        return False


def should_offer_install(*, prompt_skipped: bool) -> bool:
    if not is_windows_frozen() or is_running_from_install_dir() or prompt_skipped:
        return False
    return True


def install_application(*, desktop_shortcut: bool, start_menu_shortcut: bool = True) -> Path:
    target_dir = install_dir()
    target_dir.mkdir(parents=True, exist_ok=True)
    target_exe = installed_exe_path()

    source = Path(sys.executable).resolve()
    if source != target_exe.resolve():
        shutil.copy2(source, target_exe)

    if desktop_shortcut:
        create_shortcut(
            target_exe,
            _desktop_dir() / f'{APP_FOLDER_NAME}.lnk',
        )
    if start_menu_shortcut:
        start_menu = (
            Path(os.environ.get('APPDATA', ''))
            / 'Microsoft'
            / 'Windows'
            / 'Start Menu'
            / 'Programs'
        )
        create_shortcut(target_exe, start_menu / f'{APP_FOLDER_NAME}.lnk')

    return target_exe


def launch_installed_copy(target_exe: Path | None = None) -> None:
    exe = target_exe or installed_exe_path()
    subprocess.Popen([str(exe)], cwd=str(exe.parent), close_fds=True)


def _desktop_dir() -> Path:
    user_profile = Path(os.environ.get('USERPROFILE', ''))
    public = Path(os.environ.get('PUBLIC', r'C:\Users\Public'))
    for candidate in (
        user_profile / 'Desktop',
        user_profile / 'OneDrive' / 'Desktop',
        public / 'Desktop',
    ):
        if candidate.is_dir():
            return candidate
    return user_profile / 'Desktop'


def create_shortcut(target_exe: Path, shortcut_path: Path) -> None:
    shortcut_path.parent.mkdir(parents=True, exist_ok=True)
    ps = (
        '$shell = New-Object -ComObject WScript.Shell; '
        f'$link = $shell.CreateShortcut("{_ps_escape(shortcut_path)}"); '
        f'$link.TargetPath = "{_ps_escape(target_exe)}"; '
        f'$link.WorkingDirectory = "{_ps_escape(target_exe.parent)}"; '
        f'$link.IconLocation = "{_ps_escape(target_exe)},0"; '
        '$link.Save()'
    )
    subprocess.run(
        ['powershell', '-NoProfile', '-ExecutionPolicy', 'Bypass', '-Command', ps],
        check=False,
        creationflags=getattr(subprocess, 'CREATE_NO_WINDOW', 0),
    )


def _ps_escape(path: Path) -> str:
    return str(path).replace('\\', '\\\\')
