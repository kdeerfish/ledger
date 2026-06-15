#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
配置管理模块 - 从环境变量和 .env 文件加载配置
优先级：系统环境变量 > .env 文件 > 默认值
"""

import os

# 项目根目录（自动检测）
ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# .env 文件路径
ENV_FILE = os.path.join(ROOT_DIR, '.env')


def load_env_file():
    """加载 .env 文件到 os.environ（如果存在）"""
    if not os.path.exists(ENV_FILE):
        return
    
    try:
        with open(ENV_FILE, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                # 跳过空行和注释
                if not line or line.startswith('#'):
                    continue
                # 解析 KEY=VALUE
                if '=' in line:
                    key, _, value = line.partition('=')
                    key = key.strip()
                    value = value.strip().strip('"').strip("'")
                    # 只在环境变量不存在时设置
                    if key and key not in os.environ:
                        os.environ[key] = value
    except Exception:
        pass  # .env 文件加载失败静默处理


def get_ledger_path():
    """获取 ledger 项目根目录"""
    load_env_file()
    path = os.environ.get('LEDGER_PATH', '').strip()
    if path and os.path.isdir(path):
        return path
    return ROOT_DIR


def get_db_path():
    """获取数据库路径"""
    load_env_file()
    db_path = os.environ.get('LEDGER_DB_PATH', '').strip()
    if db_path:
        # 如果是相对路径，基于项目根目录解析
        if not os.path.isabs(db_path):
            db_path = os.path.join(ROOT_DIR, db_path)
        # 确保目录存在
        db_dir = os.path.dirname(db_path)
        if db_dir and not os.path.exists(db_dir):
            os.makedirs(db_dir, exist_ok=True)
        return db_path
    # 默认：项目根目录下的 ledger.db
    return os.path.join(ROOT_DIR, 'ledger.db')


# 兼容旧代码：导出 DB_PATH
DB_PATH = get_db_path()

