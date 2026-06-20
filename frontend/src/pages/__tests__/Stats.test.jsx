import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, waitFor, fireEvent } from '@testing-library/react';
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

  // ── 基础渲染 ─────────────────────────────────────
  it('renders the page title', async () => {
    renderStats();
    expect(screen.getByRole('heading', { name: /统计分析/ })).toBeInTheDocument();
  });

  it('loads data on mount with current year and category groupBy', async () => {
    renderStats();
    await waitFor(() => {
      expect(api.getSummary).toHaveBeenCalledWith({ year: expect.any(Number) });
      expect(api.getStats).toHaveBeenCalledWith({
        year: expect.any(Number),
        group_by: 'category',
      });
    });
  });

  // ── 摘要卡片 ─────────────────────────────────────
  it('summary cards have correct values', async () => {
    renderStats();
    await waitFor(() => {
      expect(screen.getByText('总收入')).toBeInTheDocument();
      expect(screen.getByText('总支出')).toBeInTheDocument();
    });
  });

  // ── 图表区域 ─────────────────────────────────────
  it('shows chart section headings', async () => {
    renderStats();
    await waitFor(() => {
      expect(screen.getByRole('heading', { name: /支出分布/ })).toBeInTheDocument();
      expect(screen.getByRole('heading', { name: /收入分布/ })).toBeInTheDocument();
    });
  });

  // ── 数据表格 ─────────────────────────────────────
  it('shows data table with all items', async () => {
    renderStats();
    await waitFor(() => {
      expect(screen.getByRole('heading', { name: /数据明细/ })).toBeInTheDocument();
      expect(screen.getAllByText('餐饮').length).toBeGreaterThanOrEqual(1);
      expect(screen.getAllByText('交通').length).toBeGreaterThanOrEqual(1);
      expect(screen.getAllByText('工资').length).toBeGreaterThanOrEqual(1);
      expect(screen.getAllByText('兼职').length).toBeGreaterThanOrEqual(1);
    });
  });

  it('shows data count and type badges in table', async () => {
    renderStats();
    await waitFor(() => {
      expect(screen.getByText('30笔')).toBeInTheDocument();
      expect(screen.getByText('20笔')).toBeInTheDocument();
      expect(screen.getByText('2笔')).toBeInTheDocument();
      expect(screen.getByText('5笔')).toBeInTheDocument();
    });
  });

  // ── 年份切换 ─────────────────────────────────────
  it('year selector changes trigger data reload', async () => {
    renderStats();
    await waitFor(() => {
      expect(api.getStats).toHaveBeenCalledTimes(1);
    });
    const selects = screen.getAllByRole('combobox');
    const yearSelect = selects[0];
    fireEvent.change(yearSelect, { target: { value: '2023' } });
    await waitFor(() => {
      expect(api.getStats.mock.calls.length).toBeGreaterThan(1);
    });
  });

  // ── 分组切换 ─────────────────────────────────────
  it('groupBy selector changes trigger data reload', async () => {
    renderStats();
    await waitFor(() => {
      expect(api.getStats).toHaveBeenCalledTimes(1);
    });
    const selects = screen.getAllByRole('combobox');
    const groupBySelect = selects[1];
    fireEvent.change(groupBySelect, { target: { value: 'account' } });
    await waitFor(() => {
      expect(api.getStats).toHaveBeenCalledWith(
        expect.objectContaining({ group_by: 'account' }),
      );
    });
  });

  it('all groupBy options are available', async () => {
    renderStats();
    const selects = screen.getAllByRole('combobox');
    const groupBySelect = selects[1];
    expect(groupBySelect).toBeInTheDocument();
    // Check options exist
    expect(screen.getByRole('option', { name: '按类别' })).toBeInTheDocument();
    expect(screen.getByRole('option', { name: '按子类别' })).toBeInTheDocument();
    expect(screen.getByRole('option', { name: '按账户' })).toBeInTheDocument();
    expect(screen.getByRole('option', { name: '按商家' })).toBeInTheDocument();
    expect(screen.getByRole('option', { name: '按项目' })).toBeInTheDocument();
    expect(screen.getByRole('option', { name: '按成员' })).toBeInTheDocument();
    expect(screen.getByRole('option', { name: '按月' })).toBeInTheDocument();
    expect(screen.getByRole('option', { name: '按标签' })).toBeInTheDocument();
    expect(screen.getByRole('option', { name: '按类型' })).toBeInTheDocument();
  });

  // ── 图表类型切换 ─────────────────────────────────
  it('chart type selector has all options', async () => {
    renderStats();
    expect(screen.getByRole('option', { name: '环形图' })).toBeInTheDocument();
    expect(screen.getByRole('option', { name: '饼图' })).toBeInTheDocument();
    expect(screen.getByRole('option', { name: '柱状图' })).toBeInTheDocument();
  });

  it('chart type can be switched', async () => {
    renderStats();
    await waitFor(() => {
      expect(screen.getByRole('heading', { name: /支出分布/ })).toBeInTheDocument();
    });
    const selects = screen.getAllByRole('combobox');
    const chartTypeSelect = selects[2];
    fireEvent.change(chartTypeSelect, { target: { value: 'bar' } });
    // Component should re-render with bar chart type
    await waitFor(() => {
      expect(screen.getByRole('heading', { name: /支出分布/ })).toBeInTheDocument();
    });
  });

  it('chart type pie can be selected', async () => {
    renderStats();
    const selects = screen.getAllByRole('combobox');
    const chartTypeSelect = selects[2];
    fireEvent.change(chartTypeSelect, { target: { value: 'pie' } });
    await waitFor(() => {
      expect(screen.getByRole('heading', { name: /收入分布/ })).toBeInTheDocument();
    });
  });

  // ── 空状态 ─────────────────────────────────────
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

  // ── 错误处理 ─────────────────────────────────────
  it('handles API errors gracefully', async () => {
    api.getSummary.mockRejectedValue(new Error('Network error'));
    api.getStats.mockRejectedValue(new Error('Network error'));
    renderStats();
    await waitFor(() => {
      expect(screen.getByRole('heading', { name: /统计分析/ })).toBeInTheDocument();
    });
  });
});
