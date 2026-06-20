import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import TagSelector from '../TagSelector';

const mockTags = [
  { id: 1, name: '餐饮', color: '#ef4444' },
  { id: 2, name: '交通', color: '#3b82f6' },
  { id: 3, name: '娱乐', color: '#10b981' },
];

vi.mock('../../api', () => ({
  api: {
    getTags: vi.fn(),
    createTag: vi.fn(),
  },
}));

import { api } from '../../api';

function renderTagSelector(props = {}) {
  const defaultProps = {
    value: [],
    onChange: vi.fn(),
    ...props,
  };
  return { ...defaultProps, ...render(<TagSelector {...defaultProps} />) };
}

describe('TagSelector', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    api.getTags.mockResolvedValue({ data: mockTags });
  });

  it('renders input placeholder', async () => {
    renderTagSelector();
    expect(screen.getByPlaceholderText('输入标签名...')).toBeInTheDocument();
  });

  it('loads tags on mount', async () => {
    renderTagSelector();
    expect(api.getTags).toHaveBeenCalled();
  });

  it('shows selected tags as badges', async () => {
    renderTagSelector({ value: [1, 2] });
    await waitFor(() => {
      expect(screen.getByText('餐饮')).toBeInTheDocument();
      expect(screen.getByText('交通')).toBeInTheDocument();
    });
  });

  it('removes tag when clicking x icon', async () => {
    const onChange = vi.fn();
    renderTagSelector({ value: [1, 2], onChange });

    await waitFor(() => {
      expect(screen.getByText('餐饮')).toBeInTheDocument();
    });

    // Click the x icon next to "餐饮" to remove it
    const removeButtons = screen.getAllByText('');
    // Find the bi-x icon for the first tag (餐饮)
    const tagBadges = document.querySelectorAll('.tag-badge');
    const firstBadge = tagBadges[0];
    const removeIcon = firstBadge.querySelector('.bi-x');
    fireEvent.click(removeIcon);

    expect(onChange).toHaveBeenCalledWith([2]);
  });

  it('shows dropdown with filtered tags on focus', async () => {
    renderTagSelector();

    await waitFor(() => {
      expect(api.getTags).toHaveBeenCalled();
    });

    const input = screen.getByPlaceholderText('输入标签名...');
    fireEvent.focus(input);

    await waitFor(() => {
      expect(screen.getByText('餐饮')).toBeInTheDocument();
      expect(screen.getByText('交通')).toBeInTheDocument();
      expect(screen.getByText('娱乐')).toBeInTheDocument();
    });
  });

  it('filters tags based on input', async () => {
    renderTagSelector();

    await waitFor(() => {
      expect(api.getTags).toHaveBeenCalled();
    });

    const input = screen.getByPlaceholderText('输入标签名...');
    await userEvent.type(input, '餐');

    await waitFor(() => {
      expect(screen.getByText('餐饮')).toBeInTheDocument();
      // 交通 and 娱乐 should not be in the dropdown
      const dropdownItems = document.querySelectorAll('.dropdown-item');
      const visibleNames = Array.from(dropdownItems).map(el => el.textContent);
      expect(visibleNames.some(n => n.includes('餐饮'))).toBe(true);
      expect(visibleNames.some(n => n.includes('交通'))).toBe(false);
    });
  });

  it('creates a new tag on Enter when no match', async () => {
    const onChange = vi.fn();
    const newTag = { id: 4, name: '购物', color: '#6366f1' };
    api.createTag.mockResolvedValue({ data: { id: 4, name: '购物' } });
    api.getTags
      .mockResolvedValueOnce({ data: mockTags })
      .mockResolvedValueOnce({ data: [...mockTags, newTag] });

    renderTagSelector({ onChange });

    await waitFor(() => {
      expect(api.getTags).toHaveBeenCalled();
    });

    const input = screen.getByRole('textbox');
    fireEvent.focus(input);
    await userEvent.type(input, '购物');
    fireEvent.keyDown(input, { key: 'Enter' });

    await waitFor(() => {
      expect(api.createTag).toHaveBeenCalledWith({ name: '购物' });
    });
  });

  it('selects first matching tag on Enter', async () => {
    const onChange = vi.fn();
    renderTagSelector({ onChange });

    await waitFor(() => {
      expect(api.getTags).toHaveBeenCalled();
    });

    const input = screen.getByPlaceholderText('输入标签名...');
    fireEvent.focus(input);
    await userEvent.type(input, '交');
    fireEvent.keyDown(input, { key: 'Enter' });

    await waitFor(() => {
      expect(onChange).toHaveBeenCalledWith([2]);
    });
  });

  it('removes last tag on Backspace with empty input', async () => {
    const onChange = vi.fn();
    renderTagSelector({ value: [1, 2], onChange });

    await waitFor(() => {
      expect(screen.getByText('餐饮')).toBeInTheDocument();
    });

    const input = screen.getByRole('textbox');
    fireEvent.keyDown(input, { key: 'Backspace' });

    expect(onChange).toHaveBeenCalledWith([1]);
  });

  it('hides input placeholder when tags are selected', async () => {
    renderTagSelector({ value: [1] });
    await waitFor(() => {
      expect(screen.getByText('餐饮')).toBeInTheDocument();
    });
    const input = screen.getByRole('textbox');
    expect(input.placeholder).toBe('');
  });

  it('shows create option in dropdown when input has text and no match', async () => {
    renderTagSelector();

    await waitFor(() => {
      expect(api.getTags).toHaveBeenCalled();
    });

    const input = screen.getByRole('textbox');
    fireEvent.focus(input);
    await userEvent.type(input, '新标签');

    await waitFor(() => {
      expect(screen.getByText(/创建.*新标签/)).toBeInTheDocument();
    });
  });
});
