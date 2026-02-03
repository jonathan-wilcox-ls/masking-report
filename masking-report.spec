# -*- mode: python ; coding: utf-8 -*-
"""PyInstaller spec file for masking-report executable."""

import os
import sys

# Add src to path for proper imports
src_path = os.path.join(os.path.dirname(os.path.abspath(SPEC)), 'src')

a = Analysis(
    ['src/masking_report/__main__.py'],
    pathex=[src_path],
    binaries=[],
    datas=[],
    hiddenimports=[
        'masking_report',
        'masking_report.cli',
        'masking_report.client',
        'masking_report.models',
        'masking_report.report',
        'click',
        'httpx',
        'httpx._transports',
        'httpx._transports.default',
        'rich',
        'rich.console',
        'rich.table',
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
    optimize=0,
)

pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name='masking-report',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=True,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)
