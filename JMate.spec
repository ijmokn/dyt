# -*- mode: python ; coding: utf-8 -*-
from PyInstaller.utils.hooks import collect_all, collect_dynamic_libs

# Spec 构建阶段：Analysis 分析依赖 → PYZ 打包模块 → EXE 生成启动程序
# → COLLECT 收集为 onedir。推荐命令：
# pyinstaller --clean --noconfirm --distpath dist_upx JMate.spec

# shiboken6 是 PySide6 的 Python/C++ 绑定层，需要显式收集动态库。
binaries = []
binaries += collect_dynamic_libs('shiboken6')

# 每项格式为：(源码路径, 打包后的相对目录)。三个源码包保留原目录结构，
# Azure 环境文件和默认业务配置模板放到应用资源根目录。
datas = [
    ('frontend', 'frontend'),
    ('shared', 'shared'),
    ('backend', 'backend'),
    ('azure.env', '.'),
    ('.attendance-config.json', '.'),
]

hiddenimports = [
    # Qt/Shiboken 模块可能由运行时机制加载，静态分析未必能完整发现。
    'shiboken6.Shiboken',
    'PySide6.QtCore',
    'PySide6.QtGui',
    'PySide6.QtWidgets',
    # attendance_config → crypto_service 使用 Fernet 处理密码字段。
    'cryptography',
    'cryptography.fernet',
]

# Agent Framework 的 Foundry/OpenAI 扩展包含动态导入，PyInstaller 静态分析
# 无法完整发现，因此显式收集三个包的数据文件、二进制和隐藏模块。
# collect_all 返回 datas、binaries、hiddenimports，并合并到 Analysis 输入。
for package in (
    'agent_framework',
    'agent_framework_foundry',
    'agent_framework_openai',
):
    package_datas, package_binaries, package_hiddenimports = collect_all(package)
    datas += package_datas
    binaries += package_binaries
    hiddenimports += package_hiddenimports


# 从统一入口 main.py 开始分析所有 Python 模块、动态库和资源。
a = Analysis(
    ['main.py'],
    # main.py 会配置项目根目录和 frontend 导入路径，无需额外 pathex。
    pathex=[],
    binaries=binaries,
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    # 只有确认模块未被运行时导入时，才应加入 excludes 缩减体积。
    excludes=[],
    noarchive=False,
    optimize=0,
)
# 将 Analysis 找到的纯 Python 模块组成 PYZ 归档。
pyz = PYZ(a.pure)

# 生成 JMate.exe 启动程序。onedir 模式不把 binaries/datas 直接嵌入 EXE，
# 而由下方 COLLECT 收集；exclude_binaries=True 是 onedir 的关键配置。
exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='JMate',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    # 对启动程序启用 UPX；下列敏感运行库保持未压缩状态。
    upx=True,
    upx_exclude=['python3.dll', 'python312.dll', 'Qt6Core.dll', 'Qt6Gui.dll', 'Qt6Widgets.dll', 'shiboken6.abi3.dll', 'Shiboken.pyd', 'VCRUNTIME140.dll', 'VCRUNTIME140_1.dll', 'MSVCP140.dll', 'api-ms-win-crt-*.dll'],
    runtime_tmpdir=None,
    # GUI 程序不显示控制台；运行日志由应用写入 logs/jmate.log。
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)

# onedir 模式：把主程序、Python/Qt 动态库、第三方包和项目资源收集到
# <distpath>/JMate/。使用推荐命令时即为 dist_upx/JMate/，其目录结构
# 与 JMateInstaller.iss 的 [Files] Source 一致。
coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    # COLLECT 阶段压缩目录内可安全处理的动态库。
    upx=True,
    # Python、Qt、Shiboken 和 VC Runtime 对压缩较敏感，排除后更稳定。
    upx_exclude=[
        'python3.dll',
        'python312.dll',
        'Qt6Core.dll',
        'Qt6Gui.dll',
        'Qt6Widgets.dll',
        'shiboken6.abi3.dll',
        'Shiboken.pyd',
        'VCRUNTIME140.dll',
        'VCRUNTIME140_1.dll',
        'MSVCP140.dll',
        'api-ms-win-crt-*.dll',
    ],
    name='JMate',
)
