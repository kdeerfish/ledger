(function() {
  let agentChatOpen = false;
  let agentConfig = null;
  let agentProviders = {};
  let chatHistory = [];

  async function initAgent() {
    try {
      const res = await fetch('/api/agent/providers');
      const data = await res.json();
      if (data.success) {
        agentProviders = data.data;
      }
    } catch (e) {}
    const saved = localStorage.getItem('agentConfig');
    if (saved) {
      try { agentConfig = JSON.parse(saved); } catch (e) {}
    }
  }

  function toggleAgentChat() {
    agentChatOpen = !agentChatOpen;
    const win = document.getElementById('agentChatWindow');
    const toggle = document.getElementById('agentChatToggle');
    if (win) win.style.display = agentChatOpen ? 'flex' : 'none';
    if (toggle) toggle.innerHTML = agentChatOpen ? '<i class="bi bi-x-lg"></i>' : '<i class="bi bi-robot"></i>';
    if (agentChatOpen && chatHistory.length === 0) {
      addAgentMessage('system', 'Hello! Try: add a lunch 30 yuan, check this month expenses.');
    }
  }

  function showAgentSettings() {
    renderProviders();
    document.getElementById('agentSettingsModal').style.display = 'flex';
  }

  function closeAgentSettings() {
    document.getElementById('agentSettingsModal').style.display = 'none';
  }

  function renderProviders() {
    const sel = document.getElementById('agentProvider');
    sel.innerHTML = '';
    const groups = {
      'International': ['openai', 'claude', 'ollama'],
      'China': ['qwen', 'wenxin', 'glm', 'moonshot', 'hunyuan', 'spark', 'doubao', 'minimax', 'deepseek'],
      'Custom': ['custom']
    };
    for (const g in groups) {
      const og = document.createElement('optgroup');
      og.label = g;
      for (const id of groups[g]) {
        if (agentProviders[id]) {
          const opt = document.createElement('option');
          opt.value = id;
          opt.textContent = agentProviders[id].name;
          og.appendChild(opt);
        }
      }
      sel.appendChild(og);
    }
    if (agentConfig && agentConfig.provider) {
      sel.value = agentConfig.provider;
      onProviderChange();
      if (agentConfig.model) {
        const modelSel = document.getElementById('agentModel');
        const opt = Array.from(modelSel.options).find(function(o) { return o.value === agentConfig.model; });
        if (opt) modelSel.value = agentConfig.model;
        else document.getElementById('agentModelCustom').value = agentConfig.model;
      }
      if (agentConfig.api_key) document.getElementById('agentApiKey').value = agentConfig.api_key;
      if (agentConfig.base_url) document.getElementById('agentBaseUrl').value = agentConfig.base_url;
    }
  }

  function onProviderChange() {
    const provider = document.getElementById('agentProvider').value;
    const modelSel = document.getElementById('agentModel');
    const customInput = document.getElementById('agentModelCustom');
    const hint = document.getElementById('agentProviderHint');
    modelSel.innerHTML = '';
    
    const p = agentProviders[provider];
    if (!p) return;

    if (p.models && p.models.length > 0) {
      modelSel.style.display = 'block';
      customInput.style.display = 'none';
      p.models.forEach(function(m) {
        const opt = document.createElement('option');
        opt.value = m;
        opt.textContent = m;
        modelSel.appendChild(opt);
      });
      const customOpt = document.createElement('option');
      customOpt.value = '__custom__';
      customOpt.textContent = '-- Custom --';
      modelSel.appendChild(customOpt);
    } else {
      modelSel.style.display = 'none';
      customInput.style.display = 'block';
    }

    const hints = {
      'custom': 'Custom: fill Base URL, model name and API Key. OpenAI compatible.',
      'ollama': 'Ollama local. Default: http://localhost:11434. API Key optional.',
      'wenxin': 'Wenxin uses Qianfan API. Get API Key from Baidu Cloud.'
    };
    if (hints[provider]) {
      hint.textContent = hints[provider];
      hint.style.display = 'block';
    } else {
      hint.style.display = 'none';
    }
  }

  async function fetchModels() {
    const provider = document.getElementById('agentProvider').value;
    const apiKey = document.getElementById('agentApiKey').value.trim();
    const baseUrl = document.getElementById('agentBaseUrl').value.trim();
    
    if (!apiKey && provider !== 'ollama') {
      alert('Please enter API Key first');
      return;
    }

    const btn = document.getElementById('fetchModelsBtn');
    btn.disabled = true;
    btn.innerHTML = 'Loading...';
    
    try {
      const res = await fetch('/api/agent/fetch_models', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ provider: provider, api_key: apiKey, base_url: baseUrl })
      });
      const data = await res.json();
      if (data.success && data.data.models) {
        const modelSel = document.getElementById('agentModel');
        const currentModels = Array.from(modelSel.options).map(function(o) { return o.value; }).filter(function(v) { return v !== '__custom__'; });
        const newModels = data.data.models.filter(function(m) { return currentModels.indexOf(m) === -1; });
        
        if (newModels.length > 0) {
          const customOpt = modelSel.querySelector('option[value="__custom__"]');
          newModels.forEach(function(m) {
            const opt = document.createElement('option');
            opt.value = m;
            opt.textContent = m + ' (live)';
            if (customOpt) modelSel.insertBefore(opt, customOpt);
            else modelSel.appendChild(opt);
          });
          addAgentMessage('system', 'Fetched ' + newModels.length + ' live models');
        } else {
          addAgentMessage('system', 'No new models found');
        }
      } else {
        alert('Failed: ' + (data.error || 'Unknown'));
      }
    } catch (e) {
      alert('Error: ' + e.message);
    } finally {
      btn.disabled = false;
      btn.innerHTML = 'Fetch';
    }
  }

  function saveAgentSettings() {
    const provider = document.getElementById('agentProvider').value;
    let model = document.getElementById('agentModel').value;
    if (model === '__custom__') {
      model = document.getElementById('agentModelCustom').value.trim();
    }
    const apiKey = document.getElementById('agentApiKey').value;
    const baseUrl = document.getElementById('agentBaseUrl').value;
    
    if (!provider) { alert('Select provider'); return; }
    if (!model) { alert('Enter model name'); return; }
    if (!apiKey && provider !== 'ollama') { alert('Enter API Key'); return; }
    
    agentConfig = { provider: provider, api_key: apiKey, model: model, base_url: baseUrl };
    localStorage.setItem('agentConfig', JSON.stringify(agentConfig));
    closeAgentSettings();
    addAgentMessage('system', 'Settings saved!');
  }

  function addAgentMessage(role, content) {
    const div = document.getElementById('agentChatMessages');
    const msg = document.createElement('div');
    msg.className = 'agent-msg ' + role;
    msg.textContent = content;
    div.appendChild(msg);
    div.scrollTop = div.scrollHeight;
    chatHistory.push({ role: role, content: content });
  }

  async function sendAgentMessage() {
    const input = document.getElementById('agentInput');
    const message = input.value.trim();
    if (!message) return;
    input.value = '';
    addAgentMessage('user', message);
    
    if (!agentConfig) {
      addAgentMessage('system', 'Configure AI first (gear icon)');
      return;
    }

    addAgentMessage('system', 'Thinking...');
    
    try {
      const response = await fetch('/api/agent/chat', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ message: message, config: agentConfig, history: chatHistory.slice(-10) })
      });
      const data = await response.json();
      console.log('[AgentChat] API response:', data);
      
      // Remove "Thinking..." message
      const msgs = document.getElementById('agentChatMessages').children;
      if (msgs.length > 0 && msgs[msgs.length-1].textContent === 'Thinking...') {
        document.getElementById('agentChatMessages').removeChild(msgs[msgs.length-1]);
        chatHistory.pop();
      }
      
      // Backend returns {success: true, data: {response: "..."}} or {success: false, error: "..."}
      if (data.success === false) {
        // Explicit error from backend
        addAgentMessage('system', '错误: ' + (data.error || '未知错误'));
      } else if (data.data && data.data.response) {
        // Normal response
        addAgentMessage('assistant', data.data.response);
      } else if (data.data && data.data.tool_calls) {
        // Tool calls returned
        addAgentMessage('assistant', data.data.response || '(模型请求调用工具，但前端暂不支持自动执行)');
      } else {
        // Empty response - show something
        console.warn('[AgentChat] Unexpected response format:', data);
        addAgentMessage('system', '(未收到回复，请检查模型配置或查看控制台日志)');
      }
    } catch (e) {
      addAgentMessage('system', 'Failed: ' + e.message);
    }
  }

  window.toggleAgentChat = toggleAgentChat;
  window.showAgentSettings = showAgentSettings;
  window.closeAgentSettings = closeAgentSettings;
  window.onProviderChange = onProviderChange;
  window.fetchModels = fetchModels;
  window.saveAgentSettings = saveAgentSettings;
  window.sendAgentMessage = sendAgentMessage;

  document.addEventListener('DOMContentLoaded', function() {
    initAgent();
    const input = document.getElementById('agentInput');
    if (input) {
      input.addEventListener('keypress', function(e) {
        if (e.key === 'Enter') sendAgentMessage();
      });
    }
  });
})();
