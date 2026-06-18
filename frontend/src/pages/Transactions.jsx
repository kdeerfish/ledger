import { useState, useEffect, useCallback, useRef } from 'react';
import { useSearchParams } from 'react-router-dom';
import { api } from '../api';
import TransactionForm from '../components/TransactionForm';

export default function Transactions() {
  const [searchParams, setSearchParams] = useSearchParams();
  const [txs, setTxs] = useState([]);
  const [total, setTotal] = useState(0);
  const [page, setPage] = useState(1);
  const [showForm, setShowForm] = useState(false);
  const [editId, setEditId] = useState(null);
  const [suggestions, setSuggestions] = useState({});
  const [tags, setTags] = useState([]);
  const pageSize = 20;

  // 筛选状态
  const [filters, setFilters] = useState({
    keyword: searchParams.get('keyword') || searchParams.get('search') || '',
    type: searchParams.get('type') || '',
    category: searchParams.get('category') || '',
    subcategory: searchParams.get('subcategory') || '',
    account: searchParams.get('account') || '',
    project: searchParams.get('project') || '',
    member: searchParams.get('member') || '',
    merchant: searchParams.get('merchant') || '',
    tag_ids: searchParams.get('tag_ids') || '',
    start_date: searchParams.get('start_date') || '',
    end_date: searchParams.get('end_date') || '',
  });

  const searchTimer = useRef(null);

  const loadData = useCallback(async () => {
    const params = {
      limit: pageSize,
      offset: (page - 1) * pageSize,
    };
    // 只添加有值的参数
    Object.entries(filters).forEach(([k, v]) => {
      if (v) params[k] = v;
    });

    try {
      const res = await api.getTransactions(params);
      if (res.data) {
        setTxs(res.data.transactions || []);
        setTotal(res.data.total || 0);
      }
    } catch (e) {}
  }, [filters, page]);

  const loadSuggestions = useCallback(async () => {
    try {
      const [s, t] = await Promise.all([
        api.getSuggestions({ field: 'all' }),
        api.getTags(),
      ]);
      if (s.data) setSuggestions(s.data);
      if (t.data) setTags(t.data);
    } catch (e) {}
  }, []);

  useEffect(() => {
    loadData();
    loadSuggestions();
  }, [loadData, loadSuggestions]);

  const setFilter = (key, val) => {
    setFilters(prev => ({ ...prev, [key]: val }));
    setPage(1);
  };

  const handleSearch = (val) => {
    setFilter('keyword', val);
    // 更新 URL
    const p = new URLSearchParams(searchParams);
    if (val) p.set('keyword', val);
    else p.delete('keyword');
    setSearchParams(p, { replace: true });
  };

  const clearFilters = () => {
    setFilters({
      keyword: '', type: '', category: '', subcategory: '', account: '',
      project: '', member: '', merchant: '', tag_ids: '',
      start_date: '', end_date: '',
    });
    setPage(1);
    setSearchParams({}, { replace: true });
  };

  const handleEdit = (id) => {
    setEditId(id);
    setShowForm(true);
  };

  const handleSaved = () => {
    loadData();
    loadSuggestions();
  };

  const handleDelete = async (id) => {
    if (!confirm(`确认删除交易 #${id}？可恢复。`)) return;
    try {
      await api.deleteTransaction(id);
      toast('已删除');
      loadData();
    } catch (e) {}
  };

  const handleTagClick = (tagId) => {
    const current = filters.tag_ids ? filters.tag_ids.split(',').map(Number) : [];
    if (current.includes(tagId)) {
      setFilter('tag_ids', current.filter(id => id !== tagId).join(','));
    } else {
      setFilter('tag_ids', [...current, tagId].join(','));
    }
  };

  // 图表点击后的筛选
  useEffect(() => {
    const category = searchParams.get('category');
    if (category) {
      setFilter('category', category);
    }
  }, [searchParams]);

  const totalPages = Math.ceil(total / pageSize);

  return (
    <div className="page-content">
      <div className="d-flex justify-content-between align-items-center mb-3 flex-wrap gap-2">
        <h4 className="mb-0"><i className="bi bi-list-ul"></i> 交易记录</h4>
        <button className="btn btn-ledger" onClick={() => { setEditId(null); setShowForm(true); }}>
          <i className="bi bi-plus-lg"></i> 记一笔
        </button>
      </div>

      {/* ── 筛选栏 ── */}
      <div className="filter-bar">
        <div className="row g-2">
          <div className="col-md-3">
            <input type="text" className="form-control form-control-sm"
              placeholder="🔍 搜索备注、类别、商家..." value={filters.keyword}
              onChange={e => {
                const v = e.target.value;
                clearTimeout(searchTimer.current);
                searchTimer.current = setTimeout(() => handleSearch(v), 300);
              }} />
          </div>
          <div className="col-md-1-5 col-4">
            <select className="form-select form-select-sm" value={filters.type}
              onChange={e => setFilter('type', e.target.value)}>
              <option value="">全部类型</option>
              <option value="支出">支出</option>
              <option value="收入">收入</option>
            </select>
          </div>
          <div className="col-md-1-5 col-4">
            <select className="form-select form-select-sm" value={filters.category}
              onChange={e => setFilter('category', e.target.value)}>
              <option value="">全部类别</option>
              {(suggestions.categories || []).map(c => (
                <option key={c.name} value={c.name}>{c.name}</option>
              ))}
            </select>
          </div>
          <div className="col-md-1-5 col-4">
            <select className="form-select form-select-sm" value={filters.account}
              onChange={e => setFilter('account', e.target.value)}>
              <option value="">全部账户</option>
              {(suggestions.accounts || []).map(a => (
                <option key={a.name} value={a.name}>{a.name}</option>
              ))}
            </select>
          </div>
          <div className="col-md-3">
            <div className="date-range-group">
              <input type="date" className="form-control form-control-sm"
                value={filters.start_date}
                onChange={e => setFilter('start_date', e.target.value)} />
              <span className="text-muted">~</span>
              <input type="date" className="form-control form-control-sm"
                value={filters.end_date}
                onChange={e => setFilter('end_date', e.target.value)} />
            </div>
          </div>
          <div className="col-auto">
            <button className="btn btn-sm btn-outline-secondary" onClick={clearFilters}>
              <i className="bi bi-x-circle"></i> 清除
            </button>
          </div>
        </div>

        {/* Tag 筛选 */}
        {tags.length > 0 && (
          <div className="mt-2 d-flex flex-wrap align-items-center gap-1">
            <small className="text-muted me-1">标签：</small>
            {tags.map(tag => {
              const active = filters.tag_ids.includes(String(tag.id));
              return (
                <span key={tag.id}
                  className={`tag-badge tag-badge-sm ${active ? '' : ''}`}
                  style={{
                    background: active ? tag.color + '33' : '#f1f5f9',
                    color: active ? tag.color : '#64748b',
                    border: `1px solid ${active ? tag.color + '66' : '#e2e8f0'}`,
                    cursor: 'pointer',
                  }}
                  onClick={() => handleTagClick(tag.id)}>
                  {tag.name}
                </span>
              );
            })}
          </div>
        )}
      </div>

      {/* ── 表格 ── */}
      <div className="card shadow-sm">
        <div className="card-body p-0">
          <div className="table-responsive" style={{ maxHeight: '60vh' }}>
            <table className="table table-ledger table-hover mb-0">
              <thead>
                <tr>
                  <th>日期</th>
                  <th>类型</th>
                  <th>金额</th>
                  <th>类别</th>
                  <th>子类别</th>
                  <th>账户</th>
                  <th>商家</th>
                  <th>项目</th>
                  <th>成员</th>
                  <th>标签</th>
                  <th>备注</th>
                  <th style={{ width: 70 }}>操作</th>
                </tr>
              </thead>
              <tbody>
                {txs.length === 0 ? (
                  <tr><td colSpan="12" className="text-center text-muted py-4">📭 暂无交易记录</td></tr>
                ) : txs.map(t => (
                  <tr key={t.id}>
                    <td className="text-nowrap"><small>{t.date?.slice(0, 10)}</small></td>
                    <td><span className={`badge ${t.type === '收入' ? 'badge-type-income' : 'badge-type-expense'}`}>{t.type}</span></td>
                    <td className={`${t.type === '收入' ? 'amount-income' : 'amount-expense'} text-nowrap`}>¥ {fmt(t.amount)}</td>
                    <td><small>{trunc(t.category, 8)}</small></td>
                    <td><small>{trunc(t.subcategory, 10)}</small></td>
                    <td><small>{trunc(t.account, 8)}</small></td>
                    <td><small>{trunc(t.merchant, 10)}</small></td>
                    <td><small>{trunc(t.project, 8)}</small></td>
                    <td><small>{trunc(t.member, 6)}</small></td>
                    <td>
                      {(t.tags || []).map(tag => (
                        <span key={tag.id} className="tag-badge tag-badge-sm"
                          style={{ background: tag.color + '22', color: tag.color, border: '1px solid ' + tag.color + '44' }}>
                          {tag.name}
                        </span>
                      ))}
                    </td>
                    <td><small className="text-muted">{trunc(t.note, 10)}</small></td>
                    <td className="text-nowrap">
                      <button className="btn btn-sm btn-outline-primary py-0 px-1 me-1"
                        onClick={() => handleEdit(t.id)} title="编辑">
                        <i className="bi bi-pencil"></i>
                      </button>
                      <button className="btn btn-sm btn-outline-danger py-0 px-1"
                        onClick={() => handleDelete(t.id)} title="删除">
                        <i className="bi bi-trash"></i>
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      </div>

      {/* ── 分页 ── */}
      <div className="d-flex justify-content-between align-items-center mt-2">
        <small className="text-muted">共 {total} 条记录</small>
        {totalPages > 1 && (
          <nav>
            <ul className="pagination pagination-sm mb-0">
              {Array.from({ length: Math.min(totalPages, 20) }, (_, i) => i + 1).map(p => (
                <li key={p} className={`page-item ${p === page ? 'active' : ''}`}>
                  <button className="page-link" onClick={() => setPage(p)}>{p}</button>
                </li>
              ))}
            </ul>
          </nav>
        )}
      </div>

      {/* ── Modal ── */}
      {showForm && (
        <TransactionForm
          show={showForm}
          onClose={() => { setShowForm(false); setEditId(null); }}
          onSaved={handleSaved}
          editId={editId}
        />
      )}
    </div>
  );
}

function fmt(v) {
  return Number(v || 0).toLocaleString('zh-CN', { minimumFractionDigits: 2, maximumFractionDigits: 2 });
}

function trunc(s, n = 15) {
  if (!s) return '-';
  return s.length > n ? s.slice(0, n) + '...' : s;
}

function toast(msg, type = 'success') {
  const container = document.querySelector('.toast-container') || (() => {
    const c = document.createElement('div');
    c.className = 'toast-container';
    document.body.appendChild(c);
    return c;
  })();
  const el = document.createElement('div');
  el.className = 'toast align-items-center border-0 bg-white shadow-sm';
  el.style.borderRadius = '12px';
  el.innerHTML = `<div class="d-flex">
    <div class="toast-body"><i class="bi bi-${type === 'danger' ? 'exclamation-circle' : 'check-circle'}" style="color:${type === 'danger' ? '#ef4444' : '#10b981'}"></i> ${msg}</div>
    <button type="button" class="btn-close me-2 m-auto" data-bs-dismiss="toast"></button>
  </div>`;
  container.appendChild(el);
  const bs = new bootstrap.Toast(el, { delay: 3000 });
  bs.show();
  el.addEventListener('hidden.bs.toast', () => el.remove());
}
