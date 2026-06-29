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


def _load_providers_config():
    """从配置文件加载 provider 配置"""
    config_path = os.path.join(os.path.dirname(__file__), 'providers_config.json')
    try:
        with open(config_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
            return data.get('providers', {})
    except Exception as e:
        print(f"[Agent] Failed to load providers config: {e}")
        return {}


# 从配置文件加载 provider 配置
PROVIDERS_CONFIG = _load_providers_config()


@dataclass
class LLMConfig:
    """LLM 配置"""
    provider: str  # 国内：deepseek, qwen_cn, qwen_global, wenxin, glm_cn, glm_global, moonshot_cn, moonshot_global, hunyuan, spark, doubao, minimax, mimo, stepfun, yi, baichuan, siliconflow, dashscope | 国际：openai, claude, ollama, groq, together, mistral, cohere, jina | 自定义：custom
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
                    "description": "查询交易记录。支持按月份或日期范围查询。用户问花了多少、有哪些记录、这两天、最近几天时调用。",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "month": {"type": "string", "description": "月份 YYYY-MM，如 2026-06。与 start_date/end_date 二选一。", "default": ""},
                            "start_date": {"type": "string", "description": "开始日期 YYYY-MM-DD，如 2026-06-22。用于查询特定日期范围。", "default": ""},
                            "end_date": {"type": "string", "description": "结束日期 YYYY-MM-DD，如 2026-06-24。用于查询特定日期范围。", "default": ""},
                            "category": {"type": "string", "description": "类别（可选），如 食品酒水、交通", "default": ""},
                            "type": {"type": "string", "enum": ["支出", "收入"], "description": "类型：支出=花费, 收入=进账", "default": ""}
                        },
                        "required": []
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "add_transaction",
                    "description": "添加一条交易记录（记账）。用户说记一笔、花了、买了时调用。",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "amount": {"type": "number", "description": "金额（必填），数字"},
                            "type": {"type": "string", "enum": ["支出", "收入"], "description": "类型：支出=花费, 收入=进账（必填）"},
                            "category": {"type": "string", "description": "类别（必填），如 食品酒水、交通、购物"},
                            "description": {"type": "string", "description": "备注描述（可选）", "default": ""},
                            "date": {"type": "string", "description": "日期 YYYY-MM-DD（可选，默认为今天）", "default": ""}
                        },
                        "required": ["amount", "type", "category"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "query_budgets",
                    "description": "查询指定月份的预算信息。用户问预算、还剩多少时调用。",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "month": {"type": "string", "description": "月份 YYYY-MM（可选，默认为本月）", "default": ""}
                        }
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "get_statistics",
                    "description": "获取收支统计汇总。用户问统计、汇总、总共有多少时调用。",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "period": {"type": "string", "enum": ["month", "year"], "description": "统计周期：month=月度, year=年度（可选，默认月）", "default": "month"},
                            "year": {"type": "integer", "description": "年份（可选，默认为今年）", "default": 0},
                            "month": {"type": "integer", "description": "月份 1-12（可选，默认为本月）", "default": 0},
                            "group_by": {"type": "string", "enum": ["category", "account", "month"], "description": "分组维度：category=按类别, account=按账户, month=按月", "default": "category"}
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
        """获取提供商配置信息（从配置文件加载）"""
        provider = self.config.provider if self.config else 'openai'
        
        # 从配置文件加载的 PROVIDERS_CONFIG
        if PROVIDERS_CONFIG:
            config = PROVIDERS_CONFIG.get(provider, PROVIDERS_CONFIG.get('openai', {}))
            # 添加 default_model 字段（使用 models 列表的第一个作为默认）
            if 'default_model' not in config and config.get('models'):
                config['default_model'] = config['models'][0]
            return config
        
        # 备用：如果配置文件加载失败，返回基本配置
        return {
            'name': provider,
            'default_base_url': 'https://api.openai.com/v1',
            'default_model': 'gpt-3.5-turbo',
            'models': [],
            'api_style': 'openai',
            'auth_header': 'Authorization',
            'auth_prefix': 'Bearer '
        }
    
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
    
    async def chat_stream(self, messages: List[Dict]):
        """流式聊天，返回思考过程和内容，支持工具调用循环"""
        if not self.config:
            raise ValueError("未配置 LLM")
        
        base_url = self.get_default_base_url()
        headers = self.build_headers()
        provider_config = self.get_provider_config()
        
        # 工具调用循环（最多3轮）
        current_messages = list(messages)
        max_tool_rounds = 3
        full_content = ""
        
        for round_idx in range(max_tool_rounds):
            print(f"[Agent Stream] Round {round_idx + 1}: provider={self.config.provider}, model={self.config.model}")
            
            payload = {
                "model": self.config.model,
                "messages": current_messages,
                "temperature": self.config.temperature,
                "max_tokens": self.config.max_tokens,
                "stream": True
            }
            
            # 添加工具定义
            if self.tools and provider_config['api_style'] != 'claude':
                payload["tools"] = self.tools
                payload["tool_choice"] = "auto"
            
            # Claude 特殊处理
            if provider_config['api_style'] == 'claude':
                system_msg = None
                conv_messages = []
                for msg in current_messages:
                    if msg['role'] == 'system':
                        system_msg = msg['content']
                    else:
                        conv_messages.append(msg)
                
                claude_payload = {
                    "model": self.config.model,
                    "messages": conv_messages,
                    "max_tokens": self.config.max_tokens,
                    "temperature": self.config.temperature,
                    "stream": True
                }
                if system_msg:
                    claude_payload['system'] = system_msg
                
                url = f"{base_url.rstrip('/')}/messages"
                payload = claude_payload
            else:
                url = f"{base_url.rstrip('/')}/chat/completions"
            
            print(f"[Agent Stream] Request URL: {url}")
            
            tool_calls = []
            
            async with httpx.AsyncClient() as client:
                async with client.stream(
                    "POST",
                    url,
                    headers=headers,
                    json=payload,
                    timeout=120.0
                ) as response:
                    response.raise_for_status()
                    
                    full_content = ""
                    current_tool_call = None
                    in_think_block = False
                    think_buffer = ""
                    
                    async for line in response.aiter_lines():
                        if not line.startswith("data: "):
                            continue
                        
                        data = line[6:]
                        if data.strip() == "[DONE]":
                            break
                        
                        try:
                            chunk = json.loads(data)
                            
                            # OpenAI 格式
                            if provider_config['api_style'] != 'claude':
                                if not chunk.get("choices"):
                                    continue
                                
                                delta = chunk["choices"][0].get("delta", {})
                                
                                # 内容增量 - 处理 <think> 标签
                                if delta.get("content"):
                                    content_piece = delta["content"]
                                    while content_piece:
                                        if not in_think_block:
                                            think_start = content_piece.find("<think>")
                                            if think_start >= 0:
                                                before = content_piece[:think_start]
                                                if before:
                                                    full_content += before
                                                    yield {"type": "content", "content": before}
                                                in_think_block = True
                                                think_buffer = ""
                                                content_piece = content_piece[think_start + len("<think>"):]
                                            else:
                                                full_content += content_piece
                                                yield {"type": "content", "content": content_piece}
                                                content_piece = ""
                                        else:
                                            think_end = content_piece.find("</think>")
                                            if think_end >= 0:
                                                think_buffer += content_piece[:think_end]
                                                yield {"type": "thinking", "content": think_buffer}
                                                think_buffer = ""
                                                in_think_block = False
                                                content_piece = content_piece[think_end + len("</think>"):]
                                            else:
                                                think_buffer += content_piece
                                                content_piece = ""
                                
                                # reasoning_content 字段
                                if delta.get("reasoning_content"):
                                    yield {"type": "thinking", "content": delta["reasoning_content"]}
                                
                                # 工具调用
                                if delta.get("tool_calls"):
                                    for tc in delta["tool_calls"]:
                                        if tc.get("index") is not None:
                                            idx = tc["index"]
                                            while len(tool_calls) <= idx:
                                                tool_calls.append({"id": "", "type": "function", "function": {"name": "", "arguments": ""}})
                                            
                                            if tc.get("id"):
                                                tool_calls[idx]["id"] = tc["id"]
                                            if tc.get("function", {}).get("name"):
                                                tool_calls[idx]["function"]["name"] = tc["function"]["name"]
                                            if tc.get("function", {}).get("arguments"):
                                                tool_calls[idx]["function"]["arguments"] += tc["function"]["arguments"]
                            
                            # Claude 格式
                            else:
                                if chunk.get("type") == "content_block_start":
                                    block = chunk.get("content_block", {})
                                    if block.get("type") == "tool_use":
                                        current_tool_call = {
                                            "id": block.get("id", ""),
                                            "type": "function",
                                            "function": {
                                                "name": block.get("name", ""),
                                                "arguments": ""
                                            }
                                        }
                                elif chunk.get("type") == "content_block_delta":
                                    delta = chunk.get("delta", {})
                                    if delta.get("type") == "thinking_delta":
                                        yield {"type": "thinking", "content": delta.get("thinking", "")}
                                    elif delta.get("type") == "text_delta":
                                        text = delta.get("text", "")
                                        content_piece = text
                                        while content_piece:
                                            if not in_think_block:
                                                think_start = content_piece.find("<think>")
                                                if think_start >= 0:
                                                    before = content_piece[:think_start]
                                                    if before:
                                                        full_content += before
                                                        yield {"type": "content", "content": before}
                                                    in_think_block = True
                                                    think_buffer = ""
                                                    content_piece = content_piece[think_start + len("<think>"):]
                                                else:
                                                    full_content += content_piece
                                                    yield {"type": "content", "content": content_piece}
                                                    content_piece = ""
                                            else:
                                                think_end = content_piece.find("</think>")
                                                if think_end >= 0:
                                                    think_buffer += content_piece[:think_end]
                                                    yield {"type": "thinking", "content": think_buffer}
                                                    think_buffer = ""
                                                    in_think_block = False
                                                    content_piece = content_piece[think_end + len("</think>"):]
                                                else:
                                                    think_buffer += content_piece
                                                    content_piece = ""
                                    elif delta.get("type") == "input_json_delta" and current_tool_call:
                                        current_tool_call["function"]["arguments"] += delta.get("partial_json", "")
                                elif chunk.get("type") == "content_block_stop":
                                    if current_tool_call:
                                        tool_calls.append(current_tool_call)
                                        current_tool_call = None
                        
                        except json.JSONDecodeError:
                            continue
                
                # 处理未闭合的思考块
                if think_buffer:
                    yield {"type": "thinking", "content": think_buffer}
            
            # 没有工具调用，本轮结束
            if not tool_calls:
                yield {"type": "done", "full_content": full_content}
                return
            
            # 有工具调用，执行并继续
            # 构建 assistant 消息（含工具调用）
            assistant_msg = {"role": "assistant", "content": full_content or None}
            if provider_config['api_style'] == 'claude':
                assistant_msg["content"] = [{"type": "text", "text": full_content}] if full_content else []
                for tc in tool_calls:
                    assistant_msg["content"].append({
                        "type": "tool_use",
                        "id": tc["id"],
                        "name": tc["function"]["name"],
                        "input": json.loads(tc["function"]["arguments"]) if tc["function"]["arguments"] else {}
                    })
            else:
                assistant_msg["tool_calls"] = tool_calls
            current_messages.append(assistant_msg)
            
            # 执行工具并收集结果
            for tc in tool_calls:
                yield {"type": "tool_call", "tool_call": tc}
                try:
                    args = json.loads(tc["function"]["arguments"]) if tc["function"]["arguments"] else {}
                    result = self.execute_tool(tc["function"]["name"], args)
                    yield {"type": "tool_result", "tool_call": tc, "result": result}
                except Exception as e:
                    result = f"工具执行失败: {str(e)}"
                    yield {"type": "tool_result", "tool_call": tc, "result": result}
                
                # 添加工具结果消息
                if provider_config['api_style'] == 'claude':
                    current_messages.append({
                        "role": "user",
                        "content": [{"type": "tool_result", "tool_use_id": tc["id"], "content": result}]
                    })
                else:
                    current_messages.append({
                        "role": "tool",
                        "tool_call_id": tc["id"],
                        "content": result
                    })
            
            # 继续下一轮（让 LLM 根据工具结果生成回复）
            print(f"[Agent Stream] Tool calls executed, starting round {round_idx + 2}")
        
        # 超过最大轮数
        yield {"type": "done", "full_content": full_content}
    
    def execute_tool(self, tool_name: str, arguments: Dict) -> str:
        """执行工具调用"""
        import ledger_modules.transactions as tx_module
        from datetime import datetime
        import sqlite3
        from ledger_modules.config import get_db_path
        
        try:
            if tool_name == "query_transactions":
                month = arguments.get('month', '')
                start_date_arg = arguments.get('start_date', '')
                end_date_arg = arguments.get('end_date', '')
                category = arguments.get('category')
                type_ = arguments.get('type')
                
                # 调试日志
                print(f"[Tool] query_transactions: month={month}, start_date={start_date_arg}, end_date={end_date_arg}, category={category}, type={type_}")
                
                # 确定查询日期范围
                if start_date_arg and end_date_arg:
                    # 验证日期格式和顺序
                    from datetime import datetime, timedelta
                    try:
                        start_dt = datetime.strptime(start_date_arg, '%Y-%m-%d')
                        end_dt = datetime.strptime(end_date_arg, '%Y-%m-%d')
                        # 如果日期顺序反了，自动交换
                        if start_dt > end_dt:
                            start_dt, end_dt = end_dt, start_dt
                            start_date_arg = start_dt.strftime('%Y-%m-%d')
                            end_date_arg = end_dt.strftime('%Y-%m-%d')
                        # end_date 需要包含当天，所以用下一天
                        end_date = (end_dt + timedelta(days=1)).strftime('%Y-%m-%d')
                        start_date = start_date_arg
                    except ValueError:
                        return "日期格式错误，请使用 YYYY-MM-DD 格式"
                elif month:
                    # 使用月份
                    year_str, m_str = month.split('-')
                    year_int, m_int = int(year_str), int(m_str)
                    start_date = f"{year_int}-{m_int:02d}-01"
                    if m_int == 12:
                        end_date = f"{year_int+1}-01-01"
                    else:
                        end_date = f"{year_int}-{m_int+1:02d}-01"
                else:
                    # 默认本月
                    now = datetime.now()
                    start_date = f"{now.year}-{now.month:02d}-01"
                    if now.month == 12:
                        end_date = f"{now.year+1}-01-01"
                    else:
                        end_date = f"{now.year}-{now.month+1:02d}-01"
                
                # 直接查询数据库
                conn = sqlite3.connect(get_db_path())
                c = conn.cursor()
                sql = '''SELECT id, trans_date, type, amount, category, account, note 
                         FROM transactions 
                         WHERE is_deleted = 0 AND trans_date >= ? AND trans_date < ?'''
                params = [start_date, end_date]
                if category:
                    sql += ' AND (category = ? OR subcategory = ?)'
                    params.extend([category, category])
                # 类型过滤：直接使用中文值
                if type_:
                    sql += ' AND type = ?'
                    params.append(type_)
                sql += ' ORDER BY trans_date DESC LIMIT 200'
                c.execute(sql, params)
                rows = c.fetchall()
                conn.close()
                
                # 构建查询描述
                if start_date_arg and end_date_arg:
                    query_desc = f"{start_date_arg} 至 {end_date_arg}"
                elif month:
                    query_desc = month
                else:
                    query_desc = "本月"
                
                if not rows:
                    return f"{query_desc} 没有找到交易记录"
                
                total = sum(row[3] for row in rows)
                # 返回详细记录
                lines = [f"{query_desc} 共 {len(rows)} 笔交易，总计 {total:.2f} 元：\n"]
                for row in rows[:20]:  # 最多显示20条
                    id_, date, typ, amt, cat, acc, note = row
                    lines.append(f"  {date[:10]} | {typ} | {amt:.2f} | {cat} | {note or ''}")
                if len(rows) > 20:
                    lines.append(f"  ... 还有 {len(rows) - 20} 条记录")
                return "\n".join(lines)
            
            elif tool_name == "add_transaction":
                amount = arguments.get('amount')
                type_ = arguments.get('type')
                category = arguments.get('category')
                description = arguments.get('description', '')
                date = arguments.get('date', datetime.now().strftime('%Y-%m-%d'))
                
                if not all([amount, type_, category]):
                    return "缺少必要参数：amount, type, category"
                
                # 添加交易（匹配实际函数签名）
                # add_transaction(type_, amount, category, subcategory, account, project, member, merchant, note, trans_date=None, force=False)
                tx_id = tx_module.add_transaction(
                    type_=type_,
                    amount=amount,
                    category=category,
                    subcategory='',
                    account='',
                    project='',
                    member='',
                    merchant='',
                    note=description,
                    trans_date=date,
                    force=True
                )
                
                if tx_id is None:
                    return f"添加失败：检测到重复记录"
                return f"已添加交易：{type_} {amount} 元，类别：{category}，ID：{tx_id}"
            
            elif tool_name == "query_budgets":
                month = arguments.get('month', datetime.now().strftime('%Y-%m'))
                year_str, m_str = month.split('-')
                year_int, m_int = int(year_str), int(m_str)
                
                # 直接查询数据库
                conn = sqlite3.connect(get_db_path())
                c = conn.cursor()
                c.execute('''SELECT category, amount FROM budgets WHERE year=? AND month=?''', (year_int, m_int))
                budgets = c.fetchall()
                conn.close()
                
                if not budgets:
                    return f"{month} 没有设置预算"
                
                result = []
                for cat, budget_amount in budgets:
                    result.append(f"{cat}: 预算 {budget_amount:.2f} 元")
                return "\n".join(result)
            
            elif tool_name == "get_statistics":
                period = arguments.get('period', 'month')
                year = arguments.get('year', datetime.now().year)
                month = arguments.get('month', datetime.now().month)
                group_by = arguments.get('group_by', 'category')
                
                # 获取统计数据
                if period == 'year':
                    stats = tx_module.get_statistics(year=year, group_by=group_by)
                else:
                    stats = tx_module.get_statistics(year=year, month=month, group_by=group_by)
                
                if not stats:
                    if period == 'year':
                        return f"{year}年 没有统计数据"
                    return f"{year}年{month}月 没有统计数据"
                
                return stats
            
            else:
                return f"未知工具：{tool_name}"
        
        except Exception as e:
            return f"工具执行失败：{str(e)}"


# 全局实例
agent_service = AgentService()
