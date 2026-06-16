"""Windows: install to per-user folder, remember preferences, create shortcuts."""

from __future__ import annotations

import os
import json
import shutil
import subprocess
import sys
from pathlib import Path

APP_FOLDER_NAME = 'Сборщик протокола'
EXE_NAME = 'ПротоколСборщик.exe'
SETTINGS_ORG = 'ProtocolBuilder'
SETTINGS_APP = 'Сборщик протокола'

CONFIG_DIR_NAME = 'ProtocolBuilder'
CONFIG_FILE_NAME = 'config.json'

CONFIG_INSTALL_DIR_KEY = 'install_dir'
CONFIG_OUTPUT_DIR_KEY = 'output_dir'
CONFIG_PROMPT_SKIPPED_KEY = 'install_prompt_skipped'


def _config_path() -> Path:
    local_app_data = os.environ.get('LOCALAPPDATA', '')
    return Path(local_app_data) / CONFIG_DIR_NAME / CONFIG_FILE_NAME


def _load_config() -> dict:
    path = _config_path()
    try:
        if not path.is_file():
            return {}
        return json.loads(path.read_text(encoding='utf-8'))
    except (OSError, json.JSONDecodeError):
        return {}


def _save_config(cfg: dict) -> None:
    path = _config_path()
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(cfg, ensure_ascii=False, indent=2), encoding='utf-8')
    except OSError:
        # если не можем записать настройки — приложение всё равно должно работать
        pass


def _documents_default_dir() -> Path:
    user_profile = Path(os.environ.get('USERPROFILE', ''))
    docs = user_profile / 'Documents'
    base = docs if docs.is_dir() else user_profile
    return base / APP_FOLDER_NAME


def install_prompt_skipped() -> bool:
    cfg = _load_config()
    return bool(cfg.get(CONFIG_PROMPT_SKIPPED_KEY, False))


def set_install_prompt_skipped(skipped: bool) -> None:
    cfg = _load_config()
    cfg[CONFIG_PROMPT_SKIPPED_KEY] = bool(skipped)
    _save_config(cfg)


def set_install_dir(path: Path) -> None:
    cfg = _load_config()
    cfg[CONFIG_INSTALL_DIR_KEY] = str(path)
    _save_config(cfg)


def set_output_dir(path: Path) -> None:
    cfg = _load_config()
    cfg[CONFIG_OUTPUT_DIR_KEY] = str(path)
    _save_config(cfg)


def install_dir() -> Path:
    cfg = _load_config()
    override = cfg.get(CONFIG_INSTALL_DIR_KEY)
    if override:
        return Path(override)
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


def should_offer_install(*, prompt_skipped: bool | None = None) -> bool:
    if not is_windows_frozen() or is_running_from_install_dir():
        return False
    if prompt_skipped is None:
        prompt_skipped = install_prompt_skipped()
    if prompt_skipped:
        return False
    return True


def output_dir() -> Path:
    cfg = _load_config()
    override = cfg.get(CONFIG_OUTPUT_DIR_KEY)
    if override:
        return Path(override)
    return _documents_default_dir()


def install_application(
    *,
    desktop_shortcut: bool,
    start_menu_shortcut: bool = True,
    custom_install_dir: Path | None = None,
    default_output_dir: Path | None = None,
) -> Path:
    if custom_install_dir is not None:
        set_install_dir(custom_install_dir)
    if default_output_dir is not None:
        set_output_dir(default_output_dir)
    set_install_prompt_skipped(False)

    target_dir = custom_install_dir or install_dir()
    target_dir.mkdir(parents=True, exist_ok=True)
    target_exe = target_dir / EXE_NAME

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
