# -*- mode: python ; coding: utf-8 -*-

a = Analysis(
    ['compression.pyw'],
    pathex=[],
    binaries=[],
    datas=[('Assets/*', 'Assets')],
    hiddenimports=[],
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
    [],
    exclude_binaries=True,
    name='Compression',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,  # Désactiver la console
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity="Your Code Signing Certificate",  # Certificat de signature
    entitlements_file=None,
    icon='Assets/icon.ico',
    version='version.txt', 
)

coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='Compression',
)
