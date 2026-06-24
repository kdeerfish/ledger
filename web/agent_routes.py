#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Agent API Routes"""

import asyncio
import json
import os
from flask import request, jsonify
import httpx


# Provider configuration - latest models
# 中国厂商优先，分组顺序：国内 → 国际 → 自定义
# 有国内/海外双版本的厂商已分开：
#   - 智谱AI (国内) / Z.AI (海外 GLM)
#   - 通义千问 (国内百炼) / Qwen (国际 ModelScope/DashScope Intl)
#   - 文心一言 (国内千帆) / 暂不分离
#   - 豆包 (国内火山引擎) / 暂不分离
PROVIDERS_CONFIG = {
    # ===== 国内厂商 =====
    'deepseek': {
        'name': 'DeepSeek (深度求索)', 'api_style': 'openai',
        'default_base_url': 'https://api.deepseek.com/v1', 'models_url': '/models',
        'auth_header': 'Authorization', 'auth_prefix': 'Bearer ',
        'models': ['deepseek-chat', 'deepseek-reasoner', 'deepseek-coder', 'deepseek-v3']
    },
    'qwen_cn': {
        'name': '通义千问 Qwen-CN (阿里百炼-国内)', 'api_style': 'openai',
        'default_base_url': 'https://dashscope.aliyuncs.com/compatible-mode/v1', 'models_url': '/models',
        'auth_header': 'Authorization', 'auth_prefix': 'Bearer ',
        'models': [
            'qwen-max', 'qwen-plus', 'qwen-turbo', 'qwen-long',
            'qwen3-max', 'qwen3-plus', 'qwen3-235b-a22b',
            'qwen2.5-72b-instruct', 'qwen2.5-32b-instruct', 'qwen2.5-14b-instruct', 'qwen2.5-7b-instruct',
            'qwen-coder-plus', 'qwen-vl-max', 'qwen-vl-plus'
        ]
    },
    'qwen_global': {
        'name': '通义千问 Qwen-Global (阿里百炼-国际)', 'api_style': 'openai',
        'default_base_url': 'https://dashscope-intl.aliyuncs.com/compatible-mode/v1', 'models_url': '/models',
        'auth_header': 'Authorization', 'auth_prefix': 'Bearer ',
        'models': [
            'qwen-max', 'qwen-plus', 'qwen-turbo', 'qwen-long',
            'qwen3-max', 'qwen3-plus', 'qwen3-235b-a22b',
            'qwen2.5-72b-instruct', 'qwen2.5-32b-instruct',
            'qwen-coder-plus', 'qwen-vl-max', 'qwen-vl-plus'
        ]
    },
    'wenxin': {
        'name': '文心一言 (百度千帆-国内)', 'api_style': 'openai',
        'default_base_url': 'https://qianfan.baidubce.com/v2', 'models_url': '/models',
        'auth_header': 'Authorization', 'auth_prefix': 'Bearer ',
        'models': [
            'ernie-4.5-8k', 'ernie-4.5-turbo-128k', 'ernie-4.0-turbo-8k', 'ernie-4.0-8k',
            'ernie-3.5-8k', 'ernie-3.5-128k', 'ernie-speed-pro-128k',
            'ernie-lite-8k', 'ernie-tiny-8k'
        ]
    },
    'glm_cn': {
        'name': '智谱AI GLM-CN (国内)', 'api_style': 'openai',
        'default_base_url': 'https://open.bigmodel.cn/api/paas/v4', 'models_url': '/models',
        'auth_header': 'Authorization', 'auth_prefix': 'Bearer ',
        'models': [
            'glm-4-plus', 'glm-4-0520', 'glm-4-air', 'glm-4-airx', 'glm-4-long',
            'glm-4-flash', 'glm-4-flashx', 'glm-zero-preview', 'glm-3-turbo'
        ]
    },
    'glm_global': {
        'name': '智谱AI GLM-Global (海外)', 'api_style': 'openai',
        'default_base_url': 'https://api.z.ai/api/paas/v4', 'models_url': '/models',
        'auth_header': 'Authorization', 'auth_prefix': 'Bearer ',
        'models': [
            'glm-4.5', 'glm-4.5-air', 'glm-4.5-x', 'glm-4.5-airx',
            'glm-4-plus', 'glm-4-air', 'glm-4-flash'
        ]
    },
    'moonshot_cn': {
        'name': 'Kimi-CN (月之暗面-国内)', 'api_style': 'openai',
        'default_base_url': 'https://api.moonshot.cn/v1', 'models_url': '/models',
        'auth_header': 'Authorization', 'auth_prefix': 'Bearer ',
        'models': [
            'moonshot-v1-8k', 'moonshot-v1-32k', 'moonshot-v1-128k', 'moonshot-v1-auto',
            'kimi-k2-0905-preview', 'kimi-latest'
        ]
    },
    'moonshot_global': {
        'name': 'Kimi-Global (月之暗面-海外)', 'api_style': 'openai',
        'default_base_url': 'https://api.moonshot.ai/v1', 'models_url': '/models',
        'auth_header': 'Authorization', 'auth_prefix': 'Bearer ',
        'models': [
            'moonshot-v1-8k', 'moonshot-v1-32k', 'moonshot-v1-128k', 'moonshot-v1-auto',
            'kimi-k2-0905-preview', 'kimi-latest'
        ]
    },
    'hunyuan': {
        'name': '腾讯混元', 'api_style': 'openai',
        'default_base_url': 'https://api.hunyuan.cloud.tencent.com/v1', 'models_url': '/models',
        'auth_header': 'Authorization', 'auth_prefix': 'Bearer ',
        'models': [
            'hunyuan-turbo', 'hunyuan-turbos', 'hunyuan-pro', 'hunyuan-standard',
            'hunyuan-standard-256k', 'hunyuan-lite', 'hunyuan-code', 'hunyuan-role', 'hunyuan-vision'
        ]
    },
    'spark': {
        'name': '讯飞星火', 'api_style': 'openai',
        'default_base_url': 'https://spark-api-open.xf-yun.com/v1', 'models_url': '/models',
        'auth_header': 'Authorization', 'auth_prefix': 'Bearer ',
        'models': [
            'generalv3.5', 'generalv3', 'pro-128k', 'max-32k', 'lite',
            'spark-3.0-ultra', 'spark-v3.5'
        ]
    },
    'doubao': {
        'name': '豆包 (字节火山引擎-国内)', 'api_style': 'openai',
        'default_base_url': 'https://ark.cn-beijing.volces.com/api/v3', 'models_url': '/models',
        'auth_header': 'Authorization', 'auth_prefix': 'Bearer ',
        'models': [
            'doubao-pro-32k', 'doubao-pro-256k', 'doubao-lite-4k', 'doubao-lite-32k', 'doubao-lite-128k',
            'doubao-1-5-pro-32k', 'doubao-1-5-pro-256k'
        ]
    },
    'minimax': {
        'name': 'MiniMax (稀宇科技)', 'api_style': 'openai',
        'default_base_url': 'https://api.MiniMax.chat/v1', 'models_url': '/models',
        'auth_header': 'Authorization', 'auth_prefix': 'Bearer ',
        'models': ['MiniMax-Text-01', 'MiniMax-VL-01', 'MiniMax-Text-02', 'MiniMax-Reasoning-01']
    },
    'mimo': {
        'name': '小米 MiMo', 'api_style': 'openai',
        'default_base_url': 'https://api.mimo.ai/v1', 'models_url': '/models',
        'auth_header': 'Authorization', 'auth_prefix': 'Bearer ',
        'models': ['mimo-v2.5-pro', 'mimo-v2.5-flash', 'mimo-v2.5-plus']
    },
    'stepfun': {
        'name': '阶跃星辰 StepFun', 'api_style': 'openai',
        'default_base_url': 'https://api.stepfun.com/v1', 'models_url': '/models',
        'auth_header': 'Authorization', 'auth_prefix': 'Bearer ',
        'models': [
            'step-1-200k', 'step-1-32k', 'step-1-8k', 'step-2-16k',
            'step-2-16k-chat', 'step-1-flash', 'step-1-plus', 'step-1-pro'
        ]
    },
    'yi': {
        'name': '零一万物 Yi', 'api_style': 'openai',
        'default_base_url': 'https://api.lingyiwanwu.com/v1', 'models_url': '/models',
        'auth_header': 'Authorization', 'auth_prefix': 'Bearer ',
        'models': [
            'yi-large', 'yi-medium', 'yi-spark', 'yi-large-turbo',
            'yi-medium-200k', 'yi-lightning'
        ]
    },
    'baichuan': {
        'name': '百川智能 Baichuan', 'api_style': 'openai',
        'default_base_url': 'https://api.baichuan-ai.com/v1', 'models_url': '/models',
        'auth_header': 'Authorization', 'auth_prefix': 'Bearer ',
        'models': [
            'Baichuan4', 'Baichuan3-Turbo', 'Baichuan3-Turbo-128k',
            'Baichuan2-Turbo', 'Baichuan2-Turbo-192k'
        ]
    },
    'siliconflow': {
        'name': '硅基流动 SiliconFlow', 'api_style': 'openai',
        'default_base_url': 'https://api.siliconflow.cn/v1', 'models_url': '/models',
        'auth_header': 'Authorization', 'auth_prefix': 'Bearer ',
        'models': [
            'Qwen/Qwen2.5-7B-Instruct', 'Qwen/Qwen2.5-72B-Instruct',
            'deepseek-ai/DeepSeek-V2.5', '01ai/Yi-1.5-9B-Chat',
            'THUDM/glm-4-9b-chat', 'THUDM/glm-4-72b-chat'
        ]
    },
    'dashscope': {
        'name': '阿里云百炼 (多模型聚合)', 'api_style': 'openai',
        'default_base_url': 'https://dashscope.aliyuncs.com/compatible-mode/v1', 'models_url': '/models',
        'auth_header': 'Authorization', 'auth_prefix': 'Bearer ',
        'models': [
            'qwen-plus', 'qwen-max', 'qwen-turbo', 'qwen-long',
            'qwen2.5-72b-instruct', 'qwen2.5-32b-instruct',
            'deepseek-v3', 'glm-4-9b', 'kimi-k2.7-code',
            'minimax/MiniMax-M2.7', 'mimo-v2.5-pro'
        ]
    },
    # ===== 国际厂商 =====
    'openai': {
        'name': 'OpenAI',
        'api_style': 'openai',
        'default_base_url': 'https://api.openai.com/v1',
        'models_url': '/models',
        'auth_header': 'Authorization',
        'auth_prefix': 'Bearer ',
        'models': [
            'gpt-4o', 'gpt-4o-mini', 'gpt-4.1', 'gpt-4.1-mini', 'gpt-4.1-nano',
            'o1', 'o1-mini', 'o1-pro', 'o3', 'o3-mini', 'o3-pro', 'o4-mini',
            'gpt-4-turbo', 'gpt-3.5-turbo'
        ]
    },
    'claude': {
        'name': 'Claude (Anthropic)',
        'api_style': 'claude',
        'default_base_url': 'https://api.anthropic.com',
        'models_url': '/v1/models',
        'auth_header': 'x-api-key',
        'auth_prefix': '',
        'models': [
            'claude-sonnet-4-5', 'claude-sonnet-4-20250514', 'claude-3-7-sonnet-20250219',
            'claude-opus-4-1-20250805', 'claude-opus-4-20250514',
            'claude-3-5-sonnet-20241022', 'claude-3-5-haiku-20241022'
        ]
    },
    'ollama': {
        'name': 'Ollama (本地部署)', 'api_style': 'openai',
        'default_base_url': 'http://localhost:11434/v1', 'models_url': '/models',
        'auth_header': 'Authorization', 'auth_prefix': 'Bearer ',
        'models': [
            'llama3.3', 'llama3.2', 'qwen2.5', 'qwen2.5-coder', 'mistral', 'mixtral',
            'gemma2', 'phi3', 'codellama', 'deepseek-coder-v2'
        ]
    },
    'groq': {
        'name': 'Groq (高速推理)', 'api_style': 'openai',
        'default_base_url': 'https://api.groq.com/openai/v1', 'models_url': '/models',
        'auth_header': 'Authorization', 'auth_prefix': 'Bearer ',
        'models': [
            'llama-3.3-70b-versatile', 'llama-3.1-8b-instant', 'mixtral-8x7b-32768',
            'gemma2-9b-it', 'llama3-groq-8b-8192-tool-use-preview'
        ]
    },
    'together': {
        'name': 'Together AI (开源模型聚合)', 'api_style': 'openai',
        'default_base_url': 'https://api.together.xyz/v1', 'models_url': '/models',
        'auth_header': 'Authorization', 'auth_prefix': 'Bearer ',
        'models': [
            'meta-llama/Llama-3.3-70B-Instruct-Turbo', 'meta-llama/Meta-Llama-3.1-405B-Instruct-Turbo',
            'deepseek-ai/DeepSeek-R1', 'Qwen/Qwen2.5-72B-Instruct-Turbo'
        ]
    },
    'mistral': {
        'name': 'Mistral AI', 'api_style': 'openai',
        'default_base_url': 'https://api.mistral.ai/v1', 'models_url': '/models',
        'auth_header': 'Authorization', 'auth_prefix': 'Bearer ',
        'models': [
            'mistral-large-latest', 'mistral-small-latest', 'open-mixtral-8x22b',
            'open-mixtral-8x7b', 'codestral-latest', 'pixtral-large-latest'
        ]
    },
    'cohere': {
        'name': 'Cohere', 'api_style': 'openai',
        'default_base_url': 'https://api.cohere.com/v2', 'models_url': '/models',
        'auth_header': 'Authorization', 'auth_prefix': 'Bearer ',
        'models': [
            'command-r-plus', 'command-r', 'command-light', 'command'
        ]
    },
    'jina': {
        'name': 'Jina AI (多模态/Embedding)', 'api_style': 'openai',
        'default_base_url': 'https://api.jina.ai/v1', 'models_url': '/models',
        'auth_header': 'Authorization', 'auth_prefix': 'Bearer ',
        'models': [
            'jina-ai/jina-clip-1', 'jina-ai/jina-embeddings-v3',
            'jina-ai/deepseek-pro', 'jina-ai/jina-reranker-v2'
        ]
    },
    # ===== 自定义 =====
    'custom': {
        'name': '自定义 (OpenAI 兼容)', 'api_style': 'openai',
        'default_base_url': '', 'models_url': '/models',
        'auth_header': 'Authorization', 'auth_prefix': 'Bearer ',
        'models': []
    }
}


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
        
        system_prompt = f"""你是 Ledger AI 助手，由 {provider_names.get(provider, provider)} 驱动。

## 你的能力

你可以帮助用户进行个人记账管理。你有两个工具可以使用：
1. **内置工具**：query_transactions, add_transaction, query_budgets, get_statistics
2. **HTTP API**：通过 curl 调用 Ledger REST API（详见下方 Skills 文档）

## Skills 文档

以下是你可以使用的完整 API 文档，请根据用户需求选择合适的 API 调用：

{skills_content if skills_content else "（未找到 Skills 文档，请使用内置工具）"}

## 重要提示

1. 当用户要求记账、查账、统计、预算等操作时，优先使用 Skills 文档中的 HTTP API
2. 使用 curl 调用 API 时，BASE_URL 默认为 http://127.0.0.1:5800
3. 所有 API 返回 JSON 格式：{{"success": true, "data": {{...}}}} 或 {{"success": false, "error": "..."}}
4. 回复请使用中文，简洁明了

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
        
        system_prompt = f"""你是 Ledger AI 助手，由 {provider_names.get(provider, provider)} 驱动。

## 你的能力

你可以帮助用户进行个人记账管理。你有两个工具可以使用：
1. **内置工具**：query_transactions, add_transaction, query_budgets, get_statistics
2. **HTTP API**：通过 curl 调用 Ledger REST API（详见下方 Skills 文档）

## Skills 文档

以下是你可以使用的完整 API 文档，请根据用户需求选择合适的 API 调用：

{skills_content if skills_content else "（未找到 Skills 文档，请使用内置工具）"}

## 重要提示

1. 当用户要求记账、查账、统计、预算等操作时，优先使用 Skills 文档中的 HTTP API
2. 使用 curl 调用 API 时，BASE_URL 默认为 http://127.0.0.1:5800
3. 所有 API 返回 JSON 格式：{{"success": true, "data": {{...}}}} 或 {{"success": false, "error": "..."}}
4. 回复请使用中文，简洁明了

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
