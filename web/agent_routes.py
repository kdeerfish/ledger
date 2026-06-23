#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Agent API Routes
"""

import asyncio
from flask import request, jsonify
from functools import wraps


def register_agent_routes(app, api_error, api_success, sync_db_path, db_module):
    """注册 Agent API 路由"""
    import ledger_modules.agent as agent_module
    
    @app.route('/api/agent/chat', methods=['POST'])
    def agent_chat():
        """Agent 聊天接口"""
        sync_db_path()
        data = request.get_json(silent=True)
        if not data:
            return api_error('请求数据不能为空')
        
        message = data.get('message', '').strip()
        if not message:
            return api_error('消息不能为空')
        
        config = data.get('config', {})
        if not config:
            return api_error('请先配置 AI 设置')
        
        if not agent_module.agent_service.load_config(config):
            return api_error('配置加载失败')
        
        system_prompt = """你是 Ledger 记账系统的 AI 助手。你可以帮助用户：
1. 记账：用户说"记一笔午餐30元"，你调用 add_transaction 工具
2. 查询：用户说"查本月支出"，你调用 query_transactions 工具
3. 统计：用户说"本月统计"，你调用 get_statistics 工具
4. 预算：用户说"查预算"，你调用 query_budgets 工具

请用中文回复，简洁明了。如果用户没有明确说日期，默认使用今天。
"""
        
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": message}
        ]
        
        try:
            response = asyncio.run(agent_module.agent_service.chat(messages))
            
            if response.get('choices', [{}])[0].get('message', {}).get('tool_calls'):
                tool_calls = response['choices'][0]['message']['tool_calls']
                return api_success({
                    'response': response['choices'][0]['message']['content'] or '正在处理...',
                    'tool_calls': tool_calls
                })
            
            return api_success({
                'response': response['choices'][0]['message']['content']
            })
        except Exception as e:
            return api_error(f'请求失败: {str(e)}')
    
    @app.route('/api/agent/config', methods=['POST'])
    def save_agent_config():
        """保存 Agent 配置"""
        data = request.get_json(silent=True)
        if not data:
            return api_error('请求数据不能为空')
        return api_success({'message': '配置已保存'})
