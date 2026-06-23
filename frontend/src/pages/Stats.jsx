import { useState, useEffect, useCallback } from 'react';
import { Chart as ChartJS, CategoryScale, LinearScale, BarElement, ArcElement, PointElement, LineElement, Title, Tooltip, Legend, Filler } from 'chart.js';
import { Bar, Doughnut, Pie, Line } from 'react-chartjs-2';
import { api } from '../api';
import TransactionForm from '../components/TransactionForm';

ChartJS.register(CategoryScale, LinearScale, BarElement, ArcElement, PointElement, LineElement, Title, Tooltip, Legend, Filler);

const GROUP_OPTIONS = [
  { value: 'category', label: '按类别' },
  { value: 'subcategory', label: '按子类别' },
  { value: 'account', label: '按账户' },
  { value: 'merchant', label: '按商家' },
  { value: 'project', label: '按项目' },
  { value: 'member', label: '按成员' },
  { value: 'month', label: '按月' },
  { value: 'tag', label: '按标签' },
  { value: 'type', label: '按类型' },
];

const CHART_COLORS = ['#ef4444','#f59e0b','#10b981','#3b82f6','#8b5cf6','#ec4899','#14b8a6','#f97316','#6366f1','#84cc16','#e11d48','#0891b2','#a855f7','#06b6d4','#d946ef','#22c55e'];

const CHART_TYPES = [
  { value: 'doughnut', label: '环形图', icon: '○' },
  { value: 'pie', label: '饼图', icon: '◕' },
  { value: 'bar', label: '柱状图', icon: '▃' },
  { value: 'hbar', label: '水平柱状图', icon: '▎' },
  { value: 'line', label: '趋势图', icon: '╱' },
];

