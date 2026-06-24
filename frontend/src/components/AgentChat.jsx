import { useState, useEffect, useRef, useCallback } from 'react';

const PROVIDERS_GROUPS = {
  '国内': ['deepseek', 'qwen_cn', 'qwen_global', 'wenxin', 'glm_cn', 'glm_global', 'moonshot_cn', 'moonshot_global', 'hunyuan', 'spark', 'doubao', 'minimax', 'mimo', 'stepfun', 'yi', 'baichuan', 'siliconflow', 'dashscope'],
  '国际': ['openai', 'claude', 'groq', 'together', 'mistral', 'cohere', 'jina', 'ollama'],
  '自定义': ['custom']
};

const HINTS = {
  'custom': 'Custom: fill Base URL, model name and API Key. OpenAI compatible.',
  'ollama': 'Ollama local. Default: http://localhost:11434. API Key optional.',
  'wenxin': 'Wenxin uses Qianfan API. Get API Key from Baidu Cloud.'
};

export default function AgentChat() {
  // 基础状态
  const [isOpen, setIsOpen] = useState(false);
  const [isFullscreen, setIsFullscreen] = useState(false);
  const [providers, setProviders] = useState({});
  const [messages, setMessages] = useState([]);
  const [inputValue, setInputValue] = useState('');
  const [showSettings, setShowSettings] = useState(false);
  const [loading, setLoading] = useState(false);
  const [progressStatus, setProgressStatus] = useState('idle');

  // 多套配置管理（数据层由后端 SQLite 承载；前端只缓存）
  const [configs, setConfigs] = useState([]);           // 来自 GET /api/agent/configs
  const [activeConfigId, setActiveConfigId] = useState(null);

  // 对话管理
  const [conversations, setConversations] = useState([]);
  const [currentConversationId, setCurrentConversationId] = useState(null);
  const [showConversationList, setShowConversationList] = useState(false);

  // Settings form state
  const [provider, setProvider] = useState('');
  const [apiKey, setApiKey] = useState('');
  const [model, setModel] = useState('');
  const [customModel, setCustomModel] = useState('');
  const [baseUrl, setBaseUrl] = useState('');
  const [availableModels, setAvailableModels] = useState([]);
  const [fetchingModels, setFetchingModels] = useState(false);

  // 多套配置编辑器：editingConfigId 决定「新建」还是「编辑」
  // 额外字段走「其他 (高级)」折叠区
  const [editingConfigId, setEditingConfigId] = useState(null); // null = 新建
  const [configName, setConfigName] = useState('');
  const [configIsDefault, setConfigIsDefault] = useState(false);
  const [configIsEnabled, setConfigIsEnabled] = useState(true);
  const [configSystemPrompt, setConfigSystemPrompt] = useState('');
  const [showAdvanced, setShowAdvanced] = useState(false);
  const [editorSaving, setEditorSaving] = useState(false);

  // Header 选择器
  const [showConfigPicker, setShowConfigPicker] = useState(false);
  const [toastMessage, setToastMessage] = useState(null); // 切换后的提示
  
  const messagesEndRef = useRef(null);

  // CSS动画
  useEffect(() => {
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
      @keyframes spin {
        from { transform: rotate(0deg); }
        to { transform: rotate(360deg); }
      }
      @keyframes slideIn {
        from { opacity: 0; transform: translateY(10px); }
        to { opacity: 1; transform: translateY(0); }
      }
    `;
    const styleElement = document.createElement('style');
    styleElement.textContent = styles;
    document.head.appendChild(styleElement);
    return () => document.head.removeChild(styleElement);
  }, []);

  // 自动滚动
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  // 初始化
  useEffect(() => {
    initAgent();
    loadConversations();
  }, []);

  // 加载对话列表
  const loadConversations = () => {
    try {
      const saved = localStorage.getItem('agentConversations');
      const convs = saved ? JSON.parse(saved) : [];
      setConversations(convs);
      
      // 加载最近的对话
      const currentId = localStorage.getItem('agentCurrentConversationId');
      if (currentId && convs.find(c => c.id === currentId)) {
        setCurrentConversationId(currentId);
        const conv = convs.find(c => c.id === currentId);
        setMessages(conv.messages || []);
      } else if (convs.length > 0) {
        setCurrentConversationId(convs[0].id);
        setMessages(convs[0].messages || []);
      } else {
        createNewConversation();
      }
    } catch (e) {
      createNewConversation();
    }
  };

  // 保存消息到localStorage
  const saveMessages = useCallback((msgs) => {
    if (!currentConversationId) return;
    try {
      const convs = JSON.parse(localStorage.getItem('agentConversations') || '[]');
      const idx = convs.findIndex(c => c.id === currentConversationId);
      if (idx >= 0) {
        // 过滤掉system欢迎消息，只保存有意义的对话
        const meaningfulMessages = msgs.filter(m => 
          m.role !== 'system' || !m.content.includes('你好！试试说')
        );
        convs[idx].messages = meaningfulMessages;
        convs[idx].updatedAt = Date.now();
        // 更新标题为第一条用户消息
        const firstUserMsg = meaningfulMessages.find(m => m.role === 'user');
        if (firstUserMsg) {
          convs[idx].title = firstUserMsg.content.substring(0, 30) + (firstUserMsg.content.length > 30 ? '...' : '');
        }
        // 保留最近20个对话
        if (convs.length > 20) {
          convs.splice(20);
        }
        localStorage.setItem('agentConversations', JSON.stringify(convs));
        setConversations(convs);
      }
    } catch (e) {
      console.error('Save messages failed:', e);
    }
  }, [currentConversationId]);

  // 自动保存
  useEffect(() => {
    if (messages.length > 0 && currentConversationId) {
      const timer = setTimeout(() => saveMessages(messages), 500);
      return () => clearTimeout(timer);
    }
  }, [messages, currentConversationId, saveMessages]);

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
    
    const convs = JSON.parse(localStorage.getItem('agentConversations') || '[]');
    convs.unshift(newConversation);
    if (convs.length > 20) convs.splice(20);
    localStorage.setItem('agentConversations', JSON.stringify(convs));
    
    setConversations(convs);
    setMessages([]);
    setCurrentConversationId(newId);
    localStorage.setItem('agentCurrentConversationId', newId);
    setShowConversationList(false);
  };

  // 切换对话
  const switchConversation = (convId) => {
    const convs = JSON.parse(localStorage.getItem('agentConversations') || '[]');
    const conv = convs.find(c => c.id === convId);
    if (conv) {
      setMessages(conv.messages || []);
      setCurrentConversationId(convId);
      localStorage.setItem('agentCurrentConversationId', convId);
      setShowConversationList(false);
    }
  };

  // 删除对话
  const deleteConversation = (e, convId) => {
    e.stopPropagation();
    const convs = JSON.parse(localStorage.getItem('agentConversations') || '[]');
    const filtered = convs.filter(c => c.id !== convId);
    localStorage.setItem('agentConversations', JSON.stringify(filtered));
    setConversations(filtered);
    
    if (currentConversationId === convId) {
      if (filtered.length > 0) {
        switchConversation(filtered[0].id);
      } else {
        createNewConversation();
      }
    }
  };

  const initAgent = async () => {
    try {
      const res = await fetch('/api/agent/providers');
      const data = await res.json();
      if (data.success && Array.isArray(data.data)) {
        const providersObj = {};
        data.data.forEach(p => { providersObj[p.id] = p; });
        setProviders(providersObj);
      }
    } catch (e) {}

    // 配置改由后端持久化（多套并存）
    await loadConfigs();
  };

  const loadConfigs = async () => {
    try {
      const res = await fetch('/api/agent/configs');
      const data = await res.json();
      if (data.success && data.data) {
        const list = data.data.configs || [];
        setConfigs(list);
        const defId = data.data.default_id;
        if (defId && list.find(c => c.id === defId)) {
          setActiveConfigId(defId);
        } else if (list.length > 0) {
          // 没有标记默认时，选最新更新的一条
          setActiveConfigId(list[0].id);
        }
      }
    } catch (e) {
      console.error('loadConfigs failed:', e);
    }
  };

  // 当前激活配置的派生对象（送进 sendMessage 时不需要，前端用 config_id 即可）
  const activeConfig = configs.find(c => c.id === activeConfigId) || null;

  const toggleChat = () => {
    setIsOpen(!isOpen);
  };

  // 思考过程组件
  const ThinkingProcess = ({ thinking, toolCalls, isStreaming, elapsedTime }) => {
    const [expanded, setExpanded] = useState(true);
    
    if (!thinking && (!toolCalls || toolCalls.length === 0)) {
      return null;
    }
    
    const formatTime = (seconds) => {
      if (seconds < 60) return `${seconds}秒`;
      const mins = Math.floor(seconds / 60);
      const secs = seconds % 60;
      return `${mins}分${secs}秒`;
    };
    
    return (
      <div style={{
        marginBottom: '12px',
        borderRadius: '12px',
        overflow: 'hidden',
        background: 'linear-gradient(135deg, #f5f3ff 0%, #ede9fe 100%)',
        border: '1px solid #e0d4fd',
        boxShadow: '0 2px 8px rgba(139, 92, 246, 0.08)',
        animation: 'slideIn 0.3s ease'
      }}>
        <button
          onClick={() => setExpanded(!expanded)}
          style={{
            width: '100%',
            padding: '10px 14px',
            background: 'transparent',
            border: 'none',
            display: 'flex',
            alignItems: 'center',
            gap: '10px',
            cursor: 'pointer',
            fontSize: '13px',
            color: '#6d28d9',
            fontWeight: 500
          }}
        >
          <div style={{
            width: '24px',
            height: '24px',
            borderRadius: '6px',
            background: 'linear-gradient(135deg, #8b5cf6 0%, #7c3aed 100%)',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            color: 'white',
            fontSize: '12px'
          }}>
            <i className="bi bi-lightbulb-fill"></i>
          </div>
          
          <div style={{ flex: 1, textAlign: 'left' }}>
            {isStreaming ? (
              <span>
                <span style={{ marginRight: '8px' }}>思考中</span>
                <span style={{ display: 'inline-flex', gap: '3px', alignItems: 'center' }}>
                  {[0, 0.2, 0.4].map((delay, i) => (
                    <span key={i} style={{
                      width: '4px',
                      height: '4px',
                      borderRadius: '50%',
                      background: '#8b5cf6',
                      animation: `pulse 1.2s ease-in-out infinite ${delay}s`
                    }}></span>
                  ))}
                </span>
              </span>
            ) : (
              <span>已思考 {formatTime(elapsedTime || 0)}</span>
            )}
          </div>
          
          {isStreaming && (
            <span style={{ fontSize: '12px', color: '#a78bfa', marginRight: '8px' }}>
              {formatTime(elapsedTime || 0)}
            </span>
          )}
          
          <i className={`bi bi-chevron-${expanded ? 'up' : 'down'}`} 
             style={{ fontSize: '12px', color: '#a78bfa' }}></i>
        </button>
        
        {expanded && (
          <div style={{ padding: '0 14px 14px', fontSize: '13px', lineHeight: '1.6' }}>
            {thinking && (
              <div style={{ 
                marginBottom: '10px',
                padding: '12px',
                background: 'rgba(255, 255, 255, 0.7)',
                borderRadius: '8px',
                border: '1px solid #e0d4fd'
              }}>
                <div style={{ color: '#4c1d95', whiteSpace: 'pre-wrap', fontStyle: 'italic', opacity: 0.9 }}>
                  {thinking}
                </div>
              </div>
            )}
            
            {toolCalls && toolCalls.length > 0 && (
              <div>
                {toolCalls.map((tc, idx) => (
                  <div key={idx} style={{
                    marginBottom: '8px',
                    padding: '10px 12px',
                    background: 'rgba(255, 255, 255, 0.7)',
                    borderRadius: '8px',
                    border: '1px solid #e0d4fd'
                  }}>
                    <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '8px' }}>
                      <span style={{
                        padding: '3px 8px',
                        background: 'linear-gradient(135deg, #8b5cf6 0%, #7c3aed 100%)',
                        color: 'white',
                        borderRadius: '6px',
                        fontSize: '11px',
                        fontWeight: 600,
                        display: 'flex',
                        alignItems: 'center',
                        gap: '4px'
                      }}>
                        <i className="bi bi-gear-fill"></i>
                        {tc.function?.name || 'unknown'}
                      </span>
                      <span style={{ color: '#a78bfa', fontSize: '11px', marginLeft: 'auto' }}>
                        #{idx + 1}
                      </span>
                    </div>
                    
                    <div style={{ 
                      fontSize: '11px', color: '#5b21b6',
                      fontFamily: '"SF Mono", monospace',
                      background: 'rgba(139, 92, 246, 0.08)',
                      padding: '6px 8px', borderRadius: '6px',
                      marginBottom: '6px', wordBreak: 'break-all'
                    }}>
                      {tc.function?.arguments || '{}'}
                    </div>
                    
                    {tc.result && (
                      <div style={{
                        fontSize: '11px', color: '#059669',
                        background: 'rgba(16, 185, 129, 0.08)',
                        padding: '6px 8px', borderRadius: '6px',
                        display: 'flex', alignItems: 'flex-start', gap: '6px'
                      }}>
                        <i className="bi bi-check-circle-fill" style={{ marginTop: '2px' }}></i>
                        <span>{tc.result}</span>
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

  // 发送消息
  const sendMessage = async () => {
    const message = inputValue.trim();
    if (!message || loading) return;
    setInputValue('');
    
    const userMsgId = Date.now();
    const userMsg = { id: userMsgId, role: 'user', content: message };
    setMessages(prev => [...prev, userMsg]);

    if (!activeConfigId || !activeConfig) {
      setMessages(prev => [...prev, {
        id: Date.now() + 1,
        role: 'system',
        content: '请先配置 AI（点击齿轮图标）'
      }]);
      return;
    }

    setLoading(true);
    setProgressStatus('connecting');
    
    const thinkingMsgId = Date.now() + 2;
    const thinkingMsg = { 
      id: thinkingMsgId, 
      role: 'thinking', 
      content: '',
      thinkingContent: '',
      toolCalls: [],
      isStreaming: true,
      startTime: Date.now(),
      elapsedTime: 0
    };
    setMessages(prev => [...prev, thinkingMsg]);
    
    // 计时器
    const timer = setInterval(() => {
      setMessages(prev => prev.map(m => 
        m.id === thinkingMsgId 
          ? { ...m, elapsedTime: Math.floor((Date.now() - m.startTime) / 1000) }
          : m
      ));
    }, 1000);
    
    try {
      setProgressStatus('thinking');
      
      const response = await fetch('/api/agent/chat/stream', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          message,
          config_id: activeConfigId,
          history: messages.filter(m => m.role === 'user' || m.role === 'assistant')
            .slice(-10)
            .map(m => ({ role: m.role, content: m.content }))
        })
      });
      
      if (!response.ok) throw new Error(`HTTP error! status: ${response.status}`);
      
      setProgressStatus('streaming');
      
      const reader = response.body.getReader();
      const decoder = new TextDecoder();
      let buffer = '';
      let currentContent = '';
      let currentToolCalls = [];
      let currentThinking = '';
      let eventType = '';
      
      while (true) {
        const { done, value } = await reader.read();
        if (done) break;
        
        buffer += decoder.decode(value, { stream: true });
        const lines = buffer.split('\n');
        buffer = lines.pop() || '';
        
        for (const line of lines) {
          if (line.startsWith('event: ')) {
            eventType = line.slice(7).trim();
            continue;
          }
          if (line.startsWith('data: ')) {
            try {
              const data = JSON.parse(line.slice(6));
              
              switch (eventType) {
                case 'thinking':
                  currentThinking += data.content;
                  setMessages(prev => prev.map(m => 
                    m.id === thinkingMsgId 
                      ? { ...m, thinkingContent: currentThinking }
                      : m
                  ));
                  break;
                  
                case 'content':
                  currentContent += data.content;
                  setMessages(prev => prev.map(m => 
                    m.id === thinkingMsgId 
                      ? { ...m, content: currentContent }
                      : m
                  ));
                  break;
                  
                case 'tool_call':
                  currentToolCalls.push(data.tool_call);
                  setMessages(prev => prev.map(m => 
                    m.id === thinkingMsgId 
                      ? { ...m, toolCalls: [...currentToolCalls] }
                      : m
                  ));
                  break;
                  
                case 'tool_result':
                  currentToolCalls = currentToolCalls.map(tc => 
                    tc.id === data.tool_call?.id 
                      ? { ...tc, result: data.result }
                      : tc
                  );
                  setMessages(prev => prev.map(m => 
                    m.id === thinkingMsgId 
                      ? { ...m, toolCalls: [...currentToolCalls] }
                      : m
                  ));
                  break;
                  
                case 'done':
                  setMessages(prev => prev.map(m => 
                    m.id === thinkingMsgId 
                      ? { ...m, isStreaming: false }
                      : m
                  ));
                  break;
                  
                case 'error':
                  setMessages(prev => [...prev.filter(m => m.id !== thinkingMsgId), {
                    id: Date.now(),
                    role: 'system',
                    content: '错误: ' + (data.message || '未知错误')
                  }]);
                  break;
              }
            } catch (e) {
              console.error('Parse SSE error:', e);
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
            config_id: activeConfigId,
            history: messages.filter(m => m.role === 'user' || m.role === 'assistant')
              .slice(-10)
              .map(m => ({ role: m.role, content: m.content }))
          })
        });
        const data = await response.json();
        
        setMessages(prev => prev.filter(m => m.id !== thinkingMsgId));
        
        if (data.success === false) {
          setMessages(prev => [...prev, { id: Date.now(), role: 'system', content: '错误: ' + (data.error || '未知错误') }]);
        } else if (data.data?.response) {
          setMessages(prev => [...prev, { id: Date.now(), role: 'assistant', content: data.data.response }]);
        }
      } catch (fallbackError) {
        setMessages(prev => prev.filter(m => m.id !== thinkingMsgId));
        setMessages(prev => [...prev, { id: Date.now(), role: 'system', content: '失败: ' + fallbackError.message }]);
      }
    } finally {
      clearInterval(timer);
      setLoading(false);
      setProgressStatus('idle');
    }
  };

  const handleKeyPress = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      sendMessage();
    }
  };

  const resetEditor = () => {
    setEditingConfigId(null);
    setProvider('');
    setApiKey('');
    setModel('');
    setCustomModel('');
    setBaseUrl('');
    setAvailableModels([]);
    setConfigName('');
    setConfigIsDefault(false);
    setConfigIsEnabled(true);
    setConfigSystemPrompt('');
    setShowAdvanced(false);
  };

  const loadConfigIntoEditor = (cfg) => {
    setEditingConfigId(cfg.id);
    setProvider(cfg.provider || '');
    setApiKey(cfg.api_key || '');
    setModel(cfg.model || '');
    setCustomModel('');
    setBaseUrl(cfg.base_url || '');
    setConfigName(cfg.name || '');
    setConfigIsDefault(!!cfg.is_default);
    setConfigIsEnabled(cfg.is_enabled !== false);
    setConfigSystemPrompt(cfg.system_prompt || '');
    const p = providers[cfg.provider];
    setAvailableModels(p && p.models ? p.models : []);
    setShowAdvanced(false);
  };

  const saveEditorConfig = async () => {
    const selectedModel = model === '__custom__' ? customModel : model;
    if (!provider) { alert('请选择 Provider'); return; }
    if (!selectedModel) { alert('请输入模型名称'); return; }
    if (!apiKey && provider !== 'ollama') { alert('请输入 API Key'); return; }

    const payload = {
      name: configName.trim() || (provider + ' / ' + selectedModel),
      provider,
      model: selectedModel,
      api_key: apiKey,
      base_url: baseUrl,
      system_prompt: configSystemPrompt,
      is_default: configIsDefault,
      is_enabled: configIsEnabled,
    };

    setEditorSaving(true);
    try {
      const url = editingConfigId
        ? '/api/agent/configs/' + editingConfigId
        : '/api/agent/configs';
      const method = editingConfigId ? 'PUT' : 'POST';
      const res = await fetch(url, {
        method,
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload),
      });
      const data = await res.json();
      if (!data.success) {
        alert('保存失败: ' + (data.error || '未知错误'));
        return;
      }
      const newId = data.data.id;
      await loadConfigs();
      setActiveConfigId(newId);
      setMessages(prev => [...prev, { id: Date.now(), role: 'system', content: '设置已保存！' }]);
      resetEditor();
      setShowSettings(false);
    } catch (e) {
      alert('保存失败: ' + e.message);
    } finally {
      setEditorSaving(false);
    }
  };

  const deleteConfig = async (configId, e) => {
    e.stopPropagation();
    if (!window.confirm('确定删除这条配置？')) return;
    try {
      const res = await fetch('/api/agent/configs/' + configId, { method: 'DELETE' });
      const data = await res.json();
      if (!data.success) {
        alert('删除失败: ' + (data.error || '未知错误'));
        return;
      }
      if (editingConfigId === configId) resetEditor();
      await loadConfigs();
    } catch (e) {
      alert('删除失败: ' + e.message);
    }
  };

  const setAsDefault = async (configId, e) => {
    e.stopPropagation();
    try {
      const res = await fetch('/api/agent/configs/' + configId + '/set_default', { method: 'POST' });
      const data = await res.json();
      if (!data.success) {
        alert('设置默认失败: ' + (data.error || '未知错误'));
        return;
      }
      await loadConfigs();
    } catch (e) {
      alert('设置默认失败: ' + e.message);
    }
  };

  // 聊天窗口内热切换（不进入编辑弹窗）
  const switchActiveConfig = (cfg, e) => {
    if (e) e.stopPropagation();
    if (!cfg || cfg.id === activeConfigId) {
      setShowConfigPicker(false);
      return;
    }
    setActiveConfigId(cfg.id);
    setShowConfigPicker(false);
    const label = cfg.name || (cfg.provider + ' / ' + cfg.model);
    setToastMessage('已切换到：' + label);
  };

  // 自动消失 toast
  useEffect(() => {
    if (!toastMessage) return undefined;
    const t = setTimeout(() => setToastMessage(null), 2200);
    return () => clearTimeout(t);
  }, [toastMessage]);

  const handleProviderChange = (e) => {
    const newProvider = e.target.value;
    setProvider(newProvider);
    setModel('');
    setCustomModel('');
    
    const p = providers[newProvider];
    if (p && p.models && p.models.length > 0) {
      setAvailableModels(p.models);
    } else {
      setAvailableModels([]);
    }
  };

  const fetchModels = async () => {
    if (!apiKey && provider !== 'ollama') {
      alert('请先输入 API Key');
      return;
    }

    setFetchingModels(true);
    
    try {
      const res = await fetch('/api/agent/fetch_models', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ provider, api_key: apiKey, base_url: baseUrl })
      });
      const data = await res.json();
      if (data.success && data.data.models) {
        const newModels = data.data.models.filter(m => !availableModels.includes(m));
        if (newModels.length > 0) {
          setAvailableModels(prev => [...prev, ...newModels]);
          setMessages(prev => [...prev, { id: Date.now(), role: 'system', content: '获取到 ' + newModels.length + ' 个新模型' }]);
        } else {
          setMessages(prev => [...prev, { id: Date.now(), role: 'system', content: '没有找到新模型' }]);
        }
      } else {
        alert('失败: ' + (data.error || '未知错误'));
      }
    } catch (e) {
      alert('错误: ' + e.message);
    } finally {
      setFetchingModels(false);
    }
  };

  const renderProviderOptions = () => {
    const options = [];
    for (const [group, ids] of Object.entries(PROVIDERS_GROUPS)) {
      const groupOptions = ids
        .filter(id => providers[id])
        .map(id => (
          <option key={id} value={id}>{providers[id].name}</option>
        ));
      if (groupOptions.length > 0) {
        options.push(
          <optgroup key={group} label={group}>
            {groupOptions}
          </optgroup>
        );
      }
    }
    return options;
  };

  // 渲染消息
  const renderMessage = (msg) => {
    if (msg.role === 'thinking') {
      return (
        <div key={msg.id} style={{ maxWidth: '95%', alignSelf: 'flex-start', animation: 'slideIn 0.3s ease' }}>
          <ThinkingProcess 
            thinking={msg.thinkingContent || ''}
            toolCalls={msg.toolCalls || []}
            isStreaming={msg.isStreaming}
            elapsedTime={msg.elapsedTime || 0}
          />
          {msg.content && (
            <div style={{
              padding: '10px 14px',
              background: 'white',
              borderRadius: '14px 14px 14px 4px',
              border: '1px solid #e5e7eb',
              marginTop: '8px',
              fontSize: '14px',
              lineHeight: '1.45',
              wordWrap: 'break-word',
              whiteSpace: 'pre-wrap'
            }}>
              {msg.content}
              {msg.isStreaming && (
                <span style={{ 
                  display: 'inline-block',
                  width: '2px',
                  height: '14px',
                  background: '#8b5cf6',
                  marginLeft: '2px',
                  animation: 'blink 1s infinite'
                }}></span>
              )}
            </div>
          )}
        </div>
      );
    }
    
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
          textAlign: msg.role === 'system' ? 'center' : 'left',
          animation: 'slideIn 0.3s ease'
        }}
      >
        {msg.content}
      </div>
    );
  };

  return (
    <>
      {/* Chat Toggle Button */}
      <div style={{
        position: 'fixed',
        bottom: '24px',
        right: '24px',
        zIndex: 9999,
        fontFamily: '-apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif'
      }}>
        <button
          onClick={toggleChat}
          style={{
            width: '56px',
            height: '56px',
            borderRadius: '50%',
            background: 'linear-gradient(135deg, #4f46e5 0%, #7c3aed 100%)',
            border: 'none',
            color: 'white',
            fontSize: '24px',
            cursor: 'pointer',
            boxShadow: '0 4px 16px rgba(79,70,229,0.4)',
            transition: 'all 0.2s'
          }}
          title="AI 助手"
        >
          <i className={`bi ${isOpen ? 'bi-x-lg' : 'bi-robot'}`}></i>
        </button>

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
            zIndex: isFullscreen ? 10001 : 9999,
            transition: 'all 0.3s ease'
          }}>
            {/* Header */}
            <div style={{
              background: 'linear-gradient(135deg, #4f46e5 0%, #7c3aed 100%)',
              color: 'white',
              padding: '14px 16px',
              display: 'flex',
              justifyContent: 'space-between',
              alignItems: 'center',
              fontWeight: 600
            }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: '8px', flex: 1, minWidth: 0 }}>
                <i className="bi bi-robot"></i>
                {/* 配置选择器 */}
                <button
                  onClick={() => setShowConfigPicker(!showConfigPicker)}
                  title="切换配置"
                  style={{
                    background: 'rgba(255,255,255,0.15)',
                    border: 'none',
                    color: 'white',
                    fontSize: '13px',
                    fontWeight: 600,
                    padding: '4px 10px',
                    borderRadius: '14px',
                    cursor: 'pointer',
                    display: 'flex',
                    alignItems: 'center',
                    gap: '6px',
                    maxWidth: '180px',
                    overflow: 'hidden'
                  }}
                >
                  <span style={{
                    overflow: 'hidden',
                    textOverflow: 'ellipsis',
                    whiteSpace: 'nowrap'
                  }}>
                    {activeConfig
                      ? (activeConfig.name || (activeConfig.provider + ' / ' + activeConfig.model))
                      : (configs.length === 0 ? '点此新增配置' : '选择配置')}
                  </span>
                  <i className="bi bi-chevron-down" style={{ fontSize: '10px', flexShrink: 0 }}></i>
                </button>
                {progressStatus !== 'idle' && (
                  <span style={{
                    fontSize: '11px',
                    background: 'rgba(255,255,255,0.2)',
                    padding: '2px 8px',
                    borderRadius: '10px'
                  }}>
                    {progressStatus === 'connecting' && '连接中...'}
                    {progressStatus === 'thinking' && '思考中...'}
                    {progressStatus === 'streaming' && '回复中...'}
                  </span>
                )}
              </div>
              <div style={{ display: 'flex', alignItems: 'center' }}>
                <button
                  onClick={() => setShowConversationList(!showConversationList)}
                  style={{
                    background: 'transparent',
                    border: 'none',
                    color: 'white',
                    fontSize: '16px',
                    cursor: 'pointer',
                    padding: '4px 8px',
                    borderRadius: '4px'
                  }}
                  title="对话历史"
                >
                  <i className="bi bi-clock-history"></i>
                </button>
                <button
                  onClick={createNewConversation}
                  style={{
                    background: 'transparent',
                    border: 'none',
                    color: 'white',
                    fontSize: '16px',
                    cursor: 'pointer',
                    padding: '4px 8px',
                    borderRadius: '4px'
                  }}
                  title="新建对话"
                >
                  <i className="bi bi-plus-lg"></i>
                </button>
                <button
                  onClick={() => setIsFullscreen(!isFullscreen)}
                  style={{
                    background: 'transparent',
                    border: 'none',
                    color: 'white',
                    fontSize: '16px',
                    cursor: 'pointer',
                    padding: '4px 8px',
                    borderRadius: '4px'
                  }}
                  title={isFullscreen ? '退出全屏' : '全屏'}
                >
                  <i className={`bi ${isFullscreen ? 'bi-fullscreen-exit' : 'bi-fullscreen'}`}></i>
                </button>
                <button
                  onClick={() => { resetEditor(); setShowSettings(true); }}
                  style={{
                    background: 'transparent',
                    border: 'none',
                    color: 'white',
                    fontSize: '16px',
                    cursor: 'pointer',
                    padding: '4px 8px',
                    borderRadius: '4px'
                  }}
                  title="设置"
                >
                  <i className="bi bi-gear"></i>
                </button>
                <button
                  onClick={toggleChat}
                  style={{
                    background: 'transparent',
                    border: 'none',
                    color: 'white',
                    fontSize: '16px',
                    cursor: 'pointer',
                    padding: '4px 8px',
                    borderRadius: '4px'
                  }}
                  title="关闭"
                >
                  <i className="bi bi-x-lg"></i>
                </button>
              </div>
            </div>

            {/* 配置选择下拉 */}
            {showConfigPicker && (
              <div style={{
                position: 'absolute',
                top: '56px',
                left: '0',
                right: '0',
                maxHeight: '320px',
                background: 'white',
                zIndex: 11,
                overflowY: 'auto',
                borderTop: '1px solid #e5e7eb',
                boxShadow: '0 4px 12px rgba(0,0,0,0.1)'
              }}>
                {configs.length === 0 ? (
                  <div style={{ padding: '20px', textAlign: 'center', color: '#9ca3af', fontSize: '13px' }}>
                    还没有配置，点击右下角齿轮新建
                  </div>
                ) : (
                  configs.map(cfg => {
                    const isActive = cfg.id === activeConfigId;
                    return (
                      <div
                        key={cfg.id}
                        onClick={(e) => switchActiveConfig(cfg, e)}
                        style={{
                          padding: '10px 14px',
                          borderBottom: '1px solid #f3f4f6',
                          cursor: 'pointer',
                          background: isActive ? '#eef2ff' : 'transparent',
                          opacity: cfg.is_enabled ? 1 : 0.55,
                          display: 'flex',
                          flexDirection: 'column',
                          gap: '2px'
                        }}
                      >
                        <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
                          <span style={{ fontSize: '13px', fontWeight: isActive ? 600 : 500, color: '#1f2937', flex: 1, minWidth: 0, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
                            {cfg.name || (cfg.provider + ' / ' + cfg.model)}
                          </span>
                          {cfg.is_default && (
                            <span title="默认" style={{ fontSize: '11px', color: '#4f46e5' }}>
                              <i className="bi bi-star-fill"></i>
                            </span>
                          )}
                          {isActive && (
                            <span style={{ fontSize: '11px', color: '#4f46e5' }}>
                              <i className="bi bi-check-lg"></i>
                            </span>
                          )}
                          {!cfg.is_enabled && (
                            <span title="已禁用" style={{ fontSize: '10px', color: '#9ca3af' }}>(禁用)</span>
                          )}
                        </div>
                        <div style={{ fontSize: '11px', color: '#6b7280' }}>
                          {providers[cfg.provider]?.name || cfg.provider} · {cfg.model}
                        </div>
                      </div>
                    );
                  })
                )}
                <div style={{
                  padding: '8px 14px',
                  borderTop: '1px solid #e5e7eb',
                  background: '#f9fafb',
                  display: 'flex',
                  justifyContent: 'space-between',
                  alignItems: 'center',
                  fontSize: '12px'
                }}>
                  <span style={{ color: '#6b7280' }}>共 {configs.length} 条配置</span>
                  <button
                    onClick={() => { setShowConfigPicker(false); resetEditor(); setShowSettings(true); }}
                    style={{
                      padding: '4px 10px',
                      background: '#4f46e5',
                      color: 'white',
                      border: 'none',
                      borderRadius: '4px',
                      cursor: 'pointer',
                      fontSize: '12px'
                    }}
                  >
                    <i className="bi bi-gear"></i> 管理配置
                  </button>
                </div>
              </div>
            )}

            {/* 对话列表 */}
            {showConversationList && (
              <div style={{
                position: 'absolute',
                top: '56px',
                left: '0',
                right: '0',
                maxHeight: '300px',
                background: 'white',
                zIndex: 10,
                overflowY: 'auto',
                borderTop: '1px solid #e5e7eb',
                boxShadow: '0 4px 12px rgba(0,0,0,0.1)'
              }}>
                {conversations.length === 0 ? (
                  <div style={{ padding: '20px', textAlign: 'center', color: '#9ca3af' }}>
                    暂无对话历史
                  </div>
                ) : (
                  conversations.map(conv => (
                    <div
                      key={conv.id}
                      onClick={() => switchConversation(conv.id)}
                      style={{
                        padding: '12px 16px',
                        borderBottom: '1px solid #f3f4f6',
                        cursor: 'pointer',
                        background: currentConversationId === conv.id ? '#f3f4f6' : 'transparent',
                        display: 'flex',
                        justifyContent: 'space-between',
                        alignItems: 'center',
                        transition: 'background 0.2s'
                      }}
                      onMouseEnter={(e) => e.currentTarget.style.background = '#f9fafb'}
                      onMouseLeave={(e) => e.currentTarget.style.background = currentConversationId === conv.id ? '#f3f4f6' : 'transparent'}
                    >
                      <div style={{ flex: 1, minWidth: 0 }}>
                        <div style={{ 
                          fontSize: '14px', 
                          fontWeight: currentConversationId === conv.id ? 600 : 400,
                          overflow: 'hidden',
                          textOverflow: 'ellipsis',
                          whiteSpace: 'nowrap'
                        }}>
                          {conv.title || '新对话'}
                        </div>
                        <div style={{ fontSize: '11px', color: '#9ca3af', marginTop: '4px' }}>
                          {new Date(conv.updatedAt).toLocaleString()}
                        </div>
                      </div>
                      <button
                        onClick={(e) => deleteConversation(e, conv.id)}
                        style={{
                          background: 'transparent',
                          border: 'none',
                          color: '#9ca3af',
                          cursor: 'pointer',
                          padding: '4px 8px',
                          borderRadius: '4px',
                          marginLeft: '8px'
                        }}
                        onMouseEnter={(e) => e.currentTarget.style.color = '#ef4444'}
                        onMouseLeave={(e) => e.currentTarget.style.color = '#9ca3af'}
                      >
                        <i className="bi bi-trash"></i>
                      </button>
                    </div>
                  ))
                )}
              </div>
            )}

            {/* Messages */}
            <div style={{
              flex: 1,
              overflowY: 'auto',
              padding: '16px',
              background: '#f9fafb',
              display: 'flex',
              flexDirection: 'column',
              gap: '12px'
            }}>
              {messages.length === 0 && (
                <div style={{
                  flex: 1,
                  display: 'flex',
                  flexDirection: 'column',
                  alignItems: 'center',
                  justifyContent: 'center',
                  color: '#9ca3af'
                }}>
                  <i className="bi bi-chat-dots" style={{ fontSize: '48px', marginBottom: '16px' }}></i>
                  <div style={{ fontSize: '14px' }}>试试说：记一笔午餐30元</div>
                  <div style={{ fontSize: '14px', marginTop: '4px' }}>或者查看本月支出</div>
                </div>
              )}
              {messages.map(msg => renderMessage(msg))}
              <div ref={messagesEndRef} />

              {/* 切换 toast */}
              {toastMessage && (
                <div style={{
                  position: 'absolute',
                  top: '70px',
                  left: '50%',
                  transform: 'translateX(-50%)',
                  background: 'rgba(31, 41, 55, 0.92)',
                  color: 'white',
                  padding: '6px 14px',
                  borderRadius: '14px',
                  fontSize: '12px',
                  boxShadow: '0 4px 12px rgba(0,0,0,0.2)',
                  animation: 'slideIn 0.2s ease',
                  zIndex: 5,
                  pointerEvents: 'none'
                }}>
                  {toastMessage}
                </div>
              )}
            </div>

            {/* Input */}
            <div style={{
              padding: '12px',
              borderTop: '1px solid #e5e7eb',
              background: 'white',
              display: 'flex',
              gap: '8px'
            }}>
              <input
                type="text"
                value={inputValue}
                onChange={(e) => setInputValue(e.target.value)}
                onKeyPress={handleKeyPress}
                placeholder={loading ? '等待回复中...' : '输入消息...'}
                disabled={loading}
                style={{
                  flex: 1,
                  padding: '10px 14px',
                  border: '1px solid #d1d5db',
                  borderRadius: '8px',
                  fontSize: '14px',
                  outline: 'none',
                  opacity: loading ? 0.7 : 1
                }}
              />
              <button
                onClick={sendMessage}
                disabled={loading || !inputValue.trim()}
                style={{
                  width: '40px',
                  height: '40px',
                  background: loading || !inputValue.trim() ? '#9ca3af' : '#4f46e5',
                  color: 'white',
                  border: 'none',
                  borderRadius: '8px',
                  cursor: loading || !inputValue.trim() ? 'not-allowed' : 'pointer'
                }}
              >
                <i className={`bi ${loading ? 'bi-hourglass-split' : 'bi-send'}`}></i>
              </button>
            </div>
          </div>
        )}
      </div>

      {/* Settings Modal — 多套配置：左列表 + 右编辑器 */}
      {showSettings && (
        <div style={{
          position: 'fixed',
          top: 0, left: 0, right: 0, bottom: 0,
          background: 'rgba(0,0,0,0.5)',
          zIndex: 10002,
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center'
        }}>
          <div style={{
            background: 'white',
            borderRadius: '12px',
            width: '90%',
            maxWidth: '760px',
            maxHeight: '90vh',
            overflow: 'hidden',
            display: 'flex',
            flexDirection: 'column'
          }}>
            <div style={{
              padding: '16px 20px',
              display: 'flex',
              justifyContent: 'space-between',
              alignItems: 'center',
              borderBottom: '1px solid #e5e7eb'
            }}>
              <h5 style={{ margin: 0 }}>AI 设置 · 多套配置</h5>
              <button
                onClick={() => setShowSettings(false)}
                style={{
                  background: 'transparent',
                  border: 'none',
                  fontSize: '16px',
                  cursor: 'pointer'
                }}
              >
                <i className="bi bi-x-lg"></i>
              </button>
            </div>

            <div style={{ display: 'flex', flex: 1, minHeight: 0 }}>
              {/* 左：已保存配置列表 */}
              <div style={{
                width: '260px',
                borderRight: '1px solid #e5e7eb',
                background: '#f9fafb',
                display: 'flex',
                flexDirection: 'column',
                flexShrink: 0
              }}>
                <div style={{
                  padding: '10px 12px',
                  borderBottom: '1px solid #e5e7eb',
                  display: 'flex',
                  justifyContent: 'space-between',
                  alignItems: 'center'
                }}>
                  <span style={{ fontSize: '13px', fontWeight: 600, color: '#374151' }}>
                    已保存 ({configs.length})
                  </span>
                  <button
                    onClick={() => { resetEditor(); }}
                    title="新建配置"
                    style={{
                      padding: '4px 10px',
                      fontSize: '12px',
                      background: '#4f46e5',
                      color: 'white',
                      border: 'none',
                      borderRadius: '4px',
                      cursor: 'pointer'
                    }}
                  >
                    <i className="bi bi-plus-lg"></i> 新建
                  </button>
                </div>
                <div style={{ flex: 1, overflowY: 'auto' }}>
                  {configs.length === 0 && (
                    <div style={{ padding: '20px', textAlign: 'center', color: '#9ca3af', fontSize: '12px' }}>
                      暂无配置，点击右上角「新建」
                    </div>
                  )}
                  {configs.map(cfg => {
                    const active = cfg.id === editingConfigId;
                    return (
                      <div
                        key={cfg.id}
                        onClick={() => loadConfigIntoEditor(cfg)}
                        style={{
                          padding: '10px 12px',
                          borderBottom: '1px solid #f3f4f6',
                          cursor: 'pointer',
                          background: active ? '#eef2ff' : 'transparent',
                          opacity: cfg.is_enabled ? 1 : 0.55,
                          display: 'flex',
                          flexDirection: 'column',
                          gap: '4px'
                        }}
                      >
                        <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
                          <span style={{ fontSize: '13px', fontWeight: 600, color: '#1f2937', flex: 1, minWidth: 0, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
                            {cfg.name || (cfg.provider + ' / ' + cfg.model)}
                          </span>
                          {cfg.is_default && (
                            <span title="默认" style={{ fontSize: '11px', color: '#4f46e5' }}>
                              <i className="bi bi-star-fill"></i>
                            </span>
                          )}
                          {!cfg.is_enabled && (
                            <span title="已禁用" style={{ fontSize: '10px', color: '#9ca3af' }}>(禁用)</span>
                          )}
                        </div>
                        <div style={{ fontSize: '11px', color: '#6b7280' }}>
                          {providers[cfg.provider]?.name || cfg.provider} · {cfg.model}
                        </div>
                        <div style={{ display: 'flex', gap: '6px', marginTop: '4px' }}>
                          {!cfg.is_default && (
                            <button
                              onClick={(e) => setAsDefault(cfg.id, e)}
                              style={{
                                padding: '2px 6px',
                                fontSize: '11px',
                                background: 'transparent',
                                border: '1px solid #d1d5db',
                                borderRadius: '4px',
                                color: '#4f46e5',
                                cursor: 'pointer'
                              }}
                            >
                              设为默认
                            </button>
                          )}
                          <button
                            onClick={(e) => deleteConfig(cfg.id, e)}
                            style={{
                              padding: '2px 6px',
                              fontSize: '11px',
                              background: 'transparent',
                              border: '1px solid #fecaca',
                              borderRadius: '4px',
                              color: '#ef4444',
                              cursor: 'pointer'
                            }}
                          >
                            <i className="bi bi-trash"></i>
                          </button>
                        </div>
                      </div>
                    );
                  })}
                </div>
              </div>

              {/* 右：编辑器 */}
              <div style={{ flex: 1, display: 'flex', flexDirection: 'column', minWidth: 0 }}>
                <div style={{
                  padding: '12px 20px',
                  borderBottom: '1px solid #e5e7eb',
                  display: 'flex',
                  justifyContent: 'space-between',
                  alignItems: 'center'
                }}>
                  <span style={{ fontSize: '14px', fontWeight: 600, color: '#374151' }}>
                    {editingConfigId ? '编辑配置' : '新建配置'}
                  </span>
                </div>

                <div style={{ padding: '20px', overflowY: 'auto', flex: 1 }}>
                  <div style={{ marginBottom: '14px' }}>
                    <label style={{ display: 'block', marginBottom: '6px', fontSize: '13px', fontWeight: 600, color: '#374151' }}>
                      配置备注名
                    </label>
                    <input
                      type="text"
                      value={configName}
                      onChange={(e) => setConfigName(e.target.value)}
                      placeholder="例如：日常-DeepSeek"
                      style={{ width: '100%', padding: '9px 12px', border: '1px solid #d1d5db', borderRadius: '6px', fontSize: '14px', boxSizing: 'border-box' }}
                    />
                  </div>

                  <div style={{ marginBottom: '14px' }}>
                    <label style={{ display: 'block', marginBottom: '6px', fontSize: '13px', fontWeight: 600, color: '#374151' }}>
                      Provider
                    </label>
                    <select
                      value={provider}
                      onChange={handleProviderChange}
                      style={{ width: '100%', padding: '9px 12px', border: '1px solid #d1d5db', borderRadius: '6px', fontSize: '14px' }}
                    >
                      <option value="">选择 Provider</option>
                      {renderProviderOptions()}
                    </select>
                  </div>

                  <div style={{ marginBottom: '14px' }}>
                    <label style={{ display: 'block', marginBottom: '6px', fontSize: '13px', fontWeight: 600, color: '#374151' }}>
                      API Key
                    </label>
                    <input
                      type="password"
                      value={apiKey}
                      onChange={(e) => setApiKey(e.target.value)}
                      placeholder="sk-..."
                      style={{ width: '100%', padding: '9px 12px', border: '1px solid #d1d5db', borderRadius: '6px', fontSize: '14px', boxSizing: 'border-box' }}
                    />
                  </div>

                  <div style={{ marginBottom: '14px' }}>
                    <label style={{ display: 'block', marginBottom: '6px', fontSize: '13px', fontWeight: 600, color: '#374151' }}>
                      模型
                      <button
                        type="button"
                        onClick={fetchModels}
                        disabled={fetchingModels}
                        style={{
                          marginLeft: '8px',
                          padding: '4px 10px',
                          fontSize: '12px',
                          background: '#f3f4f6',
                          border: '1px solid #d1d5db',
                          borderRadius: '4px',
                          cursor: fetchingModels ? 'not-allowed' : 'pointer'
                        }}
                      >
                        <i className="bi bi-arrow-clockwise" style={fetchingModels ? { animation: 'spin 1s linear infinite' } : {}}></i>
                        {fetchingModels ? '加载中...' : '获取'}
                      </button>
                    </label>
                    {availableModels.length > 0 ? (
                      <select
                        value={model}
                        onChange={(e) => setModel(e.target.value)}
                        style={{ width: '100%', padding: '9px 12px', border: '1px solid #d1d5db', borderRadius: '6px', fontSize: '14px', boxSizing: 'border-box' }}
                      >
                        <option value="">选择模型</option>
                        {availableModels.map(m => (
                          <option key={m} value={m}>{m}</option>
                        ))}
                        <option value="__custom__">-- 自定义 --</option>
                      </select>
                    ) : (
                      <input
                        type="text"
                        value={customModel}
                        onChange={(e) => setCustomModel(e.target.value)}
                        placeholder="输入模型名称"
                        style={{ width: '100%', padding: '9px 12px', border: '1px solid #d1d5db', borderRadius: '6px', fontSize: '14px', boxSizing: 'border-box' }}
                      />
                    )}
                    {model === '__custom__' && (
                      <input
                        type="text"
                        value={customModel}
                        onChange={(e) => setCustomModel(e.target.value)}
                        placeholder="输入自定义模型名称"
                        style={{ width: '100%', padding: '9px 12px', border: '1px solid #d1d5db', borderRadius: '6px', fontSize: '14px', marginTop: '8px', boxSizing: 'border-box' }}
                      />
                    )}
                  </div>

                  <div style={{ marginBottom: '14px' }}>
                    <label style={{ display: 'block', marginBottom: '6px', fontSize: '13px', fontWeight: 600, color: '#374151' }}>
                      Base URL (可选，用于自定义)
                    </label>
                    <input
                      type="text"
                      value={baseUrl}
                      onChange={(e) => setBaseUrl(e.target.value)}
                      placeholder="https://api.openai.com/v1"
                      style={{ width: '100%', padding: '9px 12px', border: '1px solid #d1d5db', borderRadius: '6px', fontSize: '14px', boxSizing: 'border-box' }}
                    />
                  </div>

                  {HINTS[provider] && (
                    <div style={{
                      marginTop: '12px',
                      padding: '10px 12px',
                      background: '#eff6ff',
                      color: '#1e40af',
                      borderRadius: '6px',
                      fontSize: '12px',
                      lineHeight: 1.5
                    }}>
                      {HINTS[provider]}
                    </div>
                  )}

                  {/* 其他 (高级) 折叠区 */}
                  <div style={{ marginTop: '20px', borderTop: '1px solid #e5e7eb', paddingTop: '14px' }}>
                    <button
                      type="button"
                      onClick={() => setShowAdvanced(!showAdvanced)}
                      style={{
                        background: 'transparent',
                        border: 'none',
                        color: '#4f46e5',
                        fontSize: '13px',
                        fontWeight: 600,
                        cursor: 'pointer',
                        padding: 0,
                        display: 'flex',
                        alignItems: 'center',
                        gap: '6px'
                      }}
                    >
                      <i className={`bi bi-chevron-${showAdvanced ? 'down' : 'right'}`}></i>
                      其他 (高级)
                    </button>
                    {showAdvanced && (
                      <div style={{ marginTop: '12px' }}>
                        <div style={{ marginBottom: '14px', display: 'flex', gap: '18px' }}>
                          <label style={{ display: 'flex', alignItems: 'center', gap: '6px', fontSize: '13px', color: '#374151', cursor: 'pointer' }}>
                            <input
                              type="checkbox"
                              checked={configIsDefault}
                              onChange={(e) => setConfigIsDefault(e.target.checked)}
                            />
                            设为默认
                          </label>
                          <label style={{ display: 'flex', alignItems: 'center', gap: '6px', fontSize: '13px', color: '#374151', cursor: 'pointer' }}>
                            <input
                              type="checkbox"
                              checked={configIsEnabled}
                              onChange={(e) => setConfigIsEnabled(e.target.checked)}
                            />
                            启用
                          </label>
                        </div>
                        <div>
                          <label style={{ display: 'block', marginBottom: '6px', fontSize: '13px', fontWeight: 600, color: '#374151' }}>
                            System Prompt 覆盖 (可选)
                          </label>
                          <textarea
                            value={configSystemPrompt}
                            onChange={(e) => setConfigSystemPrompt(e.target.value)}
                            placeholder="留空则使用默认 Ledger AI 提示词"
                            rows={4}
                            style={{
                              width: '100%',
                              padding: '9px 12px',
                              border: '1px solid #d1d5db',
                              borderRadius: '6px',
                              fontSize: '13px',
                              boxSizing: 'border-box',
                              fontFamily: 'inherit',
                              resize: 'vertical'
                            }}
                          />
                        </div>
                      </div>
                    )}
                  </div>
                </div>

                <div style={{
                  padding: '14px 20px',
                  borderTop: '1px solid #e5e7eb',
                  display: 'flex',
                  justifyContent: 'flex-end',
                  gap: '8px',
                  background: '#fafafa'
                }}>
                  <button
                    onClick={() => { resetEditor(); setShowSettings(false); }}
                    style={{
                      padding: '8px 16px',
                      border: '1px solid #d1d5db',
                      background: 'white',
                      borderRadius: '6px',
                      cursor: 'pointer',
                      fontSize: '14px'
                    }}
                  >
                    取消
                  </button>
                  <button
                    onClick={saveEditorConfig}
                    disabled={editorSaving}
                    style={{
                      padding: '8px 16px',
                      border: '1px solid #4f46e5',
                      background: '#4f46e5',
                      color: 'white',
                      borderRadius: '6px',
                      cursor: editorSaving ? 'wait' : 'pointer',
                      fontSize: '14px',
                      opacity: editorSaving ? 0.7 : 1
                    }}
                  >
                    {editorSaving ? '保存中...' : (editingConfigId ? '保存修改' : '保存配置')}
                  </button>
                </div>
              </div>
            </div>
          </div>
        </div>
      )}
    </>
  );
}
