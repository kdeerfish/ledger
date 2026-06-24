# AI 思考过程显示功能实现计划

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 在聊天界面实时显示AI助手的思考过程，包括推理步骤和工具调用

**Architecture:** 后端使用SSE（Server-Sent Events）流式返回思考过程，前端通过EventSource实时接收并渲染。思考过程以可折叠区域展示，工具调用以卡片形式显示。

**Tech Stack:** Flask SSE, React EventSource, Bootstrap Icons

---

## 文件结构

| 文件 | 操作 | 职责 |
|------|------|------|
| `web/agent_routes.py` | 修改 | 添加SSE流式端点 |
| `ledger_modules/agent.py` | 修改 | 完善流式响应，提取思考过程 |
| `frontend/src/components/AgentChat.jsx` | 修改 | 添加SSE连接和思考过程UI |

---

## Task 1: 后端 - 添加SSE流式端点

**Files:**
- Modify: `web/agent_routes.py:258-333`

### Step 1: 添加SSE工具函数

在 `register_agent_routes` 函数开头添加SSE辅助函数：

```python
def register_agent_routes(app, api_error, api_success, sync_db_path, db_module):
    """Register Agent API routes"""
    import ledger_modules.agent as agent_module
    from flask import Response, stream_with_context
    
    def sse_event(event_type, data):
        """格式化SSE事件"""
        import json
        return f"event: {event_type}\ndata: {json.dumps(data, ensure_ascii=False)}\n\n"
```

### Step 2: 添加流式聊天端点

在 `agent_chat` 路由后添加新路由：

```python
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
    
    system_prompt = "You are Ledger AI assistant powered by " + provider_names.get(provider, provider) + ". Help with: 1) Add transaction, 2) Query, 3) Statistics, 4) Budget. Reply in Chinese concisely. Today: " + __import__("datetime").datetime.now().strftime("%Y-%m-%d")
    
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
```

---

## Task 2: 后端 - 完善流式响应方法

**Files:**
- Modify: `ledger_modules/agent.py:283-375`

### Step 1: 添加流式聊天方法

在 `AgentService` 类中添加新方法：

```python
async def chat_stream(self, messages: List[Dict]):
    """流式聊天，返回思考过程和内容"""
    if not self.config:
        raise ValueError("未配置 LLM")
    
    base_url = self.get_default_base_url()
    headers = self.build_headers()
    provider_config = self.get_provider_config()
    
    payload = {
        "model": self.config.model,
        "messages": messages,
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
            "stream": True
        }
        if system_msg:
            claude_payload['system'] = system_msg
        
        url = f"{base_url.rstrip('/')}/messages"
        payload = claude_payload
    else:
        url = f"{base_url.rstrip('/')}/chat/completions"
    
    print(f"[Agent Stream] Calling: {url}")
    
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
            tool_calls = []
            current_tool_call = None
            
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
                        
                        # 内容增量
                        if delta.get("content"):
                            full_content += delta["content"]
                            yield {"type": "content", "content": delta["content"]}
                        
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
                        if chunk.get("type") == "content_block_delta":
                            delta = chunk.get("delta", {})
                            if delta.get("type") == "text_delta":
                                full_content += delta.get("text", "")
                                yield {"type": "content", "content": delta.get("text", "")}
                        elif chunk.get("type") == "content_block_start":
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
                            if current_tool_call and chunk.get("delta", {}).get("type") == "input_json_delta":
                                current_tool_call["function"]["arguments"] += chunk["delta"].get("partial_json", "")
                        elif chunk.get("type") == "content_block_stop":
                            if current_tool_call:
                                tool_calls.append(current_tool_call)
                                current_tool_call = None
                
                except json.JSONDecodeError:
                    continue
            
            # 发送工具调用
            if tool_calls:
                for tc in tool_calls:
                    yield {"type": "tool_call", "tool_call": tc}
                    
                    # 执行工具调用
                    try:
                        args = json.loads(tc["function"]["arguments"])
                        result = self.execute_tool(tc["function"]["name"], args)
                        yield {"type": "tool_result", "tool_call": tc, "result": result}
                    except Exception as e:
                        yield {"type": "tool_result", "tool_call": tc, "result": f"工具执行失败: {str(e)}"}
            
            yield {"type": "done", "full_content": full_content}
```

---

## Task 3: 前端 - 添加SSE连接和思考过程UI

**Files:**
- Modify: `frontend/src/components/AgentChat.jsx`

### Step 1: 添加状态变量

在组件开头添加新状态：

