"""Cross-platform helpers for opening files and folders."""
import os
import sys
import subprocess


def open_path(path: str) -> None:
    """Open path with the system default app (cross-platform)."""
    if not path or not os.path.exists(path):
        return
    if sys.platform == 'win32':
        os.startfile(path)  # type: ignore[attr-defined]
    elif sys.platform == 'darwin':
        subprocess.run(['open', path], check=False)
    else:
        subprocess.run(['xdg-open', path], check=False)


def reveal_path(path: str) -> None:
    """Show file/folder in the system file manager (cross-platform)."""
    if not path:
        return
    if sys.platform == 'win32':
        if os.path.isfile(path):
            subprocess.run(['explorer', '/select,', os.path.normpath(path)], check=False)
        else:
            subprocess.run(['explorer', os.path.normpath(path)], check=False)
    elif sys.platform == 'darwin':
        if os.path.isfile(path):
            subprocess.run(['open', '-R', path], check=False)
        else:
            subprocess.run(['open', path], check=False)
    else:
        folder = os.path.dirname(path) if os.path.isfile(path) else path
        subprocess.run(['xdg-open', folder], check=False)
