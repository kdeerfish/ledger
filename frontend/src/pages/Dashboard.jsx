import { useState, useEffect, useRef, useCallback } from 'react';
import { Chart as ChartJS, CategoryScale, LinearScale, BarElement, PointElement, LineElement, ArcElement, Title, Tooltip, Legend, Filler } from 'chart.js';
import { Bar, Line, Doughnut } from 'react-chartjs-2';
import { api } from '../api';

ChartJS.register(CategoryScale, LinearScale, BarElement, PointElement, LineElement, ArcElement, Title, Tooltip, Legend, Filler);

export default function Dashboard() {
  const year = new Date().getFullYear();
  const [summary, setSummary] = useState(null);
  const [trendData, setTrendData] = useState({ items: [], cumulative: [] });
  const [categoryStats, setCategoryStats] = useState([]);
  const [recentTx, setRecentTx] = useState([]);
  const [selectedYear, setSelectedYear] = useState(year);
  const [excludeTagged, setExcludeTagged] = useState(true);

  // 展开明细
  const [selectedCategory, setSelectedCategory] = useState(null);
  const [detailTx, setDetailTx] = useState([]);
  const [detailLoading, setDetailLoading] = useState(false);

  useEffect(() => {
    loadData();
  }, [selectedYear, excludeTagged]);

  // 饼图点击 → 展开明细（不跳转）
  const handleCategoryClick = useCallback(async (label) => {
    if (!label) return;
    if (selectedCategory === label) {
      setSelectedCategory(null);
      setDetailTx([]);
      return;
    }
    setSelectedCategory(label);
    setDetailLoading(true);
    try {
      const res = await api.getTransactions({ category: label, limit: 50, year: selectedYear });
      setDetailTx(res.data?.transactions || []);
    } catch (e) {
      setDetailTx([]);
    } finally {
      setDetailLoading(false);
    }
  }, [selectedCategory, selectedYear]);

  const loadData = async () => {
    try {
      const params = { year: selectedYear, exclude_tagged: excludeTagged.toString() };
      const [s, t, cs, r] = await Promise.all([
        api.getSummary(params),
        api.getTrends({ ...params, granularity: 'month' }),
        api.getStats({ ...params, group_by: 'category' }),
        api.getTransactions({ limit: 5 }),
      ]);
      if (s.data) setSummary(s.data);
      if (t.data) setTrendData(t.data);
      if (cs.data) setCategoryStats(cs.data.items || []);
      if (r.data) setRecentTx(r.data.transactions || []);
    } catch (e) {}
  };

  // 月度趋势图
  const trendChart = (() => {
    const items = trendData.items || [];
    const months = [...new Set(items.map(i => i.period))].sort();
    const income = months.map(m => items.find(i => i.period === m && i.type === '收入')?.amount || 0);
    const expense = months.map(m => items.find(i => i.period === m && i.type === '支出')?.amount || 0);
    return {
      labels: months.map(m => m?.slice(5) || m),
      datasets: [
        { label: '收入', data: income, backgroundColor: 'rgba(16,185,129,.7)', borderRadius: 4 },
        { label: '支出', data: expense, backgroundColor: 'rgba(239,68,68,.7)', borderRadius: 4 },
      ],
    };
  })();

  // 累计趋势
  const cumChart = (() => {
    const items = trendData.cumulative || [];
    const labels = items.map(i => i.period?.slice(5) || i.period);
    return {
      labels,
      datasets: [
        { label: '累计收入', data: items.map(i => i.income), borderColor: '#10b981', backgroundColor: 'rgba(16,185,129,.1)', fill: true, tension: .3 },
        { label: '累计支出', data: items.map(i => i.expense), borderColor: '#ef4444', backgroundColor: 'rgba(239,68,68,.1)', fill: true, tension: .3 },
      ],
    };
  })();

  // 类别饼图
  const pieChart = (() => {
    const expense = (categoryStats || []).filter(i => i.type === '支出').sort((a, b) => b.total - a.total);
    const colors = ['#ef4444','#f59e0b','#10b981','#3b82f6','#8b5cf6','#ec4899','#14b8a6','#f97316','#6366f1','#84cc16','#e11d48','#0891b2'];
    return {
      labels: expense.map(i => i.group),
      datasets: [{
        data: expense.map(i => i.total),
        backgroundColor: colors.slice(0, expense.length),
        borderWidth: 2,
      }],
    };
  })();

  const years = [];
  for (let i = year - 2; i <= year + 1; i++) years.push(i);

  const chartOpts = (clickHandler) => ({
    responsive: true,
    maintainAspectRatio: false,
    onClick: clickHandler ? (e, elements) => {
      if (elements.length > 0) {
        const idx = elements[0].index;
        const label = e.chart.data.labels[idx];
        clickHandler(label);
      }
    } : undefined,
    plugins: { legend: { position: 'top', labels: { boxWidth: 12, padding: 10, font: { size: 11 } } } },
  });

  return (
    <div className="page-content">
      <div className="d-flex justify-content-between align-items-center mb-4 flex-wrap gap-2">
        <h4 className="mb-0"><i className="bi bi-speedometer2"></i> 收支概览</h4>
        <div className="d-flex gap-2 align-items-center">
          <div className="form-check form-switch">
            <input className="form-check-input" type="checkbox" id="dashboardExcludeToggle"
              checked={excludeTagged} onChange={e => setExcludeTagged(e.target.checked)} />
            <label className="form-check-label small" htmlFor="dashboardExcludeToggle">
              排除标记交易
            </label>
          </div>
          <select className="form-select form-select-sm" style={{ width: 'auto' }}
            value={selectedYear} onChange={e => setSelectedYear(Number(e.target.value))}>
            {years.map(y => <option key={y} value={y}>{y}年</option>)}
          </select>
        </div>
      </div>

      {/* Summary Cards */}
      <div className="row g-3 mb-4">
        <div className="col-md-4">
          <div className="summary-card income">
            <div className="card-body">
              <div className="card-title"><i className="bi bi-arrow-down-circle"></i> 收入</div>
              <p className="amount">¥ {fmt(summary?.income)}</p>
              <small className="text-muted">{summary?.income_count || 0} 笔</small>
            </div>
          </div>
        </div>
        <div className="col-md-4">
          <div className="summary-card expense">
            <div className="card-body">
              <div className="card-title"><i className="bi bi-arrow-up-circle"></i> 支出</div>
              <p className="amount">¥ {fmt(summary?.expense)}</p>
              <small className="text-muted">{summary?.expense_count || 0} 笔 · 日均 ¥{fmt(summary?.daily_avg_expense)}</small>
            </div>
          </div>
        </div>
        <div className="col-md-4">
          <div className="summary-card balance">
            <div className="card-body">
              <div className="card-title"><i className="bi bi-wallet2"></i> 结余</div>
              <p className="amount">¥ {fmt(summary?.balance)}</p>
              <small className="text-muted">{summary?.total_count || 0} 笔总计</small>
            </div>
          </div>
        </div>
      </div>

      {/* Charts Row 1 */}
      <div className="row g-3 mb-4">
        <div className="col-lg-7">
          <div className="card shadow-sm">
            <div className="card-body">
              <h6 className="card-title mb-3"><i className="bi bi-bar-chart"></i> 月度收支趋势</h6>
              <div className="chart-container">
                <Bar data={trendChart} options={{
                  ...chartOpts(),
                  scales: { y: { beginAtZero: true, ticks: { callback: v => '¥' + v.toLocaleString() } } },
                }} />
              </div>
            </div>
          </div>
        </div>
        <div className="col-lg-5">
          <div className="card shadow-sm">
            <div className="card-body">
              <h6 className="card-title mb-3"><i className="bi bi-pie-chart"></i> 支出类别占比</h6>
              <div className="chart-container">
                {pieChart.datasets[0].data.length > 0 ? (
                  <Doughnut data={pieChart} options={{
                    ...chartOpts((label) => handleCategoryClick(label)),
                    plugins: { legend: { position: 'right', labels: { boxWidth: 10, padding: 6, font: { size: 10 } } } },
                    cutout: '55%',
                  }} />
                ) : (
                  <div className="empty-state"><div className="icon">📊</div><p>暂无数据</p></div>
                )}
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Charts Row 2 */}
      <div className="row g-3 mb-4">
        <div className="col-lg-7">
          <div className="card shadow-sm">
            <div className="card-body">
              <h6 className="card-title mb-3"><i className="bi bi-graph-up"></i> 累计趋势</h6>
              <div className="chart-container chart-container-sm">
                {cumChart.labels.length > 0 ? (
                  <Line data={cumChart} options={{
                    ...chartOpts(),
                    scales: { y: { beginAtZero: true, ticks: { callback: v => '¥' + v.toLocaleString() } } },
                  }} />
                ) : (
                  <div className="empty-state"><div className="icon">📈</div><p>暂无数据</p></div>
                )}
              </div>
            </div>
          </div>
        </div>
        <div className="col-lg-5">
          <div className="card shadow-sm">
            <div className="card-body">
              <div className="d-flex justify-content-between align-items-center mb-3">
                <h6 className="mb-0"><i className="bi bi-clock-history"></i> 最近交易</h6>
                <a href="/transactions" className="btn btn-sm btn-outline-ledger">
                  查看全部
                </a>
              </div>
              <div>
                {recentTx.length === 0 ? (
                  <div className="empty-state"><div className="icon">📭</div><p>暂无交易记录</p></div>
                ) : recentTx.map(t => (
                  <div key={t.id} className="d-flex justify-content-between align-items-center py-2 border-bottom"
                    style={{ cursor: 'pointer' }}
                    onClick={() => {}}>
                    <div>
                      <small className="text-muted">{t.date?.slice(0, 10)}</small>
                      <div>
                        <span className={`badge ${t.type === '收入' ? 'badge-type-income' : 'badge-type-expense'}`}>{t.type}</span>
                        <small className="text-muted ms-1">{trunc(t.category, 8)}</small>
                      </div>
                    </div>
                    <div className="text-end">
                      <div className={t.type === '收入' ? 'amount-income' : 'amount-expense'}>¥ {fmt(t.amount)}</div>
                      <small className="text-muted">{trunc(t.account, 8)}</small>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* 饼图点击后展开的明细区域 */}
      {selectedCategory && (
        <div className="card shadow-sm border-primary mb-3">
          <div className="card-header d-flex justify-content-between align-items-center bg-primary bg-opacity-10">
            <h6 className="mb-0">
              <i className="bi bi-list-ul me-2"></i>
              {selectedCategory}
              <span className="text-muted ms-2">
                · 共 {detailTx.length} 笔
              </span>
            </h6>
            <button className="btn btn-sm btn-outline-secondary" onClick={() => { setSelectedCategory(null); setDetailTx([]); }}>
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
                      <th>账户</th>
                      <th>商家</th>
                      <th>备注</th>
                    </tr>
                  </thead>
                  <tbody>
                    {detailTx.map(tx => (
                      <tr key={tx.id}>
                        <td><small>{tx.date?.slice(0, 10)}</small></td>
                        <td><span className={`badge ${tx.type === '收入' ? 'badge-type-income' : 'badge-type-expense'}`}>{tx.type}</span></td>
                        <td className={tx.type === '收入' ? 'amount-income' : 'amount-expense'}>¥ {fmt(tx.amount)}</td>
                        <td><small>{tx.account}</small></td>
                        <td><small>{tx.merchant}</small></td>
                        <td><small className="text-muted">{trunc(tx.note, 12)}</small></td>
                      </tr>
                    ))}
                  </tbody>
                </table>
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
