# -*- mode: python ; coding: utf-8 -*-
"""
PyInstaller spec 文件 - Ledger 桌面应用打包配置
用法: pyinstaller ledger.spec
"""

import os
import sys

block_cipher = None

# 项目根目录
ROOT = os.path.abspath('.')

# ─── pywebview 需要的 DLL 搜索路径 ──────────────────────
# pywebview 在 Windows 上依赖 EdgeChromium (mshtml) 或 CEF
# PyInstaller 需要知道这些 DLL 的位置
webview_import_path = None
try:
    import webview
    webview_import_path = os.path.dirname(webview.__file__)
except ImportError:
    pass

a = Analysis(
    ['scripts/desktop_entry.py'],
    pathex=[ROOT],
    binaries=[],
    datas=[
        # 前端静态文件
        ('frontend/dist', 'frontend/dist'),
        # 设置窗口页面
        ('frontend/settings.html', 'frontend'),
        # 模块数据文件
        ('ledger_modules', 'ledger_modules'),
        # 项目配置
        ('pyproject.toml', '.'),
    ] + (
        # pywebview 数据文件（DLL、HTML 等）
        [(webview_import_path, 'webview')] if webview_import_path else []
    ),
    hiddenimports=[
        # Flask
        'flask',
        'flask_cors',
        'werkzeug.serving',
        'werkzeug.debug',
        # Ledger 模块
        'ledger_modules',
        'ledger_modules.db',
        'ledger_modules.config',
        'ledger_modules.transactions',
        'ledger_modules.budgets',
        'web',
        'web.app',
        # pywebview 及其平台后端
        'webview',
        'webview.platforms.edgechromium',
        'webview.platforms.mshtml',
        'webview.platforms.cef',
        'clr_loader',
        'pythonnet',
        # 桌面配置模块
        'scripts.webview_api',
        'ledger_modules.desktop_config',
        # 系统托盘 (可选 - 源码用 try/except 守护, 包内未安装 pystray 也能跑)
        'pystray',
        # 图标处理（托盘图标需要）
        'PIL', 'PIL.Image', 'PIL.ImageDraw',
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[
        'tkinter', 'matplotlib', 'numpy', 'pandas',
        'scipy', 'cv2', 'torch',
        'PyQt5', 'PyQt6', 'PySide2', 'PySide6',
        'pytest', 'coverage',
    ],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='ledger',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,  # 桌面应用：不显示控制台窗口
    icon=None,  # 可以后续添加 .ico 图标
    # 管理员权限提示（UAC）- 可选
    # uac_admin=True,
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='ledger',
)
