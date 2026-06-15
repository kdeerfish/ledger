#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
随手记 CSV 导入工具
将所有业务逻辑委托给 ledger_modules/，本文件仅处理命令行参数和入口。
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import ledger_modules.db as db_module
import ledger_modules.transactions as tx_module
from ledger_modules.config import get_db_path

DB_PATH = get_db_path()


def main():
    if len(sys.argv) < 2:
        print("用法: python scripts/import_ledger.py <CSV文件路径>")
        print("示例: python scripts/import_ledger.py data/sample/mymoney_data.csv")
        sys.exit(1)

    csv_file = sys.argv[1]

    # 同步数据库路径
    db_module.DB_PATH = DB_PATH
    tx_module.DB_PATH = DB_PATH

    # 初始化 + 导入
    db_module.init_db()
    tx_module.import_csv(csv_file)


if __name__ == "__main__":
    main()
