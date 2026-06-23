# -*- mode: python ; coding: utf-8 -*-
from PyInstaller.utils.hooks import collect_all, collect_dynamic_libs

binaries = []
binaries += collect_dynamic_libs('shiboken6')

datas = [
    ('frontend', 'frontend'),
    ('shared', 'shared'),
    ('backend', 'backend'),
    ('azure.env', '.'),
    ('.attendance-config.json', '.'),
]

hiddenimports = [
    'shiboken6.Shiboken',
    'PySide6.QtCore',
    'PySide6.QtGui',
    'PySide6.QtWidgets',
    'cryptography',
    'cryptography.fernet',
]

# Agent Framework 的 Foundry/OpenAI 扩展包含动态导入，PyInstaller 静态分析
# 无法完整发现，因此显式收集三个包的数据文件、二进制和隐藏模块。
for package in (
    'agent_framework',
    'agent_framework_foundry',
    'agent_framework_openai',
):
    package_datas, package_binaries, package_hiddenimports = collect_all(package)
    datas += package_datas
    binaries += package_binaries
    hiddenimports += package_hiddenimports


a = Analysis(
    ['main.py'],
    pathex=[],
    binaries=binaries,
    datas=datas,
    hiddenimports=hiddenimports,
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
    name='JMate',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=['python3.dll', 'python312.dll', 'Qt6Core.dll', 'Qt6Gui.dll', 'Qt6Widgets.dll', 'shiboken6.abi3.dll', 'Shiboken.pyd', 'VCRUNTIME140.dll', 'VCRUNTIME140_1.dll', 'MSVCP140.dll', 'api-ms-win-crt-*.dll'],
    runtime_tmpdir=None,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)
