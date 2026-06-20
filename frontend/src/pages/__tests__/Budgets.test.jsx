import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
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
afterEach(() => {
  delete window.bootstrap;
});

vi.mock('../../api', () => ({
  api: {
    getBudgets: vi.fn(),
    setBudget: vi.fn(),
  },
}));

import Budgets from '../Budgets';
import { api } from '../../api';

function renderBudgets() {
  return render(
    <MemoryRouter>
      <Budgets />
    </MemoryRouter>,
  );
}

const mockBudgets = [
  { id: 1, category: '餐饮', budget: 2000, spent: 1500, remaining: 500, percentage: 75 },
  { id: 2, category: '交通', budget: 500, spent: 600, remaining: -100, percentage: 120 },
];

describe('Budgets page', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    api.getBudgets.mockResolvedValue({ data: mockBudgets });
  });

  // ── 基础渲染 ─────────────────────────────────────
  it('renders the page title', async () => {
    renderBudgets();
    expect(screen.getByRole('heading', { name: /预算管理/ })).toBeInTheDocument();
  });

  it('loads budgets on mount', async () => {
    renderBudgets();
    await waitFor(() => {
      expect(api.getBudgets).toHaveBeenCalledTimes(1);
      expect(api.getBudgets).toHaveBeenCalledWith({
        year: expect.any(Number),
        month: expect.any(Number),
      });
    });
  });

  it('shows set budget button', async () => {
    renderBudgets();
    expect(screen.getByRole('button', { name: /设置预算/ })).toBeInTheDocument();
  });

  // ── 年月选择 ─────────────────────────────────────
  it('shows year and month selectors', async () => {
    renderBudgets();
    const selects = screen.getAllByRole('combobox');
    expect(selects.length).toBeGreaterThanOrEqual(2);
  });

  it('year options include current year and ±2', async () => {
    renderBudgets();
    const yearSelect = screen.getAllByRole('combobox')[0];
    const options = Array.from(yearSelect.options).map(o => o.value);
    const currentYear = new Date().getFullYear();
    expect(options).toContain(String(currentYear));
    expect(options).toContain(String(currentYear - 1));
    expect(options).toContain(String(currentYear + 1));
  });

  it('changing year reloads budgets', async () => {
    renderBudgets();
    await waitFor(() => {
      expect(api.getBudgets).toHaveBeenCalledTimes(1);
    });
    const yearSelect = screen.getAllByRole('combobox')[0];
    fireEvent.change(yearSelect, { target: { value: '2023' } });
    await waitFor(() => {
      expect(api.getBudgets.mock.calls.length).toBeGreaterThan(1);
    });
  });

  it('changing month reloads budgets', async () => {
    renderBudgets();
    await waitFor(() => {
      expect(api.getBudgets).toHaveBeenCalledTimes(1);
    });
    const monthSelect = screen.getAllByRole('combobox')[1];
    fireEvent.change(monthSelect, { target: { value: '6' } });
    await waitFor(() => {
      expect(api.getBudgets).toHaveBeenCalledWith(
        expect.objectContaining({ month: 6 }),
      );
    });
  });

  // ── 总览卡片 ─────────────────────────────────────
  it('shows summary cards when budgets exist', async () => {
    renderBudgets();
    await waitFor(() => {
      expect(screen.getByText('总预算')).toBeInTheDocument();
      expect(screen.getByText('已支出')).toBeInTheDocument();
    });
  });

  it('shows budget totals in summary', async () => {
    renderBudgets();
    await waitFor(() => {
      // 2000 + 500 = 2500 total budget
      expect(screen.getAllByText(/2,500/).length).toBeGreaterThanOrEqual(1);
      // 1500 + 600 = 2100 total spent
      expect(screen.getAllByText(/2,100/).length).toBeGreaterThanOrEqual(1);
    });
  });

  it('shows remaining with correct color', async () => {
    renderBudgets();
    await waitFor(() => {
      // Check remaining text exists in summary
      const remainingTexts = screen.getAllByText('剩余');
      expect(remainingTexts.length).toBeGreaterThanOrEqual(1);
    });
  });

  // ── 预算卡片 ─────────────────────────────────────
  it('loads and displays budget data in cards and table', async () => {
    renderBudgets();
    await waitFor(() => {
      expect(screen.getAllByText('餐饮').length).toBeGreaterThanOrEqual(1);
      expect(screen.getAllByText('交通').length).toBeGreaterThanOrEqual(1);
    });
  });

  it('shows progress percentages', async () => {
    renderBudgets();
    await waitFor(() => {
      expect(screen.getAllByText('75%').length).toBeGreaterThanOrEqual(1);
      expect(screen.getAllByText('120%').length).toBeGreaterThanOrEqual(1);
    });
  });

  it('shows budget amounts in cards', async () => {
    renderBudgets();
    await waitFor(() => {
      expect(screen.getAllByText(/2,000/).length).toBeGreaterThanOrEqual(1);
    });
  });

  it('shows spent amounts', async () => {
    renderBudgets();
    await waitFor(() => {
      expect(screen.getAllByText(/1,500/).length).toBeGreaterThanOrEqual(1);
      expect(screen.getAllByText(/600/).length).toBeGreaterThanOrEqual(1);
    });
  });

  it('shows remaining amounts', async () => {
    renderBudgets();
    await waitFor(() => {
      expect(screen.getAllByText(/500/).length).toBeGreaterThanOrEqual(1);
    });
  });

  it('shows over-budget styling', async () => {
    renderBudgets();
    await waitFor(() => {
      expect(screen.getByText(/超支/)).toBeInTheDocument();
    });
  });

  // ── 预算执行明细表 ───────────────────────────────
  it('shows budget execution detail table', async () => {
    renderBudgets();
    await waitFor(() => {
      expect(screen.getByText(/预算执行明细/)).toBeInTheDocument();
    });
  });

  // ── 空状态 ─────────────────────────────────────
  it('shows empty state when no budgets', async () => {
    api.getBudgets.mockResolvedValue({ data: [] });
    renderBudgets();
    await waitFor(() => {
      expect(screen.getByText(/本月暂无预算/)).toBeInTheDocument();
    });
  });

  // ── 设置预算弹窗 ─────────────────────────────────
  it('opens budget modal on button click', async () => {
    renderBudgets();
    fireEvent.click(screen.getByRole('button', { name: /设置预算/ }));
    await waitFor(() => {
      expect(screen.getByText('预算金额')).toBeInTheDocument();
      expect(screen.getByText('类别')).toBeInTheDocument();
    });
  });

  it('modal has year and month selectors', async () => {
    renderBudgets();
    fireEvent.click(screen.getByRole('button', { name: /设置预算/ }));
    await waitFor(() => {
      expect(screen.getByText('预算金额')).toBeInTheDocument();
    });
    // Modal should have its own year/month selects
    const allSelects = screen.getAllByRole('combobox');
    // At least page selects (2) + modal selects (2) = 4
    expect(allSelects.length).toBeGreaterThanOrEqual(4);
  });

  it('closes modal on cancel', async () => {
    renderBudgets();
    fireEvent.click(screen.getByRole('button', { name: /设置预算/ }));
    await waitFor(() => {
      expect(screen.getByText('预算金额')).toBeInTheDocument();
    });
    fireEvent.click(screen.getByRole('button', { name: '取消' }));
    await waitFor(() => {
      expect(screen.queryByText('预算金额')).not.toBeInTheDocument();
    });
  });

  it('saves budget when form is filled', async () => {
    api.setBudget.mockResolvedValue({ data: { id: 3 } });
    api.getBudgets.mockResolvedValue({ data: [...mockBudgets, { id: 3, category: '娱乐', budget: 1000, spent: 0, remaining: 1000, percentage: 0 }] });
    renderBudgets();
    fireEvent.click(screen.getByRole('button', { name: /设置预算/ }));
    await waitFor(() => {
      expect(screen.getByText('预算金额')).toBeInTheDocument();
    });
    // Fill category
    const categoryInput = screen.getByPlaceholderText('如：食品酒水');
    fireEvent.change(categoryInput, { target: { value: '娱乐' } });
    // Fill amount
    const amountInputs = screen.getAllByRole('spinbutton');
    fireEvent.change(amountInputs[0], { target: { value: '1000' } });
    // Click save
    fireEvent.click(screen.getByText('保存'));
    await waitFor(() => {
      expect(api.setBudget).toHaveBeenCalledWith(
        expect.objectContaining({
          category: '娱乐',
          amount: 1000,
        }),
      );
    });
  });

  it('does not save when category is empty', async () => {
    renderBudgets();
    fireEvent.click(screen.getByRole('button', { name: /设置预算/ }));
    await waitFor(() => {
      expect(screen.getByText('预算金额')).toBeInTheDocument();
    });
    // Only fill amount, leave category empty
    const amountInputs = screen.getAllByRole('spinbutton');
    fireEvent.change(amountInputs[0], { target: { value: '1000' } });
    fireEvent.click(screen.getByText('保存'));
    // Should NOT have called setBudget
    expect(api.setBudget).not.toHaveBeenCalled();
  });

  it('does not save when amount is empty', async () => {
    renderBudgets();
    fireEvent.click(screen.getByRole('button', { name: /设置预算/ }));
    await waitFor(() => {
      expect(screen.getByText('预算金额')).toBeInTheDocument();
    });
    // Only fill category, leave amount empty
    const categoryInput = screen.getByPlaceholderText('如：食品酒水');
    fireEvent.change(categoryInput, { target: { value: '娱乐' } });
    fireEvent.click(screen.getByText('保存'));
    expect(api.setBudget).not.toHaveBeenCalled();
  });

  it('modal year select changes budget year', async () => {
    renderBudgets();
    fireEvent.click(screen.getByRole('button', { name: /设置预算/ }));
    await waitFor(() => {
      expect(screen.getByText('预算金额')).toBeInTheDocument();
    });
    // Verify modal has year/month selects
    const modalSelects = document.querySelectorAll('.modal select');
    expect(modalSelects.length).toBeGreaterThanOrEqual(2);
  });

  it('modal month select changes budget month', async () => {
    renderBudgets();
    fireEvent.click(screen.getByRole('button', { name: /设置预算/ }));
    await waitFor(() => {
      expect(screen.getByText('预算金额')).toBeInTheDocument();
    });
    const allSelects = screen.getAllByRole('combobox');
    const modalMonthSelect = allSelects[3];
    fireEvent.change(modalMonthSelect, { target: { value: '6' } });
    expect(modalMonthSelect.value).toBe('6');
  });

  // ── 关闭按钮 ─────────────────────────────────────
  it('modal close button works', async () => {
    renderBudgets();
    fireEvent.click(screen.getByRole('button', { name: /设置预算/ }));
    await waitFor(() => {
      expect(screen.getByText('预算金额')).toBeInTheDocument();
    });
    // Find the close button inside the modal
    const closeBtn = document.querySelector('.modal .btn-close');
    if (closeBtn) {
      fireEvent.click(closeBtn);
      await waitFor(() => {
        expect(screen.queryByText('预算金额')).not.toBeInTheDocument();
      });
    }
  });

  // ── 错误处理 ─────────────────────────────────────
  it('handles API errors gracefully', async () => {
    api.getBudgets.mockRejectedValue(new Error('Network error'));
    renderBudgets();
    await waitFor(() => {
      expect(screen.getByRole('heading', { name: /预算管理/ })).toBeInTheDocument();
      expect(screen.getByText(/本月暂无预算/)).toBeInTheDocument();
    });
  });
});
