import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, waitFor } from '@testing-library/react';
import { MemoryRouter } from 'react-router-dom';

vi.mock('chart.js', () => ({
  Chart: { register: vi.fn() },
  CategoryScale: {},
  LinearScale: {},
  BarElement: {},
  PointElement: {},
  LineElement: {},
  ArcElement: {},
  Title: {},
  Tooltip: {},
  Legend: {},
  Filler: {},
}));

vi.mock('react-chartjs-2', () => ({
  Bar: () => null,
  Line: () => null,
  Doughnut: () => null,
  Pie: () => null,
}));

vi.mock('../../api', () => ({
  api: {
    getSummary: vi.fn(),
    getTrends: vi.fn(),
    getStats: vi.fn(),
    getTransactions: vi.fn(),
  },
}));

import Dashboard from '../Dashboard';
import { api } from '../../api';

function renderDashboard() {
  return render(
    <MemoryRouter>
      <Dashboard />
    </MemoryRouter>,
  );
}

describe('Dashboard', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    api.getSummary.mockResolvedValue({
      data: {
        income: 10000,
        expense: 5000,
        balance: 5000,
        income_count: 10,
        expense_count: 20,
        total_count: 30,
        daily_avg_expense: 166.67,
      },
    });
    api.getTrends.mockResolvedValue({
      data: {
        items: [
          { period: '2024-01', type: '收入', amount: 8000 },
          { period: '2024-01', type: '支出', amount: 3000 },
          { period: '2024-02', type: '收入', amount: 10000 },
          { period: '2024-02', type: '支出', amount: 5000 },
        ],
        cumulative: [
          { period: '2024-01', income: 8000, expense: 3000 },
          { period: '2024-02', income: 18000, expense: 8000 },
        ],
      },
    });
    api.getStats.mockResolvedValue({
      data: {
        items: [
          { group: '餐饮', type: '支出', total: 2000 },
          { group: '交通', type: '支出', total: 1000 },
          { group: '工资', type: '收入', total: 10000 },
        ],
      },
    });
    api.getTransactions.mockResolvedValue({
      data: {
        transactions: [
          { id: 1, date: '2024-02-01 10:00', type: '支出', amount: 50, category: '午餐', account: '微信' },
          { id: 2, date: '2024-02-01 12:00', type: '收入', amount: 100, category: '红包', account: '支付宝' },
        ],
      },
    });
  });

  it('renders the page title', async () => {
    renderDashboard();
    expect(screen.getByRole('heading', { name: /收支概览/ })).toBeInTheDocument();
  });

  it('displays summary card headings', async () => {
    renderDashboard();
    await waitFor(() => {
      expect(screen.getByText('收入', { selector: '.card-title' })).toBeInTheDocument();
      expect(screen.getByText('支出', { selector: '.card-title' })).toBeInTheDocument();
      expect(screen.getByText('结余', { selector: '.card-title' })).toBeInTheDocument();
    });
  });

  it('displays summary amounts after load', async () => {
    renderDashboard();
    await waitFor(() => {
      expect(screen.getByText(/10,000/)).toBeInTheDocument();
    });
  });

  it('shows year selector', async () => {
    renderDashboard();
    const yearSelect = screen.getByRole('combobox');
    expect(yearSelect).toBeInTheDocument();
  });

  it('renders chart section headings', async () => {
    renderDashboard();
    await waitFor(() => {
      expect(screen.getByRole('heading', { name: /月度收支趋势/ })).toBeInTheDocument();
      expect(screen.getByRole('heading', { name: /支出类别占比/ })).toBeInTheDocument();
      expect(screen.getByRole('heading', { name: /累计趋势/ })).toBeInTheDocument();
    });
  });

  it('shows recent transactions', async () => {
    renderDashboard();
    await waitFor(() => {
      expect(screen.getByText('午餐')).toBeInTheDocument();
      expect(screen.getByText('红包')).toBeInTheDocument();
    });
  });

  it('shows view all link', async () => {
    renderDashboard();
    expect(screen.getByRole('button', { name: '查看全部' })).toBeInTheDocument();
  });

  it('shows empty state when no recent transactions', async () => {
    api.getTransactions.mockResolvedValue({ data: { transactions: [] } });
    renderDashboard();
    await waitFor(() => {
      expect(screen.getByText('暂无交易记录')).toBeInTheDocument();
    });
  });

  it('shows empty chart states when no data', async () => {
    api.getTrends.mockResolvedValue({ data: { items: [], cumulative: [] } });
    api.getStats.mockResolvedValue({ data: { items: [] } });
    api.getTransactions.mockResolvedValue({ data: { transactions: [] } });
    renderDashboard();
    await waitFor(() => {
      expect(screen.getAllByText(/暂无数据/).length).toBeGreaterThanOrEqual(1);
    });
  });

  it('handles API errors gracefully', async () => {
    api.getSummary.mockRejectedValue(new Error('Network error'));
    api.getTrends.mockRejectedValue(new Error('Network error'));
    api.getStats.mockRejectedValue(new Error('Network error'));
    api.getTransactions.mockRejectedValue(new Error('Network error'));

    renderDashboard();
    await waitFor(() => {
      expect(screen.getByRole('heading', { name: /收支概览/ })).toBeInTheDocument();
    });
  });
});
