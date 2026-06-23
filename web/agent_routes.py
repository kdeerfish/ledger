#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Agent API Routes"""

import asyncio
import json
import os
from flask import request, jsonify
import httpx


# Provider configuration - latest models
PROVIDERS_CONFIG = {
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
        'name': 'Claude',
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
    'deepseek': {
        'name': 'DeepSeek', 'api_style': 'openai',
        'default_base_url': 'https://api.deepseek.com/v1', 'models_url': '/models',
        'auth_header': 'Authorization', 'auth_prefix': 'Bearer ',
        'models': ['deepseek-chat', 'deepseek-reasoner', 'deepseek-coder', 'deepseek-v3']
    },
    'qwen': {
        'name': 'Qwen (Alibaba)', 'api_style': 'openai',
        'default_base_url': 'https://dashscope.aliyuncs.com/compatible-mode/v1', 'models_url': '/models',
        'auth_header': 'Authorization', 'auth_prefix': 'Bearer ',
        'models': [
            'qwen-max', 'qwen-plus', 'qwen-turbo', 'qwen-long',
            'qwen3-max', 'qwen3-plus', 'qwen3-235b-a22b',
            'qwen2.5-72b-instruct', 'qwen2.5-32b-instruct', 'qwen2.5-14b-instruct', 'qwen2.5-7b-instruct',
            'qwen-coder-plus', 'qwen-vl-max', 'qwen-vl-plus'
        ]
    },
    'wenxin': {
        'name': 'Wenxin (Baidu)', 'api_style': 'openai',
        'default_base_url': 'https://qianfan.baidubce.com/v2', 'models_url': '/models',
        'auth_header': 'Authorization', 'auth_prefix': 'Bearer ',
        'models': [
            'ernie-4.5-8k', 'ernie-4.5-turbo-128k', 'ernie-4.0-turbo-8k', 'ernie-4.0-8k',
            'ernie-3.5-8k', 'ernie-3.5-128k', 'ernie-speed-pro-128k',
            'ernie-lite-8k', 'ernie-tiny-8k'
        ]
    },
    'glm': {
        'name': 'GLM (Zhipu)', 'api_style': 'openai',
        'default_base_url': 'https://open.bigmodel.cn/api/paas/v4', 'models_url': '/models',
        'auth_header': 'Authorization', 'auth_prefix': 'Bearer ',
        'models': [
            'glm-4-plus', 'glm-4-0520', 'glm-4-air', 'glm-4-airx', 'glm-4-long',
            'glm-4-flash', 'glm-4-flashx', 'glm-zero-preview', 'glm-3-turbo'
        ]
    },
    'moonshot': {
        'name': 'Kimi (Moonshot)', 'api_style': 'openai',
        'default_base_url': 'https://api.moonshot.cn/v1', 'models_url': '/models',
        'auth_header': 'Authorization', 'auth_prefix': 'Bearer ',
        'models': [
            'moonshot-v1-8k', 'moonshot-v1-32k', 'moonshot-v1-128k', 'moonshot-v1-auto',
            'kimi-k2-0905-preview', 'kimi-latest'
        ]
    },
    'hunyuan': {
        'name': 'Hunyuan (Tencent)', 'api_style': 'openai',
        'default_base_url': 'https://api.hunyuan.cloud.tencent.com/v1', 'models_url': '/models',
        'auth_header': 'Authorization', 'auth_prefix': 'Bearer ',
        'models': [
            'hunyuan-turbo', 'hunyuan-turbos', 'hunyuan-pro', 'hunyuan-standard',
            'hunyuan-standard-256k', 'hunyuan-lite', 'hunyuan-code', 'hunyuan-role', 'hunyuan-vision'
        ]
    },
    'spark': {
        'name': 'Spark (iFlytek)', 'api_style': 'openai',
        'default_base_url': 'https://spark-api-open.xf-yun.com/v1', 'models_url': '/models',
        'auth_header': 'Authorization', 'auth_prefix': 'Bearer ',
        'models': [
            'generalv3.5', 'generalv3', 'pro-128k', 'max-32k', 'lite',
            'spark-3.0-ultra', 'spark-v3.5'
        ]
    },
    'doubao': {
        'name': 'Doubao (ByteDance)', 'api_style': 'openai',
        'default_base_url': 'https://ark.cn-beijing.volces.com/api/v3', 'models_url': '/models',
        'auth_header': 'Authorization', 'auth_prefix': 'Bearer ',
        'models': [
            'doubao-pro-32k', 'doubao-pro-256k', 'doubao-lite-4k', 'doubao-lite-32k', 'doubao-lite-128k',
            'doubao-1-5-pro-32k', 'doubao-1-5-pro-256k'
        ]
    },
    'minimax': {
        'name': 'MiniMax', 'api_style': 'openai',
        'default_base_url': 'https://api.MiniMax.chat/v1', 'models_url': '/models',
        'auth_header': 'Authorization', 'auth_prefix': 'Bearer ',
        'models': ['MiniMax-Text-01', 'MiniMax-VL-01', 'MiniMax-Text-02', 'MiniMax-Reasoning-01']
    },
    'ollama': {
        'name': 'Ollama (Local)', 'api_style': 'openai',
        'default_base_url': 'http://localhost:11434/v1', 'models_url': '/models',
        'auth_header': 'Authorization', 'auth_prefix': 'Bearer ',
        'models': [
            'llama3.3', 'llama3.2', 'qwen2.5', 'qwen2.5-coder', 'mistral', 'mixtral',
            'gemma2', 'phi3', 'codellama', 'deepseek-coder-v2'
        ]
    },
    'groq': {
        'name': 'Groq (Fast Inference)', 'api_style': 'openai',
        'default_base_url': 'https://api.groq.com/openai/v1', 'models_url': '/models',
        'auth_header': 'Authorization', 'auth_prefix': 'Bearer ',
        'models': [
            'llama-3.3-70b-versatile', 'llama-3.1-8b-instant', 'mixtral-8x7b-32768',
            'gemma2-9b-it', 'llama3-groq-8b-8192-tool-use-preview'
        ]
    },
    'together': {
        'name': 'Together AI', 'api_style': 'openai',
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
    'yi': {
        'name': 'Yi (零一万物)', 'api_style': 'openai',
        'default_base_url': 'https://api.lingyiwanwu.com/v1', 'models_url': '/models',
        'auth_header': 'Authorization', 'auth_prefix': 'Bearer ',
        'models': [
            'yi-large', 'yi-medium', 'yi-spark', 'yi-large-turbo',
            'yi-medium-200k', 'yi-lightning'
        ]
    },
    'baichuan': {
        'name': 'Baichuan (百川)', 'api_style': 'openai',
        'default_base_url': 'https://api.baichuan-ai.com/v1', 'models_url': '/models',
        'auth_header': 'Authorization', 'auth_prefix': 'Bearer ',
        'models': [
            'Baichuan4', 'Baichuan3-Turbo', 'Baichuan3-Turbo-128k',
            'Baichuan2-Turbo', 'Baichuan2-Turbo-192k'
        ]
    },
    'stepfun': {
        'name': 'StepFun (阶跃星辰)', 'api_style': 'openai',
        'default_base_url': 'https://api.stepfun.com/v1', 'models_url': '/models',
        'auth_header': 'Authorization', 'auth_prefix': 'Bearer ',
        'models': [
            'step-1-200k', 'step-1-32k', 'step-1-8k', 'step-2-16k',
            'step-2-16k-chat', 'step-1-flash'
        ]
    },
    'custom': {
        'name': 'Custom (OpenAI compatible)', 'api_style': 'openai',
        'default_base_url': '', 'models_url': '/models',
        'auth_header': 'Authorization', 'auth_prefix': 'Bearer ',
        'models': []
    }
}


def register_agent_routes(app, api_error, api_success, sync_db_path, db_module):
    """Register Agent API routes"""
    import ledger_modules.agent as agent_module
    
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
        
        system_prompt = "You are Ledger AI assistant powered by " + provider_names.get(provider, provider) + ". Help with: 1) Add transaction (e.g. add lunch 30 yuan -> use add_transaction tool), 2) Query (check this month expenses -> query_transactions), 3) Statistics (this month stats -> get_statistics), 4) Budget (check budget -> query_budgets). Reply in Chinese concisely. Today: " + __import__("datetime").datetime.now().strftime("%Y-%m-%d")
        
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
    
    @app.route("/api/agent/config", methods=["POST"])
    def save_agent_config():
        data = request.get_json(silent=True)
        if not data:
            return api_error("Empty request")
        return api_success({"message": "Config saved"})
