import { useState, useEffect, useRef } from 'react';

const PROVIDERS_GROUPS = {
  'International': ['openai', 'claude', 'groq', 'together', 'mistral', 'cohere', 'ollama'],
  'China': ['deepseek', 'qwen', 'wenxin', 'glm', 'moonshot', 'hunyuan', 'spark', 'doubao', 'minimax', 'yi', 'baichuan', 'stepfun'],
  'Custom': ['custom']
};

const HINTS = {
  'custom': 'Custom: fill Base URL, model name and API Key. OpenAI compatible.',
  'ollama': 'Ollama local. Default: http://localhost:11434. API Key optional.',
  'wenxin': 'Wenxin uses Qianfan API. Get API Key from Baidu Cloud.'
};

export default function AgentChat() {
  const [isOpen, setIsOpen] = useState(false);
  const [config, setConfig] = useState(null);
  const [providers, setProviders] = useState({});
  const [messages, setMessages] = useState([]);
  const [inputValue, setInputValue] = useState('');
  const [showSettings, setShowSettings] = useState(false);
  const [loading, setLoading] = useState(false);
  
  // Settings form state
  const [provider, setProvider] = useState('');
  const [apiKey, setApiKey] = useState('');
  const [model, setModel] = useState('');
  const [customModel, setCustomModel] = useState('');
  const [baseUrl, setBaseUrl] = useState('');
  const [availableModels, setAvailableModels] = useState([]);
  const [fetchingModels, setFetchingModels] = useState(false);
  
  const messagesEndRef = useRef(null);

  useEffect(() => {
    initAgent();
  }, []);

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  const initAgent = async () => {
    try {
      const res = await fetch('/api/agent/providers');
      const data = await res.json();
      if (data.success && Array.isArray(data.data)) {
        // Convert array to object keyed by provider ID
        const providersObj = {};
        data.data.forEach(p => { providersObj[p.id] = p; });
        setProviders(providersObj);
      }
    } catch (e) {}
    
    const saved = localStorage.getItem('agentConfig');
    if (saved) {
      try {
        const parsed = JSON.parse(saved);
        setConfig(parsed);
        setProvider(parsed.provider || '');
        setApiKey(parsed.api_key || '');
        setModel(parsed.model || '');
        setBaseUrl(parsed.base_url || '');
      } catch (e) {}
    }
  };

  const toggleChat = () => {
    setIsOpen(!isOpen);
    if (!isOpen && messages.length === 0) {
      addMessage('system', '你好！试试说：记一笔午餐30元，或者查看本月支出。');
    }
  };

  const addMessage = (role, content) => {
    setMessages(prev => [...prev, { role, content, id: Date.now() }]);
  };

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
    addMessage('system', '思考中...');
    
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
      
      // Remove "思考中..." message
      setMessages(prev => prev.filter(m => m.content !== '思考中...'));
      
      console.log('[AgentChat] API response:', data);
      
      // Backend returns {success: true, data: {response: "..."}} or {success: false, error: "..."}
      if (data.success === false) {
        // Explicit error from backend
        addMessage('system', '错误: ' + (data.error || '未知错误'));
      } else if (data.data?.response) {
        // Normal response
        addMessage('assistant', data.data.response);
      } else if (data.data?.tool_calls) {
        // Tool calls returned (model wants to call tools)
        addMessage('assistant', data.data.response || '(模型请求调用工具，但前端暂不支持自动执行)');
      } else {
        // Empty response - show something
        console.warn('[AgentChat] Unexpected response format:', data);
        addMessage('system', '(未收到回复，请检查模型配置或查看控制台日志)');
      }
    } catch (e) {
      setMessages(prev => prev.filter(m => m.content !== '思考中...'));
      addMessage('system', '失败: ' + e.message);
    } finally {
      setLoading(false);
    }
  };

  const handleKeyPress = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      sendMessage();
    }
  };

  const openSettings = () => {
    setShowSettings(true);
  };

  const closeSettings = () => {
    setShowSettings(false);
  };

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
          addMessage('system', '获取到 ' + newModels.length + ' 个新模型');
        } else {
          addMessage('system', '没有找到新模型');
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

  const saveSettings = () => {
    const selectedModel = model === '__custom__' ? customModel : model;
    
    if (!provider) { alert('请选择 Provider'); return; }
    if (!selectedModel) { alert('请输入模型名称'); return; }
    if (!apiKey && provider !== 'ollama') { alert('请输入 API Key'); return; }
    
    const newConfig = { provider, api_key: apiKey, model: selectedModel, base_url: baseUrl };
    setConfig(newConfig);
    localStorage.setItem('agentConfig', JSON.stringify(newConfig));
    closeSettings();
    addMessage('system', '设置已保存！');
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
            position: 'absolute',
            bottom: '70px',
            right: '0',
            width: '380px',
            height: '520px',
            background: 'white',
            borderRadius: '12px',
            boxShadow: '0 12px 40px rgba(0,0,0,0.18)',
            display: 'flex',
            flexDirection: 'column',
            overflow: 'hidden',
            border: '1px solid #e5e7eb'
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
              <span><i className="bi bi-robot"></i> AI 助手</span>
              <div>
                <button
                  onClick={openSettings}
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
                    marginLeft: '4px',
                    borderRadius: '4px'
                  }}
                  title="关闭"
                >
                  <i className="bi bi-x-lg"></i>
                </button>
              </div>
            </div>

            {/* Messages */}
            <div style={{
              flex: 1,
              overflowY: 'auto',
              padding: '16px',
              background: '#f9fafb',
              display: 'flex',
              flexDirection: 'column',
              gap: '10px'
            }}>
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
                    alignSelf: msg.role === 'user' ? 'flex-end' : msg.role === 'assistant' ? 'flex-start' : 'center',
                    background: msg.role === 'user' ? '#4f46e5' : msg.role === 'assistant' ? 'white' : '#fef3c7',
                    color: msg.role === 'user' ? 'white' : msg.role === 'assistant' ? '#1f2937' : '#92400e',
                    border: msg.role === 'assistant' ? '1px solid #e5e7eb' : 'none',
                    borderRadius: msg.role === 'user' ? '14px 14px 4px 14px' : msg.role === 'assistant' ? '14px 14px 14px 4px' : '8px',
                    fontSize: msg.role === 'system' ? '12px' : '14px',
                    maxWidth: msg.role === 'system' ? '95%' : '85%',
                    textAlign: msg.role === 'system' ? 'center' : 'left'
                  }}
                >
                  {msg.content}
                </div>
              ))}
              <div ref={messagesEndRef} />
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
                placeholder="输入消息..."
                disabled={loading}
                style={{
                  flex: 1,
                  padding: '10px 14px',
                  border: '1px solid #d1d5db',
                  borderRadius: '8px',
                  fontSize: '14px',
                  outline: 'none'
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
                <i className="bi bi-send"></i>
              </button>
            </div>
          </div>
        )}
      </div>

      {/* Settings Modal */}
      {showSettings && (
        <div style={{
          position: 'fixed',
          top: 0, left: 0, right: 0, bottom: 0,
          background: 'rgba(0,0,0,0.5)',
          zIndex: 10000,
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center'
        }}>
          <div style={{
            background: 'white',
            borderRadius: '12px',
            width: '90%',
            maxWidth: '480px',
            maxHeight: '90vh',
            overflowY: 'auto'
          }}>
            <div style={{
              padding: '16px 20px',
              display: 'flex',
              justifyContent: 'space-between',
              alignItems: 'center',
              borderBottom: '1px solid #e5e7eb'
            }}>
              <h5 style={{ margin: 0 }}>AI 设置</h5>
              <button
                onClick={closeSettings}
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
            
            <div style={{ padding: '20px' }}>
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
                    <i className={`bi ${fetchingModels ? 'bi-arrow-clockwise' : 'bi-arrow-clockwise'}`} style={fetchingModels ? { animation: 'spin 1s linear infinite' } : {}}></i>
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
                  lineHeight: '1.5'
                }}>
                  {HINTS[provider]}
                </div>
              )}
            </div>

            <div style={{
              padding: '16px 20px',
              borderTop: '1px solid #e5e7eb',
              display: 'flex',
              justifyContent: 'flex-end',
              gap: '8px'
            }}>
              <button
                onClick={closeSettings}
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
                onClick={saveSettings}
                style={{
                  padding: '8px 16px',
                  border: '1px solid #4f46e5',
                  background: '#4f46e5',
                  color: 'white',
                  borderRadius: '6px',
                  cursor: 'pointer',
                  fontSize: '14px'
                }}
              >
                保存
              </button>
            </div>
          </div>
        </div>
      )}
    </>
  );
}
