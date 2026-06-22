import { useState, useEffect, useCallback, useRef } from 'react';
import { useSearchParams } from 'react-router-dom';
import { api } from '../api';
import TransactionForm from '../components/TransactionForm';

export default function Transactions() {
  const [searchParams, setSearchParams] = useSearchParams();
  const [txs, setTxs] = useState([]);
  const [total, setTotal] = useState(0);
  const [page, setPage] = useState(1);
  const [pageSize, setPageSize] = useState(50);
  const [showForm, setShowForm] = useState(false);
  const [editId, setEditId] = useState(null);
  const [suggestions, setSuggestions] = useState({});
  const [tags, setTags] = useState([]);

  // 排序
  const [sortBy, setSortBy] = useState('trans_date');
  const [sortOrder, setSortOrder] = useState('DESC');

  // 筛选
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

  // 中文输入法状态
  const isComposing = useRef(false);

  const loadData = useCallback(async () => {
    const params = {
      limit: pageSize,
      offset: (page - 1) * pageSize,
      sort_by: sortBy,
      sort_order: sortOrder,
    };
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
  }, [filters, page, pageSize, sortBy, sortOrder]);

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
      loadData();
    } catch (e) {}
  };

  const handleToggleExclude = async (tx) => {
    const excludeTagName = '排除统计';
    const currentTags = tx.tags || [];
    const isExcluded = currentTags.some(t => t.name === excludeTagName);

    // 乐观更新：先改 UI，再发请求
    const optimisticTags = isExcluded
      ? currentTags.filter(t => t.name !== excludeTagName)
      : [...currentTags, { id: -1, name: excludeTagName, color: '#6b7280' }];

    setTxs(prev => prev.map(item =>
      item.id === tx.id ? { ...item, tags: optimisticTags } : item
    ));

    let excludeTag = tags.find(t => t.name === excludeTagName);
    if (!excludeTag) {
      try {
        await api.createTag({ name: excludeTagName, color: '#6b7280' });
        const res = await api.getTags();
        if (res.data) {
          setTags(res.data);
          excludeTag = res.data.find(t => t.name === excludeTagName);
        }
      } catch (e) {}
    }

    let newTagIds;
    if (isExcluded) {
      newTagIds = currentTags.filter(t => t.name !== excludeTagName).map(t => t.id);
    } else {
      const excludeId = excludeTag?.id;
      newTagIds = [...currentTags.map(t => t.id)];
      if (excludeId && !newTagIds.includes(excludeId)) {
        newTagIds.push(excludeId);
      }
    }

    try {
      await api.updateTransaction(tx.id, { tag_ids: newTagIds });
      // 成功后刷新获取真实数据
      loadData();
    } catch (e) {
      // 失败则回滚
      setTxs(prev => prev.map(item =>
        item.id === tx.id ? { ...item, tags: currentTags } : item
      ));
    }
  };

  const handleTagClick = (tagId) => {
    const current = filters.tag_ids ? filters.tag_ids.split(',').map(Number) : [];
    if (current.includes(tagId)) {
      setFilter('tag_ids', current.filter(id => id !== tagId).join(','));
    } else {
      setFilter('tag_ids', [...current, tagId].join(','));
    }
  };

  const handleSort = (col) => {
    if (sortBy === col) {
      setSortOrder(prev => prev === 'DESC' ? 'ASC' : 'DESC');
    } else {
      setSortBy(col);
      setSortOrder('DESC');
    }
    setPage(1);
  };

  useEffect(() => {
    const category = searchParams.get('category');
    if (category) setFilter('category', category);
  }, [searchParams]);

  const totalPages = Math.ceil(total / pageSize);

  const SortIcon = ({ col }) => {
    if (sortBy !== col) return <i className="bi bi-arrow-down-up text-muted ms-1" style={{ fontSize: 10 }}></i>;
    return <i className={`bi ${sortOrder === 'DESC' ? 'bi-sort-down' : 'bi-sort-up'} ms-1`}></i>;
  };

  return (
    <div className="page-content">
      <div className="d-flex justify-content-between align-items-center mb-3 flex-wrap gap-2">
        <h4 className="mb-0"><i className="bi bi-list-ul"></i> 交易记录</h4>
        <button className="btn btn-ledger" onClick={() => { setEditId(null); setShowForm(true); }}>
          <i className="bi bi-plus-lg"></i> 记一笔
        </button>
      </div>

      {/* 筛选栏 */}
      <div className="filter-bar">
        <div className="row g-2">
          <div className="col-md-3">
            <input type="text" className="form-control form-control-sm"
              placeholder="🔍 搜索备注、类别、商家..." value={filters.keyword}
              onCompositionStart={() => { isComposing.current = true; }}
              onCompositionEnd={e => {
                isComposing.current = false;
                handleSearch(e.target.value);
              }}
              onChange={e => {
                // 组合输入期间不触发搜索，避免中文输入法被打断
                if (!isComposing.current) {
                  handleSearch(e.target.value);
                } else {
                  // 更新显示值但不触发搜索
                  setFilters(prev => ({ ...prev, keyword: e.target.value }));
                }
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
                  style={{
                    display: 'inline-block', padding: '1px 8px', borderRadius: 10, fontSize: 12,
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

      {/* 表格 */}
      <div className="card shadow-sm">
        <div className="card-body p-0">
          <div className="table-responsive" style={{ maxHeight: '65vh' }}>
            <table className="table table-ledger table-hover mb-0">
              <thead>
                <tr>
                  <th style={{ cursor: 'pointer' }} onClick={() => handleSort('trans_date')}>日期 <SortIcon col="trans_date" /></th>
                  <th style={{ cursor: 'pointer' }} onClick={() => handleSort('type')}>类型 <SortIcon col="type" /></th>
                  <th style={{ cursor: 'pointer' }} onClick={() => handleSort('amount')}>金额 <SortIcon col="amount" /></th>
                  <th style={{ cursor: 'pointer' }} onClick={() => handleSort('category')}>类别 <SortIcon col="category" /></th>
                  <th>子类别</th>
                  <th style={{ cursor: 'pointer' }} onClick={() => handleSort('account')}>账户 <SortIcon col="account" /></th>
                  <th style={{ cursor: 'pointer' }} onClick={() => handleSort('merchant')}>商家 <SortIcon col="merchant" /></th>
                  <th>标签</th>
                  <th>备注</th>
                  <th style={{ width: 70 }}>操作</th>
                </tr>
              </thead>
              <tbody>
                {txs.length === 0 ? (
                  <tr><td colSpan="10" className="text-center text-muted py-4">📭 暂无交易记录</td></tr>
                ) : txs.map(t => {
                  const isExcluded = (t.tags || []).some(tag => tag.name === '排除统计');
                  return (
                  <tr key={t.id} style={{ opacity: isExcluded ? 0.5 : 1 }}>
                    <td className="text-nowrap"><small>{t.date?.slice(0, 10)}</small></td>
                    <td><span className={`badge ${t.type === '收入' ? 'badge-type-income' : 'badge-type-expense'}`}>{t.type}</span></td>
                    <td className={`${t.type === '收入' ? 'amount-income' : 'amount-expense'} text-nowrap`}>¥ {fmt(t.amount)}</td>
                    <td><small>{trunc(t.category, 8)}</small></td>
                    <td><small>{trunc(t.subcategory, 10)}</small></td>
                    <td><small>{trunc(t.account, 8)}</small></td>
                    <td><small>{trunc(t.merchant, 10)}</small></td>
                    <td>
                      {(t.tags || []).map(tag => (
                        <span key={tag.id} style={{
                          display: 'inline-block', padding: '0 6px', borderRadius: 8, fontSize: 10,
                          background: tag.color + '22', color: tag.color, border: '1px solid ' + tag.color + '44',
                          marginRight: 2,
                        }}>{tag.name}</span>
                      ))}
                    </td>
                    <td><small className="text-muted">{trunc(t.note, 10)}</small></td>
                    <td className="text-nowrap">
                      {(() => {
                        const isEx = (t.tags || []).some(tag => tag.name === '排除统计');
                        return (
                          <button className={`btn btn-sm py-0 px-1 me-1 ${isEx ? 'btn-warning' : 'btn-outline-secondary'}`}
                            onClick={() => handleToggleExclude(t)} title={isEx ? '取消排除' : '排除统计'}>
                            <i className={`bi ${isEx ? 'bi-eye-slash' : 'bi-eye'}`}></i>
                          </button>
                        );
                      })()}
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
                )})}
              </tbody>
            </table>
          </div>
        </div>
      </div>

      {/* 分页 */}
      <div className="d-flex justify-content-between align-items-center mt-2 flex-wrap gap-2">
        <div className="d-flex align-items-center gap-2">
          <small className="text-muted">共 {total} 条</small>
          <select className="form-select form-select-sm" style={{ width: 'auto' }}
            value={pageSize} onChange={e => { setPageSize(Number(e.target.value)); setPage(1); }}>
            <option value="20">20条/页</option>
            <option value="50">50条/页</option>
            <option value="100">100条/页</option>
            <option value="200">200条/页</option>
          </select>
        </div>
        {totalPages > 1 && (
          <nav>
            <ul className="pagination pagination-sm mb-0">
              {page > 1 && <li className="page-item"><button className="page-link" onClick={() => setPage(1)}>«</button></li>}
              {page > 1 && <li className="page-item"><button className="page-link" onClick={() => setPage(page - 1)}>‹</button></li>}
              {Array.from({ length: Math.min(totalPages, 7) }, (_, i) => {
                let p;
                if (totalPages <= 7) p = i + 1;
                else if (page <= 4) p = i + 1;
                else if (page >= totalPages - 3) p = totalPages - 6 + i;
                else p = page - 3 + i;
                return (
                  <li key={p} className={`page-item ${p === page ? 'active' : ''}`}>
                    <button className="page-link" onClick={() => setPage(p)}>{p}</button>
                  </li>
                );
              })}
              {page < totalPages && <li className="page-item"><button className="page-link" onClick={() => setPage(page + 1)}>›</button></li>}
              {page < totalPages && <li className="page-item"><button className="page-link" onClick={() => setPage(totalPages)}>»</button></li>}
            </ul>
          </nav>
        )}
      </div>

      {/* Modal */}
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
