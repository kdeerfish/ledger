---
sidebar_position: 12
---

# 多套 AI 配置管理

聊天窗口的 AI 设置支持保存**多套配置**（不同的 Provider / Model / API Key），并在聊天过程中随时切换。

## 数据存储

所有配置持久化到 SQLite 的 `agent_configs` 表（用户层隔离：`user_id` 可空表示全局共享）。  
明文存储 API Key；不上云、不外发。

字段：

| 字段 | 说明 |
|------|------|
| `id` | 主键 |
| `user_id` | 归属用户（`NULL` 表示全局共享） |
| `name` | 配置备注名（如「日常-DeepSeek」） |
| `provider` | Provider ID（openai / claude / deepseek / qwen ...） |
| `model` | 模型名 |
| `base_url` | 可选，自定义 Base URL |
| `api_key` | 明文存储 |
| `system_prompt` | 可选，「其他 (高级)」里填的覆盖提示词；留空走默认 Ledger AI 提示词 |
| `is_default` | 同用户最多一条 `=1`（写入事务内清零旧默认） |
| `is_enabled` | 禁用后在下拉里灰显，仍可选中 |
| `created_at` / `updated_at` | 时间戳 |

## REST API

| Method | Path | 用途 |
|--------|------|------|
| `GET`    | `/api/agent/configs` | 列出当前用户配置（带 `default_id`） |
| `POST`   | `/api/agent/configs` | 新建一条配置 |
| `PUT`    | `/api/agent/configs/<id>` | 更新一条配置（越权返回 404） |
| `DELETE` | `/api/agent/configs/<id>` | 删除一条配置（越权返回 404） |
| `POST`   | `/api/agent/configs/<id>/set_default` | 设为该用户的默认 |

请求 / 响应均为标准 JSON 包装：`{"success": true, "data": {...}}` 或 `{"success": false, "error": "..."}`。

## 在 /chat 中使用

`/api/agent/chat` 与 `/api/agent/chat/stream` 都接受 `config_id`：

```bash
curl -X POST http://127.0.0.1:5800/api/agent/chat \
  -H 'Content-Type: application/json' \
  -d '{"message": "本月支出多少？", "config_id": 1}'
```

后端按 `config_id` 取配置覆盖请求里的 `config` 字段，再走原有 LLM 调用。  
不带 `config_id` 时仍兼容旧前端的内联 `config`（不推荐新代码使用）。

## 前端体验

- 聊天窗口 Header 左侧不再是固定的「AI 助手」，而是一个**配置徽章**，显示当前激活配置的备注名 + 下拉箭头。
- 点击徽章展开下拉，列出所有配置（默认项带 ★，禁用项灰显 + 「(禁用)」后缀），点选后立刻切换。
- 切换后浮出一条 2.2s 自动消失的 toast：「已切换到：xxx」。
- 齿轮图标打开完整管理弹窗：左侧列表 + 右侧编辑器，编辑器里提供「其他 (高级)」折叠区，包含：备注名 / 设为默认 / 启用 / System Prompt 覆盖。
