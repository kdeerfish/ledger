import { useState, useEffect, useCallback } from 'react';
import { useNavigate } from 'react-router-dom';
import { Chart as ChartJS, CategoryScale, LinearScale, BarElement, ArcElement, Title, Tooltip, Legend } from 'chart.js';
import { Bar, Doughnut, Pie } from 'react-chartjs-2';
import { api } from '../api';

ChartJS.register(CategoryScale, LinearScale, BarElement, ArcElement, Title, Tooltip, Legend);

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
  const navigate = useNavigate();
  const now = new Date();
  const [year, setYear] = useState(now.getFullYear());
  const [groupBy, setGroupBy] = useState('category');
  const [chartType, setChartType] = useState('doughnut');
  const [stats, setStats] = useState({ items: [] });
  const [summary, setSummary] = useState(null);

  useEffect(() => {
    loadData();
  }, [year, groupBy]);

  const loadData = async () => {
    try {
      const [s, st] = await Promise.all([
        api.getSummary({ year }),
        api.getStats({ year, group_by: groupBy }),
      ]);
      if (s.data) setSummary(s.data);
      if (st.data) setStats(st.data);
    } catch (e) {}
  };

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

  // 点击图表跳转到交易页并筛选
  const handleChartClick = (label) => {
    if (!label) return;
    const params = new URLSearchParams();
    if (groupBy === 'category') params.set('category', label);
    else if (groupBy === 'subcategory') params.set('subcategory', label);
    else if (groupBy === 'account') params.set('account', label);
    else if (groupBy === 'merchant') params.set('merchant', label);
    else if (groupBy === 'project') params.set('project', label);
    else if (groupBy === 'member') params.set('member', label);
    navigate(`/transactions?${params.toString()}`);
  };

  const chartOptions = (isBar) => ({
    responsive: true,
    maintainAspectRatio: false,
    onClick: (e, elements) => {
      if (elements.length > 0) {
        const idx = elements[0].index;
        const label = e.chart.data.labels[idx];
        handleChartClick(label);
      }
    },
    plugins: {
      legend: {
        display: !isBar,
        position: 'right',
        labels: { boxWidth: 12, padding: 8, font: { size: 10 } },
      },
      tooltip: {
        callbacks: {
          label: (ctx) => {
            const total = ctx.dataset.data.reduce((a, b) => a + b, 0);
            const pct = ((ctx.raw / total) * 100).toFixed(1);
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

  // 统计卡片点击也能筛选
  const StatCard = ({ label, value, color, filterKey }) => (
    <div className="summary-card" style={{ borderLeft: `4px solid ${color}`, cursor: 'pointer' }}
      onClick={() => filterKey && navigate(`/transactions?${filterKey}=${encodeURIComponent(label)}`)}>
      <div className="card-body">
        <div className="card-title">{label}</div>
        <p className="amount" style={{ color }}>¥ {fmt(value)}</p>
      </div>
    </div>
  );

  return (
    <div className="page-content">
      <div className="d-flex justify-content-between align-items-center mb-4 flex-wrap gap-2">
        <h4 className="mb-0"><i className="bi bi-graph-up"></i> 统计分析</h4>
        <div className="d-flex gap-2">
          <select className="form-select form-select-sm" style={{ width: 'auto' }}
            value={year} onChange={e => setYear(Number(e.target.value))}>
            {years.map(y => <option key={y} value={y}>{y}年</option>)}
          </select>
          <select className="form-select form-select-sm" style={{ width: 'auto' }}
            value={groupBy} onChange={e => setGroupBy(e.target.value)}>
            {GROUP_OPTIONS.map(o => <option key={o.value} value={o.value}>{o.label}</option>)}
          </select>
          <select className="form-select form-select-sm" style={{ width: 'auto' }}
            value={chartType} onChange={e => setChartType(e.target.value)}>
            <option value="doughnut">环形图</option>
            <option value="pie">饼图</option>
            <option value="bar">柱状图</option>
          </select>
        </div>
      </div>

      {/* Summary Cards */}
      {summary && (
        <div className="row g-3 mb-4">
          <div className="col-md-3">
            <StatCard label="总收入" value={summary.income} color="#10b981" filterKey="type" />
          </div>
          <div className="col-md-3">
            <StatCard label="总支出" value={summary.expense} color="#ef4444" filterKey="type" />
          </div>
          <div className="col-md-3">
            <StatCard label="结余" value={summary.balance} color="#4f46e5" />
          </div>
          <div className="col-md-3">
            <StatCard label="笔数" value={summary.total_count} color="#f59e0b" />
          </div>
        </div>
      )}

      {/* Charts */}
      <div className="row g-3 mb-4">
        {/* 支出图表 */}
        <div className="col-lg-6">
          <div className="card shadow-sm">
            <div className="card-body">
              <h6 className="card-title mb-3">
                <i className="bi bi-arrow-up-circle text-danger"></i> 支出分布
                <small className="text-muted ms-2">（点击查看明细）</small>
              </h6>
              <div className="chart-container">
                {expenseItems.length === 0 ? (
                  <div className="empty-state"><div className="icon">📊</div><p>暂无支出数据</p></div>
                ) : chartType === 'bar' ? (
                  <Bar data={expenseChartData} options={chartOptions(true)} />
                ) : (
                  <Doughnut data={expenseChartData} options={chartOptions(false)} />
                )}
              </div>
            </div>
          </div>
        </div>

        {/* 收入图表 */}
        <div className="col-lg-6">
          <div className="card shadow-sm">
            <div className="card-body">
              <h6 className="card-title mb-3">
                <i className="bi bi-arrow-down-circle text-success"></i> 收入分布
                <small className="text-muted ms-2">（点击查看明细）</small>
              </h6>
              <div className="chart-container">
                {incomeItems.length === 0 ? (
                  <div className="empty-state"><div className="icon">📊</div><p>暂无收入数据</p></div>
                ) : chartType === 'bar' ? (
                  <Bar data={incomeChartData} options={chartOptions(true)} />
                ) : (
                  <Pie data={incomeChartData} options={chartOptions(false)} />
                )}
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Data Table */}
      <div className="card shadow-sm">
        <div className="card-body">
          <h6 className="card-title mb-3"><i className="bi bi-table"></i> 数据明细（点击行可筛选）</h6>
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
                  const pct = totalByType > 0 ? ((i.total / totalByType) * 100).toFixed(1) : 0;
                  return (
                    <tr key={idx} onClick={() => handleChartClick(i.group)}
                      style={{ cursor: 'pointer' }}>
                      <td><strong>{i.group}</strong></td>
                      <td><span className={`badge ${i.type === '收入' ? 'badge-type-income' : 'badge-type-expense'}`}>{i.type}</span></td>
                      <td className={i.type === '收入' ? 'amount-income' : 'amount-expense'}>¥ {fmt(i.total)}</td>
                      <td>{i.count}笔</td>
                      <td>
                        <div className="d-flex align-items-center gap-2">
                          <div className="progress flex-grow-1" style={{ height: 6, borderRadius: 3 }}>
                            <div className={`progress-bar ${i.type === '收入' ? 'bg-success' : 'bg-danger'}`}
                              style={{ width: `${Math.min(pct, 100)}%` }}></div>
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
    </div>
  );
}

function fmt(v) {
  return Number(v || 0).toLocaleString('zh-CN', { minimumFractionDigits: 2, maximumFractionDigits: 2 });
}
