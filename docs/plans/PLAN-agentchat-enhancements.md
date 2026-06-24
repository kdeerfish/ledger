# AgentChat 增强实施计划

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 解决聊天界面的多个问题，包括样式、进度显示、消息保存、新建对话、全屏模式等

**Architecture:** 在现有AgentChat组件基础上增强，使用localStorage保存聊天记录，添加多对话管理和全屏模式

**Tech Stack:** React, localStorage, CSS animations

---

## 问题清单

| # | 问题 | 优先级 |
|---|------|--------|
| 1 | 思考记录样式未区分 | 高 |
| 2 | 发送-接收进度显示不完整 | 高 |
| 3 | AI回复两条消息/用户消息丢失 | 高 |
| 4 | 聊天记录不保存 | 高 |
| 5 | 缺少新建对话功能 | 中 |
| 6 | Agent架构问题 | - |
| 7 | 缺少全屏模式 | 中 |

---

## Task 1: 聊天记录持久化

**Files:**
- Modify: `frontend/src/components/AgentChat.jsx`

### Step 1: 添加对话管理状态

在组件开头添加对话管理相关状态：

```javascript
// 对话管理
const [conversations, setConversations] = useState(() => {
  const saved = localStorage.getItem('agentConversations');
  return saved ? JSON.parse(saved) : [];
});
const [currentConversationId, setCurrentConversationId] = useState(() => {
  return localStorage.getItem('agentCurrentConversationId') || null;
});
```

### Step 2: 添加保存消息函数

```javascript
// 保存当前对话消息到localStorage
const saveMessages = useCallback((msgs) => {
  if (!currentConversationId) return;
  const conversations = JSON.parse(localStorage.getItem('agentConversations') || '[]');
  const idx = conversations.findIndex(c => c.id === currentConversationId);
  if (idx >= 0) {
    conversations[idx].messages = msgs;
    conversations[idx].updatedAt = Date.now();
  }
  localStorage.setItem('agentConversations', JSON.stringify(conversations));
}, [currentConversationId]);

// 加载对话消息
const loadConversation = useCallback((conversationId) => {
  const conversations = JSON.parse(localStorage.getItem('agentConversations') || '[]');
  const conv = conversations.find(c => c.id === conversationId);
  if (conv) {
    setMessages(conv.messages || []);
    setCurrentConversationId(conversationId);
    localStorage.setItem('agentCurrentConversationId', conversationId);
  }
}, []);
```

### Step 3: 自动保存消息

添加useEffect自动保存：

```javascript
// 自动保存消息
useEffect(() => {
  if (messages.length > 0 && currentConversationId) {
    saveMessages(messages);
  }
}, [messages, currentConversationId, saveMessages]);
```

---

## Task 2: 新建对话功能

**Files:**
- Modify: `frontend/src/components/AgentChat.jsx`

### Step 1: 添加新建对话函数

```javascript
// 新建对话
const createNewConversation = () => {
  const newId = Date.now().toString();
  const newConversation = {
    id: newId,
    title: '新对话',
    messages: [],
    createdAt: Date.now(),
    updatedAt: Date.now()
  };
  
  const conversations = JSON.parse(localStorage.getItem('agentConversations') || '[]');
  conversations.unshift(newConversation);
  localStorage.setItem('agentConversations', JSON.stringify(conversations));
  
  // 保留最近20个对话
  if (conversations.length > 20) {
    conversations.splice(20);
    localStorage.setItem('agentConversations', JSON.stringify(conversations));
  }
  
  setMessages([]);
  setCurrentConversationId(newId);
  localStorage.setItem('agentCurrentConversationId', newId);
};

// 删除对话
const deleteConversation = (conversationId) => {
  const conversations = JSON.parse(localStorage.getItem('agentConversations') || '[]');
  const filtered = conversations.filter(c => c.id !== conversationId);
  localStorage.setItem('agentConversations', JSON.stringify(filtered));
  
  if (currentConversationId === conversationId) {
    if (filtered.length > 0) {
      loadConversation(filtered[0].id);
    } else {
      createNewConversation();
    }
  }
};
```

### Step 2: 初始化时自动创建对话

```javascript
// 初始化对话
useEffect(() => {
  if (!currentConversationId) {
    createNewConversation();
  } else {
    loadConversation(currentConversationId);
  }
}, []);
```

---

## Task 3: 修复消息渲染bug

**Files:**
- Modify: `frontend/src/components/AgentChat.jsx`

### Step 1: 简化消息渲染逻辑

替换当前的消息渲染部分，避免重复渲染：

