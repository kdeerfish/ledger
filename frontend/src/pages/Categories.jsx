import { useState, useEffect } from 'react';
import { api } from '../api';

export default function Tags() {
  const [tags, setTags] = useState([]);
  const [newTag, setNewTag] = useState({ name: '', color: '#6366f1' });
  const [batches, setBatches] = useState([]);

  useEffect(() => {
    loadTags();
    loadBatches();
  }, []);

  const loadTags = async () => {
    try {
      const res = await api.getTags();
      if (res.data) setTags(res.data);
    } catch (e) {}
  };

  const loadBatches = async () => {
    try {
      const res = await api.getImportBatches();
      if (res.data) setBatches(res.data);
    } catch (e) {}
  };

  const handleCreateTag = async () => {
    if (!newTag.name.trim()) return;
    try {
      await api.createTag(newTag);
      setNewTag({ name: '', color: '#6366f1' });
      loadTags();
    } catch (e) {}
  };

  const handleDeleteTag = async (id, name) => {
    if (name === '排除统计') return;
    if (!confirm(`确认删除标签"${name}"？此操作不可恢复。`)) return;
    try {
      await api.deleteTag(id);
      loadTags();
    } catch (e) {}
  };

  const colors = ['#6366f1', '#ef4444', '#f59e0b', '#10b981', '#3b82f6', '#ec4899', '#14b8a6', '#f97316', '#8b5cf6', '#84cc16', '#e11d48', '#0891b2'];

  return (
    <div className="page-content">
      <h4 className="mb-4"><i className="bi bi-tags"></i> 标签管理</h4>

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
                      display: 'inline-block', width: 28, height: 28,
                      borderRadius: '50%', background: c, cursor: 'pointer',
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
      <div className="card mb-4">
        <div className="card-header"><strong>所有标签</strong></div>
        <div className="card-body">
          {tags.length === 0 ? (
            <div className="text-center text-muted py-4">暂无标签</div>
          ) : (
            <div className="row g-2">
              {tags.map(tag => (
                <div key={tag.id} className="col-md-4 col-lg-3">
                  <div className="d-flex justify-content-between align-items-center p-2 border rounded">
                    <div className="d-flex align-items-center gap-2">
                      <span style={{
                        display: 'inline-block', width: 12, height: 12,
                        borderRadius: '50%', background: tag.color,
                      }}></span>
                      <div>
                        <strong>{tag.name}</strong>
                        <br /><small className="text-muted">{tag.usage_count || 0} 笔</small>
                      </div>
                    </div>
                    {tag.name !== '排除统计' && (
                      <button className="btn btn-sm btn-outline-danger py-0 px-1"
                        onClick={() => handleDeleteTag(tag.id, tag.name)}>
                        <i className="bi bi-trash"></i>
                      </button>
                    )}
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>

      {/* 导入批次历史 */}
      {batches.length > 0 && (
        <div className="card">
          <div className="card-header"><strong>导入批次历史</strong></div>
          <div className="card-body p-0">
            <table className="table table-sm mb-0">
              <thead className="table-light">
                <tr>
                  <th>时间</th>
                  <th>来源</th>
                  <th>文件名</th>
                  <th>记录数</th>
                  <th>标签</th>
                </tr>
              </thead>
              <tbody>
                {batches.map(b => (
                  <tr key={b.id}>
                    <td><small>{b.created_at?.slice(0, 16)}</small></td>
                    <td><span className="badge bg-info">{b.source}</span></td>
                    <td><small>{b.filename || '-'}</small></td>
                    <td>{b.row_count}</td>
                    <td>
                      {(() => {
                        try {
                          const t = JSON.parse(b.tags || '[]');
                          return t.map(tag => <span key={tag} className="badge bg-secondary me-1">{tag}</span>);
                        } catch { return '-'; }
                      })()}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}
    </div>
  );
}
