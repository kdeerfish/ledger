import { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { api } from '../api';

const DIMENSIONS = [
  { field: 'category', label: '类别', icon: 'folder' },
  { field: 'subcategory', label: '子类别', icon: 'folder2' },
  { field: 'account', label: '账户', icon: 'bank' },
  { field: 'merchant', label: '商家', icon: 'shop' },
  { field: 'member', label: '成员', icon: 'people' },
  { field: 'project', label: '项目', icon: 'kanban' },
];

export default function More() {
  const [suggestions, setSuggestions] = useState({});
  const [hiddenItems, setHiddenItems] = useState({});
  const [batches, setBatches] = useState([]);
  const [activeDim, setActiveDim] = useState('category');

  useEffect(() => {
    loadData();
  }, []);

  const loadData = async () => {
    try {
      const [s, b] = await Promise.all([
        api.getSuggestions({ field: 'all' }),
        api.getImportBatches(),
      ]);
      if (s.data) setSuggestions(s.data);
      if (b.data) setBatches(b.data);
    } catch (e) {}
    loadHidden();
  };

  const loadHidden = async () => {
    const result = {};
    for (const { field } of DIMENSIONS) {
      try {
        const res = await api.getHidden(field);
        if (res.data) result[field] = res.data;
      } catch (e) {}
    }
    setHiddenItems(result);
  };

  const handleHide = async (field, value) => {
    try {
      await api.hideItem(field, value);
      loadHidden();
      loadData();
    } catch (e) {}
  };

  const handleUnhide = async (field, value) => {
    try {
      await api.unhideItem(field, value);
      loadHidden();
    } catch (e) {}
  };

  // 获取某个维度的所有值（含隐藏状态）
  const getDimValues = (field) => {
    const suggestionKey = field === 'category' ? 'categories'
      : field === 'subcategory' ? 'subcategories'
      : field + 's';
    const items = suggestions[suggestionKey] || [];
    const hidden = hiddenItems[field] || [];
    return items.map(item => ({
      name: item.name || item,
      count: item.count || 0,
      amount: item.amount || 0,
      hidden: hidden.includes(item.name || item),
    }));
  };

  const dimValues = getDimValues(activeDim);
  const visibleCount = dimValues.filter(v => !v.hidden).length;
  const hiddenCount = dimValues.filter(v => v.hidden).length;

  return (
    <div className="page-content">
      <h4 className="mb-4"><i className="bi bi-gear"></i> 其他</h4>

      {/* 快捷入口 */}
      <div className="row g-3 mb-4">
        <div className="col-md-3">
          <Link to="/import" className="card text-decoration-none h-100">
            <div className="card-body text-center">
              <i className="bi bi-cloud-upload fs-3 text-primary"></i>
              <div className="mt-1 fw-bold">导入数据</div>
              <small className="text-muted">CSV 文件导入</small>
            </div>
          </Link>
        </div>
        <div className="col-md-3">
          <Link to="/export" className="card text-decoration-none h-100">
            <div className="card-body text-center">
              <i className="bi bi-cloud-download fs-3 text-success"></i>
              <div className="mt-1 fw-bold">导出数据</div>
              <small className="text-muted">Excel/CSV/PDF/JSON</small>
            </div>
          </Link>
        </div>
        <div className="col-md-3">
          <Link to="/tags" className="card text-decoration-none h-100">
            <div className="card-body text-center">
              <i className="bi bi-tags fs-3 text-warning"></i>
              <div className="mt-1 fw-bold">标签管理</div>
              <small className="text-muted">创建和管理标签</small>
            </div>
          </Link>
        </div>
        <div className="col-md-3">
          <Link to="/budgets" className="card text-decoration-none h-100">
            <div className="card-body text-center">
              <i className="bi bi-pie-chart fs-3 text-info"></i>
              <div className="mt-1 fw-bold">预算管理</div>
              <small className="text-muted">设置月度预算</small>
            </div>
          </Link>
        </div>
      </div>

      {/* 数据管理 */}
      <div className="card mb-4">
        <div className="card-header">
          <strong>数据管理</strong>
          <small className="text-muted ms-2">管理各类别选项的显示与隐藏</small>
        </div>
        <div className="card-body">
          {/* 维度选择 tabs */}
          <ul className="nav nav-pills mb-3 flex-wrap gap-1">
            {DIMENSIONS.map(({ field, label, icon }) => (
              <li key={field} className="nav-item">
                <button className={`nav-link py-1 px-3 ${activeDim === field ? 'active' : ''}`}
                  onClick={() => setActiveDim(field)}>
                  <i className={`bi bi-${icon} me-1`}></i>{label}
                </button>
              </li>
            ))}
          </ul>

          {/* 统计信息 */}
          <div className="d-flex gap-3 mb-3">
            <span className="badge bg-success">{visibleCount} 显示中</span>
            {hiddenCount > 0 && <span className="badge bg-secondary">{hiddenCount} 已隐藏</span>}
          </div>

          {/* 数据列表 */}
          {dimValues.length === 0 ? (
            <div className="text-center text-muted py-4">暂无数据</div>
          ) : (
            <div className="table-responsive" style={{ maxHeight: 400, overflowY: 'auto' }}>
              <table className="table table-sm table-hover mb-0">
                <thead style={{ position: 'sticky', top: 0, background: '#fff' }}>
                  <tr>
                    <th>{DIMENSIONS.find(d => d.field === activeDim)?.label}</th>
                    <th style={{ width: 80 }}>笔数</th>
                    <th style={{ width: 120 }}>金额</th>
                    <th style={{ width: 80 }}>操作</th>
                  </tr>
                </thead>
                <tbody>
                  {dimValues.map(v => (
                    <tr key={v.name} style={{ opacity: v.hidden ? 0.4 : 1 }}>
                      <td>
                        {v.name}
                        {v.hidden && <span className="badge bg-secondary ms-2" style={{ fontSize: 10 }}>已隐藏</span>}
                      </td>
                      <td><small>{v.count}</small></td>
                      <td><small>¥{Number(v.amount || 0).toLocaleString('zh-CN', { minimumFractionDigits: 2 })}</small></td>
                      <td>
                        {v.hidden ? (
                          <button className="btn btn-sm btn-outline-success py-0 px-2"
                            onClick={() => handleUnhide(activeDim, v.name)} title="取消隐藏">
                            <i className="bi bi-eye"></i>
                          </button>
                        ) : (
                          <button className="btn btn-sm btn-outline-secondary py-0 px-2"
                            onClick={() => handleHide(activeDim, v.name)} title="隐藏">
                            <i className="bi bi-eye-slash"></i>
                          </button>
                        )}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
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
                          return JSON.parse(b.tags || '[]').map(t => <span key={t} className="badge bg-secondary me-1">{t}</span>);
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
