#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Agent API Routes"""

import asyncio
import json
import os
from flask import request, jsonify
import httpx


def _load_providers_config():
    """从配置文件加载 provider 配置，如果文件不存在则返回空字典"""
    config_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'ledger_modules', 'providers_config.json')
    try:
        with open(config_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
            return data.get('providers', {})
    except Exception as e:
        print(f"[Agent] Failed to load providers config: {e}")
        return {}


# 从配置文件加载 provider 配置
PROVIDERS_CONFIG = _load_providers_config()


def register_agent_routes(app, api_error, api_success, sync_db_path, db_module):
    """Register Agent API routes"""
    import ledger_modules.agent as agent_module
    import ledger_modules.agent_config_store as config_store
    from flask import Response, stream_with_context
    import json as json_module
    import os

    def current_user_id():
        """从 Flask session/请求上下文取当前用户 ID；无用户体系时返回 None（视为全局共享）。

        留作未来接入登录时扩展，目前统一返回 None。
        """
        try:
            from flask import session
            uid = session.get("user_id")
            return int(uid) if uid is not None else None
        except Exception:
            return None

    def _load_config_override(config_id, user_id):
        """从数据库按 id 取一条配置；用于在 /chat 里覆盖请求直传的 config。

        返回 dict(provider/api_key/model/base_url/system_prompt) 或 None（找不到 / 越权）。
        """
        if not config_id:
            return None
        try:
            cid = int(config_id)
        except (TypeError, ValueError):
            return None
        row = config_store.get_config(cid, user_id)
        if not row:
            return None
        return {
            "provider": row["provider"],
            "api_key": row["api_key"] or "",
            "model": row["model"],
            "base_url": row["base_url"] or "",
            "system_prompt": row["system_prompt"] or "",
        }


    def load_skills_content():
        """加载Skills文档内容"""
        skills_content = []
        
        # 查找skills目录
        skills_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'skills')
        if not os.path.exists(skills_dir):
            return ""
        
        # 遍历所有skill目录
        for skill_name in os.listdir(skills_dir):
            skill_dir = os.path.join(skills_dir, skill_name)
            skill_md = os.path.join(skill_dir, 'SKILL.md')
            
            if os.path.isfile(skill_md):
                try:
                    with open(skill_md, 'r', encoding='utf-8') as f:
                        content = f.read()
                        # 移除YAML front matter
                        if content.startswith('---'):
                            end_idx = content.find('---', 3)
                            if end_idx != -1:
                                content = content[end_idx + 3:].strip()
                        skills_content.append(f"## Skill: {skill_name}\n\n{content}")
                except Exception as e:
                    print(f"[Agent] Failed to load skill {skill_name}: {e}")
                
                # 加载references目录
                refs_dir = os.path.join(skill_dir, 'references')
                if os.path.isdir(refs_dir):
                    for ref_file in os.listdir(refs_dir):
                        if ref_file.endswith('.md'):
                            ref_path = os.path.join(refs_dir, ref_file)
                            try:
                                with open(ref_path, 'r', encoding='utf-8') as f:
                                    ref_content = f.read()
                                    ref_name = ref_file.replace('.md', '')
                                    skills_content.append(f"### Reference: {ref_name}\n\n{ref_content}")
                            except Exception as e:
                                print(f"[Agent] Failed to load reference {ref_file}: {e}")
        
        return "\n\n---\n\n".join(skills_content)
    
    def sse_event(event_type, data):
        """格式化SSE事件"""
        return f"event: {event_type}\ndata: {json_module.dumps(data, ensure_ascii=False)}\n\n"
    
    @app.route("/api/agent/providers", methods=["GET"])
    def agent_providers():
        providers = []
        for pid, cfg in PROVIDERS_CONFIG.items():
            providers.append({
                "id": pid,
                "name": cfg["name"],
                "models": cfg["models"]
            })
        return api_success(providers)
    
    @app.route("/api/agent/fetch_models", methods=["POST"])
    def agent_fetch_models():
        data = request.get_json(silent=True) or {}
        provider = data.get("provider", "")
        api_key = (data.get("api_key") or "").strip()
        base_url = (data.get("base_url") or "").strip()
        
        cfg = PROVIDERS_CONFIG.get(provider)
        if not cfg:
            return api_error("Unknown provider")
        
        url = base_url or cfg["default_base_url"]
        if not url:
            return api_error("Provider requires Base URL")
        
        models_url = url.rstrip("/") + cfg["models_url"]
        
        headers = {}
        if cfg["api_style"] == "claude":
            headers["x-api-key"] = api_key
            headers["anthropic-version"] = "2023-06-01"
        else:
            auth_val = (cfg["auth_prefix"] + api_key) if api_key else cfg["auth_prefix"].rstrip() or "ollama"
            headers[cfg["auth_header"]] = auth_val
        
        try:
            with httpx.Client(timeout=15.0) as client:
                resp = client.get(models_url, headers=headers)
                if resp.status_code == 200:
                    result = resp.json()
                    models = []
                    if cfg["api_style"] == "claude":
                        for m in result.get("data", []):
                            models.append(m.get("id", ""))
                    else:
                        for m in result.get("data", []):
                            mid = m.get("id", "")
                            if mid:
                                models.append(mid)
                    return api_success({"models": models, "source": "live"})
                else:
                    return api_error(f"API returned {resp.status_code}")
        except Exception as e:
            return api_error(f"Failed: {str(e)}")
    
    @app.route("/api/agent/chat", methods=["POST"])
    def agent_chat():
        sync_db_path()
        data = request.get_json(silent=True)
        if not data:
            return api_error("Empty request")

        message = (data.get("message") or "").strip()
        if not message:
            return api_error("Empty message")

        config = data.get("config") or {}
        history = data.get("history") or []

        # 优先按 config_id 从数据库取配置；找不到 / 越权时回退到请求直传的 config（兼容旧前端）
        config_id = data.get("config_id")
        user_id = current_user_id()
        if config_id:
            override = _load_config_override(config_id, user_id)
            if not override:
                return api_error("Config not found or no permission")
            config = {**config, **override}

        if not config:
            return api_error("Please configure AI first")
        
        if not agent_module.agent_service.load_config(config):
            return api_error("Failed to load config")
        
        provider = config.get("provider", "openai")
        provider_names = {
            "openai": "OpenAI", "claude": "Claude", "deepseek": "DeepSeek",
            "qwen": "Qwen", "wenxin": "Wenxin", "glm": "GLM",
            "moonshot": "Kimi", "hunyuan": "Hunyuan", "spark": "Spark",
            "doubao": "Doubao", "minimax": "MiniMax", "ollama": "Ollama", "custom": "Custom"
        }
        
        # 加载Skills文档
        skills_content = load_skills_content()
        
        system_prompt = f"""你是 Ledger 记账助手，专注于个人财务管理。

## 核心职责

你只回答与记账相关的问题。包括：
- **记账**：记录收入、支出
- **查账**：查询交易记录、搜索商家/类别
- **统计**：收支汇总、类别分析、趋势图表
- **预算**：设置预算、查看预算执行情况
- **导入导出**：CSV数据导入导出
- **帮助**：使用指南、功能说明

## 意图识别规则

1. **识别意图**：首先判断用户问题是否与记账相关
2. **相关问题**：执行相应操作，使用工具或API
3. **无关问题**：礼貌拒绝，说明你只负责记账

## 无关问题回复模板

当用户问与记账无关的问题时，回复：
"抱歉，我是记账助手，只负责帮您管理个人财务。您可以：
- 记一笔账：如「午餐30元」
- 查看账单：如「这个月花了多少」
- 统计分析：如「各类别支出占比」
- 预算管理：如「设置本月预算」"

## 可用工具

1. **内置工具**：query_transactions, add_transaction, query_budgets, get_statistics
2. **HTTP API**：通过 curl 调用 Ledger REST API（详见下方 Skills 文档）

## 查询交易记录重要说明

query_transactions 工具支持两种查询方式：
1. **按月查询**：传 month 参数（如 "2026-06"）
2. **按日期范围查询**：传 start_date 和 end_date 参数（如 "2026-06-22", "2026-06-24"）

当用户问「这两天」「最近几天」「6月22到24号」等具体日期时，**必须使用 start_date/end_date 参数**，不要用 month 参数！

示例：
- 用户问「这两天花了多少」→ start_date="2026-06-22", end_date="2026-06-24"
- 用户问「这个月花了多少」→ month="2026-06"
- 用户问「上周五到周日」→ 计算具体日期后用 start_date/end_date

## 类型参数说明

type 参数只能是以下两个值：
- **支出**：表示花费、消费
- **收入**：表示进账、收款

不要使用英文（expense/income），必须使用中文！

## Skills 文档

{skills_content if skills_content else "（未找到 Skills 文档，请使用内置工具）"}

## 调用规范

1. 记账、查账、统计、预算操作时，优先使用 Skills 文档中的 HTTP API
2. 使用 curl 调用 API 时，BASE_URL 默认为 http://127.0.0.1:5800
3. 所有 API 返回 JSON 格式：{{"success": true, "data": {{...}}}} 或 {{"success": false, "error": "..."}}
4. 回复使用中文，简洁明了
5. 不确定是否记账相关时，默认按记账相关处理

## 当前日期

{__import__("datetime").datetime.now().strftime("%Y-%m-%d")}
"""
        
        messages = [{"role": "system", "content": system_prompt}]
        for h in history[-6:]:
            if h.get("role") in ("user", "assistant") and h.get("content"):
                if h["content"] != "Thinking...":
                    messages.append({"role": h["role"], "content": h["content"]})
        messages.append({"role": "user", "content": message})
        
        try:
            print(f"[AgentChat] Provider: {provider}, Model: {config.get('model')}, Base URL: {config.get('base_url')}")
            print(f"[AgentChat] Sending {len(messages)} messages to API")
            
            response = asyncio.run(agent_module.agent_service.chat(messages))
            
            print(f"[AgentChat] API response keys: {list(response.keys()) if isinstance(response, dict) else type(response)}")
            if isinstance(response, dict) and 'choices' in response:
                print(f"[AgentChat] Choices count: {len(response.get('choices', []))}")
                if response.get('choices'):
                    msg = response['choices'][0].get('message', {})
                    print(f"[AgentChat] Message content length: {len(msg.get('content', '') or '')}")
                    print(f"[AgentChat] Has tool_calls: {bool(msg.get('tool_calls'))}")
            
            if provider == "claude":
                content = ""
                if response.get("content"):
                    for block in response["content"]:
                        if block.get("type") == "text":
                            content += block.get("text", "")
                print(f"[AgentChat] Claude response content length: {len(content)}")
                return api_success({"response": content or "OK"})
            
            if response.get("choices") and response["choices"][0].get("message", {}).get("tool_calls"):
                tool_calls = response["choices"][0]["message"]["tool_calls"]
                return api_success({
                    "response": response["choices"][0]["message"].get("content") or "Processing...",
                    "tool_calls": tool_calls
                })
            
            msg = response.get("choices", [{}])[0].get("message", {})
            result_content = msg.get("content", "")
            print(f"[AgentChat] Final response content: '{result_content[:100]}...' " if len(result_content) > 100 else f"[AgentChat] Final response content: '{result_content}'")
            return api_success({"response": result_content})
        except Exception as e:
            import traceback
            print(f"[AgentChat] Error: {str(e)}")
            print(f"[AgentChat] Traceback: {traceback.format_exc()}")
            return api_error(f"Failed: {str(e)}")
    
    @app.route("/api/agent/chat/stream", methods=["POST"])
    def agent_chat_stream():
        sync_db_path()
        data = request.get_json(silent=True)
        if not data:
            return api_error("Empty request")

        message = (data.get("message") or "").strip()
        if not message:
            return api_error("Empty message")

        config = data.get("config") or {}
        history = data.get("history") or []

        # 优先按 config_id 从数据库取配置；找不到 / 越权时回退到请求直传的 config
        config_id = data.get("config_id")
        user_id = current_user_id()
        if config_id:
            override = _load_config_override(config_id, user_id)
            if not override:
                return api_error("Config not found or no permission")
            config = {**config, **override}

        if not config:
            return api_error("Please configure AI first")
        
        if not agent_module.agent_service.load_config(config):
            return api_error("Failed to load config")
        
        provider = config.get("provider", "openai")
        provider_names = {
            "openai": "OpenAI", "claude": "Claude", "deepseek": "DeepSeek",
            "qwen": "Qwen", "wenxin": "Wenxin", "glm": "GLM",
            "moonshot": "Kimi", "hunyuan": "Hunyuan", "spark": "Spark",
            "doubao": "Doubao", "minimax": "MiniMax", "ollama": "Ollama", "custom": "Custom"
        }
        
        # 加载Skills文档
        skills_content = load_skills_content()
        
        system_prompt = f"""你是 Ledger 记账助手，专注于个人财务管理。

## 核心职责

你只回答与记账相关的问题。包括：
- **记账**：记录收入、支出
- **查账**：查询交易记录、搜索商家/类别
- **统计**：收支汇总、类别分析、趋势图表
- **预算**：设置预算、查看预算执行情况
- **导入导出**：CSV数据导入导出
- **帮助**：使用指南、功能说明

## 意图识别规则

1. **识别意图**：首先判断用户问题是否与记账相关
2. **相关问题**：执行相应操作，使用工具或API
3. **无关问题**：礼貌拒绝，说明你只负责记账

## 无关问题回复模板

当用户问与记账无关的问题时，回复：
"抱歉，我是记账助手，只负责帮您管理个人财务。您可以：
- 记一笔账：如「午餐30元」
- 查看账单：如「这个月花了多少」
- 统计分析：如「各类别支出占比」
- 预算管理：如「设置本月预算」"

## 可用工具

1. **内置工具**：query_transactions, add_transaction, query_budgets, get_statistics
2. **HTTP API**：通过 curl 调用 Ledger REST API（详见下方 Skills 文档）

## 查询交易记录重要说明

query_transactions 工具支持两种查询方式：
1. **按月查询**：传 month 参数（如 "2026-06"）
2. **按日期范围查询**：传 start_date 和 end_date 参数（如 "2026-06-22", "2026-06-24"）

当用户问「这两天」「最近几天」「6月22到24号」等具体日期时，**必须使用 start_date/end_date 参数**，不要用 month 参数！

示例：
- 用户问「这两天花了多少」→ start_date="2026-06-22", end_date="2026-06-24"
- 用户问「这个月花了多少」→ month="2026-06"
- 用户问「上周五到周日」→ 计算具体日期后用 start_date/end_date

## 类型参数说明

type 参数只能是以下两个值：
- **支出**：表示花费、消费
- **收入**：表示进账、收款

不要使用英文（expense/income），必须使用中文！

## Skills 文档

{skills_content if skills_content else "（未找到 Skills 文档，请使用内置工具）"}

## 调用规范

1. 记账、查账、统计、预算操作时，优先使用 Skills 文档中的 HTTP API
2. 使用 curl 调用 API 时，BASE_URL 默认为 http://127.0.0.1:5800
3. 所有 API 返回 JSON 格式：{{"success": true, "data": {{...}}}} 或 {{"success": false, "error": "..."}}
4. 回复使用中文，简洁明了
5. 不确定是否记账相关时，默认按记账相关处理

## 当前日期

{__import__("datetime").datetime.now().strftime("%Y-%m-%d")}
"""
        
        messages = [{"role": "system", "content": system_prompt}]
        for h in history[-6:]:
            if h.get("role") in ("user", "assistant") and h.get("content"):
                if h["content"] != "思考中...":
                    messages.append({"role": h["role"], "content": h["content"]})
        messages.append({"role": "user", "content": message})
        
        def generate():
            try:
                # 发送开始事件
                yield sse_event("start", {"message": "开始思考..."})
                
                # 调用流式API
                import asyncio
                
                async def stream_chat():
                    full_response = ""
                    async for chunk in agent_module.agent_service.chat_stream(messages):
                        if chunk.get("type") == "thinking":
                            yield sse_event("thinking", {"content": chunk["content"]})
                        elif chunk.get("type") == "content":
                            full_response += chunk["content"]
                            yield sse_event("content", {"content": chunk["content"]})
                        elif chunk.get("type") == "tool_call":
                            yield sse_event("tool_call", chunk)
                        elif chunk.get("type") == "tool_result":
                            yield sse_event("tool_result", chunk)
                        elif chunk.get("type") == "done":
                            yield sse_event("done", {"full_response": full_response})
                            return
                
                # 运行异步生成器
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                async_gen = stream_chat()
                
                try:
                    while True:
                        try:
                            event = loop.run_until_complete(async_gen.__anext__())
                            yield event
                        except StopAsyncIteration:
                            break
                finally:
                    loop.close()
                    
            except Exception as e:
                import traceback
                print(f"[AgentChat Stream] Error: {str(e)}")
                print(f"[AgentChat Stream] Traceback: {traceback.format_exc()}")
                yield sse_event("error", {"message": str(e)})
        
        return Response(
            stream_with_context(generate()),
            mimetype='text/event-stream',
            headers={
                'Cache-Control': 'no-cache',
                'Connection': 'keep-alive',
                'X-Accel-Buffering': 'no'
            }
        )
    
    @app.route("/api/agent/configs", methods=["GET"])
    def list_agent_configs():
        sync_db_path()
        uid = current_user_id()
        rows = config_store.list_configs(uid)
        default_row = config_store.get_default_config(uid)
        return api_success({
            "configs": rows,
            "default_id": default_row["id"] if default_row else None,
        })

    @app.route("/api/agent/configs", methods=["POST"])
    def create_agent_config():
        sync_db_path()
        data = request.get_json(silent=True) or {}
        name = (data.get("name") or "").strip()
        provider = (data.get("provider") or "").strip()
        model = (data.get("model") or "").strip()
        if not name:
            return api_error("name required")
        if not provider:
            return api_error("provider required")
        if not model:
            return api_error("model required")
        uid = current_user_id()
        try:
            row = config_store.create_config(
                user_id=uid,
                name=name,
                provider=provider,
                model=model,
                base_url=(data.get("base_url") or None),
                api_key=(data.get("api_key") or None),
                system_prompt=(data.get("system_prompt") or None),
                is_default=bool(data.get("is_default", False)),
                is_enabled=bool(data.get("is_enabled", True)),
            )
        except Exception as e:
            return api_error(f"Create failed: {e}")
        return api_success(row)

    @app.route("/api/agent/configs/<int:config_id>", methods=["PUT"])
    def update_agent_config(config_id):
        sync_db_path()
        data = request.get_json(silent=True) or {}
        name = (data.get("name") or "").strip()
        provider = (data.get("provider") or "").strip()
        model = (data.get("model") or "").strip()
        if not name or not provider or not model:
            return api_error("name / provider / model required")
        uid = current_user_id()
        try:
            row = config_store.update_config(
                config_id=config_id,
                user_id=uid,
                name=name,
                provider=provider,
                model=model,
                base_url=(data.get("base_url") or None),
                api_key=(data.get("api_key") or None),
                system_prompt=(data.get("system_prompt") or None),
                is_default=bool(data.get("is_default", False)),
                is_enabled=bool(data.get("is_enabled", True)),
            )
        except Exception as e:
            return api_error(f"Update failed: {e}")
        if not row:
            return api_error("Config not found or no permission")
        return api_success(row)

    @app.route("/api/agent/configs/<int:config_id>", methods=["DELETE"])
    def delete_agent_config(config_id):
        sync_db_path()
        uid = current_user_id()
        ok = config_store.delete_config(config_id, uid)
        if not ok:
            return api_error("Config not found or no permission")
        return api_success({"deleted": config_id})

    @app.route("/api/agent/configs/<int:config_id>/set_default", methods=["POST"])
    def set_default_agent_config(config_id):
        sync_db_path()
        uid = current_user_id()
        row = config_store.set_default(config_id, uid)
        if not row:
            return api_error("Config not found or no permission")
        return api_success(row)

    @app.route("/api/agent/config", methods=["POST"])
    def save_agent_config():
        """旧版单条配置保存端点（保留以兼容旧前端；写入全局默认）。"""
        sync_db_path()
        data = request.get_json(silent=True) or {}
        provider = (data.get("provider") or "").strip()
        model = (data.get("model") or "").strip()
        if not provider or not model:
            return api_error("provider / model required")
        uid = current_user_id()
        name = (data.get("name") or f"{provider}/{model}").strip()
        try:
            row = config_store.create_config(
                user_id=uid,
                name=name,
                provider=provider,
                model=model,
                base_url=(data.get("base_url") or None),
                api_key=(data.get("api_key") or None),
                is_default=True,
                is_enabled=True,
            )
        except Exception as e:
            return api_error(f"Save failed: {e}")
        return api_success({"message": "Config saved", "config": row})
