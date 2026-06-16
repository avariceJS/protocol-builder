#!/usr/bin/env python3
"""Автоперезапуск GUI при изменении исходников (режим разработки)."""
from __future__ import annotations

import os
import signal
import subprocess
import sys
import threading
import time
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
MAIN = PROJECT_ROOT / "src" / "main.py"
WATCH_DIRS = (PROJECT_ROOT / "src", PROJECT_ROOT / "assets")
RELOAD_EXTENSIONS = {".py", ".png", ".svg", ".qss", ".ico"}
DEBOUNCE_SEC = 0.4


def _should_reload(path: str) -> bool:
    p = Path(path)
    if p.suffix.lower() not in RELOAD_EXTENSIONS:
        return False
    if "__pycache__" in p.parts:
        return False
    return True


class Reloader:
    def __init__(self) -> None:
        self._proc: subprocess.Popen | None = None
        self._lock = threading.Lock()
        self._pending_restart = False
        self._stop = False

    def start_app(self) -> None:
        env = os.environ.copy()
        env.setdefault("PYTHONPATH", str(PROJECT_ROOT))
        self._proc = subprocess.Popen(
            [sys.executable, str(MAIN)],
            cwd=str(PROJECT_ROOT),
            env=env,
        )

    def stop_app(self) -> None:
        if self._proc is None or self._proc.poll() is not None:
            self._proc = None
            return
        self._proc.terminate()
        try:
            self._proc.wait(timeout=3)
        except subprocess.TimeoutExpired:
            self._proc.kill()
            self._proc.wait()
        self._proc = None

    def restart(self) -> None:
        with self._lock:
            if self._stop:
                return
            print("\n[dev] Перезапуск после изменения файлов…")
            self.stop_app()
            self.start_app()
            print("[dev] Приложение запущено. Следим за src/ и assets/\n")

    def schedule_restart(self) -> None:
        with self._lock:
            self._pending_restart = True

        def _debounced() -> None:
            time.sleep(DEBOUNCE_SEC)
            with self._lock:
                if not self._pending_restart or self._stop:
                    return
                self._pending_restart = False
            self.restart()

        threading.Thread(target=_debounced, daemon=True).start()

    def shutdown(self) -> None:
        with self._lock:
            self._stop = True
        self.stop_app()


def main() -> None:
    try:
        from watchdog.events import FileSystemEventHandler
        from watchdog.observers import Observer
    except ImportError:
        print("Установите dev-зависимости: pip install -r requirements-dev.txt")
        sys.exit(1)

    reloader = Reloader()

    class Handler(FileSystemEventHandler):
        def on_modified(self, event) -> None:
            if not event.is_directory and _should_reload(event.src_path):
                reloader.schedule_restart()

        def on_created(self, event) -> None:
            self.on_modified(event)

    def handle_sig(*_) -> None:
        reloader.shutdown()
        sys.exit(0)

    signal.signal(signal.SIGINT, handle_sig)
    signal.signal(signal.SIGTERM, handle_sig)

    print("[dev] Режим разработки: автоперезапуск при сохранении файлов")
    print("[dev] Папки: src/, assets/  |  Ctrl+C — выход\n")
    reloader.start_app()

    observer = Observer()
    for watch_dir in WATCH_DIRS:
        if watch_dir.is_dir():
            observer.schedule(Handler(), str(watch_dir), recursive=True)

    observer.start()

    try:
        while True:
            if reloader._proc and reloader._proc.poll() is not None:
                code = reloader._proc.returncode
                if code != 0:
                    print(f"[dev] Приложение завершилось с кодом {code}. Ждём правок…")
                reloader._proc = None
            time.sleep(0.2)
    finally:
        observer.stop()
        observer.join()
        reloader.shutdown()


if __name__ == "__main__":
    main()