```javascript
{messages.map(msg => {
  // 思考消息 - 特殊渲染
  if (msg.role === 'thinking') {
    return (
      <div key={msg.id} style={{ maxWidth: '95%', alignSelf: 'flex-start' }}>
        <ThinkingProcess 
          thinking={msg.thinkingContent || ''}
          toolCalls={msg.toolCalls || []}
          isStreaming={msg.isStreaming}
        />
        {/* 思考后的回复内容 */}
        {msg.content && (
          <div style={{
            padding: '10px 14px',
            background: 'white',
            borderRadius: '14px 14px 14px 4px',
            border: '1px solid #e5e7eb',
            marginTop: '8px'
          }}>
            {msg.isStreaming ? (
              <>
                {msg.content}
                <span style={{ 
                  display: 'inline-block',
                  width: '2px',
                  height: '14px',
                  background: '#8b5cf6',
                  marginLeft: '2px',
                  animation: 'blink 1s infinite'
                }}></span>
              </>
            ) : msg.content}
          </div>
        )}
      </div>
    );
  }
  
  // 普通消息
  return (
    <div
      key={msg.id}
      style={{
        maxWidth: '85%',
        padding: '10px 14px',
        borderRadius: msg.role === 'user' ? '14px 14px 4px 14px' : 
                     msg.role === 'assistant' ? '14px 14px 14px 4px' : '8px',
        fontSize: msg.role === 'system' ? '12px' : '14px',
        lineHeight: '1.45',
        wordWrap: 'break-word',
        whiteSpace: 'pre-wrap',
        alignSelf: msg.role === 'user' ? 'flex-end' : 
                   msg.role === 'system' ? 'center' : 'flex-start',
        background: msg.role === 'user' ? '#4f46e5' : 
                   msg.role === 'system' ? '#fef3c7' : 'white',
        color: msg.role === 'user' ? 'white' : 
               msg.role === 'system' ? '#92400e' : '#1f2937',
        border: msg.role === 'assistant' ? '1px solid #e5e7eb' : 'none',
        textAlign: msg.role === 'system' ? 'center' : 'left'
      }}
    >
      {msg.content}
    </div>
  );
})}
```

---

## Task 4: 改进进度显示

**Files:**
- Modify: `frontend/src/components/AgentChat.jsx`

### Step 1: 添加进度状态

```javascript
const [progressStatus, setProgressStatus] = useState('idle'); // idle, connecting, thinking, streaming, done
```

### Step 2: 更新sendMessage函数

```javascript
const sendMessage = async () => {
  const message = inputValue.trim();
  if (!message) return;
  setInputValue('');
  
  // 添加用户消息
  const userMsg = { id: Date.now(), role: 'user', content: message };
  setMessages(prev => [...prev, userMsg]);
  
  if (!config) {
    setMessages(prev => [...prev, { 
      id: Date.now() + 1, 
      role: 'system', 
      content: '请先配置 AI（点击齿轮图标）' 
    }]);
    return;
  }

  setLoading(true);
  setProgressStatus('connecting');
  
  // 添加思考中消息
  const thinkingMsgId = Date.now() + 2;
  const thinkingMsg = { 
    id: thinkingMsgId, 
    role: 'thinking', 
    content: '',
    thinkingContent: '',
    toolCalls: [],
    isStreaming: true
  };
  setMessages(prev => [...prev, thinkingMsg]);
  
  try {
    setProgressStatus('thinking');
    
    const response = await fetch('/api/agent/chat/stream', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        message,
        config,
        history: messages.slice(-10).map(m => ({ role: m.role, content: m.content }))
      })
    });
    
    if (!response.ok) throw new Error(`HTTP error! status: ${response.status}`);
    
    setProgressStatus('streaming');
    
    // ... SSE处理逻辑 ...
    
  } catch (e) {
    setProgressStatus('error');
    // 错误处理...
  } finally {
    setLoading(false);
    setProgressStatus('idle');
  }
};
```

---

## Task 5: 全屏模式

**Files:**
- Modify: `frontend/src/components/AgentChat.jsx`

### Step 1: 添加全屏状态

```javascript
const [isFullscreen, setIsFullscreen] = useState(false);
```

### Step 2: 添加全屏切换函数

```javascript
const toggleFullscreen = () => {
  setIsFullscreen(!isFullscreen);
};
```

### Step 3: 修改聊天窗口样式

