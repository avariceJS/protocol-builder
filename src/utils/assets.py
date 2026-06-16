"""Paths to bundled static assets (dev and PyInstaller)."""

from __future__ import annotations

import os
import sys

# Largest bundled PNG — window icon and in-app branding.
APP_ICON_FILE = os.path.join('web', 'icons-310.png')


def project_root() -> str:
    return os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def assets_dir() -> str:
    if getattr(sys, 'frozen', False):
        return os.path.join(sys._MEIPASS, 'assets')
    return os.path.join(project_root(), 'assets')


def asset_path(*parts: str) -> str:
    return os.path.join(assets_dir(), *parts)


def app_icon_path() -> str:
    return asset_path(APP_ICON_FILE)
