import { useState, useEffect, useCallback } from 'react';
import { api } from '../api';

const FORMAT_OPTIONS = [
  { key: 'excel', icon: 'file-earmark-excel', label: 'Excel', desc: '多 Sheet，含汇总统计', color: '#198754' },
  { key: 'csv', icon: 'file-earmark-spreadsheet', label: 'CSV', desc: '通用交换，可重新导入', color: '#0d6efd' },
  { key: 'pdf', icon: 'file-earmark-pdf', label: 'PDF', desc: '月度报告，适合打印', color: '#dc3545' },
  { key: 'json', icon: 'filetype-json', label: 'JSON', desc: '开发者/API 用', color: '#6c757d' },
];

export default function Export() {
  const [format, setFormat] = useState('excel');
  const [startDate, setStartDate] = useState('');
  const [endDate, setEndDate] = useState('');
  const [category, setCategory] = useState('');
  const [account, setAccount] = useState('');
  const [typeFilter, setTypeFilter] = useState('');
  const [categories, setCategories] = useState([]);
  const [accounts, setAccounts] = useState([]);
  const [sheets, setSheets] = useState(['明细', '月度汇总', '分类统计', '账户统计']);
  const [importCompatible, setImportCompatible] = useState(true);
  const [preview, setPreview] = useState(null);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    Promise.all([api.getCategories(), api.getAccounts()]).then(([catRes, accRes]) => {
      if (catRes.data) {
        const cats = Array.isArray(catRes.data) ? catRes.data : [];
        setCategories(cats.map(c => typeof c === 'string' ? c : c.category || c.name || ''));
      }
      if (accRes.data) {
        setAccounts(accRes.data.map(a => typeof a === 'string' ? a : a.name || a.account || ''));
      }
    }).catch(() => {});
  }, []);

  const fetchPreview = useCallback(async () => {
    setLoading(true);
    const params = {};
    if (startDate) params.start_date = startDate;
    if (endDate) params.end_date = endDate;
    if (category) params.category = category;
    if (account) params.account = account;
    if (typeFilter) params.type = typeFilter;

    try {
      const res = await api.getExportPreview(params);
      if (res.success && res.data) {
        setPreview(res.data);
      }
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  }, [startDate, endDate, category, account, typeFilter]);

  useEffect(() => { fetchPreview(); }, []);

  const handleExport = useCallback(() => {
    const params = { format };
    if (startDate) params.start_date = startDate;
    if (endDate) params.end_date = endDate;
    if (category) params.category = category;
    if (account) params.account = account;
    if (typeFilter) params.type = typeFilter;
    if (format === 'excel' || format === 'pdf') {
      params.sheets = sheets.join(',');
    }
    if (format === 'csv') {
      params.import_compatible = importCompatible.toString();
    }

    const url = api.getExportDownloadUrl(params);
    window.open(url, '_blank');
  }, [format, startDate, endDate, category, account, typeFilter, sheets, importCompatible]);

  const toggleSheet = useCallback((sheet) => {
    setSheets(prev => prev.includes(sheet) ? prev.filter(s => s !== sheet) : [...prev, sheet]);
  }, []);

  const handleQuickRange = useCallback((range) => {
    const now = new Date();
    let start = '';
    if (range === '本月') {
      start = `${now.getFullYear()}-${String(now.getMonth() + 1).padStart(2, '0')}-01`;
    } else if (range === '本年') {
      start = `${now.getFullYear()}-01-01`;
    } else if (range === '近3月') {
      const d = new Date(now);
      d.setMonth(d.getMonth() - 2);
      start = `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, '0')}-01`;
    } else if (range === '全部') {
      start = '';
      setEndDate('');
    }
    if (start) setStartDate(start);
    if (range !== '全部') {
      setEndDate(`${now.getFullYear()}-${String(now.getMonth() + 1).padStart(2, '0')}-${String(now.getDate()).padStart(2, '0')}`);
    }
    setTimeout(fetchPreview, 100);
  }, [fetchPreview]);

  return (
    <div>
      <h4 className="mb-4"><i className="bi bi-cloud-download"></i> 数据导出</h4>

      <div className="row">
        {/* 左侧：筛选条件 */}
        <div className="col-lg-8">
          <div className="card mb-3">
            <div className="card-header"><strong>时间范围</strong></div>
            <div className="card-body">
              <div className="d-flex gap-2 mb-2 flex-wrap">
                {['本月', '本年', '近3月', '全部'].map(r => (
                  <button key={r} className="btn btn-outline-secondary btn-sm" onClick={() => handleQuickRange(r)}>{r}</button>
                ))}
              </div>
              <div className="row g-2">
                <div className="col-auto">
                  <input type="date" className="form-control form-control-sm" value={startDate}
                         onChange={e => setStartDate(e.target.value)} />
                </div>
                <div className="col-auto align-self-center">至</div>
                <div className="col-auto">
                  <input type="date" className="form-control form-control-sm" value={endDate}
                         onChange={e => setEndDate(e.target.value)} />
                </div>
                <div className="col-auto">
                  <button className="btn btn-primary btn-sm" onClick={fetchPreview} disabled={loading}>
                    <i className="bi bi-search"></i>
                  </button>
                </div>
              </div>
            </div>
          </div>

          <div className="card mb-3">
            <div className="card-header"><strong>筛选条件</strong> <small className="text-muted">（可选）</small></div>
            <div className="card-body">
              <div className="row g-2">
                <div className="col-md-4">
                  <label className="form-label small">类型</label>
                  <select className="form-select form-select-sm" value={typeFilter}
                          onChange={e => setTypeFilter(e.target.value)}>
                    <option value="">全部</option>
                    <option value="支出">支出</option>
                    <option value="收入">收入</option>
                  </select>
                </div>
                <div className="col-md-4">
                  <label className="form-label small">类别</label>
                  <select className="form-select form-select-sm" value={category}
                          onChange={e => setCategory(e.target.value)}>
                    <option value="">全部</option>
                    {categories.filter(Boolean).map(c => <option key={c} value={c}>{c}</option>)}
                  </select>
                </div>
                <div className="col-md-4">
                  <label className="form-label small">账户</label>
                  <select className="form-select form-select-sm" value={account}
                          onChange={e => setAccount(e.target.value)}>
                    <option value="">全部</option>
                    {accounts.filter(Boolean).map(a => <option key={a} value={a}>{a}</option>)}
                  </select>
                </div>
              </div>
            </div>
          </div>

          <div className="card mb-3">
            <div className="card-header"><strong>导出格式</strong></div>
            <div className="card-body">
              <div className="row g-2">
                {FORMAT_OPTIONS.map(opt => (
                  <div key={opt.key} className="col-6 col-md-3">
                    <div className={`card text-center p-3 ${format === opt.key ? 'border-primary' : ''}`}
                         style={{ cursor: 'pointer', borderWidth: format === opt.key ? 2 : 1 }}
                         onClick={() => setFormat(opt.key)}>
                      <i className={`bi bi-${opt.icon}`} style={{ fontSize: 28, color: opt.color }}></i>
                      <div className="fw-bold mt-1">{opt.label}</div>
                      <small className="text-muted">{opt.desc}</small>
                    </div>
                  </div>
                ))}
              </div>

              {/* 格式特定选项 */}
              {(format === 'excel' || format === 'pdf') && (
                <div className="mt-3">
                  <label className="form-label small">包含内容：</label>
                  <div className="d-flex gap-3 flex-wrap">
                    {['明细', '月度汇总', '分类统计', '账户统计'].map(s => (
                      <div key={s} className="form-check">
                        <input className="form-check-input" type="checkbox" id={`sheet-${s}`}
                               checked={sheets.includes(s)} onChange={() => toggleSheet(s)} />
                        <label className="form-check-label" htmlFor={`sheet-${s}`}>{s}</label>
                      </div>
                    ))}
                  </div>
                </div>
              )}

              {format === 'csv' && (
                <div className="mt-3">
                  <div className="form-check">
                    <input className="form-check-input" type="checkbox" id="importCompat"
                           checked={importCompatible} onChange={e => setImportCompatible(e.target.checked)} />
                    <label className="form-check-label" htmlFor="importCompat">
                      与导入格式兼容（列名和日期格式可直接重新导入）
                    </label>
                  </div>
                </div>
              )}
            </div>
          </div>
        </div>

        {/* 右侧：预览 */}
        <div className="col-lg-4">
          <div className="card mb-3">
            <div className="card-header"><strong>导出预览</strong></div>
            <div className="card-body">
              {preview ? (
                <div>
                  <div className="d-flex justify-content-between mb-2">
                    <span className="text-muted">记录数</span>
                    <strong>{preview.count}</strong>
                  </div>
                  <div className="d-flex justify-content-between mb-2">
                    <span className="text-muted">日期范围</span>
                    <span>{preview.date_range}</span>
                  </div>
                  <hr />
                  <div className="d-flex justify-content-between mb-1">
                    <span className="text-muted">收入</span>
                    <span className="text-success">¥{preview.income?.toLocaleString('zh-CN', { minimumFractionDigits: 2 })}</span>
                  </div>
                  <div className="d-flex justify-content-between mb-1">
                    <span className="text-muted">支出</span>
                    <span className="text-danger">¥{preview.expense?.toLocaleString('zh-CN', { minimumFractionDigits: 2 })}</span>
                  </div>
                  <div className="d-flex justify-content-between">
                    <span className="text-muted">结余</span>
                    <span className={preview.balance >= 0 ? 'text-success' : 'text-danger'}>
                      ¥{preview.balance?.toLocaleString('zh-CN', { minimumFractionDigits: 2 })}
                    </span>
                  </div>
                </div>
              ) : (
                <div className="text-center text-muted py-3">
                  {loading ? <span className="spinner-border spinner-border-sm"></span> : '选择条件后查看预览'}
                </div>
              )}
            </div>
          </div>

          <button className="btn btn-primary w-100 btn-lg" onClick={handleExport}
                  disabled={!preview || preview.count === 0}>
            <i className="bi bi-download me-2"></i>
            导出 {FORMAT_OPTIONS.find(f => f.key === format)?.label}
          </button>
        </div>
      </div>
    </div>
  );
}
