import { useState, useEffect } from 'react';
import { api } from '../api';

export default function Budgets() {
  const now = new Date();
  const [year, setYear] = useState(now.getFullYear());
  const [month, setMonth] = useState(now.getMonth() + 1);
  const [budgets, setBudgets] = useState([]);
  const [showModal, setShowModal] = useState(false);
  const [newBudget, setNewBudget] = useState({ category: '', amount: '', year: now.getFullYear(), month: now.getMonth() + 1 });

  useEffect(() => {
    loadBudgets();
  }, [year, month]);

  const loadBudgets = async () => {
    try {
      const res = await api.getBudgets({ year, month });
      if (res.data) setBudgets(res.data);
    } catch (e) {
      setBudgets([]);
    }
  };

  const handleSave = async () => {
    if (!newBudget.category || !newBudget.amount) return;
    try {
      await api.setBudget({
        category: newBudget.category,
        amount: parseFloat(newBudget.amount),
        year: newBudget.year,
        month: newBudget.month,
      });
      setShowModal(false);
      loadBudgets();
      toast('预算设置成功');
    } catch (e) {
      toast(e.message, 'danger');
    }
  };

  const years = [];
  for (let i = now.getFullYear() - 2; i <= now.getFullYear() + 1; i++) years.push(i);
  const months = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12];

  const totalBudget = budgets.reduce((s, b) => s + b.budget, 0);
  const totalSpent = budgets.reduce((s, b) => s + b.spent, 0);

  return (
    <div className="page-content">
      <div className="d-flex justify-content-between align-items-center mb-4 flex-wrap gap-2">
        <h4 className="mb-0"><i className="bi bi-pie-chart"></i> 预算管理</h4>
        <div className="d-flex gap-2">
          <select className="form-select form-select-sm" style={{ width: 'auto' }}
            value={year} onChange={e => setYear(Number(e.target.value))}>
            {years.map(y => <option key={y} value={y}>{y}年</option>)}
          </select>
          <select className="form-select form-select-sm" style={{ width: 'auto' }}
            value={month} onChange={e => setMonth(Number(e.target.value))}>
            {months.map(m => <option key={m} value={m}>{m}月</option>)}
          </select>
          <button className="btn btn-ledger btn-sm" onClick={() => setShowModal(true)}>
            <i className="bi bi-plus-lg"></i> 设置预算
          </button>
        </div>
      </div>

      {/* 总览 */}
      {budgets.length > 0 && (
        <div className="row g-3 mb-4">
          <div className="col-md-4">
            <div className="summary-card balance">
              <div className="card-body">
                <div className="card-title">总预算</div>
                <p className="amount">¥ {fmt(totalBudget)}</p>
              </div>
            </div>
          </div>
          <div className="col-md-4">
            <div className="summary-card expense">
              <div className="card-body">
                <div className="card-title">已支出</div>
                <p className="amount">¥ {fmt(totalSpent)}</p>
              </div>
            </div>
          </div>
          <div className="col-md-4">
            <div className="summary-card income">
              <div className="card-body">
                <div className="card-title">剩余</div>
                <p className="amount" style={{ color: totalBudget - totalSpent >= 0 ? '#10b981' : '#ef4444' }}>
                  ¥ {fmt(totalBudget - totalSpent)}
                </p>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Budget Cards */}
      {budgets.length === 0 ? (
        <div className="card">
          <div className="card-body">
            <div className="empty-state">
              <div className="icon">📊</div>
              <p>本月暂无预算，点击"设置预算"开始规划</p>
            </div>
          </div>
        </div>
      ) : (
        <>
          <div className="row g-3">
            {budgets.map(b => {
              const pct = b.percentage || 0;
              const barColor = pct > 100 ? 'bg-danger' : pct > 80 ? 'bg-warning' : 'bg-success';
              return (
                <div key={b.id} className="col-md-4">
                  <div className="summary-card h-100">
                    <div className="card-body">
                      <h6 className="card-title">{b.category}</h6>
                      <div className="d-flex justify-content-between mb-2">
                        <small className="text-muted">已用</small>
                        <strong className={pct > 100 ? 'text-danger' : ''}>¥ {fmt(b.spent)}</strong>
                      </div>
                      <div className="progress progress-budget mb-2">
                        <div className={`progress-bar ${barColor}`} style={{ width: `${Math.min(pct, 100)}%` }}></div>
                      </div>
                      <div className="d-flex justify-content-between">
                        <small>预算 ¥ {fmt(b.budget)}</small>
                        <small className={b.remaining < 0 ? 'text-danger fw-bold' : 'text-muted'}>
                          {b.remaining < 0 ? `超支 ¥ ${fmt(Math.abs(b.remaining))}` : `剩余 ¥ ${fmt(b.remaining)}`}
                        </small>
                      </div>
                      <div className="mt-2 text-center">
                        <span className={`badge ${pct > 100 ? 'bg-danger' : pct > 80 ? 'bg-warning' : 'bg-success'}`}>
                          {pct}%
                        </span>
                      </div>
                    </div>
                  </div>
                </div>
              );
            })}
          </div>

          {/* 明细列表 */}
          <div className="card shadow-sm mt-4">
            <div className="card-body">
              <h6 className="card-title mb-3"><i className="bi bi-list-check"></i> 预算执行明细</h6>
              <div className="table-responsive">
                <table className="table table-ledger">
                  <thead>
                    <tr><th>类别</th><th>预算</th><th>已用</th><th>剩余</th><th>进度</th></tr>
                  </thead>
                  <tbody>
                    {budgets.map(b => {
                      const pct = b.percentage || 0;
                      return (
                        <tr key={b.id}>
                          <td><strong>{b.category}</strong></td>
                          <td>¥ {fmt(b.budget)}</td>
                          <td className="amount-expense">¥ {fmt(b.spent)}</td>
                          <td className={b.remaining < 0 ? 'text-danger fw-bold' : ''}>
                            ¥ {fmt(b.remaining)}
                          </td>
                          <td>
                            <div className="d-flex align-items-center gap-2">
                              <div className="progress progress-budget flex-grow-1" style={{ height: 6 }}>
                                <div className={`progress-bar ${pct > 100 ? 'bg-danger' : pct > 80 ? 'bg-warning' : 'bg-success'}`}
                                  style={{ width: `${Math.min(pct, 100)}%` }}></div>
                              </div>
                              <small className={pct > 100 ? 'text-danger' : ''}>{pct}%</small>
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
        </>
      )}

      {/* 设置预算弹窗 */}
      {showModal && (
        <div className="modal fade show d-block" tabIndex="-1" style={{ background: 'rgba(0,0,0,.5)' }}>
          <div className="modal-dialog modal-dialog-centered">
            <div className="modal-content">
              <div className="modal-header">
                <h5 className="modal-title">设置预算</h5>
                <button type="button" className="btn-close" onClick={() => setShowModal(false)}></button>
              </div>
              <div className="modal-body">
                <div className="mb-3">
                  <label className="form-label">类别</label>
                  <input type="text" className="form-control" value={newBudget.category}
                    onChange={e => setNewBudget({ ...newBudget, category: e.target.value })}
                    placeholder="如：食品酒水" />
                </div>
                <div className="mb-3">
                  <label className="form-label">预算金额</label>
                  <input type="number" step="0.01" className="form-control" value={newBudget.amount}
                    onChange={e => setNewBudget({ ...newBudget, amount: e.target.value })} />
                </div>
                <div className="row g-2">
                  <div className="col-6">
                    <label className="form-label">年</label>
                    <select className="form-select" value={newBudget.year}
                      onChange={e => setNewBudget({ ...newBudget, year: Number(e.target.value) })}>
                      {years.map(y => <option key={y} value={y}>{y}</option>)}
                    </select>
                  </div>
                  <div className="col-6">
                    <label className="form-label">月</label>
                    <select className="form-select" value={newBudget.month}
                      onChange={e => setNewBudget({ ...newBudget, month: Number(e.target.value) })}>
                      {months.map(m => <option key={m} value={m}>{m}月</option>)}
                    </select>
                  </div>
                </div>
              </div>
              <div className="modal-footer">
                <button className="btn btn-secondary" onClick={() => setShowModal(false)}>取消</button>
                <button className="btn btn-ledger" onClick={handleSave}>
                  <i className="bi bi-check-lg"></i> 保存
                </button>
              </div>
            </div>
          </div>
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
  el.className = 'toast align-items-center border-0 bg-white shadow-sm';
  el.style.cssText = 'position:fixed;top:1rem;right:1rem;z-index:9999;border-radius:12px';
  el.innerHTML = `<div class="d-flex">
    <div class="toast-body"><i class="bi bi-${type === 'danger' ? 'exclamation-circle' : 'check-circle'}" style="color:${type === 'danger' ? '#ef4444' : '#10b981'}"></i> ${msg}</div>
    <button type="button" class="btn-close me-2 m-auto" data-bs-dismiss="toast"></button>
  </div>`;
  container.appendChild(el);
  setTimeout(() => el.remove(), 3000);
}
