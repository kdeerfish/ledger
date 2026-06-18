import { useState, useEffect } from 'react';
import { api } from '../api';

export default function Categories() {
  const [activeTab, setActiveTab] = useState('categories');
  const [categories, setCategories] = useState([]);
  const [tags, setTags] = useState([]);
  const [newTag, setNewTag] = useState({ name: '', color: '#6366f1' });

  useEffect(() => {
    loadCategories();
    loadTags();
  }, []);

  const loadCategories = async () => {
    try {
      const res = await api.getCategories();
      if (res.data) setCategories(res.data);
    } catch (e) {}
  };

  const loadTags = async () => {
    try {
      const res = await api.getTags();
      if (res.data) setTags(res.data);
    } catch (e) {}
  };

  const handleCreateTag = async () => {
    if (!newTag.name.trim()) return;
    try {
      await api.createTag(newTag);
      setNewTag({ name: '', color: '#6366f1' });
      loadTags();
      toast('标签创建成功');
    } catch (e) {
      toast(e.message, 'danger');
    }
  };

  const handleDeleteTag = async (id, name) => {
    if (!confirm(`确认删除标签"${name}"？此操作不可恢复。`)) return;
    try {
      await api.deleteTag(id);
      loadTags();
      toast('标签已删除');
    } catch (e) {}
  };

  const colors = ['#6366f1', '#ef4444', '#f59e0b', '#10b981', '#3b82f6', '#ec4899', '#14b8a6', '#f97316', '#8b5cf6', '#84cc16', '#e11d48', '#0891b2'];

  return (
    <div className="page-content">
      <h4 className="mb-4"><i className="bi bi-tags"></i> 类别与标签管理</h4>

      {/* Tabs */}
      <ul className="nav nav-tabs mb-4">
        <li className="nav-item">
          <button className={`nav-link ${activeTab === 'categories' ? 'active' : ''}`}
            onClick={() => setActiveTab('categories')}>
            <i className="bi bi-folder"></i> 类别统计
          </button>
        </li>
        <li className="nav-item">
          <button className={`nav-link ${activeTab === 'tags' ? 'active' : ''}`}
            onClick={() => setActiveTab('tags')}>
            <i className="bi bi-tag"></i> 标签管理
          </button>
        </li>
      </ul>

      {/* ══════ 类别统计 ══════ */}
      {activeTab === 'categories' && (
        <div>
          {categories.length === 0 ? (
            <div className="card">
              <div className="card-body">
                <div className="empty-state"><div className="icon">🏷️</div><p>暂无类别数据</p></div>
              </div>
            </div>
          ) : (
            <div className="row g-3">
              {categories.map(c => (
                <div key={c.name} className="col-md-6 col-lg-4">
                  <div className="summary-card h-100">
                    <div className="card-body">
                      <div className="d-flex justify-content-between align-items-center mb-2">
                        <h6 className="mb-0">{c.name}</h6>
                        <span className="badge bg-secondary">{c.total_count}笔</span>
                      </div>
                      <p className="fw-bold text-danger mb-2">
                        ¥ {fmt(Math.abs(c.total_amount))}
                      </p>
                      {c.subcategories.slice(0, 8).map((s, i) => (
                        <div key={i} className="d-flex justify-content-between small text-muted py-1 border-bottom border-light">
                          <span>{s.name}</span>
                          <span>{s.count}笔 · ¥{fmt(s.amount)}</span>
                        </div>
                      ))}
                      {c.subcategories.length > 8 && (
                        <small className="text-muted">...还有 {c.subcategories.length - 8} 个子类别</small>
                      )}
                    </div>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      )}

      {/* ══════ 标签管理 ══════ */}
      {activeTab === 'tags' && (
        <div>
          {/* 创建标签 */}
          <div className="card mb-4">
            <div className="card-body">
              <h6 className="card-title mb-3"><i className="bi bi-plus-circle"></i> 创建新标签</h6>
              <div className="row g-2 align-items-end">
                <div className="col-md-4">
                  <label className="form-label">标签名称</label>
                  <input type="text" className="form-control" value={newTag.name}
                    onChange={e => setNewTag({ ...newTag, name: e.target.value })}
                    placeholder="输入标签名"
                    onKeyDown={e => e.key === 'Enter' && handleCreateTag()} />
                </div>
                <div className="col-md-4">
                  <label className="form-label">颜色</label>
                  <div className="d-flex gap-1 flex-wrap">
                    {colors.map(c => (
                      <span key={c}
                        onClick={() => setNewTag({ ...newTag, color: c })}
                        style={{
                          display: 'inline-block',
                          width: 28, height: 28,
                          borderRadius: '50%',
                          background: c,
                          cursor: 'pointer',
                          border: newTag.color === c ? '3px solid #1e293b' : '3px solid transparent',
                        }}></span>
                    ))}
                  </div>
                </div>
                <div className="col-md-4">
                  <button className="btn btn-ledger w-100" onClick={handleCreateTag}>
                    <i className="bi bi-plus-lg"></i> 创建标签
                  </button>
                </div>
              </div>
            </div>
          </div>

          {/* 标签列表 */}
          {tags.length === 0 ? (
            <div className="card">
              <div className="card-body">
                <div className="empty-state"><div className="icon">🏷️</div><p>暂无标签，创建一个吧</p></div>
              </div>
            </div>
          ) : (
            <div className="row g-3">
              {tags.map(tag => (
                <div key={tag.id} className="col-md-4 col-lg-3">
                  <div className="card">
                    <div className="card-body d-flex justify-content-between align-items-center">
                      <div className="d-flex align-items-center gap-2">
                        <span style={{
                          display: 'inline-block',
                          width: 12, height: 12,
                          borderRadius: '50%',
                          background: tag.color,
                        }}></span>
                        <div>
                          <strong>{tag.name}</strong>
                          <br />
                          <small className="text-muted">{tag.usage_count || 0} 笔交易</small>
                        </div>
                      </div>
                      <button className="btn btn-sm btn-outline-danger py-0 px-1"
                        onClick={() => handleDeleteTag(tag.id, tag.name)}>
                        <i className="bi bi-trash"></i>
                      </button>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      )}
    </div>
  );
}

function fmt(v) {
  return Number(v || 0).toLocaleString('zh-CN', { minimumFractionDigits: 2, maximumFractionDigits: 2 });
}

function toast(msg, type = 'success') {
  const container = document.querySelector('.toast-container') || document.body;
  const el = document.createElement('div');
  el.style.cssText = 'position:fixed;top:1rem;right:1rem;z-index:9999;border-radius:12px';
  el.className = 'toast align-items-center border-0 bg-white shadow-sm';
  el.innerHTML = `<div class="d-flex">
    <div class="toast-body"><i class="bi bi-${type === 'danger' ? 'exclamation-circle' : 'check-circle'}" style="color:${type === 'danger' ? '#ef4444' : '#10b981'}"></i> ${msg}</div>
    <button type="button" class="btn-close me-2 m-auto" data-bs-dismiss="toast"></button>
  </div>`;
  container.appendChild(el);
  setTimeout(() => el.remove(), 3000);
}
