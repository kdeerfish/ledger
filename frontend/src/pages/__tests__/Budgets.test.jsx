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

  it('renders the page title', async () => {
    renderBudgets();
    expect(screen.getByRole('heading', { name: /预算管理/ })).toBeInTheDocument();
  });

  it('shows set budget button', async () => {
    renderBudgets();
    expect(screen.getByRole('button', { name: /设置预算/ })).toBeInTheDocument();
  });

  it('loads and displays budget data', async () => {
    renderBudgets();
    await waitFor(() => {
      // "餐饮" and "交通" appear in both card and table
      expect(screen.getAllByText('餐饮').length).toBeGreaterThanOrEqual(1);
      expect(screen.getAllByText('交通').length).toBeGreaterThanOrEqual(1);
    });
  });

  it('shows summary cards when budgets exist', async () => {
    renderBudgets();
    await waitFor(() => {
      expect(screen.getByText('总预算')).toBeInTheDocument();
      expect(screen.getByText('已支出')).toBeInTheDocument();
    });
  });

  it('shows budget amounts', async () => {
    renderBudgets();
    await waitFor(() => {
      // "2,000" appears in card and table
      expect(screen.getAllByText(/2,000/).length).toBeGreaterThanOrEqual(1);
    });
  });

  it('shows progress percentages', async () => {
    renderBudgets();
    await waitFor(() => {
      // "75%" and "120%" appear in cards and table
      expect(screen.getAllByText('75%').length).toBeGreaterThanOrEqual(1);
      expect(screen.getAllByText('120%').length).toBeGreaterThanOrEqual(1);
    });
  });

  it('shows empty state when no budgets', async () => {
    api.getBudgets.mockResolvedValue({ data: [] });
    renderBudgets();
    await waitFor(() => {
      expect(screen.getByText(/本月暂无预算/)).toBeInTheDocument();
    });
  });

  it('opens budget modal on button click', async () => {
    renderBudgets();
    const setBudgetBtn = screen.getByRole('button', { name: /设置预算/ });
    fireEvent.click(setBudgetBtn);
    await waitFor(() => {
      expect(screen.getByText('类别')).toBeInTheDocument();
    });
  });

  it('closes modal on cancel', async () => {
    renderBudgets();
    fireEvent.click(screen.getByRole('button', { name: /设置预算/ }));
    await waitFor(() => {
      expect(screen.getByText('预算金额')).toBeInTheDocument();
    });
    fireEvent.click(screen.getByRole('button', { name: '取消' }));
    // Modal should close - "预算金额" label should no longer be visible
    await waitFor(() => {
      expect(screen.queryByText('预算金额')).not.toBeInTheDocument();
    });
  });

  it('shows budget execution detail table', async () => {
    renderBudgets();
    await waitFor(() => {
      expect(screen.getByText(/预算执行明细/)).toBeInTheDocument();
    });
  });

  it('has year and month selectors', async () => {
    renderBudgets();
    const selects = screen.getAllByRole('combobox');
    expect(selects.length).toBeGreaterThanOrEqual(2);
  });

  it('handles API errors gracefully', async () => {
    api.getBudgets.mockRejectedValue(new Error('Network error'));
    renderBudgets();
    await waitFor(() => {
      expect(screen.getByRole('heading', { name: /预算管理/ })).toBeInTheDocument();
      expect(screen.getByText(/本月暂无预算/)).toBeInTheDocument();
    });
  });

  it('shows over-budget styling for exceeded budgets', async () => {
    renderBudgets();
    await waitFor(() => {
      expect(screen.getByText(/超支/)).toBeInTheDocument();
    });
  });
});
