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
        # Skills 文档（AI Agent 使用）
        ('skills', 'skills'),
    ],
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
        'ledger_modules.desktop_config',
        'web',
        'web.app',
        # 系统托盘
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
        # pywebview 不再需要
        'webview',
        'clr_loader',
        'pythonnet',
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
