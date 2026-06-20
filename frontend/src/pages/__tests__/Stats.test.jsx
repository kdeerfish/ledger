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
    getStats: vi.fn(),
  },
}));

import Stats from '../Stats';
import { api } from '../../api';

function renderStats() {
  return render(
    <MemoryRouter>
      <Stats />
    </MemoryRouter>,
  );
}

describe('Stats page', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    api.getSummary.mockResolvedValue({
      data: { income: 20000, expense: 12000, balance: 8000, total_count: 50 },
    });
    api.getStats.mockResolvedValue({
      data: {
        items: [
          { group: '餐饮', type: '支出', total: 5000, count: 30 },
          { group: '交通', type: '支出', total: 2000, count: 20 },
          { group: '工资', type: '收入', total: 15000, count: 2 },
          { group: '兼职', type: '收入', total: 5000, count: 5 },
        ],
      },
    });
  });

  it('renders the page title', async () => {
    renderStats();
    expect(screen.getByRole('heading', { name: /统计分析/ })).toBeInTheDocument();
  });

  it('displays summary card headings', async () => {
    renderStats();
    await waitFor(() => {
      expect(screen.getByText('总收入')).toBeInTheDocument();
      expect(screen.getByText('总支出')).toBeInTheDocument();
    });
  });

  it('displays summary amounts', async () => {
    renderStats();
    await waitFor(() => {
      expect(screen.getByText(/20,000/)).toBeInTheDocument();
    });
  });

  it('shows chart section headings', async () => {
    renderStats();
    await waitFor(() => {
      expect(screen.getByRole('heading', { name: /支出分布/ })).toBeInTheDocument();
      expect(screen.getByRole('heading', { name: /收入分布/ })).toBeInTheDocument();
    });
  });

  it('shows data table', async () => {
    renderStats();
    await waitFor(() => {
      expect(screen.getByRole('heading', { name: /数据明细/ })).toBeInTheDocument();
      // "餐饮" appears in both chart and table
      expect(screen.getAllByText('餐饮').length).toBeGreaterThanOrEqual(1);
    });
  });

  it('shows group by selector', async () => {
    renderStats();
    const selects = screen.getAllByRole('combobox');
    expect(selects.length).toBeGreaterThanOrEqual(3);
  });

  it('shows chart type selector', async () => {
    renderStats();
    const selects = screen.getAllByRole('combobox');
    expect(selects.length).toBeGreaterThanOrEqual(3);
  });

  it('shows empty states when no data', async () => {
    api.getStats.mockResolvedValue({ data: { items: [] } });
    renderStats();
    await waitFor(() => {
      expect(screen.getByText(/暂无支出数据/)).toBeInTheDocument();
      expect(screen.getByText(/暂无收入数据/)).toBeInTheDocument();
    });
  });

  it('shows empty table when no data', async () => {
    api.getStats.mockResolvedValue({ data: { items: [] } });
    renderStats();
    await waitFor(() => {
      expect(screen.getByText('暂无数据')).toBeInTheDocument();
    });
  });

  it('shows data count in table', async () => {
    renderStats();
    await waitFor(() => {
      expect(screen.getByText('30笔')).toBeInTheDocument();
      expect(screen.getByText('20笔')).toBeInTheDocument();
    });
  });

  it('handles API errors gracefully', async () => {
    api.getSummary.mockRejectedValue(new Error('Network error'));
    api.getStats.mockRejectedValue(new Error('Network error'));
    renderStats();
    await waitFor(() => {
      expect(screen.getByRole('heading', { name: /统计分析/ })).toBeInTheDocument();
    });
  });
});
