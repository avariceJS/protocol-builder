"""Tests for Windows install paths and prompt gating."""

from __future__ import annotations

import os
import sys
from pathlib import Path
from unittest.mock import patch

from src.utils.windows_installer import (
    APP_FOLDER_NAME,
    EXE_NAME,
    install_dir,
    installed_exe_path,
    is_running_from_install_dir,
    should_offer_install,
)


def test_install_dir_under_localappdata():
    with patch.dict(os.environ, {'LOCALAPPDATA': r'C:\Users\Test\AppData\Local'}, clear=False):
        expected = os.path.join(r'C:\Users\Test\AppData\Local', 'Programs', APP_FOLDER_NAME)
        assert os.path.normpath(str(install_dir())) == os.path.normpath(expected)


def test_installed_exe_path():
    with patch.dict(os.environ, {'LOCALAPPDATA': r'C:\Users\Test\AppData\Local'}, clear=False):
        assert installed_exe_path().name == EXE_NAME


def test_should_offer_install_only_for_portable_frozen_exe():
    with patch.object(sys, 'platform', 'win32'):
        with patch.object(sys, 'frozen', True, create=True):
            with patch.object(sys, 'executable', r'C:\Users\Test\Downloads\ПротоколСборщик.exe'):
                with patch.dict(os.environ, {'LOCALAPPDATA': r'C:\Users\Test\AppData\Local'}, clear=False):
                    assert should_offer_install(prompt_skipped=False) is True
                    assert should_offer_install(prompt_skipped=True) is False


def test_is_running_from_install_dir_when_paths_match():
    local = r'C:\Users\Test\AppData\Local'
    install_path = Path(local) / 'Programs' / APP_FOLDER_NAME / EXE_NAME
    with patch.object(sys, 'platform', 'win32'):
        with patch.object(sys, 'frozen', True, create=True):
            with patch.object(sys, 'executable', str(install_path)):
                with patch.dict(os.environ, {'LOCALAPPDATA': local}, clear=False):
                    assert is_running_from_install_dir() is True
                    assert should_offer_install(prompt_skipped=False) is False


def test_non_windows_never_offers_install():
    with patch.object(sys, 'platform', 'darwin'):
        with patch.object(sys, 'frozen', True, create=True):
            assert should_offer_install(prompt_skipped=False) is False
