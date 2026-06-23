with open('web/app.py', 'r', encoding='utf-8') as f:
    content = f.read()

marker = "if __name__ == '__main__':"

agent_register = '''# ─── Agent API 路由注册 ──────────────────────────────────────────
from web.agent_routes import register_agent_routes
register_agent_routes(app, api_error, api_success, sync_db_path, db_module)


'''

if 'register_agent_routes' not in content and marker in content:
    content = content.replace(marker, agent_register + marker)

with open('web/app.py', 'w', encoding='utf-8') as f:
    f.write(content)

print('register_agent_routes' in content)
