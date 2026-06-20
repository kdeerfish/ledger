import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, waitFor, fireEvent } from '@testing-library/react';
import { MemoryRouter } from 'react-router-dom';

beforeEach(() => {
  window.bootstrap = {
    Toast: vi.fn(function() {
      this.show = vi.fn();
      this.hide = vi.fn();
    }),
  };
});

vi.mock('../../api', () => ({
  api: {
    getTransactions: vi.fn(),
    getSuggestions: vi.fn(),
    getTags: vi.fn(),
    deleteTransaction: vi.fn(),
  },
}));

import Transactions from '../Transactions';
import { api } from '../../api';

function renderTransactions(route = '/transactions') {
  return render(
    <MemoryRouter initialEntries={[route]}>
      <Transactions />
    </MemoryRouter>,
  );
}

const mockTransactions = [
  {
    id: 1, date: '2024-01-15 10:00', type: '支出', amount: 35.5,
    category: '餐饮', subcategory: '午餐', account: '微信',
    merchant: '美团', project: '工作', member: '本人', note: '工作日午餐',
    tags: [{ id: 1, name: '日常', color: '#6366f1' }],
  },
  {
    id: 2, date: '2024-01-15 18:00', type: '收入', amount: 5000,
    category: '工资', subcategory: '月薪', account: '银行',
    merchant: '公司', project: '', member: '本人', note: '月度工资',
    tags: [],
  },
];

