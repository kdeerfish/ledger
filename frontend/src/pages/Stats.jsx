import { useState, useEffect, useCallback } from 'react';
import { Chart as ChartJS, CategoryScale, LinearScale, BarElement, ArcElement, PointElement, LineElement, Title, Tooltip, Legend, Filler } from 'chart.js';
import { Bar, Doughnut, Pie, Line } from 'react-chartjs-2';
import { api } from '../api';

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

export default function Stats() {
  const now = new Date();
  const [year, setYear] = useState(now.getFullYear());
  const [groupBy, setGroupBy] = useState('category');
  const [chartType, setChartType] = useState('doughnut');
  const [excludeTagged, setExcludeTagged] = useState(true);
  const [stats, setStats] = useState({ items: [] });
  const [summary, setSummary] = useState(null);

  // 展开明细相关 state
  const [selectedGroup, setSelectedGroup] = useState(null);
  const [detailTx, setDetailTx] = useState([]);
  const [detailLoading, setDetailLoading] = useState(false);

  useEffect(() => {
    loadData();
    setSelectedGroup(null);
    setDetailTx([]);
  }, [year, groupBy, excludeTagged]);

  const loadData = async () => {
    try {
      const params = { year, exclude_tagged: excludeTagged.toString() };
      const [s, st] = await Promise.all([
        api.getSummary(params),
        api.getStats({ ...params, group_by: groupBy }),
      ]);
      if (s.data) setSummary(s.data);
      if (st.data) setStats(st.data);
    } catch (e) {}
  };

  // 点击图表/表格行 → 展开明细（不跳转）
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
      const params = { limit: 50, year };
      if (groupBy === 'category') params.category = label;
      else if (groupBy === 'subcategory') params.subcategory = label;
      else if (groupBy === 'account') params.account = label;
      else if (groupBy === 'merchant') params.merchant = label;
      else if (groupBy === 'project') params.project = label;
      else if (groupBy === 'member') params.member = label;
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

  // 折线图数据：按月度趋势（需要按月数据）
  const [trendData, setTrendData] = useState([]);
  useEffect(() => {
    if (groupBy !== 'month') return;
    api.getTrends({ year, granularity: 'month' }).then(res => {
      if (res.data) setTrendData(res.data.items || []);
    }).catch(() => {});
  }, [year, groupBy]);

  const lineChartData = (() => {
    if (groupBy !== 'month' || !trendData.length) return null;
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
    onClick: (e, elements) => {
      if (elements.length > 0) {
        const idx = elements[0].index;
        const label = e.chart.data.labels[idx];
        handleGroupClick(label);
      }
    },
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

  const years = [];
  for (let i = now.getFullYear() - 2; i <= now.getFullYear() + 1; i++) years.push(i);

  // 图表类型列表（包含新增的）
  const CHART_TYPES = [
    { value: 'doughnut', label: '环形图', icon: '○' },
    { value: 'pie', label: '饼图', icon: '◕' },
    { value: 'bar', label: '柱状图', icon: '▃' },
    { value: 'hbar', label: '水平柱状图', icon: '▎' },
    { value: 'line', label: '折线图', icon: '╱' },
  ];

  const renderChart = (data, isExpense) => {
    if (!data || !data.datasets[0].data.length) {
      return <div className="empty-state"><div className="icon">📊</div><p>暂无数据</p></div>;
    }
    const color = isExpense ? '#ef4444' : '#10b981';
    switch (chartType) {
      case 'hbar':
        return <Bar data={data} options={{ ...chartOptions(true), indexAxis: 'y' }} />;
      case 'line':
        if (lineChartData) {
          return <Line data={lineChartData} options={{
            ...chartOptions(false),
            plugins: { ...chartOptions(false).plugins, legend: { display: true, position: 'top', labels: { boxWidth: 12 } } },
            scales: { y: { beginAtZero: true, ticks: { callback: v => '¥' + v.toLocaleString() } } },
          }} />;
        }
        return <Bar data={data} options={chartOptions(true)} />;
      case 'bar':
        return <Bar data={data} options={chartOptions(true)} />;
      case 'pie':
        return <Pie data={data} options={chartOptions(false)} />;
      default:
        return <Doughnut data={data} options={{ ...chartOptions(false), cutout: '55%' }} />;
    }
  };

  // 详情交易列表的选中组信息
  const selectedGroupInfo = items.find(i => i.group === selectedGroup);

  return (
    <div className="page-content">
      <div className="d-flex justify-content-between align-items-center mb-4 flex-wrap gap-2">
        <h4 className="mb-0"><i className="bi bi-graph-up"></i> 统计分析</h4>
        <div className="d-flex gap-2 align-items-center">
          <div className="form-check form-switch">
            <input className="form-check-input" type="checkbox" id="excludeToggle"
              checked={excludeTagged} onChange={e => setExcludeTagged(e.target.checked)} />
            <label className="form-check-label small" htmlFor="excludeToggle">
              排除标记交易
            </label>
          </div>
          <select className="form-select form-select-sm" style={{ width: 'auto' }}
            value={year} onChange={e => setYear(Number(e.target.value))}>
            {years.map(y => <option key={y} value={y}>{y}年</option>)}
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
          <div className="col-md-3">
            <div className="summary-card" style={{ borderLeft: '4px solid #10b981' }}>
              <div className="card-body">
                <div className="card-title">总收入</div>
                <p className="amount" style={{ color: '#10b981' }}>¥ {fmt(summary.income)}</p>
              </div>
            </div>
          </div>
          <div className="col-md-3">
            <div className="summary-card" style={{ borderLeft: '4px solid #ef4444' }}>
              <div className="card-body">
                <div className="card-title">总支出</div>
                <p className="amount" style={{ color: '#ef4444' }}>¥ {fmt(summary.expense)}</p>
              </div>
            </div>
          </div>
          <div className="col-md-3">
            <div className="summary-card" style={{ borderLeft: '4px solid #4f46e5' }}>
              <div className="card-body">
                <div className="card-title">结余</div>
                <p className="amount" style={{ color: '#4f46e5' }}>¥ {fmt(summary.balance)}</p>
              </div>
            </div>
          </div>
          <div className="col-md-3">
            <div className="summary-card" style={{ borderLeft: '4px solid #f59e0b' }}>
              <div className="card-body">
                <div className="card-title">笔数</div>
                <p className="amount" style={{ color: '#f59e0b' }}>{summary.total_count || 0}</p>
              </div>
            </div>
          </div>
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
      <div className="row g-3 mb-4">
        <div className="col-lg-6">
          <div className="card shadow-sm">
            <div className="card-body">
              <h6 className="card-title mb-3">
                <i className="bi bi-arrow-up-circle text-danger"></i> 支出分布
                <small className="text-muted ms-2">（点击查看详情）</small>
              </h6>
              <div className="chart-container">
                {renderChart(expenseChartData, true)}
              </div>
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
              <div className="chart-container">
                {renderChart(incomeChartData, false)}
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Data Table — 点击行展开明细 */}
      <div className="card shadow-sm mb-3">
        <div className="card-body">
          <h6 className="card-title mb-3"><i className="bi bi-table"></i> 数据明细（点击行查看详情）</h6>
          <div className="table-responsive">
            <table className="table stats-table">
              <thead>
                <tr>
                  <th>分组</th>
                  <th>类型</th>
                  <th>金额</th>
                  <th>笔数</th>
                  <th>占比</th>
                </tr>
              </thead>
              <tbody>
                {items.length === 0 ? (
                  <tr><td colSpan="5" className="text-center text-muted py-3">暂无数据</td></tr>
                ) : items.map((i, idx) => {
                  const totalByType = items.filter(x => x.type === i.type).reduce((s, x) => s + x.total, 0);
                  const pct = totalByType > 0 ? ((i.total / totalByType) * 100).toFixed(1) : '0.0';
                  const isSelected = selectedGroup === i.group;
                  return (
                    <tr key={idx}
                      onClick={() => handleGroupClick(i.group)}
                      style={{ cursor: 'pointer', backgroundColor: isSelected ? 'rgba(99,102,241,.08)' : undefined }}>
                      <td><strong>{i.group}</strong> {isSelected && <i className="bi bi-chevron-down ms-1 text-primary"></i>}</td>
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
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        </div>
      </div>

      {/* 展开的明细区域 */}
      {selectedGroup && (
        <div className="card shadow-sm border-primary mb-3">
          <div className="card-header d-flex justify-content-between align-items-center bg-primary bg-opacity-10">
            <h6 className="mb-0">
              <i className="bi bi-list-ul me-2"></i>
              {selectedGroup}
              {selectedGroupInfo && (
                <span className="text-muted ms-2">
                  · {selectedGroupInfo.count}笔 · ¥{fmt(selectedGroupInfo.total)}
                </span>
              )}
            </h6>
            <button className="btn btn-sm btn-outline-secondary" onClick={() => { setSelectedGroup(null); setDetailTx([]); }}>
              <i className="bi bi-x"></i> 收起
            </button>
          </div>
          <div className="card-body p-0">
            {detailLoading ? (
              <div className="text-center py-4"><span className="spinner-border spinner-border-sm"></span> 加载中...</div>
            ) : detailTx.length === 0 ? (
              <div className="text-center text-muted py-4">暂无交易记录</div>
            ) : (
              <div className="table-responsive">
                <table className="table table-sm table-hover mb-0">
                  <thead className="table-light">
                    <tr>
                      <th>日期</th>
                      <th>类型</th>
                      <th>金额</th>
                      <th>类别</th>
                      <th>账户</th>
                      <th>商家</th>
                      <th>备注</th>
                    </tr>
                  </thead>
                  <tbody>
                    {detailTx.map(tx => (
                      <tr key={tx.id}>
                        <td><small>{tx.date?.slice(0, 16)}</small></td>
                        <td><span className={`badge ${tx.type === '收入' ? 'badge-type-income' : 'badge-type-expense'}`}>{tx.type}</span></td>
                        <td className={tx.type === '收入' ? 'amount-income' : 'amount-expense'}>¥ {fmt(tx.amount)}</td>
                        <td><small>{tx.category}</small></td>
                        <td><small>{tx.account}</small></td>
                        <td><small>{tx.merchant}</small></td>
                        <td><small className="text-muted">{trunc(tx.note, 15)}</small></td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}
            {detailTx.length > 0 && (
              <div className="text-center py-2 border-top">
                <small className="text-muted">共 {selectedGroupInfo?.count || detailTx.length} 笔，合计 ¥{fmt(selectedGroupInfo?.total)}</small>
              </div>
            )}
          </div>
        </div>
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
