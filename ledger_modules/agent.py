#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Agent 模块 - 提供 AI Agent 对话功能
支持多种 LLM API：OpenAI、Claude、DeepSeek、Ollama 等
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
    provider: str  # openai, claude, deepseek, ollama
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
    
    def get_default_base_url(self) -> str:
        """获取默认 base_url"""
        if not self.config:
            return "https://api.openai.com/v1"
        
        urls = {
            "openai": "https://api.openai.com/v1",
            "claude": "https://api.anthropic.com/v1",
            "deepseek": "https://api.deepseek.com/v1",
            "ollama": "http://localhost:11434/v1"
        }
        return self.config.base_url or urls.get(self.config.provider, "https://api.openai.com/v1")
    
    async def chat(self, messages: List[Dict], stream: bool = False):
        """发送聊天请求"""
        if not self.config:
            raise ValueError("未配置 LLM")
        
        base_url = self.get_default_base_url()
        
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.config.api_key}"
        }
        
        if self.config.provider == "claude":
            headers["x-api-key"] = self.config.api_key
            headers["anthropic-version"] = "2023-06-01"
        
        payload = {
            "model": self.config.model,
            "messages": messages,
            "temperature": self.config.temperature,
            "max_tokens": self.config.max_tokens,
            "stream": stream
        }
        
        # 添加工具定义
        if self.tools and self.config.provider != "claude":
            payload["tools"] = self.tools
            payload["tool_choice"] = "auto"
        
        async with httpx.AsyncClient() as client:
            if stream:
                return self._stream_response(client, base_url, headers, payload)
            else:
                response = await client.post(
                    f"{base_url}/chat/completions",
                    headers=headers,
                    json=payload,
                    timeout=60.0
                )
                response.raise_for_status()
                return response.json()
    
    async def _stream_response(self, client, base_url, headers, payload):
        """流式响应"""
        async with client.stream(
            "POST",
            f"{base_url}/chat/completions",
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
