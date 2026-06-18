import { useState, useEffect } from 'react';
import { NavLink, Outlet } from 'react-router-dom';
import { api } from '../api';

export default function Layout() {
  const [recordCount, setRecordCount] = useState('-');
  const [collapsed, setCollapsed] = useState(true);

  useEffect(() => {
    api.getInfo().then(res => {
      if (res.data) setRecordCount(res.data.active_records || 0);
    }).catch(() => {});
  }, []);

  const navItems = [
    { path: '/', icon: 'speedometer2', label: '概览' },
    { path: '/transactions', icon: 'list-ul', label: '交易' },
    { path: '/budgets', icon: 'pie-chart', label: '预算' },
    { path: '/categories', icon: 'tags', label: '类别' },
    { path: '/stats', icon: 'graph-up', label: '统计' },
  ];

  return (
    <>
      <nav className="navbar navbar-expand-lg navbar-dark navbar-ledger sticky-top">
        <div className="container">
          <NavLink className="navbar-brand" to="/">
            <i className="bi bi-journal-text"></i> Ledger
          </NavLink>
          <button
            className="navbar-toggler"
            type="button"
            onClick={() => setCollapsed(!collapsed)}
          >
            <span className="navbar-toggler-icon"></span>
          </button>
          <div className={`collapse navbar-collapse ${collapsed ? '' : 'show'}`}>
            <ul className="navbar-nav me-auto">
              {navItems.map(item => (
                <li className="nav-item" key={item.path}>
                  <NavLink
                    className={({ isActive }) => `nav-link ${isActive ? 'active' : ''}`}
                    to={item.path}
                    end={item.path === '/'}
                    onClick={() => setCollapsed(true)}
                  >
                    <i className={`bi bi-${item.icon}`}></i> {item.label}
                  </NavLink>
                </li>
              ))}
            </ul>
            <span className="navbar-text">
              <i className="bi bi-database"></i>{' '}
              <span id="recordCount">{recordCount}</span> 条记录
            </span>
          </div>
        </div>
      </nav>

      <div className="container py-4">
        <Outlet />
      </div>

      <div className="footer-ledger">
        <small>
          Ledger · 个人记账系统 · {recordCount} 条记录
        </small>
      </div>
    </>
  );
}
