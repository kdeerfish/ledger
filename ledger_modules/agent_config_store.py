#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Agent 多套配置的数据访问层。

配置按 user_id 隔离（user_id 为 NULL 表示全局共享）。
明文存储 API Key；不进行加密。
"""

import sqlite3
from typing import Optional, List, Dict, Any

from .config import get_db_path


DB_PATH = get_db_path()


def _connect():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def _row_to_dict(row: sqlite3.Row) -> Dict[str, Any]:
    return {
        "id": row["id"],
        "user_id": row["user_id"],
        "name": row["name"],
        "provider": row["provider"],
        "model": row["model"],
        "base_url": row["base_url"],
        "api_key": row["api_key"],
        "system_prompt": row["system_prompt"],
        "is_default": bool(row["is_default"]),
        "is_enabled": bool(row["is_enabled"]),
        "created_at": row["created_at"],
        "updated_at": row["updated_at"],
    }


def list_configs(user_id: Optional[int] = None) -> List[Dict[str, Any]]:
    """列出某用户的所有 agent 配置。

    user_id 为 None 时返回 user_id IS NULL 的全局配置。
    """
    conn = _connect()
    try:
        if user_id is None:
            cur = conn.execute(
                "SELECT * FROM agent_configs WHERE user_id IS NULL "
                "ORDER BY is_default DESC, updated_at DESC"
            )
        else:
            cur = conn.execute(
                "SELECT * FROM agent_configs WHERE user_id = ? "
                "ORDER BY is_default DESC, updated_at DESC",
                (user_id,),
            )
        return [_row_to_dict(r) for r in cur.fetchall()]
    finally:
        conn.close()


def get_config(config_id: int, user_id: Optional[int] = None) -> Optional[Dict[str, Any]]:
    """按 id 取一条配置；带 user_id 校验时充当权限边界。"""
    conn = _connect()
    try:
        if user_id is None:
            cur = conn.execute(
                "SELECT * FROM agent_configs WHERE id = ? AND user_id IS NULL",
                (config_id,),
            )
        else:
            cur = conn.execute(
                "SELECT * FROM agent_configs WHERE id = ? AND user_id = ?",
                (config_id, user_id),
            )
        row = cur.fetchone()
        return _row_to_dict(row) if row else None
    finally:
        conn.close()


def get_default_config(user_id: Optional[int] = None) -> Optional[Dict[str, Any]]:
    """取默认配置；若无标记则取最近更新的一条。"""
    conn = _connect()
    try:
        if user_id is None:
            cur = conn.execute(
                "SELECT * FROM agent_configs WHERE user_id IS NULL AND is_default = 1 "
                "ORDER BY updated_at DESC LIMIT 1"
            )
        else:
            cur = conn.execute(
                "SELECT * FROM agent_configs WHERE user_id = ? AND is_default = 1 "
                "ORDER BY updated_at DESC LIMIT 1",
                (user_id,),
            )
        row = cur.fetchone()
        if row:
            return _row_to_dict(row)

        if user_id is None:
            cur = conn.execute(
                "SELECT * FROM agent_configs WHERE user_id IS NULL AND is_enabled = 1 "
                "ORDER BY updated_at DESC, id DESC LIMIT 1"
            )
        else:
            cur = conn.execute(
                "SELECT * FROM agent_configs WHERE user_id = ? AND is_enabled = 1 "
                "ORDER BY updated_at DESC, id DESC LIMIT 1",
                (user_id,),
            )
        row = cur.fetchone()
        return _row_to_dict(row) if row else None
    finally:
        conn.close()


def create_config(
    user_id: Optional[int],
    name: str,
    provider: str,
    model: str,
    base_url: Optional[str] = None,
    api_key: Optional[str] = None,
    system_prompt: Optional[str] = None,
    is_default: bool = False,
    is_enabled: bool = True,
) -> Dict[str, Any]:
    """新增一条配置。"""
    conn = _connect()
    try:
        cur = conn.execute(
            """INSERT INTO agent_configs
               (user_id, name, provider, model, base_url, api_key,
                system_prompt, is_default, is_enabled)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (
                user_id,
                name,
                provider,
                model,
                base_url,
                api_key,
                system_prompt,
                1 if is_default else 0,
                1 if is_enabled else 0,
            ),
        )
        new_id = cur.lastrowid
        if is_default:
            _clear_other_defaults_in_tx(conn, user_id, new_id)
        conn.commit()
        row = conn.execute("SELECT * FROM agent_configs WHERE id = ?", (new_id,)).fetchone()
        return _row_to_dict(row)
    finally:
        conn.close()


