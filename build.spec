# -*- mode: python ; coding: utf-8 -*-
# Build .exe on Windows:  pyinstaller build.spec
# Build .app on macOS:    pyinstaller build.spec
import os
import sys

block_cipher = None

_spec_dir = os.path.dirname(os.path.abspath(SPEC))
_win_icon = os.path.join(_spec_dir, 'assets', 'app_icon.ico')
_mac_icon = os.path.join(_spec_dir, 'assets', 'app_icon.icns')

a = Analysis(
    ['src/main.py'],
    pathex=['.'],
    binaries=[],
    datas=[
        ('assets', 'assets'),
    ],
    hiddenimports=[
        'PySide6.QtCore',
        'PySide6.QtGui',
        'PySide6.QtWidgets',
        'lxml.etree',
        'lxml._elementpath',
        'docx',
        'docx.oxml',
        'docx.oxml.ns',
        'pdfplumber',
        'fitz',
        'PIL',
        'PIL.Image',
        'pytesseract',
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

# ── Windows: single-file .exe ──────────────────────────────────────────────
if sys.platform == 'win32':
    exe = EXE(
        pyz,
        a.scripts,
        a.binaries,
        a.zipfiles,
        a.datas,
        [],
        name='ПротоколСборщик',
        debug=False,
        bootloader_ignore_signals=False,
        strip=False,
        upx=True,
        upx_exclude=[],
        runtime_tmpdir=None,
        console=False,
        disable_windowed_traceback=False,
        argv_emulation=False,
        target_arch=None,
        codesign_identity=None,
        entitlements_file=None,
        icon=_win_icon if os.path.isfile(_win_icon) else None,
        onefile=True,
    )

# ── macOS: .app bundle ────────────────────────────────────────────────────
else:
    exe = EXE(
        pyz,
        a.scripts,
        [],
        exclude_binaries=True,
        name='ПротоколСборщик',
        debug=False,
        bootloader_ignore_signals=False,
        strip=False,
        upx=True,
        console=False,
        argv_emulation=False,
        target_arch=None,
        codesign_identity=None,
        entitlements_file=None,
        icon=_mac_icon if os.path.isfile(_mac_icon) else None,
    )
    coll = COLLECT(
        exe,
        a.binaries,
        a.zipfiles,
        a.datas,
        strip=False,
        upx=True,
        upx_exclude=[],
        name='ПротоколСборщик',
    )
    app = BUNDLE(
        coll,
        name='ПротоколСборщик.app',
        icon=_mac_icon if os.path.isfile(_mac_icon) else None,
        bundle_identifier='ru.protocol.builder',
        info_plist={
            'CFBundleName': 'Сборщик протокола',
            'CFBundleDisplayName': 'Сборщик протокола',
            'CFBundleVersion': '1.0.0',
            'CFBundleShortVersionString': '1.0.0',
            'NSHighResolutionCapable': True,
        },
    )
