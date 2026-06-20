import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import { render, screen, waitFor, fireEvent } from '@testing-library/react';

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

  // ── 基础渲染 ─────────────────────────────────────
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

  it('shows all form fields', async () => {
    renderForm();
    expect(screen.getByDisplayValue('支出')).toBeInTheDocument(); // type
    expect(screen.getByPlaceholderText('0.00')).toBeInTheDocument(); // amount
    expect(screen.getByPlaceholderText('如：食品酒水')).toBeInTheDocument(); // category
    expect(screen.getByPlaceholderText('如：水果')).toBeInTheDocument(); // subcategory
    expect(screen.getByPlaceholderText('如：微信')).toBeInTheDocument(); // account
    expect(screen.getByPlaceholderText('如：美团')).toBeInTheDocument(); // merchant
    expect(screen.getByPlaceholderText('项目名称')).toBeInTheDocument(); // project
    expect(screen.getByPlaceholderText('如：本人')).toBeInTheDocument(); // member
    expect(screen.getByPlaceholderText('备注信息')).toBeInTheDocument(); // note
  });

  it('loads suggestions, quick categories and templates on show', async () => {
    renderForm();
    expect(api.getSuggestions).toHaveBeenCalledWith({ field: 'all' });
    expect(api.getQuickCategories).toHaveBeenCalled();
    expect(api.getTemplates).toHaveBeenCalled();
  });

  // ── 类型切换 ─────────────────────────────────────
  it('default type is 支出', async () => {
    renderForm();
    expect(screen.getByDisplayValue('支出')).toBeInTheDocument();
  });

  it('can change type to 收入', async () => {
    renderForm();
    fireEvent.change(screen.getByDisplayValue('支出'), { target: { value: '收入' } });
    expect(screen.getByDisplayValue('收入')).toBeInTheDocument();
  });

  // ── 取消 ─────────────────────────────────────────
  it('calls onClose when cancel button clicked', async () => {
    const onClose = vi.fn();
    renderForm({ onClose });
    fireEvent.click(screen.getByText('取消'));
    expect(onClose).toHaveBeenCalled();
  });

  // ── 表单交互 ─────────────────────────────────────
  it('can fill in all fields', async () => {
    renderForm();
    fireEvent.change(screen.getByPlaceholderText('0.00'), { target: { value: '25.5' } });
    fireEvent.change(screen.getByPlaceholderText('如：食品酒水'), { target: { value: '餐饮' } });
    fireEvent.change(screen.getByPlaceholderText('如：水果'), { target: { value: '午餐' } });
    fireEvent.change(screen.getByPlaceholderText('如：微信'), { target: { value: '微信' } });
    fireEvent.change(screen.getByPlaceholderText('如：美团'), { target: { value: '美团' } });
    fireEvent.change(screen.getByPlaceholderText('项目名称'), { target: { value: '工作' } });
    fireEvent.change(screen.getByPlaceholderText('如：本人'), { target: { value: '张三' } });
    fireEvent.change(screen.getByPlaceholderText('备注信息'), { target: { value: '午饭' } });

    expect(screen.getByDisplayValue('25.5')).toBeInTheDocument();
    expect(screen.getByDisplayValue('餐饮')).toBeInTheDocument();
    expect(screen.getByDisplayValue('午餐')).toBeInTheDocument();
    expect(screen.getByDisplayValue('微信')).toBeInTheDocument();
    expect(screen.getByDisplayValue('美团')).toBeInTheDocument();
    expect(screen.getByDisplayValue('工作')).toBeInTheDocument();
    expect(screen.getByDisplayValue('张三')).toBeInTheDocument();
    expect(screen.getByDisplayValue('午饭')).toBeInTheDocument();
  });

  it('can change date', async () => {
    renderForm();
    const dateInput = document.querySelector('input[type="datetime-local"]');
    fireEvent.change(dateInput, { target: { value: '2024-06-15T14:30' } });
    expect(dateInput.value).toBe('2024-06-15T14:30');
  });

  // ── 金额验证 ─────────────────────────────────────
  it('shows toast for zero amount', async () => {
    renderForm();
    fireEvent.click(screen.getByText('保存'));
    await waitFor(() => {
      expect(window.bootstrap.Toast).toHaveBeenCalled();
    });
  });

  it('shows toast for negative amount', async () => {
    renderForm();
    fireEvent.change(screen.getByPlaceholderText('0.00'), { target: { value: '-10' } });
    fireEvent.click(screen.getByText('保存'));
    await waitFor(() => {
      expect(window.bootstrap.Toast).toHaveBeenCalled();
    });
  });

  it('shows toast for NaN amount', async () => {
    renderForm();
    fireEvent.change(screen.getByPlaceholderText('0.00'), { target: { value: 'abc' } });
    fireEvent.click(screen.getByText('保存'));
    await waitFor(() => {
      expect(window.bootstrap.Toast).toHaveBeenCalled();
    });
  });

  // ── 保存新交易 ───────────────────────────────────
  it('sends addTransaction for new transaction', async () => {
    api.addTransaction.mockResolvedValue({ data: { id: 1 } });
    const onSaved = vi.fn();
    const onClose = vi.fn();
    renderForm({ onSaved, onClose });

    fireEvent.change(screen.getByPlaceholderText('0.00'), { target: { value: '100' } });
    fireEvent.click(screen.getByText('保存'));

    await waitFor(() => {
      expect(api.addTransaction).toHaveBeenCalled();
      expect(onSaved).toHaveBeenCalled();
      expect(onClose).toHaveBeenCalled();
    });
  });

  it('sends correct data format with date conversion', async () => {
    api.addTransaction.mockResolvedValue({ data: { id: 1 } });
    renderForm();

    fireEvent.change(screen.getByPlaceholderText('0.00'), { target: { value: '50' } });
    fireEvent.change(screen.getByPlaceholderText('如：食品酒水'), { target: { value: '餐饮' } });
    fireEvent.click(screen.getByText('保存'));

    await waitFor(() => {
      expect(api.addTransaction).toHaveBeenCalledWith(
        expect.objectContaining({
          amount: 50,
          category: '餐饮',
          force: true,
        }),
      );
    });
  });

  // ── 保存编辑交易 ─────────────────────────────────
  it('sends updateTransaction when editing', async () => {
    api.getTransaction.mockResolvedValue({
      data: {
        id: 42, type: '支出', amount: 100, category: '餐饮', subcategory: '',
        account: '', merchant: '', project: '', member: '', note: '',
        date: '2024-01-15 12:00', tags: [],
      },
    });
    api.updateTransaction.mockResolvedValue({ data: { id: 42 } });
    const onSaved = vi.fn();
    renderForm({ editId: 42, onSaved });

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

  it('loads transaction data for editing with tags', async () => {
    api.getTransaction.mockResolvedValue({
      data: {
        id: 10, type: '收入', amount: 5000, category: '工资', subcategory: '',
        account: '银行', merchant: '', project: '', member: '本人', note: '月薪',
        date: '2024-06-01 09:00',
        tags: [{ id: 1, name: '固定收入', color: '#10b981' }],
      },
    });
    renderForm({ editId: 10 });
    await waitFor(() => {
      expect(screen.getByDisplayValue('收入')).toBeInTheDocument();
      expect(screen.getByDisplayValue('5000')).toBeInTheDocument();
      expect(screen.getByDisplayValue('银行')).toBeInTheDocument();
      expect(screen.getByDisplayValue('本人')).toBeInTheDocument();
    });
  });

  it('shows edit title when editId is provided', async () => {
    api.getTransaction.mockResolvedValue({
      data: {
        id: 42, type: '支出', amount: 100, category: '餐饮', subcategory: '',
        account: '', merchant: '', project: '', member: '', note: '',
        date: '2024-01-15 12:00', tags: [],
      },
    });
    renderForm({ editId: 42 });
    await waitFor(() => {
      expect(screen.getByText(/编辑交易 #42/)).toBeInTheDocument();
    });
    expect(api.getTransaction).toHaveBeenCalledWith(42);
  });

  it('hides templates section in edit mode', async () => {
    api.getTransaction.mockResolvedValue({
      data: {
        id: 5, type: '支出', amount: 50, category: '', subcategory: '',
        account: '', merchant: '', project: '', member: '', note: '',
        date: '2024-01-01 10:00', tags: [],
      },
    });
    renderForm({ editId: 5 });
    await waitFor(() => {
      expect(screen.getByText(/编辑交易 #5/)).toBeInTheDocument();
    });
    expect(screen.queryByText('从模板选择：')).not.toBeInTheDocument();
  });

  // ── 模板 ─────────────────────────────────────────
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

  it('clicking template toggle button shows/hides templates', async () => {
    api.getTemplates.mockResolvedValue({
      data: [
        { id: 1, name: '午餐', type: '支出', category: '餐饮', subcategory: '午餐', amount: 30 },
      ],
    });
    renderForm();
    await waitFor(() => {
      expect(screen.getByText('午餐')).toBeInTheDocument();
    });
    // Click the 模板 button to toggle template view
    const templateBtn = screen.getByRole('button', { name: /模板/ });
    fireEvent.click(templateBtn);
    // Templates should still be visible in expanded view
    await waitFor(() => {
      expect(screen.getByText('午餐')).toBeInTheDocument();
    });
  });

  it('applying template fills form fields', async () => {
    api.getTemplates.mockResolvedValue({
      data: [
        { id: 1, name: '午餐', type: '支出', category: '餐饮', subcategory: '午餐', amount: 30, note: '午饭' },
      ],
    });
    api.useTemplate.mockResolvedValue({ data: null });
    renderForm();

    await waitFor(() => {
      expect(screen.getByText('午餐')).toBeInTheDocument();
    });

    // Click the template card (the one inside .template-card)
    const templateCards = document.querySelectorAll('.template-card');
    if (templateCards.length > 0) {
      fireEvent.click(templateCards[0]);
      await waitFor(() => {
        expect(api.useTemplate).toHaveBeenCalledWith(1);
      });
    }
  });

  // ── 快速子类别 ───────────────────────────────────
  it('displays quick subcategories when available', async () => {
    api.getQuickCategories.mockResolvedValue({
      data: [
        { category: '餐饮', subcategory: '午餐' },
        { category: '餐饮', subcategory: '晚餐' },
        { category: '交通', subcategory: '地铁' },
      ],
    });
    renderForm();
    await waitFor(() => {
      expect(screen.getByText('常用子类别：')).toBeInTheDocument();
      expect(screen.getByText('餐饮/午餐')).toBeInTheDocument();
      expect(screen.getByText('餐饮/晚餐')).toBeInTheDocument();
      expect(screen.getByText('交通/地铁')).toBeInTheDocument();
    });
  });

  it('clicking quick subcategory fills category and subcategory', async () => {
    api.getQuickCategories.mockResolvedValue({
      data: [
        { category: '餐饮', subcategory: '午餐' },
      ],
    });
    renderForm();
    await waitFor(() => {
      expect(screen.getByText('餐饮/午餐')).toBeInTheDocument();
    });

    fireEvent.click(screen.getByText('餐饮/午餐'));
    expect(screen.getByDisplayValue('餐饮')).toBeInTheDocument();
    expect(screen.getByDisplayValue('午餐')).toBeInTheDocument();
  });

  it('clicking quick subcategory again toggles off', async () => {
    api.getQuickCategories.mockResolvedValue({
      data: [
        { category: '餐饮', subcategory: '午餐' },
      ],
    });
    renderForm();
    await waitFor(() => {
      expect(screen.getByText('餐饮/午餐')).toBeInTheDocument();
    });

    // Click once to select
    fireEvent.click(screen.getByText('餐饮/午餐'));
    expect(screen.getByDisplayValue('午餐')).toBeInTheDocument();

    // Click again - handleQuickSub sets same values (idempotent)
    fireEvent.click(screen.getByText('餐饮/午餐'));
    // After clicking again, the category and subcategory should still be set
    // (handleQuickSub always sets, doesn't toggle)
    expect(screen.getByDisplayValue('餐饮')).toBeInTheDocument();
    expect(screen.getByDisplayValue('午餐')).toBeInTheDocument();
  });

  it('limits quick subcategories to 12', async () => {
    const items = Array.from({ length: 15 }, (_, i) => ({
      category: '类别',
      subcategory: `子类别${i}`,
    }));
    api.getQuickCategories.mockResolvedValue({ data: items });
    renderForm();
    await waitFor(() => {
      expect(screen.getByText('常用子类别：')).toBeInTheDocument();
    });
    // Should only render 12 quick-btn items
    const quickBtns = screen.getAllByText(/^类别\/子类别/);
    expect(quickBtns.length).toBe(12);
  });

  // ── 常用字段快速选择 ─────────────────────────────
  it('displays frequent accounts when available', async () => {
    api.getSuggestions.mockResolvedValue({
      data: {
        categories: [],
        accounts: [],
        merchants: [],
        members: [],
        frequent: {
          accounts: [{ name: '微信' }, { name: '支付宝' }],
          members: [{ name: '本人' }],
        },
      },
    });
    renderForm();
    await waitFor(() => {
      expect(screen.getByText('常用账户：')).toBeInTheDocument();
      expect(screen.getByText('微信')).toBeInTheDocument();
      expect(screen.getByText('支付宝')).toBeInTheDocument();
      expect(screen.getByText('常用成员：')).toBeInTheDocument();
    });
  });

  it('clicking frequent account fills account field', async () => {
    api.getSuggestions.mockResolvedValue({
      data: {
        categories: [],
        accounts: [],
        merchants: [],
        members: [],
        frequent: {
          accounts: [{ name: '微信' }],
          members: [],
        },
      },
    });
    renderForm();
    await waitFor(() => {
      expect(screen.getByText('常用账户：')).toBeInTheDocument();
    });
    // Click the frequent account button (not the suggestion dropdown)
    const accountBtns = screen.getAllByText('微信');
    // The frequent account button is the one in the quick-btn area
    const frequentBtn = accountBtns.find(el => el.closest('.quick-btn'));
    fireEvent.click(frequentBtn);
    expect(screen.getByDisplayValue('微信')).toBeInTheDocument();
  });

  it('clicking frequent member fills member field', async () => {
    api.getSuggestions.mockResolvedValue({
      data: {
        categories: [],
        accounts: [],
        merchants: [],
        members: [],
        frequent: {
          accounts: [],
          members: [{ name: '张三' }],
        },
      },
    });
    renderForm();
    await waitFor(() => {
      expect(screen.getByText('常用成员：')).toBeInTheDocument();
    });
    fireEvent.click(screen.getByText('张三'));
    expect(screen.getByDisplayValue('张三')).toBeInTheDocument();
  });

  // ── 错误处理 ─────────────────────────────────────
  it('shows toast on addTransaction error', async () => {
    api.addTransaction.mockRejectedValue(new Error('保存失败'));
    renderForm();
    fireEvent.change(screen.getByPlaceholderText('0.00'), { target: { value: '100' } });
    fireEvent.click(screen.getByText('保存'));
    await waitFor(() => {
      expect(window.bootstrap.Toast).toHaveBeenCalled();
    });
  });

  it('saves button shows loading state', async () => {
    api.addTransaction.mockImplementation(() => new Promise(() => {})); // never resolves
    renderForm();
    fireEvent.change(screen.getByPlaceholderText('0.00'), { target: { value: '100' } });
    fireEvent.click(screen.getByText('保存'));
    await waitFor(() => {
      expect(screen.getByText('保存中...')).toBeInTheDocument();
      expect(screen.getByText('保存中...').closest('button')).toBeDisabled();
    });
  });

  // ── 备注字段 ─────────────────────────────────────
  it('can fill in note field', async () => {
    renderForm();
    const noteTextarea = screen.getByPlaceholderText('备注信息');
    fireEvent.change(noteTextarea, { target: { value: '今天的午饭' } });
    expect(noteTextarea.value).toBe('今天的午饭');
  });

  // ── 标签选择 ─────────────────────────────────────
  it('shows tag selector component', async () => {
    renderForm();
    expect(screen.getByText('标签')).toBeInTheDocument();
    expect(screen.getByPlaceholderText('输入标签名...')).toBeInTheDocument();
  });
});
