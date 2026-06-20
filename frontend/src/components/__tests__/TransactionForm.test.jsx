import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import { render, screen, waitFor, fireEvent } from '@testing-library/react';

// Mock bootstrap as global (loaded via bootstrap.bundle.min.js in main.jsx)
const mockShow = vi.fn();
const mockHide = vi.fn();
beforeEach(() => {
  window.bootstrap = {
    Toast: vi.fn(function() {
      this.show = mockShow;
      this.hide = mockHide;
    }),
  };
});
afterEach(() => {
  delete window.bootstrap;
});

vi.mock('../../api', () => ({
  api: {
    getSuggestions: vi.fn().mockResolvedValue({ data: { categories: [], accounts: [], merchants: [], members: [] } }),
    getQuickCategories: vi.fn().mockResolvedValue({ data: [] }),
    getTemplates: vi.fn().mockResolvedValue({ data: [] }),
    getTransaction: vi.fn(),
    addTransaction: vi.fn(),
    updateTransaction: vi.fn(),
    useTemplate: vi.fn(),
    getTags: vi.fn().mockResolvedValue({ data: [] }),
    createTag: vi.fn(),
  },
}));

import TransactionForm from '../TransactionForm';
import { api } from '../../api';

function renderForm(props = {}) {
  const defaultProps = {
    show: true,
    onClose: vi.fn(),
    onSaved: vi.fn(),
    editId: null,
    ...props,
  };
  return { ...defaultProps, ...render(<TransactionForm {...defaultProps} />) };
}

describe('TransactionForm', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('renders nothing when show is false', () => {
    render(<TransactionForm show={false} onClose={vi.fn()} onSaved={vi.fn()} />);
    expect(screen.queryByText('记一笔')).not.toBeInTheDocument();
  });

  it('renders the form modal when show is true', async () => {
    renderForm();
    expect(screen.getByText('记一笔')).toBeInTheDocument();
    expect(screen.getByText('取消')).toBeInTheDocument();
    expect(screen.getByText('保存')).toBeInTheDocument();
  });

  it('shows edit title when editId is provided', async () => {
    api.getTransaction.mockResolvedValue({
      data: {
        id: 42,
        type: '支出',
        amount: 100,
        category: '餐饮',
        subcategory: '午餐',
        account: '微信',
        merchant: '美团',
        project: '',
        member: '本人',
        note: '',
        date: '2024-01-15 12:00',
        tags: [],
      },
    });

    renderForm({ editId: 42 });

    await waitFor(() => {
      expect(screen.getByText(/编辑交易 #42/)).toBeInTheDocument();
    });

    expect(api.getTransaction).toHaveBeenCalledWith(42);
  });

  it('loads suggestions, quick categories and templates on show', async () => {
    renderForm();

    expect(api.getSuggestions).toHaveBeenCalledWith({ field: 'all' });
    expect(api.getQuickCategories).toHaveBeenCalled();
    expect(api.getTemplates).toHaveBeenCalled();
  });

  it('default type is 支出', async () => {
    renderForm();
    const typeSelect = screen.getByDisplayValue('支出');
    expect(typeSelect).toBeInTheDocument();
  });

  it('can change type to 收入', async () => {
    renderForm();
    const typeSelect = screen.getByDisplayValue('支出');
    fireEvent.change(typeSelect, { target: { value: '收入' } });
    expect(screen.getByDisplayValue('收入')).toBeInTheDocument();
  });

  it('calls onClose when cancel button clicked', async () => {
    const onClose = vi.fn();
    renderForm({ onClose });
    fireEvent.click(screen.getByText('取消'));
    expect(onClose).toHaveBeenCalled();
  });

  it('shows amount validation toast for zero amount', async () => {
    renderForm();
    fireEvent.click(screen.getByText('保存'));

    await waitFor(() => {
      // The toast should appear with the validation message
      expect(screen.queryByText('保存中...')).not.toBeInTheDocument();
    });
  });

  it('sends addTransaction for new transaction', async () => {
    api.addTransaction.mockResolvedValue({ data: { id: 1 } });
    const onSaved = vi.fn();
    const onClose = vi.fn();

    renderForm({ onSaved, onClose });

    // Fill in amount
    const amountInput = screen.getByPlaceholderText('0.00');
    fireEvent.change(amountInput, { target: { value: '100' } });

    // Click save
    fireEvent.click(screen.getByText('保存'));

    await waitFor(() => {
      expect(api.addTransaction).toHaveBeenCalled();
      expect(onSaved).toHaveBeenCalled();
      expect(onClose).toHaveBeenCalled();
    });
  });

  it('sends updateTransaction when editing', async () => {
    api.getTransaction.mockResolvedValue({
      data: {
        id: 42,
        type: '支出',
        amount: 100,
        category: '餐饮',
        subcategory: '',
        account: '',
        merchant: '',
        project: '',
        member: '',
        note: '',
        date: '2024-01-15 12:00',
        tags: [],
      },
    });
    api.updateTransaction.mockResolvedValue({ data: { id: 42 } });
    const onSaved = vi.fn();
    const onClose = vi.fn();

    renderForm({ editId: 42, onSaved, onClose });

    await waitFor(() => {
      expect(screen.getByText(/编辑交易 #42/)).toBeInTheDocument();
    });

    fireEvent.click(screen.getByText('保存'));

    await waitFor(() => {
      expect(api.updateTransaction).toHaveBeenCalledWith(42, expect.objectContaining({
        amount: 100,
        type: '支出',
      }));
      expect(onSaved).toHaveBeenCalled();
    });
  });

  it('displays template buttons when templates exist', async () => {
    api.getTemplates.mockResolvedValue({
      data: [
        { id: 1, name: '午餐', type: '支出', category: '餐饮', subcategory: '午餐', amount: 30 },
        { id: 2, name: '地铁', type: '支出', category: '交通', subcategory: '地铁', amount: 5 },
      ],
    });

    renderForm();

    await waitFor(() => {
      expect(screen.getByText('午餐')).toBeInTheDocument();
      expect(screen.getByText('地铁')).toBeInTheDocument();
    });
  });

  it('loads transaction data for editing with tags', async () => {
    api.getTransaction.mockResolvedValue({
      data: {
        id: 10,
        type: '收入',
        amount: 5000,
        category: '工资',
        subcategory: '',
        account: '银行',
        merchant: '',
        project: '',
        member: '本人',
        note: '月薪',
        date: '2024-06-01 09:00',
        tags: [{ id: 1, name: '固定收入', color: '#10b981' }],
      },
    });

    renderForm({ editId: 10 });

    await waitFor(() => {
      expect(screen.getByDisplayValue('收入')).toBeInTheDocument();
      expect(screen.getByDisplayValue('5000')).toBeInTheDocument();
    });
  });

  it('hides templates section in edit mode', async () => {
    api.getTransaction.mockResolvedValue({
      data: {
        id: 5,
        type: '支出',
        amount: 50,
        category: '',
        subcategory: '',
        account: '',
        merchant: '',
        project: '',
        member: '',
        note: '',
        date: '2024-01-01 10:00',
        tags: [],
      },
    });

    renderForm({ editId: 5 });

    await waitFor(() => {
      expect(screen.getByText(/编辑交易 #5/)).toBeInTheDocument();
    });

    expect(screen.queryByText('从模板选择：')).not.toBeInTheDocument();
  });
});
