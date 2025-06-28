# -*- mode: python ; coding: utf-8 -*-

import os
import sys
from PyInstaller.utils.hooks import collect_all, collect_data_files, collect_submodules

# 收集所有必要的模块和数据
datas = []
binaries = []
hiddenimports = []

# 收集PyQt6相关文件
pyqt6_datas, pyqt6_binaries, pyqt6_hiddenimports = collect_all('PyQt6')
datas.extend(pyqt6_datas)
binaries.extend(pyqt6_binaries)
hiddenimports.extend(pyqt6_hiddenimports)

# 收集PIL相关文件
pil_datas, pil_binaries, pil_hiddenimports = collect_all('PIL')
datas.extend(pil_datas)
binaries.extend(pil_binaries)
hiddenimports.extend(pil_hiddenimports)

# 收集其他依赖
for module in ['pillow_heif', 'exif']:
    module_datas, module_binaries, module_hiddenimports = collect_all(module)
    datas.extend(module_datas)
    binaries.extend(module_binaries)
    hiddenimports.extend(module_hiddenimports)

# 添加必要的隐藏导入
hiddenimports.extend([
    'pkgutil',
    'pkg_resources',
    'importlib',
    'importlib.metadata',
    'importlib.util',
    'importlib.abc',
    'importlib.machinery',
    'importlib.resources',
    'PyQt6.sip',
    'PyQt6.QtCore',
    'PyQt6.QtWidgets',
    'PyQt6.QtGui',
    'PyQt6.QtPrintSupport',
])

# 添加项目文件
datas.extend([
    ('icon.ico', '.'),
    ('settings.json', '.'),
    ('qt.conf', '.'),
    ('targets', 'targets'),
])

a = Analysis(
    ['Qdrop2name.py'],
    pathex=[],
    binaries=binaries,
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],  # 移除所有排除项，确保稳定性
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=None,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=None)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='Qdrop2name',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,  # 关闭strip以避免问题
    upx=False,    # 关闭UPX压缩以避免问题
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon='icon.ico',
) 