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

# 排除不必要的模块以减小体积
excludes = [
    'tkinter',
    'matplotlib',
    'numpy',
    'scipy',
    'pandas',
    'IPython',
    'jupyter',
    'notebook',
    'sphinx',
    'pytest',
    'unittest',
    'doctest',
    'pdb',
    'profile',
    'cProfile',
    'pstats',
    'trace',
    'turtle',
    'xmlrpc',
    'email',
    'http',
    'urllib',
    'ftplib',
    'telnetlib',
    'smtplib',
    'poplib',
    'imaplib',
    'nntplib',
    'socketserver',
    'xml',
    'html',
    'cgi',
    'wsgiref',
    'multiprocessing',
    'concurrent',
    'asyncio',
    'selectors',
    'ssl',
    'hashlib',
    'hmac',
    'secrets',
    'cryptography',
    'PyQt6.QtNetwork',
    'PyQt6.QtSql',
    'PyQt6.QtTest',
    'PyQt6.QtXml',
    'PyQt6.QtXmlPatterns',
    'PyQt6.QtOpenGL',
    'PyQt6.QtOpenGLWidgets',
    'PyQt6.QtHelp',
    'PyQt6.QtDesigner',
    'PyQt6.QtUiTools',
    'PyQt6.QtMultimedia',
    'PyQt6.QtMultimediaWidgets',
    'PyQt6.QtBluetooth',
    'PyQt6.QtDBus',
    'PyQt6.QtLocation',
    'PyQt6.QtNfc',
    'PyQt6.QtPositioning',
    'PyQt6.QtQuick',
    'PyQt6.QtQuickWidgets',
    'PyQt6.QtQml',
    'PyQt6.QtWebChannel',
    'PyQt6.QtWebEngine',
    'PyQt6.QtWebEngineCore',
    'PyQt6.QtWebEngineWidgets',
    'PyQt6.QtWebSockets',
    'PyQt6.Qt3DCore',
    'PyQt6.Qt3DRender',
    'PyQt6.Qt3DInput',
    'PyQt6.Qt3DLogic',
    'PyQt6.Qt3DAnimation',
    'PyQt6.Qt3DExtras',
    'PyQt6.QtCharts',
    'PyQt6.QtDataVisualization',
    'PyQt6.QtPurchasing',
    'PyQt6.QtGamepad',
    'PyQt6.QtScxml',
    'PyQt6.QtRemoteObjects',
    'PyQt6.QtTextToSpeech',
    'PyQt6.QtWebView',
]

a = Analysis(
    ['Qdrop2name.py'],
    pathex=[],
    binaries=binaries,
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=excludes,
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
    strip=True,  # 启用strip以减小体积
    upx=True,    # 启用UPX压缩
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