```javascript
export default function AgentChat() {
  const [isOpen, setIsOpen] = useState(false);
  const [config, setConfig] = useState(null);
  const [providers, setProviders] = useState({});
  const [messages, setMessages] = useState([]);
  const [inputValue, setInputValue] = useState('');
  const [showSettings, setShowSettings] = useState(false);
  const [loading, setLoading] = useState(false);
  
  // 新增：思考过程相关状态
  const [thinkingContent, setThinkingContent] = useState('');
  const [toolCalls, setToolCalls] = useState([]);
  const [showThinking, setShowThinking] = useState(false);
  const [streamingContent, setStreamingContent] = useState('');
  
  // Settings form state
  const [provider, setProvider] = useState('');
  const [apiKey, setApiKey] = useState('');
  const [model, setModel] = useState('');
  const [customModel, setCustomModel] = useState('');
  const [baseUrl, setBaseUrl] = useState('');
  const [availableModels, setAvailableModels] = useState([]);
  const [fetchingModels, setFetchingModels] = useState(false);
  
  const messagesEndRef = useRef(null);
  const eventSourceRef = useRef(null);
```

### Step 2: 添加SSE连接函数

替换 `sendMessage` 函数：

```javascript
const sendMessage = async () => {
  const message = inputValue.trim();
  if (!message) return;
  setInputValue('');
  addMessage('user', message);
  
  if (!config) {
    addMessage('system', '请先配置 AI（点击齿轮图标）');
    return;
  }

  setLoading(true);
  setThinkingContent('');
  setToolCalls([]);
  setStreamingContent('');
  setShowThinking(true);
  
  // 添加思考中消息
  const thinkingMsgId = Date.now();
  setMessages(prev => [...prev, { 
    id: thinkingMsgId, 
    role: 'thinking', 
    content: '',
    toolCalls: [],
    isStreaming: true
  }]);
  
  try {
    // 使用SSE流式请求
    const response = await fetch('/api/agent/chat/stream', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        message,
        config,
        history: messages.slice(-10).map(m => ({ role: m.role, content: m.content }))
      })
    });
    
    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`);
    }
    
    const reader = response.body.getReader();
    const decoder = new TextDecoder();
    let buffer = '';
    let currentContent = '';
    let currentToolCalls = [];
    
    while (true) {
      const { done, value } = await reader.read();
      if (done) break;
      
      buffer += decoder.decode(value, { stream: true });
      const lines = buffer.split('\n');
      buffer = lines.pop() || '';
      
      for (const line of lines) {
        if (line.startsWith('event: ')) {
          const eventType = line.slice(7).trim();
          continue;
        }
        if (line.startsWith('data: ')) {
          try {
            const data = JSON.parse(line.slice(6));
            
            switch (eventType) {
              case 'thinking':
                setThinkingContent(prev => prev + data.content);
                break;
                
              case 'content':
                currentContent += data.content;
                setStreamingContent(currentContent);
                // 更新消息
                setMessages(prev => prev.map(m => 
                  m.id === thinkingMsgId 
                    ? { ...m, content: currentContent, isStreaming: true }
                    : m
                ));
                break;
                
              case 'tool_call':
                currentToolCalls.push(data.tool_call);
                setToolCalls([...currentToolCalls]);
                // 更新消息
                setMessages(prev => prev.map(m => 
                  m.id === thinkingMsgId 
                    ? { ...m, toolCalls: [...currentToolCalls] }
                    : m
                ));
                break;
                
              case 'tool_result':
                // 更新工具调用结果
                const updatedCalls = currentToolCalls.map(tc => 
                  tc.id === data.tool_call.id 
                    ? { ...tc, result: data.result }
                    : tc
                );
                currentToolCalls = updatedCalls;
                setToolCalls([...currentToolCalls]);
                setMessages(prev => prev.map(m => 
                  m.id === thinkingMsgId 
                    ? { ...m, toolCalls: [...currentToolCalls] }
                    : m
                ));
                break;
                
              case 'done':
                // 完成，更新最终消息
                setMessages(prev => prev.map(m => 
                  m.id === thinkingMsgId 
                    ? { ...m, isStreaming: false, role: 'assistant' }
                    : m
                ));
                break;
                
              case 'error':
                addMessage('system', '错误: ' + data.message);
                break;
            }
          } catch (e) {
            console.error('Parse SSE data error:', e);
          }
        }
      }
    }
    
  } catch (e) {
    console.error('SSE Error:', e);
    // 回退到普通请求
    try {
      const response = await fetch('/api/agent/chat', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          message,
          config,
          history: messages.slice(-10).map(m => ({ role: m.role, content: m.content }))
        })
      });
      const data = await response.json();
      
      // 移除思考中消息
      setMessages(prev => prev.filter(m => m.id !== thinkingMsgId));
      
      if (data.success === false) {
        addMessage('system', '错误: ' + (data.error || '未知错误'));
      } else if (data.data?.response) {
        addMessage('assistant', data.data.response);
      } else if (data.data?.tool_calls) {
        addMessage('assistant', data.data.response || '(模型请求调用工具)');
      }
    } catch (fallbackError) {
      setMessages(prev => prev.filter(m => m.id !== thinkingMsgId));
      addMessage('system', '失败: ' + fallbackError.message);
    }
  } finally {
    setLoading(false);
    setShowThinking(false);
  }
};
```

### Step 3: 添加思考过程渲染组件

在消息渲染部分添加思考过程组件：

```javascript
// 思考过程组件
const ThinkingProcess = ({ thinking, toolCalls, isStreaming }) => {
  const [expanded, setExpanded] = useState(false);
  
  if (!thinking && (!toolCalls || toolCalls.length === 0)) {
    return null;
  }
  
  return (
    <div style={{
      marginBottom: '8px',
      borderRadius: '8px',
      overflow: 'hidden',
      border: '1px solid #e5e7eb',
      background: '#f9fafb'
    }}>
      <button
        onClick={() => setExpanded(!expanded)}
        style={{
          width: '100%',
          padding: '8px 12px',
          background: 'transparent',
          border: 'none',
          display: 'flex',
          alignItems: 'center',
          gap: '8px',
          cursor: 'pointer',
          fontSize: '12px',
          color: '#6b7280'
        }}
      >
        <i className={`bi bi-chevron-${expanded ? 'down' : 'right'}`} style={{ fontSize: '10px' }}></i>
        <i className="bi bi-gear" style={{ fontSize: '14px' }}></i>
        <span>思考过程</span>
        {isStreaming && (
          <span style={{ 
            marginLeft: 'auto',
            width: '8px', 
            height: '8px', 
            borderRadius: '50%', 
            background: '#10b981',
            animation: 'pulse 1.5s infinite'
          }}></span>
        )}
      </button>
      
      {expanded && (
        <div style={{ 
          padding: '0 12px 12px',
          fontSize: '12px',
          lineHeight: '1.5'
        }}>
          {thinking && (
            <div style={{ 
              marginBottom: '8px',
              padding: '8px',
              background: '#fff',
              borderRadius: '6px',
              border: '1px solid #e5e7eb'
            }}>
              <div style={{ fontWeight: 600, marginBottom: '4px', color: '#374151' }}>
                <i className="bi bi-lightbulb"></i> 推理
              </div>
              <div style={{ color: '#4b5563', whiteSpace: 'pre-wrap' }}>
                {thinking}
              </div>
            </div>
          )}
          
          {toolCalls && toolCalls.length > 0 && (
            <div>
              <div style={{ fontWeight: 600, marginBottom: '4px', color: '#374151' }}>
                <i className="bi bi-tools"></i> 工具调用
              </div>
              {toolCalls.map((tc, idx) => (
                <div key={idx} style={{
                  marginBottom: '6px',
                  padding: '8px',
                  background: '#fff',
                  borderRadius: '6px',
                  border: '1px solid #e5e7eb'
                }}>
                  <div style={{ 
                    display: 'flex', 
                    alignItems: 'center', 
                    gap: '6px',
                    marginBottom: '4px'
                  }}>
                    <span style={{
                      padding: '2px 6px',
                      background: '#dbeafe',
                      color: '#1e40af',
                      borderRadius: '4px',
                      fontSize: '11px',
                      fontWeight: 500
                    }}>
                      {tc.function?.name || 'unknown'}
                    </span>
                    <span style={{ color: '#9ca3af', fontSize: '11px' }}>
                      {tc.id?.slice(0, 8)}...
                    </span>
                  </div>
                  
                  <div style={{ 
                    fontSize: '11px', 
                    color: '#6b7280',
                    fontFamily: 'monospace',
                    background: '#f3f4f6',
                    padding: '4px 6px',
                    borderRadius: '4px',
                    marginBottom: '4px'
                  }}>
                    {tc.function?.arguments || '{}'}
                  </div>
                  
                  {tc.result && (
                    <div style={{
                      fontSize: '11px',
                      color: '#059669',
                      background: '#ecfdf5',
                      padding: '4px 6px',
                      borderRadius: '4px'
                    }}>
                      <i className="bi bi-check-circle"></i> {tc.result}
                    </div>
                  )}
                </div>
              ))}
            </div>
          )}
        </div>
      )}
    </div>
  );
};
```

### Step 4: 更新消息渲染

修改消息渲染部分，添加思考过程显示：

```javascript
{messages.map(msg => (
  <div
    key={msg.id}
    style={{
      maxWidth: '85%',
      padding: '10px 14px',
      borderRadius: '14px',
      fontSize: '14px',
      lineHeight: '1.45',
      wordWrap: 'break-word',
      whiteSpace: 'pre-wrap',
      alignSelf: msg.role === 'user' ? 'flex-end' : msg.role === 'assistant' || msg.role === 'thinking' ? 'flex-start' : 'center',
      background: msg.role === 'user' ? '#4f46e5' : msg.role === 'assistant' || msg.role === 'thinking' ? 'white' : '#fef3c7',
      color: msg.role === 'user' ? 'white' : msg.role === 'assistant' || msg.role === 'thinking' ? '#1f2937' : '#92400e',
      border: msg.role === 'assistant' || msg.role === 'thinking' ? '1px solid #e5e7eb' : 'none',
      borderRadius: msg.role === 'user' ? '14px 14px 4px 14px' : msg.role === 'assistant' || msg.role === 'thinking' ? '14px 14px 14px 4px' : '8px',
      fontSize: msg.role === 'system' ? '12px' : '14px',
      maxWidth: msg.role === 'system' ? '95%' : '85%',
      textAlign: msg.role === 'system' ? 'center' : 'left'
    }}
  >
    {/* 思考过程 */}
    {msg.role === 'thinking' && (
      <ThinkingProcess 
        thinking={thinkingContent}
        toolCalls={msg.toolCalls}
        isStreaming={msg.isStreaming}
      />
    )}
    
    {/* 消息内容 */}
    {msg.content && (
      <div>
        {msg.role === 'thinking' && msg.isStreaming ? (
          <span>{msg.content}<span style={{ 
            display: 'inline-block',
            width: '2px',
            height: '14px',
            background: '#4f46e5',
            marginLeft: '2px',
            animation: 'blink 1s infinite'
          }}></span></span>
        ) : (
          msg.content
        )}
      </div>
    )}
    
    {/* 加载动画 */}
    {msg.role === 'thinking' && !msg.content && msg.isStreaming && (
      <div style={{ display: 'flex', gap: '4px', padding: '4px 0' }}>
        <span style={{ 
          width: '6px', 
          height: '6px', 
          borderRadius: '50%', 
          background: '#9ca3af',
          animation: 'bounce 1.4s infinite ease-in-out both',
          animationDelay: '-0.32s'
        }}></span>
        <span style={{ 
          width: '6px', 
          height: '6px', 
          borderRadius: '50%', 
          background: '#9ca3af',
          animation: 'bounce 1.4s infinite ease-in-out both',
          animationDelay: '-0.16s'
        }}></span>
        <span style={{ 
          width: '6px', 
          height: '6px', 
          borderRadius: '50%', 
          background: '#9ca3af',
          animation: 'bounce 1.4s infinite ease-in-out both'
        }}></span>
      </div>
    )}
  </div>
))}
```

### Step 5: 添加CSS动画

在组件开头添加样式：

```javascript
// 添加到组件外部或使用内联样式
const styles = `
  @keyframes pulse {
    0%, 100% { opacity: 1; }
    50% { opacity: 0.5; }
  }
  
  @keyframes blink {
    0%, 100% { opacity: 1; }
    50% { opacity: 0; }
  }
  
  @keyframes bounce {
    0%, 80%, 100% { transform: scale(0); }
    40% { transform: scale(1); }
  }
`;

