#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Agent API Routes
"""

import asyncio
from flask import request, jsonify


def register_agent_routes(app, api_error, api_success, sync_db_path, db_module):
    """注册 Agent API 路由"""
    import ledger_modules.agent as agent_module
    
    @app.route('/api/agent/providers', methods=['GET'])
    def agent_providers():
        """获取支持的 AI 厂商列表"""
        providers = [
            {'id': 'openai', 'name': 'OpenAI', 'models': ['gpt-3.5-turbo', 'gpt-4', 'gpt-4o', 'gpt-4o-mini', 'gpt-4-turbo']},
            {'id': 'claude', 'name': 'Claude', 'models': ['claude-3-5-sonnet-20241022', 'claude-3-opus-20240229', 'claude-3-haiku-20240307']},
            {'id': 'deepseek', 'name': 'DeepSeek', 'models': ['deepseek-chat', 'deepseek-coder', 'deepseek-reasoner']},
            {'id': 'qwen', 'name': '通义千问 (阿里)', 'models': ['qwen-turbo', 'qwen-plus', 'qwen-max', 'qwen-long', 'qwen2.5-72b-instruct', 'qwen2.5-32b-instruct', 'qwen2.5-14b-instruct', 'qwen2.5-7b-instruct']},
            {'id': 'wenxin', 'name': '文心一言 (百度)', 'models': ['ernie-4.0-8k', 'ernie-3.5-8k', 'ernie-3.5-128k', 'ernie-speed-8k', 'ernie-lite-8k', 'ernie-tiny-8k']},
            {'id': 'glm', 'name': '智谱AI (GLM)', 'models': ['glm-4', 'glm-4-plus', 'glm-4-0520', 'glm-4-air', 'glm-4-airx', 'glm-4-long', 'glm-4-flash', 'glm-3-turbo']},
            {'id': 'moonshot', 'name': 'Kimi (月之暗面)', 'models': ['moonshot-v1-8k', 'moonshot-v1-32k', 'moonshot-v1-128k', 'moonshot-v1-auto']},
            {'id': 'hunyuan', 'name': '腾讯混元', 'models': ['hunyuan-pro', 'hunyuan-standard', 'hunyuan-lite', 'hunyuan-turbo', 'hunyuan-code', 'hunyuan-role']},
            {'id': 'spark', 'name': '讯飞星火', 'models': ['general', 'generalv3', 'generalv3.5', 'pro-128k', 'max-32k', 'lite']},
            {'id': 'doubao', 'name': '豆包 (字节跳动)', 'models': ['doubao-pro-32k', 'doubao-pro-128k', 'doubao-lite-4k', 'doubao-lite-32k', 'doubao-lite-128k']},
            {'id': 'minimax', 'name': 'MiniMax', 'models': ['MiniMax-text-01', 'MiniMax-VL-01']},
            {'id': 'ollama', 'name': 'Ollama (本地)', 'models': ['llama3', 'qwen2', 'mistral', 'gemma2', 'phi3', 'codellama']},
            {'id': 'custom', 'name': '自定义 (OpenAI兼容)', 'models': []},
        ]
        return api_success(providers)
    
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
        
        provider = config.get('provider', 'openai')
        provider_names = {
            'openai': 'OpenAI', 'claude': 'Claude', 'deepseek': 'DeepSeek',
            'qwen': '通义千问', 'wenxin': '文心一言', 'glm': '智谱GLM',
            'moonshot': 'Kimi', 'hunyuan': '腾讯混元', 'spark': '讯飞星火',
            'doubao': '豆包', 'minimax': 'MiniMax', 'ollama': 'Ollama', 'custom': '自定义'
        }
        
        system_prompt = f"""你是 Ledger 记账系统的 AI 助手（由 {provider_names.get(provider, provider)} 提供能力）。你可以帮助用户：
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
            
            # 处理 Claude 响应
            if provider == 'claude':
                content = ''
                tool_calls = None
                if response.get('content'):
                    for block in response['content']:
                        if block.get('type') == 'text':
                            content += block.get('text', '')
                return api_success({
                    'response': content or '收到回复',
                    'tool_calls': tool_calls
                })
            
            # OpenAI 兼容响应
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
