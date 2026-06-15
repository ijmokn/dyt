# -*- mode: python ; coding: utf-8 -*-
from PyInstaller.utils.hooks import collect_dynamic_libs, collect_submodules

binaries = []
binaries += collect_dynamic_libs('shiboken6')

# Azure SDK 在运行时会动态加载部分子模块，打包时需要显式收集。
azure_hiddenimports = []
azure_hiddenimports += collect_submodules('azure.ai.projects')
azure_hiddenimports += collect_submodules('azure.identity')
azure_hiddenimports += collect_submodules('azure.core')


a = Analysis(
    ['main.py'],
    pathex=[],
    binaries=binaries,
    datas=[('frontend', 'frontend'), ('shared', 'shared'), ('backend', 'backend'), ('azure.env', '.')],
    hiddenimports=['shiboken6.Shiboken', 'PySide6.QtCore', 'PySide6.QtGui', 'PySide6.QtWidgets'] + azure_hiddenimports,
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
    name='JMate',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)
coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=['python3.dll', 'python312.dll', 'Qt6Core.dll', 'Qt6Gui.dll', 'Qt6Widgets.dll', 'shiboken6.abi3.dll', 'Shiboken.pyd', 'VCRUNTIME140.dll', 'VCRUNTIME140_1.dll', 'MSVCP140.dll', 'api-ms-win-crt-*.dll'],
    name='JMate',
)