// 在组件渲染前添加样式标签
useEffect(() => {
  const styleElement = document.createElement('style');
  styleElement.textContent = styles;
  document.head.appendChild(styleElement);
  return () => document.head.removeChild(styleElement);
}, []);
```

---

## Task 4: 测试和验证

### Step 1: 测试后端SSE端点

```bash
# 启动服务器
python web/run.py

# 使用curl测试SSE
curl -X POST http://localhost:5000/api/agent/chat/stream \
  -H "Content-Type: application/json" \
  -d '{"message": "查询本月支出", "config": {"provider": "deepseek", "api_key": "your-key", "model": "deepseek-chat"}, "history": []}'
```

### Step 2: 测试前端功能

1. 打开聊天界面
2. 配置AI（选择provider、输入API Key、选择模型）
3. 发送消息，观察：
   - 思考过程是否显示
   - 工具调用是否实时展示
   - 最终结果是否正确

### Step 3: 检查边界情况

- 无API Key时的错误处理
- 网络断开时的回退机制
- 长时间无响应的超时处理

---

## 验收标准

1. ✅ 发送消息后，显示"思考中"动画
2. ✅ 思考过程以可折叠区域展示
3. ✅ 工具调用实时显示（函数名、参数、结果）
4. ✅ 最终回复正确显示
5. ✅ 流式输出时有光标动画
6. ✅ 错误时有友好提示

---

## 后续优化

1. 添加思考过程的复制按钮
2. 支持展开/折叠所有思考过程
3. 添加思考过程的搜索功能
4. 优化长文本的渲染性能
