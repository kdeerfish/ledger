#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Agent 模块 - 提供 AI Agent 对话功能
支持多种 LLM API：OpenAI、Claude、DeepSeek、Ollama 等
以及国内厂商：通义千问、文心一言、智谱AI、Kimi、腾讯混元等
"""

import os
import json
import httpx
from typing import Optional, Dict, Any, List
from dataclasses import dataclass
from datetime import datetime


@dataclass
class LLMConfig:
    """LLM 配置"""
    provider: str  # openai, claude, deepseek, ollama, qwen, wenxin, glm, moonshot, hunyuan, custom
    api_key: str
    model: str
    base_url: Optional[str] = None
    temperature: float = 0.7
    max_tokens: int = 2000


class AgentService:
    """Agent 服务类"""
    
    def __init__(self):
        self.config: Optional[LLMConfig] = None
        self.tools = self._init_tools()
    
    def _init_tools(self) -> List[Dict]:
        """初始化可用工具"""
        return [
            {
                "type": "function",
                "function": {
                    "name": "query_transactions",
                    "description": "查询交易记录",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "month": {"type": "string", "description": "月份，格式 YYYY-MM"},
                            "category": {"type": "string", "description": "类别"},
                            "type": {"type": "string", "enum": ["income", "expense"], "description": "类型"}
                        }
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "add_transaction",
                    "description": "添加交易记录",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "amount": {"type": "number", "description": "金额"},
                            "type": {"type": "string", "enum": ["income", "expense"], "description": "类型"},
                            "category": {"type": "string", "description": "类别"},
                            "description": {"type": "string", "description": "描述"},
                            "date": {"type": "string", "description": "日期 YYYY-MM-DD"}
                        },
                        "required": ["amount", "type", "category"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "query_budgets",
                    "description": "查询预算信息",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "month": {"type": "string", "description": "月份"}
                        }
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "get_statistics",
                    "description": "获取统计数据",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "period": {"type": "string", "enum": ["month", "year"], "description": "统计周期"},
                            "year": {"type": "integer", "description": "年份"},
                            "month": {"type": "integer", "description": "月份"}
                        }
                    }
                }
            }
        ]
    
    def load_config(self, config_dict: Dict) -> bool:
        """加载 LLM 配置"""
        try:
            self.config = LLMConfig(
                provider=config_dict.get('provider', 'openai'),
                api_key=config_dict.get('api_key', ''),
                model=config_dict.get('model', 'gpt-3.5-turbo'),
                base_url=config_dict.get('base_url'),
                temperature=config_dict.get('temperature', 0.7),
                max_tokens=config_dict.get('max_tokens', 2000)
            )
            return True
        except Exception as e:
            print(f"加载配置失败: {e}")
            return False
    
    def get_provider_config(self) -> Dict[str, Any]:
        """获取提供商配置信息"""
        provider = self.config.provider if self.config else 'openai'
        
        # OpenAI 兼容 API 厂商配置
        configs = {
            # 国际厂商
            'openai': {
                'name': 'OpenAI',
                'default_base_url': 'https://api.openai.com/v1',
                'default_model': 'gpt-3.5-turbo',
                'models': ['gpt-3.5-turbo', 'gpt-4', 'gpt-4o', 'gpt-4o-mini', 'gpt-4-turbo'],
                'api_style': 'openai',
                'auth_header': 'Authorization',
                'auth_prefix': 'Bearer '
            },
            'claude': {
                'name': 'Claude',
                'default_base_url': 'https://api.anthropic.com/v1',
                'default_model': 'claude-3-5-sonnet-20241022',
                'models': ['claude-3-5-sonnet-20241022', 'claude-3-opus-20240229', 'claude-3-haiku-20240307'],
                'api_style': 'claude',
                'auth_header': 'x-api-key',
                'auth_prefix': ''
            },
            'deepseek': {
                'name': 'DeepSeek',
                'default_base_url': 'https://api.deepseek.com/v1',
                'default_model': 'deepseek-chat',
                'models': ['deepseek-chat', 'deepseek-coder', 'deepseek-reasoner'],
                'api_style': 'openai',
                'auth_header': 'Authorization',
                'auth_prefix': 'Bearer '
            },
            'ollama': {
                'name': 'Ollama (本地)',
                'default_base_url': 'http://localhost:11434/v1',
                'default_model': 'llama3',
                'models': ['llama3', 'qwen2', 'mistral', 'gemma2', 'phi3', 'codellama'],
                'api_style': 'openai',
                'auth_header': 'Authorization',
                'auth_prefix': 'Bearer '
            },
            # 国内厂商
            'qwen': {
                'name': '通义千问 (阿里)',
                'default_base_url': 'https://dashscope.aliyuncs.com/compatible-mode/v1',
                'default_model': 'qwen-turbo',
                'models': ['qwen-turbo', 'qwen-plus', 'qwen-max', 'qwen-long', 'qwen2.5-72b-instruct', 'qwen2.5-32b-instruct', 'qwen2.5-14b-instruct', 'qwen2.5-7b-instruct'],
                'api_style': 'openai',
                'auth_header': 'Authorization',
                'auth_prefix': 'Bearer '
            },
            'wenxin': {
                'name': '文心一言 (百度)',
                'default_base_url': 'https://qianfan.baidubce.com/v2',
                'default_model': 'ernie-4.0-8k',
                'models': ['ernie-4.0-8k', 'ernie-3.5-8k', 'ernie-3.5-128k', 'ernie-speed-8k', 'ernie-lite-8k', 'ernie-tiny-8k'],
                'api_style': 'openai',
                'auth_header': 'Authorization',
                'auth_prefix': 'Bearer '
            },
            'glm': {
                'name': '智谱AI (GLM)',
                'default_base_url': 'https://open.bigmodel.cn/api/paas/v4',
                'default_model': 'glm-4',
                'models': ['glm-4', 'glm-4-plus', 'glm-4-0520', 'glm-4-air', 'glm-4-airx', 'glm-4-long', 'glm-4-flash', 'glm-3-turbo'],
                'api_style': 'openai',
                'auth_header': 'Authorization',
                'auth_prefix': 'Bearer '
            },
            'moonshot': {
                'name': 'Kimi (月之暗面)',
                'default_base_url': 'https://api.moonshot.cn/v1',
                'default_model': 'moonshot-v1-8k',
                'models': ['moonshot-v1-8k', 'moonshot-v1-32k', 'moonshot-v1-128k', 'moonshot-v1-auto'],
                'api_style': 'openai',
                'auth_header': 'Authorization',
                'auth_prefix': 'Bearer '
            },
            'hunyuan': {
                'name': '腾讯混元',
                'default_base_url': 'https://api.hunyuan.cloud.tencent.com/v1',
                'default_model': 'hunyuan-pro',
                'models': ['hunyuan-pro', 'hunyuan-standard', 'hunyuan-lite', 'hunyuan-turbo', 'hunyuan-code', 'hunyuan-role'],
                'api_style': 'openai',
                'auth_header': 'Authorization',
                'auth_prefix': 'Bearer '
            },
            'spark': {
                'name': '讯飞星火',
                'default_base_url': 'https://spark-api-open.xf-yun.com/v1',
                'default_model': 'general',
                'models': ['general', 'generalv3', 'generalv3.5', 'pro-128k', 'max-32k', 'lite'],
                'api_style': 'openai',
                'auth_header': 'Authorization',
                'auth_prefix': 'Bearer '
            },
            'doubao': {
                'name': '豆包 (字节跳动)',
                'default_base_url': 'https://ark.cn-beijing.volces.com/api/v3',
                'default_model': 'doubao-pro-32k',
                'models': ['doubao-pro-32k', 'doubao-pro-128k', 'doubao-lite-4k', 'doubao-lite-32k', 'doubao-lite-128k'],
                'api_style': 'openai',
                'auth_header': 'Authorization',
                'auth_prefix': 'Bearer '
            },
            'minimax': {
                'name': 'MiniMax',
                'default_base_url': 'https://api.MiniMax.chat/v1',
                'default_model': 'MiniMax-text-01',
                'models': ['MiniMax-text-01', 'MiniMax-VL-01'],
                'api_style': 'openai',
                'auth_header': 'Authorization',
                'auth_prefix': 'Bearer '
            },
            'custom': {
                'name': '自定义 (OpenAI兼容)',
                'default_base_url': '',
                'default_model': '',
                'models': [],
                'api_style': 'openai',
                'auth_header': 'Authorization',
                'auth_prefix': 'Bearer '
            }
        }
        
        return configs.get(provider, configs['openai'])
    
    def get_default_base_url(self) -> str:
        """获取默认 base_url"""
        if not self.config:
            return "https://api.openai.com/v1"
        
        provider_config = self.get_provider_config()
        return self.config.base_url or provider_config['default_base_url']
    
    def build_headers(self) -> Dict[str, str]:
        """构建请求头"""
        if not self.config:
            return {}
        
        provider_config = self.get_provider_config()
        api_key = self.config.api_key
        auth_header = provider_config['auth_header']
        auth_prefix = provider_config['auth_prefix']
        
        headers = {
            "Content-Type": "application/json"
        }
        
        if provider_config['api_style'] == 'claude':
            headers['x-api-key'] = api_key
            headers['anthropic-version'] = '2023-06-01'
            if auth_header == 'Authorization':
                headers['Authorization'] = f"{auth_prefix}{api_key}"
            else:
                headers[auth_header] = f"{auth_prefix}{api_key}"
        else:
            if auth_prefix:
                headers[auth_header] = f"{auth_prefix}{api_key}"
            else:
                headers[auth_header] = api_key
        
        return headers
    
    async def chat(self, messages: List[Dict], stream: bool = False):
        """发送聊天请求"""
        if not self.config:
            raise ValueError("未配置 LLM")
        
        base_url = self.get_default_base_url()
        headers = self.build_headers()
        provider_config = self.get_provider_config()
        
        print(f"[Agent] Calling API: provider={self.config.provider}, model={self.config.model}")
        print(f"[Agent] Base URL: {base_url}")
        print(f"[Agent] Messages count: {len(messages)}")
        
        payload = {
            "model": self.config.model,
            "messages": messages,
            "temperature": self.config.temperature,
            "max_tokens": self.config.max_tokens,
            "stream": stream
        }
        
        # 添加工具定义（OpenAI兼容模式）
        if self.tools and provider_config['api_style'] != 'claude':
            payload["tools"] = self.tools
            payload["tool_choice"] = "auto"
        
        # Claude 特殊处理：max_tokens 必须显式设置
        if provider_config['api_style'] == 'claude':
            # Claude API 格式不同
            system_msg = None
            conv_messages = []
            for msg in messages:
                if msg['role'] == 'system':
                    system_msg = msg['content']
                else:
                    conv_messages.append(msg)
            
            claude_payload = {
                "model": self.config.model,
                "messages": conv_messages,
                "max_tokens": self.config.max_tokens,
                "temperature": self.config.temperature,
            }
            if system_msg:
                claude_payload['system'] = system_msg
            
            url = f"{base_url.rstrip('/')}/messages"
            payload = claude_payload
        else:
            url = f"{base_url.rstrip('/')}/chat/completions"
        
        print(f"[Agent] Request URL: {url}")
        
        async with httpx.AsyncClient() as client:
            if stream:
                return self._stream_response(client, url, headers, payload)
            else:
                print(f"[Agent] Sending POST request...")
                response = await client.post(
                    url,
                    headers=headers,
                    json=payload,
                    timeout=60.0
                )
                print(f"[Agent] Response status: {response.status_code}")
                response.raise_for_status()
                result = response.json()
                print(f"[Agent] Response keys: {list(result.keys()) if isinstance(result, dict) else 'not a dict'}")
                return result
    
    async def _stream_response(self, client, url, headers, payload):
        """流式响应"""
        async with client.stream(
            "POST",
            url,
            headers=headers,
            json=payload,
            timeout=60.0
        ) as response:
            response.raise_for_status()
            async for line in response.aiter_lines():
                if line.startswith("data: "):
                    data = line[6:]
                    if data.strip() == "[DONE]":
                        break
                    try:
                        chunk = json.loads(data)
                        if chunk.get("choices"):
                            delta = chunk["choices"][0].get("delta", {})
                            if delta.get("content"):
                                yield delta["content"]
                    except json.JSONDecodeError:
                        continue
    
    def execute_tool(self, tool_name: str, arguments: Dict) -> str:
        """执行工具调用"""
        import ledger_modules.transactions as tx_module
        import ledger_modules.budgets as budget_module
        from datetime import datetime, timedelta
        
        try:
            if tool_name == "query_transactions":
                month = arguments.get('month', datetime.now().strftime('%Y-%m'))
                category = arguments.get('category')
                type_ = arguments.get('type')
                
                # 查询交易记录
                result = tx_module.search_transactions(
                    start_date=f"{month}-01",
                    end_date=f"{month}-31",
                    category=category,
                    type_=type_
                )
                
                if not result:
                    return f"{month} 没有找到交易记录"
                
                total = sum(t.get('amount', 0) for t in result)
                return f"{month} 共 {len(result)} 笔交易，总计 {total:.2f} 元"
            
            elif tool_name == "add_transaction":
                amount = arguments.get('amount')
                type_ = arguments.get('type')
                category = arguments.get('category')
                description = arguments.get('description', '')
                date = arguments.get('date', datetime.now().strftime('%Y-%m-%d'))
                
                if not all([amount, type_, category]):
                    return "缺少必要参数：amount, type, category"
                
                # 添加交易
                tx_id = tx_module.add_transaction(
                    amount=amount,
                    type_=type_,
                    category=category,
                    description=description,
                    date=date
                )
                
                return f"已添加交易：{type_} {amount} 元，类别：{category}，ID：{tx_id}"
            
            elif tool_name == "query_budgets":
                month = arguments.get('month', datetime.now().strftime('%Y-%m'))
                
                # 查询预算
                budgets = budget_module.get_budgets(month=month)
                
                if not budgets:
                    return f"{month} 没有设置预算"
                
                result = []
                for b in budgets:
                    result.append(f"{b.get('category', '未知')}: 预算 {b.get('budget', 0):.2f} 元，已用 {b.get('used', 0):.2f} 元")
                
                return "\n".join(result)
            
            elif tool_name == "get_statistics":
                period = arguments.get('period', 'month')
                year = arguments.get('year', datetime.now().year)
                month = arguments.get('month', datetime.now().month)
                
                # 获取统计数据
                if period == 'month':
                    stats = tx_module.get_monthly_stats(year=year, month=month)
                else:
                    stats = tx_module.get_yearly_stats(year=year)
                
                if not stats:
                    return f"没有找到 {year}年{month}月 的统计数据"
                
                return f"{year}年{month}月 统计：收入 {stats.get('income', 0):.2f} 元，支出 {stats.get('expense', 0):.2f} 元，结余 {stats.get('balance', 0):.2f} 元"
            
            else:
                return f"未知工具：{tool_name}"
        
        except Exception as e:
            return f"工具执行失败：{str(e)}"


# 全局实例
agent_service = AgentService()
