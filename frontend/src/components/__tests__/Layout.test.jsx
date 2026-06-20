import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen } from '@testing-library/react';
import { MemoryRouter } from 'react-router-dom';
import Layout from '../Layout';

// Mock api
vi.mock('../../api', () => ({
  api: {
    getInfo: vi.fn().mockResolvedValue({ data: { active_records: 42 } }),
  },
}));

function renderLayout(route = '/') {
  return render(
    <MemoryRouter initialEntries={[route]}>
      <Layout />
    </MemoryRouter>,
  );
}

describe('Layout', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('renders the brand name', async () => {
    renderLayout();
    expect(screen.getByText('Ledger')).toBeInTheDocument();
  });

  it('renders all navigation items', async () => {
    renderLayout();
    expect(screen.getByText('概览')).toBeInTheDocument();
    expect(screen.getByText('交易')).toBeInTheDocument();
    expect(screen.getByText('预算')).toBeInTheDocument();
    expect(screen.getByText('类别')).toBeInTheDocument();
    expect(screen.getByText('统计')).toBeInTheDocument();
  });

  it('shows loading placeholder for record count', async () => {
    renderLayout();
    expect(screen.getByText('-')).toBeInTheDocument();
  });

  it('renders footer', async () => {
    renderLayout();
    expect(screen.getByText(/个人记账系统/)).toBeInTheDocument();
  });

  it('has correct nav links', async () => {
    renderLayout();
    const links = screen.getAllByRole('link');
    const hrefs = links.map(l => l.getAttribute('href'));
    expect(hrefs).toContain('/');
    expect(hrefs).toContain('/transactions');
    expect(hrefs).toContain('/budgets');
    expect(hrefs).toContain('/categories');
    expect(hrefs).toContain('/stats');
  });
});