def update_config(
    config_id: int,
    user_id: Optional[int],
    name: str,
    provider: str,
    model: str,
    base_url: Optional[str] = None,
    api_key: Optional[str] = None,
    system_prompt: Optional[str] = None,
    is_default: bool = False,
    is_enabled: bool = True,
) -> Optional[Dict[str, Any]]:
    """更新一条配置。返回更新后的行；不存在或越权时返回 None。"""
    conn = _connect()
    try:
        if user_id is None:
            existing = conn.execute(
                "SELECT id FROM agent_configs WHERE id = ? AND user_id IS NULL",
                (config_id,),
            ).fetchone()
        else:
            existing = conn.execute(
                "SELECT id FROM agent_configs WHERE id = ? AND user_id = ?",
                (config_id, user_id),
            ).fetchone()
        if not existing:
            return None

        conn.execute(
            """UPDATE agent_configs
               SET name = ?, provider = ?, model = ?, base_url = ?, api_key = ?,
                   system_prompt = ?, is_default = ?, is_enabled = ?,
                   updated_at = datetime('now', 'localtime')
               WHERE id = ?""",
            (
                name,
                provider,
                model,
                base_url,
                api_key,
                system_prompt,
                1 if is_default else 0,
                1 if is_enabled else 0,
                config_id,
            ),
        )
        if is_default:
            _clear_other_defaults_in_tx(conn, user_id, config_id)
        conn.commit()

        row = conn.execute("SELECT * FROM agent_configs WHERE id = ?", (config_id,)).fetchone()
        return _row_to_dict(row) if row else None
    finally:
        conn.close()


def delete_config(config_id: int, user_id: Optional[int]) -> bool:
    """删除一条配置；越权返回 False。"""
    conn = _connect()
    try:
        if user_id is None:
            cur = conn.execute(
                "DELETE FROM agent_configs WHERE id = ? AND user_id IS NULL",
                (config_id,),
            )
        else:
            cur = conn.execute(
                "DELETE FROM agent_configs WHERE id = ? AND user_id = ?",
                (config_id, user_id),
            )
        conn.commit()
        return cur.rowcount > 0
    finally:
        conn.close()


def set_default(config_id: int, user_id: Optional[int]) -> Optional[Dict[str, Any]]:
    """把指定配置设为该用户的默认；同事务内清空其它默认。"""
    conn = _connect()
    try:
        if user_id is None:
            existing = conn.execute(
                "SELECT id FROM agent_configs WHERE id = ? AND user_id IS NULL",
                (config_id,),
            ).fetchone()
        else:
            existing = conn.execute(
                "SELECT id FROM agent_configs WHERE id = ? AND user_id = ?",
                (config_id, user_id),
            ).fetchone()
        if not existing:
            return None

        conn.execute(
            "UPDATE agent_configs SET is_default = 0, updated_at = datetime('now', 'localtime') "
            "WHERE id != ? AND " + ("user_id IS NULL" if user_id is None else "user_id = ?"),
            (config_id,) if user_id is None else (config_id, user_id),
        )
        conn.execute(
            "UPDATE agent_configs SET is_default = 1, updated_at = datetime('now', 'localtime') "
            "WHERE id = ?",
            (config_id,),
        )
        conn.commit()
        row = conn.execute("SELECT * FROM agent_configs WHERE id = ?", (config_id,)).fetchone()
        return _row_to_dict(row) if row else None
    finally:
        conn.close()


def _clear_other_defaults_in_tx(conn: sqlite3.Connection, user_id: Optional[int], keep_id: int) -> None:
    """同事务内把同一用户其他行的 is_default 清零（每用户唯一默认）。"""
    if user_id is None:
        conn.execute(
            "UPDATE agent_configs SET is_default = 0 WHERE id != ? AND user_id IS NULL",
            (keep_id,),
        )
    else:
        conn.execute(
            "UPDATE agent_configs SET is_default = 0 WHERE id != ? AND user_id = ?",
            (keep_id, user_id),
        )
