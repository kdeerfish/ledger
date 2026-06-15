#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
配置管理模块 - 统一管理所有配置项
"""

import os
import json

# 项目根目录（自动检测）
ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# 配置文件路径
CONFIG_FILE = os.path.join(ROOT_DIR, 'config.json')


def load_config():
    """加载配置文件"""
    if not os.path.exists(CONFIG_FILE):
        return get_default_config()
    
    try:
        with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
            config = json.load(f)
        return config
    except Exception as e:
        print(f"⚠️ 加载配置文件失败: {e}，使用默认配置")
        return get_default_config()


def get_default_config():
    """获取默认配置"""
    return {
        "database": {
            "name": "ledger.db"
        },
        "defaults": {
            "currency": "CNY",
            "language": "zh",
            "date_format": "%Y-%m-%d %H:%M:%S"
        },
        "categories": {
            "expense": [
                "食品酒水", "居家物业", "行车交通", "服饰饰品",
                "医疗保健", "休闲娱乐", "交流通讯", "学习进修",
                "人情往来", "其他杂项", "金融保险", "自由职业",
                "外贸电商", "项目投入"
            ],
            "income": [
                "职业收入", "其他收入"
            ]
        },
        "members": ["本人", "fish", "妈妈", "家庭公用"]
    }


def get_db_path():
    """获取数据库路径（相对于项目根目录）"""
    config = load_config()
    db_name = config.get('database', {}).get('name', 'ledger.db')
    return os.path.join(ROOT_DIR, db_name)


def get_root_dir():
    """获取项目根目录"""
    return ROOT_DIR


def get_config():
    """获取完整配置"""
    return load_config()


def get_categories(category_type=None):
    """获取类别列表"""
    config = load_config()
    categories = config.get('categories', {})
    if category_type:
        return categories.get(category_type, [])
    return categories


def get_members():
    """获取成员列表"""
    config = load_config()
    return config.get('members', [])


def get_defaults():
    """获取默认设置"""
    config = load_config()
    return config.get('defaults', {})


# 兼容旧代码：导出 DB_PATH
DB_PATH = get_db_path()