describe('Transactions page', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    window.confirm = vi.fn(() => true);
    api.getTransactions.mockResolvedValue({
      data: { transactions: mockTransactions, total: 2 },
    });
    api.getSuggestions.mockResolvedValue({
      data: {
        categories: [{ name: '餐饮' }, { name: '交通' }],
        accounts: [{ name: '微信' }, { name: '银行' }],
      },
    });
    api.getTags.mockResolvedValue({
      data: [{ id: 1, name: '日常', color: '#6366f1' }],
    });
  });

  // ── 基础渲染 ─────────────────────────────────────
  it('renders the page title', async () => {
    renderTransactions();
    expect(screen.getByRole('heading', { name: /交易记录/ })).toBeInTheDocument();
  });

  it('shows add button and opens form modal', async () => {
    renderTransactions();
    fireEvent.click(screen.getByRole('button', { name: /记一笔/ }));
    await waitFor(() => {
      expect(screen.getByText('取消')).toBeInTheDocument();
    });
  });

  it('loads and displays transactions', async () => {
    renderTransactions();
    await waitFor(() => {
      expect(api.getTransactions).toHaveBeenCalled();
    });
    // Should have 2 edit buttons (one per transaction)
    expect(screen.getAllByTitle('编辑').length).toBe(2);
    expect(screen.getAllByTitle('删除').length).toBe(2);
  });

  it('displays transaction amounts', async () => {
    renderTransactions();
    await waitFor(() => {
      expect(screen.getAllByText(/35/).length).toBeGreaterThanOrEqual(1);
      expect(screen.getAllByText(/5,000/).length).toBeGreaterThanOrEqual(1);
    });
  });

  it('shows transaction count', async () => {
    renderTransactions();
    await waitFor(() => {
      expect(screen.getByText(/共 2 条记录/)).toBeInTheDocument();
    });
  });

  it('shows empty state when no transactions', async () => {
    api.getTransactions.mockResolvedValue({ data: { transactions: [], total: 0 } });
    renderTransactions();
    await waitFor(() => {
      expect(screen.getByText(/📭 暂无交易记录/)).toBeInTheDocument();
    });
  });

  // ── 筛选 ─────────────────────────────────────────
  it('renders filter controls', async () => {
    renderTransactions();
    expect(screen.getByPlaceholderText(/搜索备注/)).toBeInTheDocument();
    expect(screen.getByRole('button', { name: /清除/ })).toBeInTheDocument();
  });

  it('shows filter dropdowns with options', async () => {
    renderTransactions();
    await waitFor(() => {
      expect(screen.getByRole('option', { name: '全部类型' })).toBeInTheDocument();
      expect(screen.getByRole('option', { name: '支出' })).toBeInTheDocument();
      expect(screen.getByRole('option', { name: '全部类别' })).toBeInTheDocument();
      expect(screen.getByRole('option', { name: '全部账户' })).toBeInTheDocument();
    });
  });

  it('search input renders', async () => {
    renderTransactions();
    const input = screen.getByPlaceholderText(/搜索备注/);
    expect(input).toBeInTheDocument();
    expect(input.type).toBe('text');
  });

  it('type filter change triggers reload', async () => {
    renderTransactions();
    await waitFor(() => {
      expect(api.getTransactions).toHaveBeenCalledTimes(1);
    });
    // Find the select with 支出 option by looking at all selects
    const selects = document.querySelectorAll('select');
    let typeSelect = null;
    for (const sel of selects) {
      for (const opt of sel.options) {
        if (opt.value === '支出') {
          typeSelect = sel;
          break;
        }
      }
      if (typeSelect) break;
    }
    if (typeSelect) {
      fireEvent.change(typeSelect, { target: { value: '支出' } });
      await waitFor(() => {
        expect(api.getTransactions).toHaveBeenCalledWith(
          expect.objectContaining({ type: '支出' }),
        );
      });
    }
  });

  it('category filter change triggers reload', async () => {
    renderTransactions();
    await waitFor(() => {
      expect(api.getTransactions).toHaveBeenCalledTimes(1);
    });
    const allSelects = screen.getAllByRole('combobox');
    const catSelect = allSelects.find(s => {
      const opts = Array.from(s.options).map(o => o.textContent);
      return opts.includes('餐饮');
    });
    if (catSelect) {
      fireEvent.change(catSelect, { target: { value: '餐饮' } });
      await waitFor(() => {
        expect(api.getTransactions).toHaveBeenCalledWith(
          expect.objectContaining({ category: '餐饮' }),
        );
      });
    }
  });

  it('account filter change triggers reload', async () => {
    renderTransactions();
    await waitFor(() => {
      expect(api.getTransactions).toHaveBeenCalledTimes(1);
    });
    const allSelects = screen.getAllByRole('combobox');
    const accSelect = allSelects.find(s => {
      const opts = Array.from(s.options).map(o => o.textContent);
      return opts.includes('微信');
    });
    if (accSelect) {
      fireEvent.change(accSelect, { target: { value: '微信' } });
      await waitFor(() => {
        expect(api.getTransactions).toHaveBeenCalledWith(
          expect.objectContaining({ account: '微信' }),
        );
      });
    }
  });

  it('clear filters resets all', async () => {
    renderTransactions('/transactions?category=餐饮&keyword=午餐');
    await waitFor(() => {
      expect(api.getTransactions).toHaveBeenCalled();
    });
    fireEvent.click(screen.getByRole('button', { name: /清除/ }));
    await waitFor(() => {
      const lastCall = api.getTransactions.mock.calls[api.getTransactions.mock.calls.length - 1][0];
      expect(lastCall.category).toBeUndefined();
      expect(lastCall.keyword).toBeUndefined();
    });
  });

  it('reads filter params from URL', async () => {
    renderTransactions('/transactions?category=餐饮&keyword=午餐&type=支出');
    await waitFor(() => {
      expect(api.getTransactions).toHaveBeenCalledWith(
        expect.objectContaining({ category: '餐饮', keyword: '午餐', type: '支出' }),
      );
    });
  });

  // ── 标签筛选 ─────────────────────────────────────
  it('shows tag filter and click toggles', async () => {
    renderTransactions();
    await waitFor(() => {
      expect(screen.getAllByText('日常').length).toBeGreaterThanOrEqual(1);
    });
    const tagBadges = screen.getAllByText('日常');
    fireEvent.click(tagBadges[0]);
    await waitFor(() => {
      expect(api.getTransactions).toHaveBeenCalledWith(
        expect.objectContaining({ tag_ids: '1' }),
      );
    });
  });

  // ── 操作 ─────────────────────────────────────────
  it('shows edit/delete buttons', async () => {
    renderTransactions();
    await waitFor(() => {
      expect(screen.getAllByTitle('编辑').length).toBe(2);
      expect(screen.getAllByTitle('删除').length).toBe(2);
    });
  });

  it('has edit and delete buttons', async () => {
    renderTransactions();
    await waitFor(() => {
      expect(screen.getAllByTitle('编辑').length).toBe(2);
      expect(screen.getAllByTitle('删除').length).toBe(2);
    });
  });

  it('delete calls deleteTransaction after confirm', async () => {
    api.deleteTransaction.mockResolvedValue({ data: null });
    renderTransactions();
    await waitFor(() => { expect(screen.getAllByTitle('删除').length).toBe(2); });
    fireEvent.click(screen.getAllByTitle('删除')[0]);
    expect(window.confirm).toHaveBeenCalled();
    await waitFor(() => {
      expect(api.deleteTransaction).toHaveBeenCalledWith(1);
    });
  });

  it('cancel confirm prevents delete', async () => {
    window.confirm.mockReturnValue(false);
    renderTransactions();
    await waitFor(() => { expect(screen.getAllByTitle('删除').length).toBe(2); });
    fireEvent.click(screen.getAllByTitle('删除')[0]);
    expect(api.deleteTransaction).not.toHaveBeenCalled();
  });

  // ── 分页 ─────────────────────────────────────────
  it('shows pagination when total > pageSize', async () => {
    api.getTransactions.mockResolvedValue({
      data: { transactions: mockTransactions, total: 40 },
    });
    renderTransactions();
    await waitFor(() => {
      expect(screen.getByText(/共 40 条记录/)).toBeInTheDocument();
    });
  });

  it('page 2 reloads with offset', async () => {
    api.getTransactions.mockResolvedValue({
      data: { transactions: mockTransactions, total: 40 },
    });
    renderTransactions();
    await waitFor(() => { expect(screen.getByText(/共 40 条记录/)).toBeInTheDocument(); });
    const page2Btn = screen.getAllByRole('button', { name: '2' })[0];
    fireEvent.click(page2Btn);
    await waitFor(() => {
      expect(api.getTransactions).toHaveBeenCalledWith(
        expect.objectContaining({ offset: 20 }),
      );
    });
  });

  // ── 图表筛选 ─────────────────────────────────────
  it('applies category from URL', async () => {
    renderTransactions('/transactions?category=交通');
    await waitFor(() => {
      expect(api.getTransactions).toHaveBeenCalledWith(
        expect.objectContaining({ category: '交通' }),
      );
    });
  });

  // ── 错误处理 ─────────────────────────────────────
  it('handles API errors gracefully', async () => {
    api.getTransactions.mockRejectedValue(new Error('Network error'));
    api.getSuggestions.mockRejectedValue(new Error('Network error'));
    api.getTags.mockRejectedValue(new Error('Network error'));
    renderTransactions();
    await waitFor(() => {
      expect(screen.getByRole('heading', { name: /交易记录/ })).toBeInTheDocument();
    });
  });
});
