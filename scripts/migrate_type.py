#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
数据迁移脚本 - 将 type 字段从英文改为中文
将 'income' 改为 '收入'，将 'expense' 改为 '支出'
"""

import os
import sys
import sqlite3
from datetime import datetime

# 强制 UTF-8 输出（修复 Windows 编码问题）
if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')
    sys.stderr.reconfigure(encoding='utf-8', errors='replace')
    os.environ['PYTHONUTF8'] = '1'

# 添加项目根目录到 sys.path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from ledger_modules.config import get_db_path


def migrate_type_to_chinese(db_path=None, dry_run=False):
    """
    将数据库中的 type 字段从英文改为中文
    
    参数：
        db_path: 数据库路径，如果为 None 则使用默认路径
        dry_run: 如果为 True，只显示会修改的内容，不实际修改
    """
    if db_path is None:
        db_path = get_db_path()
    
    if not os.path.exists(db_path):
        print(f"❌ 数据库文件不存在: {db_path}")
        return False
    
    conn = sqlite3.connect(db_path)
    c = conn.cursor()
    
    # 检查需要迁移的记录
    c.execute("SELECT COUNT(*) FROM transactions WHERE type = 'income'")
    income_count = c.fetchone()[0]
    
    c.execute("SELECT COUNT(*) FROM transactions WHERE type = 'expense'")
    expense_count = c.fetchone()[0]
    
    total = income_count + expense_count
    
    if total == 0:
        print("✅ 数据库已经是中文类型，无需迁移")
        conn.close()
        return True
    
    print(f"📊 发现需要迁移的记录:")
    print(f"  - income (收入): {income_count} 条")
    print(f"  - expense (支出): {expense_count} 条")
    print(f"  - 总计: {total} 条")
    
    if dry_run:
        print("\n🔍 预览模式（不会实际修改）:")
        c.execute("SELECT id, type, amount, category, trans_date FROM transactions WHERE type IN ('income', 'expense') LIMIT 10")
        rows = c.fetchall()
        for row in rows:
            print(f"  ID={row[0]}: {row[1]} -> {'收入' if row[1] == 'income' else '支出'} | {row[2]:.2f} | {row[3]} | {row[4]}")
        if total > 10:
            print(f"  ... 还有 {total - 10} 条记录")
        conn.close()
        return True
    
    # 执行迁移
    print("\n🔄 开始迁移...")
    
    # 备份原数据（可选）
    backup_file = db_path + f".backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    print(f"📦 创建备份: {backup_file}")
    
    # 创建备份表
    c.execute("DROP TABLE IF EXISTS transactions_backup")
    c.execute("CREATE TABLE transactions_backup AS SELECT * FROM transactions")
    
    try:
        # 迁移 income -> 收入
        c.execute("UPDATE transactions SET type = '收入' WHERE type = 'income'")
        income_migrated = c.rowcount
        print(f"  ✅ 迁移 income -> 收入: {income_migrated} 条")
        
        # 迁移 expense -> 支出
        c.execute("UPDATE transactions SET type = '支出' WHERE type = 'expense'")
        expense_migrated = c.rowcount
        print(f"  ✅ 迁移 expense -> 支出: {expense_migrated} 条")
        
        conn.commit()
        
        # 验证迁移结果
        c.execute("SELECT COUNT(*) FROM transactions WHERE type IN ('income', 'expense')")
        remaining = c.fetchone()[0]
        
        if remaining == 0:
            print(f"\n🎉 迁移完成！共迁移 {income_migrated + expense_migrated} 条记录")
            
            # 清理备份表
            c.execute("DROP TABLE IF EXISTS transactions_backup")
            conn.commit()
            conn.close()
            return True
        else:
            print(f"\n⚠️ 迁移后仍有 {remaining} 条未迁移记录")
            conn.close()
            return False
            
    except Exception as e:
        print(f"\n❌ 迁移失败: {e}")
        print("🔄 尝试从备份恢复...")
        try:
            c.execute("DELETE FROM transactions")
            c.execute("INSERT INTO transactions SELECT * FROM transactions_backup")
            conn.commit()
            print("✅ 已从备份恢复")
        except Exception as restore_error:
            print(f"❌ 恢复失败: {restore_error}")
        conn.close()
        return False


def main():
    import argparse
    
    parser = argparse.ArgumentParser(description="迁移 type 字段从英文到中文")
    parser.add_argument("--db", help="数据库文件路径")
    parser.add_argument("--dry-run", action="store_true", help="预览模式，不实际修改")
    
    args = parser.parse_args()
    
    success = migrate_type_to_chinese(args.db, args.dry_run)
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