```javascript
{/* Chat Window */}
{isOpen && (
  <div style={{
    position: isFullscreen ? 'fixed' : 'absolute',
    top: isFullscreen ? '0' : 'auto',
    left: isFullscreen ? '0' : 'auto',
    right: isFullscreen ? '0' : '0',
    bottom: isFullscreen ? '0' : '70px',
    width: isFullscreen ? '100%' : '380px',
    height: isFullscreen ? '100%' : '520px',
    background: 'white',
    borderRadius: isFullscreen ? '0' : '12px',
    boxShadow: '0 12px 40px rgba(0,0,0,0.18)',
    display: 'flex',
    flexDirection: 'column',
    overflow: 'hidden',
    border: isFullscreen ? 'none' : '1px solid #e5e7eb',
    zIndex: isFullscreen ? 10000 : 9999,
    transition: 'all 0.3s ease'
  }}>
```

### Step 4: 添加全屏按钮

在Header中添加全屏切换按钮：

```javascript
<button
  onClick={toggleFullscreen}
  style={{
    background: 'transparent',
    border: 'none',
    color: 'white',
    fontSize: '16px',
    cursor: 'pointer',
    padding: '4px 8px',
    marginLeft: '4px',
    borderRadius: '4px'
  }}
  title={isFullscreen ? '退出全屏' : '全屏'}
>
  <i className={`bi ${isFullscreen ? 'bi-fullscreen-exit' : 'bi-fullscreen'}`}></i>
</button>
```

---

## Task 6: 对话列表UI

**Files:**
- Modify: `frontend/src/components/AgentChat.jsx`

### Step 1: 添加对话列表状态

```javascript
const [showConversationList, setShowConversationList] = useState(false);
```

### Step 2: 添加对话列表组件

```javascript
{/* 对话列表 */}
{showConversationList && (
  <div style={{
    position: 'absolute',
    top: '60px',
    left: '0',
    right: '0',
    bottom: '0',
    background: 'white',
    zIndex: 10,
    overflowY: 'auto',
    borderTop: '1px solid #e5e7eb'
  }}>
    <div style={{
      padding: '12px',
      borderBottom: '1px solid #e5e7eb',
      display: 'flex',
      justifyContent: 'space-between',
      alignItems: 'center'
    }}>
      <span style={{ fontWeight: 600 }}>对话历史</span>
      <button
        onClick={createNewConversation}
        style={{
          padding: '6px 12px',
          background: '#4f46e5',
          color: 'white',
          border: 'none',
          borderRadius: '6px',
          fontSize: '12px',
          cursor: 'pointer'
        }}
      >
        <i className="bi bi-plus"></i> 新建
      </button>
    </div>
    {conversations.map(conv => (
      <div
        key={conv.id}
        onClick={() => {
          loadConversation(conv.id);
          setShowConversationList(false);
        }}
        style={{
          padding: '12px',
          borderBottom: '1px solid #f3f4f6',
          cursor: 'pointer',
          background: currentConversationId === conv.id ? '#f3f4f6' : 'transparent',
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'center'
        }}
      >
        <div>
          <div style={{ fontSize: '14px', fontWeight: 500 }}>
            {conv.title || '新对话'}
          </div>
          <div style={{ fontSize: '12px', color: '#9ca3af', marginTop: '4px' }}>
            {new Date(conv.updatedAt).toLocaleString()}
          </div>
        </div>
        <button
          onClick={(e) => {
            e.stopPropagation();
            deleteConversation(conv.id);
          }}
          style={{
            background: 'transparent',
            border: 'none',
            color: '#9ca3af',
            cursor: 'pointer',
            padding: '4px'
          }}
        >
          <i className="bi bi-trash"></i>
        </button>
      </div>
    ))}
  </div>
)}
```

---

## 关于Agent的说明

**回答问题6：Agent架构**

1. **Agent没有经过专门训练** - 它是一个通用LLM调用封装，使用各厂商的原生API
2. **不会自动查看Skills** - Skills是给Reasonix（你现在用的这个AI）看的，不是给聊天Agent看的
3. **如需增强Agent能力**，可以：
   - 在system_prompt中添加更多指令
   - 添加更多工具定义
   - 使用RAG检索相关文档

---

## 验收标准

1. ✅ 思考过程有明显的紫色渐变样式区分
2. ✅ 发送消息后显示连接中→思考中→流式输出的完整进度
3. ✅ 用户消息不会消失，AI不会重复回复
4. ✅ 聊天记录保存在localStorage，刷新页面不丢失
5. ✅ 可以新建对话、切换对话、删除对话
6. ✅ 可以切换全屏模式
7. ✅ 最多保留20个对话历史
