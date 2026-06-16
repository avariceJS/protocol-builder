#!/usr/bin/env python3
"""Regenerate app_icon.ico / app_icon.icns from assets/web/icons-310.png."""

from __future__ import annotations

import shutil
import subprocess
import sys
from pathlib import Path

from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / 'assets' / 'web' / 'icons-310.png'
ICO_OUT = ROOT / 'assets' / 'app_icon.ico'
ICNS_OUT = ROOT / 'assets' / 'app_icon.icns'


def _load_source() -> Image.Image:
    if not SRC.is_file():
        raise FileNotFoundError(f'Missing source icon: {SRC}')
    return Image.open(SRC).convert('RGBA')


def _flatten_for_windows(src: Image.Image) -> Image.Image:
    """Windows desktop icons look washed-out on semi-transparent PNG sources."""
    background = Image.new('RGBA', src.size, (255, 255, 255, 255))
    return Image.alpha_composite(background, src)


def build_ico(src: Image.Image) -> None:
    sizes = [16, 24, 32, 48, 64, 128, 256]
    # На некоторых версиях Pillow append_images для ICO делает только один кадр.
    # Вариант через параметр `sizes` даёт multi-size иконку.
    src.save(ICO_OUT, format='ICO', sizes=[(s, s) for s in sizes])


def build_icns(src: Image.Image) -> None:
    if sys.platform != 'darwin':
        print('Skipping .icns (macOS only)')
        return

    iconset = ROOT / 'assets' / 'app_icon.iconset'
    if iconset.exists():
        shutil.rmtree(iconset)
    iconset.mkdir(parents=True)

    mapping = {
        'icon_16x16.png': 16,
        'icon_16x16@2x.png': 32,
        'icon_32x32.png': 32,
        'icon_32x32@2x.png': 64,
        'icon_128x128.png': 128,
        'icon_128x128@2x.png': 256,
        'icon_256x256.png': 256,
        'icon_256x256@2x.png': 512,
        'icon_512x512.png': 512,
        'icon_512x512@2x.png': 1024,
    }
    for name, size in mapping.items():
        target = min(size, max(src.width, src.height))
        src.resize((target, target), Image.Resampling.LANCZOS).save(iconset / name)

    subprocess.run(
        ['iconutil', '-c', 'icns', str(iconset), '-o', str(ICNS_OUT)],
        check=True,
    )
    shutil.rmtree(iconset)


def main() -> None:
    raw = _load_source()
    flat = _flatten_for_windows(raw)
    build_ico(flat)
    build_icns(flat)
    print(f'Wrote {ICO_OUT}')
    if ICNS_OUT.is_file():
        print(f'Wrote {ICNS_OUT}')


if __name__ == '__main__':
    main()
