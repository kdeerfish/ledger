import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import { render, screen, waitFor, fireEvent } from '@testing-library/react';
import { MemoryRouter } from 'react-router-dom';

// Mock bootstrap as global
beforeEach(() => {
  window.bootstrap = {
    Toast: vi.fn(function() {
      this.show = vi.fn();
      this.hide = vi.fn();
    }),
  };
});
afterEach(() => {
  delete window.bootstrap;
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
    id: 1,
    date: '2024-01-15 10:00',
    type: '支出',
    amount: 35.5,
    category: '餐饮',
    subcategory: '午餐',
    account: '微信',
    merchant: '美团',
    project: '',
    member: '本人',
    note: '工作日午餐',
    tags: [{ id: 1, name: '日常', color: '#6366f1' }],
  },
  {
    id: 2,
    date: '2024-01-15 18:00',
    type: '收入',
    amount: 5000,
    category: '工资',
    subcategory: '',
    account: '银行',
    merchant: '',
    project: '',
    member: '本人',
    note: '',
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

  it('renders the page title', async () => {
    renderTransactions();
    expect(screen.getByRole('heading', { name: /交易记录/ })).toBeInTheDocument();
  });

  it('shows add button', async () => {
    renderTransactions();
    expect(screen.getByRole('button', { name: /记一笔/ })).toBeInTheDocument();
  });

  it('loads and displays transactions', async () => {
    renderTransactions();
    await waitFor(() => {
      // Category should appear in the table
      expect(screen.getAllByText('餐饮').length).toBeGreaterThanOrEqual(1);
      expect(screen.getAllByText('工资').length).toBeGreaterThanOrEqual(1);
    });
  });

  it('displays transaction amounts', async () => {
    renderTransactions();
    await waitFor(() => {
      expect(screen.getByText(/35/)).toBeInTheDocument();
      expect(screen.getByText(/5,000/)).toBeInTheDocument();
    });
  });

  it('shows transaction count', async () => {
    renderTransactions();
    await waitFor(() => {
      expect(screen.getByText(/共 2 条记录/)).toBeInTheDocument();
    });
  });

  it('shows empty state when no transactions', async () => {
    api.getTransactions.mockResolvedValue({
      data: { transactions: [], total: 0 },
    });
    renderTransactions();
    await waitFor(() => {
      expect(screen.getByText(/📭 暂无交易记录/)).toBeInTheDocument();
    });
  });

  it('shows filter controls', async () => {
    renderTransactions();
    expect(screen.getByPlaceholderText(/搜索备注/)).toBeInTheDocument();
  });

  it('shows clear filter button', async () => {
    renderTransactions();
    expect(screen.getByRole('button', { name: /清除/ })).toBeInTheDocument();
  });

  it('shows edit and delete buttons for each transaction', async () => {
    renderTransactions();
    await waitFor(() => {
      const editButtons = screen.getAllByTitle('编辑');
      const deleteButtons = screen.getAllByTitle('删除');
      expect(editButtons.length).toBe(2);
      expect(deleteButtons.length).toBe(2);
    });
  });

  it('shows tag badges for transactions with tags', async () => {
    renderTransactions();
    await waitFor(() => {
      // "日常" appears both in tag filter bar and in the transaction row tag badge
      expect(screen.getAllByText('日常').length).toBeGreaterThanOrEqual(1);
    });
  });

  it('shows filter dropdowns', async () => {
    renderTransactions();
    await waitFor(() => {
      expect(screen.getByRole('option', { name: '全部类型' })).toBeInTheDocument();
      expect(screen.getByRole('option', { name: '全部类别' })).toBeInTheDocument();
      expect(screen.getByRole('option', { name: '全部账户' })).toBeInTheDocument();
    });
  });

  it('handles API errors gracefully', async () => {
    api.getTransactions.mockRejectedValue(new Error('Network error'));
    api.getSuggestions.mockRejectedValue(new Error('Network error'));
    api.getTags.mockRejectedValue(new Error('Network error'));

    renderTransactions();
    await waitFor(() => {
      expect(screen.getByRole('heading', { name: /交易记录/ })).toBeInTheDocument();
    });
  });

  it('reads category from URL params', async () => {
    renderTransactions('/transactions?category=餐饮');
    await waitFor(() => {
      expect(api.getTransactions).toHaveBeenCalledWith(
        expect.objectContaining({ category: '餐饮' }),
      );
    });
  });
});
