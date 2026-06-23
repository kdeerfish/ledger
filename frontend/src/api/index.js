/**
 * Ledger API 客户端
 */
const BASE = '/api';

async function request(path, opts = {}) {
  const res = await fetch(BASE + path, {
    headers: { 'Content-Type': 'application/json', ...opts.headers },
    ...opts,
  });
  const data = await res.json();
  if (!data.success) throw new Error(data.error || '请求失败');
  return data;
}

export const api = {
  // 交易
  getTransactions(params) {
    const q = new URLSearchParams(params || {}).toString();
    return request('/transactions' + (q ? '?' + q : ''));
  },
  getTransaction(id) {
    return request('/transactions/' + id);
  },
  addTransaction(data) {
    return request('/transactions', { method: 'POST', body: JSON.stringify(data) });
  },
  updateTransaction(id, data) {
    return request('/transactions/' + id, { method: 'PUT', body: JSON.stringify(data) });
  },
  deleteTransaction(id) {
    return request('/transactions/' + id, { method: 'DELETE' });
  },

  // Tags
  getTags() {
    return request('/tags');
  },
  createTag(data) {
    return request('/tags', { method: 'POST', body: JSON.stringify(data) });
  },
  deleteTag(id) {
    return request('/tags/' + id, { method: 'DELETE' });
  },

  // 模板
  getTemplates() {
    return request('/templates');
  },
  createTemplate(data) {
    return request('/templates', { method: 'POST', body: JSON.stringify(data) });
  },
  deleteTemplate(id) {
    return request('/templates/' + id, { method: 'DELETE' });
  },
  useTemplate(id) {
    return request('/templates/' + id + '/use', { method: 'POST' });
  },

  // 摘要
  getSummary(params) {
    const q = new URLSearchParams(params || {}).toString();
    return request('/summary' + (q ? '?' + q : ''));
  },

  // 统计
  getStats(params) {
    const q = new URLSearchParams(params || {}).toString();
    return request('/stats?' + q);
  },

  // 趋势
  getTrends(params) {
    const q = new URLSearchParams(params || {}).toString();
    return request('/trends?' + q);
  },

  // 建议
  getSuggestions(params) {
    const q = new URLSearchParams(params || {}).toString();
    return request('/suggestions?' + q);
  },

  // 其它
  getCategories() {
    return request('/categories');
  },
  getQuickCategories() {
    return request('/categories/quick');
  },
  getAccounts() {
    return request('/accounts');
  },
  getMembers() {
    return request('/members');
  },
  getProjects() {
    return request('/projects');
  },
  getMerchants() {
    return request('/merchants');
  },
  getBudgets(params) {
    const q = new URLSearchParams(params || {}).toString();
    return request('/budgets/check?' + q);
  },
  setBudget(data) {
    return request('/budgets', { method: 'POST', body: JSON.stringify(data) });
  },
  getInfo() {
    return request('/info');
  },

  // 隐藏项管理
  getHidden(field) {
    return request('/hidden/' + field);
  },
  hideItem(field, value) {
    return request('/hidden/' + field, { method: 'POST', body: JSON.stringify({ value }) });
  },
  unhideItem(field, value) {
    return request('/hidden/' + field, { method: 'DELETE', body: JSON.stringify({ value }) });
  },

  // 导入
  importPreview(formData) {
    return fetch(BASE + '/import/preview', { method: 'POST', body: formData })
      .then(res => res.json());
  },
  importExecute(formData) {
    return fetch(BASE + '/import/execute', { method: 'POST', body: formData })
      .then(res => res.json());
  },
  getImportBatches() {
    return request('/import/batches');
  },

  // 导出
  getExportPreview(params) {
    const q = new URLSearchParams(params || {}).toString();
    return request('/export/preview' + (q ? '?' + q : ''));
  },
  getExportDownloadUrl(params) {
    const q = new URLSearchParams(params || {}).toString();
    return BASE + '/export/v2?' + q;
  },
};