export default function Stats() {
  const now = new Date();
  const [year, setYear] = useState('all');  // 'all' 或具体年份
  const [groupBy, setGroupBy] = useState('category');
  const [chartType, setChartType] = useState('doughnut');
  const [excludeTagged, setExcludeTagged] = useState(true);
  const [stats, setStats] = useState({ items: [] });
  const [summary, setSummary] = useState(null);
  const [trendData, setTrendData] = useState([]);

  // 展开明细
  const [selectedGroup, setSelectedGroup] = useState(null);
  const [detailTx, setDetailTx] = useState([]);
  const [detailLoading, setDetailLoading] = useState(false);

  // 大额筛选
  const [largeAmount, setLargeAmount] = useState('');

  useEffect(() => {
    loadData();
    setSelectedGroup(null);
    setDetailTx([]);
  }, [year, groupBy, excludeTagged]);

  const loadData = async () => {
    try {
      const params = { exclude_tagged: excludeTagged.toString() };
      if (year !== 'all') params.year = year;
      const [s, st, t] = await Promise.all([
        api.getSummary(params),
        api.getStats({ ...params, group_by: groupBy }),
        api.getTrends({ ...params, granularity: 'month', year: year === 'all' ? now.getFullYear() : year }),
      ]);
      if (s.data) setSummary(s.data);
      if (st.data) setStats(st.data);
      if (t.data) setTrendData(t.data.items || []);
    } catch (e) {}
  };

  // 点击 → 展开明细
  const handleGroupClick = useCallback(async (label) => {
    if (!label) return;
    if (selectedGroup === label) {
      setSelectedGroup(null);
      setDetailTx([]);
      return;
    }
    setSelectedGroup(label);
    setDetailLoading(true);
    try {
      const params = { limit: 100 };
      if (groupBy === 'category') params.category = label;
      else if (groupBy === 'subcategory') params.subcategory = label;
      else if (groupBy === 'account') params.account = label;
      else if (groupBy === 'merchant') params.merchant = label;
      else if (groupBy === 'project') params.project = label;
      else if (groupBy === 'member') params.member = label;
      if (year !== 'all') {
        params.start_date = `${year}-01-01`;
        params.end_date = `${year}-12-31`;
      }
      const res = await api.getTransactions(params);
      setDetailTx(res.data?.transactions || []);
    } catch (e) {
      setDetailTx([]);
    } finally {
      setDetailLoading(false);
    }
  }, [selectedGroup, groupBy, year]);

  const items = stats.items || [];
  const expenseItems = items.filter(i => i.type === '支出').sort((a, b) => b.total - a.total);
  const incomeItems = items.filter(i => i.type === '收入').sort((a, b) => b.total - a.total);

  // 大额交易筛选
  const filteredItems = largeAmount
    ? items.filter(i => i.total >= Number(largeAmount))
    : items;

  const expenseChartData = {
    labels: expenseItems.map(i => i.group),
    datasets: [{
      data: expenseItems.map(i => i.total),
      backgroundColor: CHART_COLORS.slice(0, expenseItems.length),
      borderWidth: chartType === 'doughnut' ? 2 : 0,
      borderRadius: chartType === 'bar' ? 4 : 0,
    }],
  };

  const incomeChartData = {
    labels: incomeItems.map(i => i.group),
    datasets: [{
      data: incomeItems.map(i => i.total),
      backgroundColor: CHART_COLORS.slice(0, incomeItems.length),
      borderWidth: chartType === 'doughnut' ? 2 : 0,
      borderRadius: chartType === 'bar' ? 4 : 0,
    }],
  };

  // 趋势折线图：各类别月度趋势
  const lineChartData = (() => {
    if (!trendData.length) return null;
    const months = [...new Set(trendData.map(i => i.period))].sort();
    const income = months.map(m => trendData.find(i => i.period === m && i.type === '收入')?.amount || 0);
    const expense = months.map(m => trendData.find(i => i.period === m && i.type === '支出')?.amount || 0);
    return {
      labels: months.map(m => m?.slice(5) || m),
      datasets: [
        { label: '收入', data: income, borderColor: '#10b981', backgroundColor: 'rgba(16,185,129,.1)', fill: true, tension: .3, pointRadius: 4 },
        { label: '支出', data: expense, borderColor: '#ef4444', backgroundColor: 'rgba(239,68,68,.1)', fill: true, tension: .3, pointRadius: 4 },
      ],
    };
  })();

  const chartOptions = (isBar) => ({
    responsive: true,
    maintainAspectRatio: false,
    interaction: { mode: 'index', intersect: false },
    onClick: chartType !== 'line' ? (e, elements) => {
      if (elements.length > 0) {
        const idx = elements[0].index;
        const label = e.chart.data.labels[idx];
        handleGroupClick(label);
      }
    } : undefined,
    plugins: {
      legend: {
        display: !isBar && chartType !== 'line',
        position: 'right',
        labels: { boxWidth: 12, padding: 8, font: { size: 10 } },
      },
      tooltip: {
        callbacks: {
          label: (ctx) => {
            const total = ctx.dataset.data.reduce((a, b) => a + b, 0);
            const pct = total > 0 ? ((ctx.raw / total) * 100).toFixed(1) : '0.0';
            return `¥ ${fmt(ctx.raw)} (${pct}%)`;
          },
        },
      },
    },
    scales: isBar ? {
      y: { beginAtZero: true, ticks: { callback: v => '¥' + v.toLocaleString(), maxTicksLimit: 8 } },
      x: { ticks: { maxRotation: 45, font: { size: 10 } } },
    } : {},
  });

  const years = ['all'];
  for (let i = now.getFullYear(); i >= now.getFullYear() - 2; i--) years.push(i);

  // 明细排序
  const [detailSortBy, setDetailSortBy] = useState('date');
  const [detailSortOrder, setDetailSortOrder] = useState('DESC');
  const [detailModalTx, setDetailModalTx] = useState(null);
  const [editId, setEditId] = useState(null);

  const sortedDetailTx = [...detailTx].sort((a, b) => {
    let va = a[detailSortBy] ?? '', vb = b[detailSortBy] ?? '';
    if (detailSortBy === 'amount') { va = Number(va); vb = Number(vb); }
    if (detailSortBy === 'date') { va = va || ''; vb = vb || ''; }
    if (va < vb) return detailSortOrder === 'ASC' ? -1 : 1;
    if (va > vb) return detailSortOrder === 'ASC' ? 1 : -1;
    return 0;
  });

  const handleDetailSort = (col) => {
    if (detailSortBy === col) {
      setDetailSortOrder(prev => prev === 'DESC' ? 'ASC' : 'DESC');
    } else {
      setDetailSortBy(col);
      setDetailSortOrder('DESC');
    }
  };

  const renderChart = (data, isExpense) => {
    if (chartType === 'line') {
      if (!lineChartData || !lineChartData.labels.length) {
        return <div className="empty-state"><div className="icon">📈</div><p>暂无趋势数据</p></div>;
      }
      return <Line data={lineChartData} options={{
        responsive: true, maintainAspectRatio: false,
        interaction: { mode: 'index', intersect: false },
        plugins: {
          legend: { display: true, position: 'top', labels: { boxWidth: 12 } },
          tooltip: {
            mode: 'index',
            intersect: false,
            callbacks: {
              label: (ctx) => `${ctx.dataset.label}: ¥${Number(ctx.raw).toLocaleString()}`,
            },
          },
        },
        scales: { y: { beginAtZero: true, ticks: { callback: v => '¥' + v.toLocaleString() } } },
      }} />;
    }
    if (!data || !data.datasets[0].data.length) {
      return <div className="empty-state"><div className="icon">📊</div><p>暂无数据</p></div>;
    }
    switch (chartType) {
      case 'hbar':
        return <Bar key="hbar" data={data} options={{ ...chartOptions(true), indexAxis: 'y' }} />;
      case 'bar':
        return <Bar key="bar" data={data} options={chartOptions(true)} />;
      case 'pie':
        return <Pie key="pie" data={data} options={chartOptions(false)} />;
      default:
        return <Doughnut key="doughnut" data={data} options={{ ...chartOptions(false), cutout: '55%' }} />;
    }
  };

  const selectedGroupInfo = items.find(i => i.group === selectedGroup);

  return (
    <div className="page-content">
      <div className="d-flex justify-content-between align-items-center mb-4 flex-wrap gap-2">
        <h4 className="mb-0"><i className="bi bi-graph-up"></i> 统计分析</h4>
        <div className="d-flex gap-2 align-items-center">
          <div className="form-check form-switch">
            <input className="form-check-input" type="checkbox" id="excludeToggle"
              checked={excludeTagged} onChange={e => setExcludeTagged(e.target.checked)} />
            <label className="form-check-label small" htmlFor="excludeToggle">排除标记交易</label>
          </div>
          <select className="form-select form-select-sm" style={{ width: 'auto' }}
            value={year} onChange={e => setYear(e.target.value === 'all' ? 'all' : Number(e.target.value))}>
            {years.map(y => <option key={y} value={y}>{y === 'all' ? '全部' : `${y}年`}</option>)}
          </select>
          <select className="form-select form-select-sm" style={{ width: 'auto' }}
            value={groupBy} onChange={e => setGroupBy(e.target.value)}>
            {GROUP_OPTIONS.map(o => <option key={o.value} value={o.value}>{o.label}</option>)}
          </select>
        </div>
      </div>

      {/* Summary Cards — 不跳转 */}
      {summary && (
        <div className="row g-3 mb-4">
          {[
            { label: '总收入', value: summary.income, color: '#10b981' },
            { label: '总支出', value: summary.expense, color: '#ef4444' },
            { label: '结余', value: summary.balance, color: '#4f46e5' },
            { label: '笔数', value: summary.total_count, color: '#f59e0b' },
          ].map(c => (
            <div key={c.label} className="col-md-3">
              <div className="summary-card" style={{ borderLeft: `4px solid ${c.color}` }}>
                <div className="card-body">
                  <div className="card-title">{c.label}</div>
                  <p className="amount" style={{ color: c.color }}>¥ {fmt(c.value)}</p>
                </div>
              </div>
            </div>
          ))}
        </div>
      )}

      {/* 图表类型选择器 */}
      <div className="d-flex gap-2 mb-3 flex-wrap">
        {CHART_TYPES.map(ct => (
          <button key={ct.value}
            className={`btn btn-sm ${chartType === ct.value ? 'btn-primary' : 'btn-outline-secondary'}`}
            onClick={() => setChartType(ct.value)}>
            {ct.icon} {ct.label}
          </button>
        ))}
      </div>

      {/* Charts */}
      {chartType === 'line' ? (
        <div className="card shadow-sm mb-4">
          <div className="card-body">
            <h6 className="card-title mb-3">
              <i className="bi bi-graph-up text-primary"></i> 月度收支趋势
            </h6>
            <div className="chart-container">
              {renderChart(null, false)}
            </div>
          </div>
        </div>
      ) : (
        <div className="row g-3 mb-4">
          <div className="col-lg-6">
            <div className="card shadow-sm">
              <div className="card-body">
                <h6 className="card-title mb-3">
                  <i className="bi bi-arrow-up-circle text-danger"></i> 支出分布
                  <small className="text-muted ms-2">（点击查看详情）</small>
                </h6>
                <div className="chart-container">{renderChart(expenseChartData, true)}</div>
              </div>
            </div>
          </div>
          <div className="col-lg-6">
            <div className="card shadow-sm">
              <div className="card-body">
                <h6 className="card-title mb-3">
                  <i className="bi bi-arrow-down-circle text-success"></i> 收入分布
                  <small className="text-muted ms-2">（点击查看详情）</small>
                </h6>
                <div className="chart-container">{renderChart(incomeChartData, false)}</div>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* 大额筛选 */}
      <div className="d-flex align-items-center gap-2 mb-2">
        <small className="text-muted">筛选金额 ≥</small>
        <input type="number" className="form-control form-control-sm" style={{ width: 120 }}
          placeholder="如 1000" value={largeAmount} onChange={e => setLargeAmount(e.target.value)} />
        {largeAmount && <span className="badge bg-warning text-dark">筛选: {filteredItems.length} 项</span>}
      </div>

      {/* Data Table — 点击行展开明细（嵌入行内） */}
      <div className="card shadow-sm mb-3">
        <div className="card-body">
          <h6 className="card-title mb-3"><i className="bi bi-table"></i> 分类明细</h6>
          <div className="table-responsive" style={{ maxHeight: 500, overflowY: 'auto' }}>
            <table className="table stats-table table-hover">
              <thead style={{ position: 'sticky', top: 0, background: '#fff', zIndex: 1 }}>
                <tr>
                  <th>分组</th>
                  <th>类型</th>
                  <th>金额</th>
                  <th>笔数</th>
                  <th>占比</th>
                </tr>
              </thead>
              <tbody>
                {(largeAmount ? filteredItems : items).length === 0 ? (
                  <tr><td colSpan="5" className="text-center text-muted py-3">暂无数据</td></tr>
                ) : (largeAmount ? filteredItems : items).flatMap((i, idx) => {
                  const totalByType = items.filter(x => x.type === i.type).reduce((s, x) => s + x.total, 0);
                  const pct = totalByType > 0 ? ((i.total / totalByType) * 100).toFixed(1) : '0.0';
                  const isSelected = selectedGroup === i.group;
                  const rows = [
                    <tr key={idx}
                      onClick={() => handleGroupClick(i.group)}
                      style={{ cursor: 'pointer', backgroundColor: isSelected ? 'rgba(99,102,241,.08)' : undefined }}>
                      <td><strong>{i.group}</strong> {isSelected && <i className="bi bi-chevron-up ms-1 text-primary"></i>}</td>
                      <td><span className={`badge ${i.type === '收入' ? 'badge-type-income' : 'badge-type-expense'}`}>{i.type}</span></td>
                      <td className={i.type === '收入' ? 'amount-income' : 'amount-expense'}>¥ {fmt(i.total)}</td>
                      <td>{i.count}笔</td>
                      <td>
                        <div className="d-flex align-items-center gap-2">
                          <div className="progress flex-grow-1" style={{ height: 6, borderRadius: 3 }}>
                            <div className={`progress-bar ${i.type === '收入' ? 'bg-success' : 'bg-danger'}`}
                              style={{ width: `${Math.min(parseFloat(pct), 100)}%` }}></div>
                          </div>
                          <small className="text-muted" style={{ minWidth: 40 }}>{pct}%</small>
                        </div>
                      </td>
                    </tr>,
                  ];
                  // 选中行下方插入明细
                  if (isSelected) {
                    rows.push(
                      <tr key={`${idx}-detail`} style={{ backgroundColor: '#f8f9ff' }}>
                        <td colSpan="5" style={{ padding: 0 }}>
                          <div style={{ padding: '8px 12px' }}>
                            {detailLoading ? (
                              <div className="text-center py-2"><span className="spinner-border spinner-border-sm"></span></div>
                            ) : detailTx.length === 0 ? (
                              <div className="text-center text-muted py-2"><small>暂无记录</small></div>
                            ) : (
                              <div style={{ maxHeight: 250, overflowY: 'auto' }}>
                                <table className="table table-sm mb-0" style={{ fontSize: 12 }}>
                                  <thead className="table-light">
                                    <tr>
                                      <th style={{ cursor: 'pointer' }} onClick={() => handleDetailSort('date')}>日期</th>
                                      <th style={{ cursor: 'pointer' }} onClick={() => handleDetailSort('type')}>类型</th>
                                      <th style={{ cursor: 'pointer' }} onClick={() => handleDetailSort('amount')}>金额</th>
                                      <th>类别</th>
                                      <th>账户</th>
                                      <th>商家</th>
                                      <th>备注</th>
                                    </tr>
                                  </thead>
                                  <tbody>
                                    {sortedDetailTx.map(tx => (
                                      <tr key={tx.id} style={{ cursor: 'pointer' }}
                                        onClick={() => setDetailModalTx(tx)}>
                                        <td>{tx.date?.slice(0, 10)}</td>
                                        <td><span className={`badge ${tx.type === '收入' ? 'badge-type-income' : 'badge-type-expense'}`} style={{ fontSize: 10 }}>{tx.type}</span></td>
                                        <td className={tx.type === '收入' ? 'amount-income' : 'amount-expense'}>¥{fmt(tx.amount)}</td>
                                        <td>{tx.category}</td>
                                        <td>{tx.account}</td>
                                        <td>{tx.merchant}</td>
                                        <td className="text-muted">{trunc(tx.note, 12)}</td>
                                      </tr>
                                    ))}
                                  </tbody>
                                </table>
                              </div>
                            )}
                          </div>
                        </td>
                      </tr>
                    );
                  }
                  return rows;
                })}
              </tbody>
            </table>
          </div>
        </div>
      </div>

      {/* 交易详情弹窗 */}
      {detailModalTx && (
        <div className="modal d-block" tabIndex="-1" style={{ backgroundColor: 'rgba(0,0,0,.4)' }}
          onClick={() => setDetailModalTx(null)}>
          <div className="modal-dialog modal-dialog-centered" onClick={e => e.stopPropagation()}>
            <div className="modal-content" style={{ borderRadius: 16 }}>
              <div className="modal-header border-0 pb-0">
                <h6 className="modal-title">
                  <span className={`badge me-2 ${detailModalTx.type === '收入' ? 'badge-type-income' : 'badge-type-expense'}`}>{detailModalTx.type}</span>
                  交易详情
                </h6>
                <button type="button" className="btn-close" onClick={() => setDetailModalTx(null)}></button>
              </div>
              <div className="modal-body">
                <div className="text-center mb-3">
                  <div className={detailModalTx.type === '收入' ? 'amount-income' : 'amount-expense'}
                    style={{ fontSize: 28, fontWeight: 700 }}>
                    ¥ {fmt(detailModalTx.amount)}
                  </div>
                </div>
                <div className="row g-2 small">
                  <div className="col-6"><span className="text-muted">日期：</span>{detailModalTx.date?.slice(0, 16)}</div>
                  <div className="col-6"><span className="text-muted">类别：</span>{detailModalTx.category || '-'}</div>
                  <div className="col-6"><span className="text-muted">账户：</span>{detailModalTx.account || '-'}</div>
                  <div className="col-6"><span className="text-muted">商家：</span>{detailModalTx.merchant || '-'}</div>
                  <div className="col-12"><span className="text-muted">备注：</span>{detailModalTx.note || '-'}</div>
                </div>
              </div>
              <div className="modal-footer border-0 pt-0">
                <button className="btn btn-sm btn-primary"
                  onClick={() => { setEditId(detailModalTx.id); setDetailModalTx(null); }}>
                  <i className="bi bi-pencil me-1"></i>编辑
                </button>
              </div>
            </div>
          </div>
        </div>
      )}
      {/* 编辑表单 */}
      {editId && (
        <TransactionForm
          show={true}
          onClose={() => setEditId(null)}
          onSaved={() => { setEditId(null); loadData(); }}
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
