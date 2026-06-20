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
    getCategories: vi.fn(),
    getTags: vi.fn(),
    createTag: vi.fn(),
    deleteTag: vi.fn(),
  },
}));

import Categories from '../Categories';
import { api } from '../../api';

function renderCategories() {
  return render(
    <MemoryRouter>
      <Categories />
    </MemoryRouter>,
  );
}

const mockCategories = [
  {
    name: '餐饮',
    total_count: 50,
    total_amount: 3000,
    subcategories: [
      { name: '午餐', count: 20, amount: 1200 },
      { name: '晚餐', count: 15, amount: 1500 },
      { name: '零食', count: 15, amount: 300 },
    ],
  },
  {
    name: '交通',
    total_count: 30,
    total_amount: 600,
    subcategories: [
      { name: '地铁', count: 20, amount: 400 },
      { name: '公交', count: 10, amount: 200 },
    ],
  },
];

const mockTags = [
  { id: 1, name: '日常', color: '#6366f1', usage_count: 10 },
  { id: 2, name: '固定', color: '#10b981', usage_count: 5 },
];

describe('Categories page', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    window.confirm = vi.fn(() => true);
    api.getCategories.mockResolvedValue({ data: mockCategories });
    api.getTags.mockResolvedValue({ data: mockTags });
  });

  it('renders the page title', async () => {
    renderCategories();
    expect(screen.getByText(/类别与标签管理/)).toBeInTheDocument();
  });

  it('shows tab buttons', async () => {
    renderCategories();
    expect(screen.getByRole('button', { name: /类别统计/ })).toBeInTheDocument();
    expect(screen.getByRole('button', { name: /标签管理/ })).toBeInTheDocument();
  });

  it('loads categories by default', async () => {
    renderCategories();
    await waitFor(() => {
      expect(screen.getByText('餐饮')).toBeInTheDocument();
      expect(screen.getByText('交通')).toBeInTheDocument();
    });
  });

  it('shows category amounts', async () => {
    renderCategories();
    await waitFor(() => {
      expect(screen.getByText(/3,000/)).toBeInTheDocument();
      expect(screen.getByText(/600/)).toBeInTheDocument();
    });
  });

  it('shows category counts', async () => {
    renderCategories();
    await waitFor(() => {
      expect(screen.getByText('50笔')).toBeInTheDocument();
      expect(screen.getByText('30笔')).toBeInTheDocument();
    });
  });

  it('shows subcategories', async () => {
    renderCategories();
    await waitFor(() => {
      expect(screen.getByText('午餐')).toBeInTheDocument();
      expect(screen.getByText('晚餐')).toBeInTheDocument();
      expect(screen.getByText('地铁')).toBeInTheDocument();
    });
  });

  it('shows empty state for categories', async () => {
    api.getCategories.mockResolvedValue({ data: [] });
    renderCategories();
    await waitFor(() => {
      expect(screen.getByText(/暂无类别数据/)).toBeInTheDocument();
    });
  });

  it('switches to tags tab', async () => {
    renderCategories();
    fireEvent.click(screen.getByRole('button', { name: /标签管理/ }));
    await waitFor(() => {
      expect(screen.getByText(/创建新标签/)).toBeInTheDocument();
      expect(screen.getByText('日常')).toBeInTheDocument();
      expect(screen.getByText('固定')).toBeInTheDocument();
    });
  });

  it('shows tag usage count', async () => {
    renderCategories();
    fireEvent.click(screen.getByRole('button', { name: /标签管理/ }));
    await waitFor(() => {
      expect(screen.getByText(/10 笔交易/)).toBeInTheDocument();
      expect(screen.getByText(/5 笔交易/)).toBeInTheDocument();
    });
  });

  it('shows tag creation form', async () => {
    renderCategories();
    fireEvent.click(screen.getByRole('button', { name: /标签管理/ }));
    await waitFor(() => {
      expect(screen.getByPlaceholderText('输入标签名')).toBeInTheDocument();
      expect(screen.getByText(/创建标签/)).toBeInTheDocument();
    });
  });

  it('shows empty state for tags', async () => {
    api.getTags.mockResolvedValue({ data: [] });
    renderCategories();
    fireEvent.click(screen.getByRole('button', { name: /标签管理/ }));
    await waitFor(() => {
      expect(screen.getByText(/暂无标签/)).toBeInTheDocument();
    });
  });

  it('creates a new tag', async () => {
    api.createTag.mockResolvedValue({ data: { id: 3 } });
    api.getTags.mockResolvedValueOnce({ data: mockTags });
    api.getTags.mockResolvedValueOnce({
      data: [...mockTags, { id: 3, name: '旅行', color: '#6366f1' }],
    });

    renderCategories();
    fireEvent.click(screen.getByRole('button', { name: /标签管理/ }));

    await waitFor(() => {
      expect(screen.getByPlaceholderText('输入标签名')).toBeInTheDocument();
    });

    const nameInput = screen.getByPlaceholderText('输入标签名');
    fireEvent.change(nameInput, { target: { value: '旅行' } });
    fireEvent.click(screen.getByRole('button', { name: /创建标签/ }));

    await waitFor(() => {
      expect(api.createTag).toHaveBeenCalledWith({ name: '旅行', color: '#6366f1' });
    });
  });

  it('has color picker for tag creation', async () => {
    renderCategories();
    fireEvent.click(screen.getByRole('button', { name: /标签管理/ }));
    await waitFor(() => {
      // Color picker should render multiple color options
      const colorSpans = document.querySelectorAll('[style*="border-radius: 50%"]');
      expect(colorSpans.length).toBeGreaterThanOrEqual(10);
    });
  });

  it('handles API errors gracefully', async () => {
    api.getCategories.mockRejectedValue(new Error('Network error'));
    api.getTags.mockRejectedValue(new Error('Network error'));
    renderCategories();
    await waitFor(() => {
      expect(screen.getByText(/类别与标签管理/)).toBeInTheDocument();
    });
  });
});
