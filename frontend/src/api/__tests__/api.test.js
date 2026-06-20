import { describe, it, expect, vi, beforeEach } from 'vitest';
import { api } from '../index';

// Mock fetch globally
const mockFetch = vi.fn();
global.fetch = mockFetch;

function mockResponse(data, success = true) {
  return {
    ok: true,
    json: () => Promise.resolve({ success, data, error: success ? undefined : 'error' }),
  };
}

function mockErrorResponse(error = '请求失败') {
  return {
    ok: true,
    json: () => Promise.resolve({ success: false, error }),
  };
}

beforeEach(() => {
  mockFetch.mockReset();
});

describe('api client', () => {
  describe('request helper', () => {
    it('throws on non-success response', async () => {
      mockFetch.mockResolvedValue(mockErrorResponse('余额不足'));
      await expect(api.getTransactions()).rejects.toThrow('余额不足');
    });

    it('sends correct headers', async () => {
      mockFetch.mockResolvedValue(mockResponse([]));
      await api.getTransactions();
      expect(mockFetch).toHaveBeenCalledWith(
        '/api/transactions',
        expect.objectContaining({
          headers: expect.objectContaining({
            'Content-Type': 'application/json',
          }),
        }),
      );
    });
  });

  describe('transactions', () => {
    it('getTransactions without params', async () => {
      mockFetch.mockResolvedValue(mockResponse({ transactions: [], total: 0 }));
      const res = await api.getTransactions();
      expect(mockFetch).toHaveBeenCalledWith('/api/transactions', expect.anything());
      expect(res.data.transactions).toEqual([]);
    });

    it('getTransactions with params', async () => {
      mockFetch.mockResolvedValue(mockResponse({ transactions: [], total: 0 }));
      await api.getTransactions({ type: '支出', limit: 10 });
      expect(mockFetch).toHaveBeenCalledWith(
        '/api/transactions?type=%E6%94%AF%E5%87%BA&limit=10',
        expect.anything(),
      );
    });

    it('getTransaction by id', async () => {
      const tx = { id: 1, amount: 100 };
      mockFetch.mockResolvedValue(mockResponse(tx));
      const res = await api.getTransaction(1);
      expect(mockFetch).toHaveBeenCalledWith('/api/transactions/1', expect.anything());
      expect(res.data.id).toBe(1);
    });

    it('addTransaction sends POST with body', async () => {
      mockFetch.mockResolvedValue(mockResponse({ id: 1 }));
      await api.addTransaction({ amount: 50, type: '支出' });
      expect(mockFetch).toHaveBeenCalledWith(
        '/api/transactions',
        expect.objectContaining({
          method: 'POST',
          body: JSON.stringify({ amount: 50, type: '支出' }),
        }),
      );
    });

    it('updateTransaction sends PUT', async () => {
      mockFetch.mockResolvedValue(mockResponse({ id: 1 }));
      await api.updateTransaction(1, { amount: 200 });
      expect(mockFetch).toHaveBeenCalledWith(
        '/api/transactions/1',
        expect.objectContaining({
          method: 'PUT',
          body: JSON.stringify({ amount: 200 }),
        }),
      );
    });

    it('deleteTransaction sends DELETE', async () => {
      mockFetch.mockResolvedValue(mockResponse(null));
      await api.deleteTransaction(1);
      expect(mockFetch).toHaveBeenCalledWith(
        '/api/transactions/1',
        expect.objectContaining({ method: 'DELETE' }),
      );
    });
  });

  describe('tags', () => {
    it('getTags', async () => {
      mockFetch.mockResolvedValue(mockResponse([{ id: 1, name: '餐饮' }]));
      const res = await api.getTags();
      expect(res.data).toHaveLength(1);
    });

    it('createTag sends POST', async () => {
      mockFetch.mockResolvedValue(mockResponse({ id: 2 }));
      await api.createTag({ name: '交通' });
      expect(mockFetch).toHaveBeenCalledWith(
        '/api/tags',
        expect.objectContaining({ method: 'POST' }),
      );
    });

    it('deleteTag sends DELETE', async () => {
      mockFetch.mockResolvedValue(mockResponse(null));
      await api.deleteTag(2);
      expect(mockFetch).toHaveBeenCalledWith(
        '/api/tags/2',
        expect.objectContaining({ method: 'DELETE' }),
      );
    });
  });

  describe('templates', () => {
    it('getTemplates', async () => {
      mockFetch.mockResolvedValue(mockResponse([]));
      await api.getTemplates();
      expect(mockFetch).toHaveBeenCalledWith('/api/templates', expect.anything());
    });

    it('createTemplate sends POST', async () => {
      mockFetch.mockResolvedValue(mockResponse({ id: 1 }));
      await api.createTemplate({ name: '午餐' });
      expect(mockFetch).toHaveBeenCalledWith(
        '/api/templates',
        expect.objectContaining({ method: 'POST' }),
      );
    });

    it('useTemplate sends POST to /use', async () => {
      mockFetch.mockResolvedValue(mockResponse(null));
      await api.useTemplate(5);
      expect(mockFetch).toHaveBeenCalledWith(
        '/api/templates/5/use',
        expect.objectContaining({ method: 'POST' }),
      );
    });

    it('deleteTemplate sends DELETE', async () => {
      mockFetch.mockResolvedValue(mockResponse(null));
      await api.deleteTemplate(3);
      expect(mockFetch).toHaveBeenCalledWith(
        '/api/templates/3',
        expect.objectContaining({ method: 'DELETE' }),
      );
    });
  });

  describe('summary & stats', () => {
    it('getSummary with params', async () => {
      mockFetch.mockResolvedValue(mockResponse({ income: 1000 }));
      const res = await api.getSummary({ year: 2024 });
      expect(mockFetch).toHaveBeenCalledWith('/api/summary?year=2024', expect.anything());
      expect(res.data.income).toBe(1000);
    });

    it('getSummary without params', async () => {
      mockFetch.mockResolvedValue(mockResponse({}));
      await api.getSummary();
      expect(mockFetch).toHaveBeenCalledWith('/api/summary', expect.anything());
    });

    it('getStats', async () => {
      mockFetch.mockResolvedValue(mockResponse({ items: [] }));
      await api.getStats({ year: 2024, group_by: 'category' });
      expect(mockFetch).toHaveBeenCalledWith(
        '/api/stats?year=2024&group_by=category',
        expect.anything(),
      );
    });

    it('getTrends', async () => {
      mockFetch.mockResolvedValue(mockResponse({ items: [] }));
      await api.getTrends({ year: 2024 });
      expect(mockFetch).toHaveBeenCalledWith(
        '/api/trends?year=2024',
        expect.anything(),
      );
    });

    it('getSuggestions', async () => {
      mockFetch.mockResolvedValue(mockResponse({ categories: [] }));
      await api.getSuggestions({ field: 'all' });
      expect(mockFetch).toHaveBeenCalledWith(
        '/api/suggestions?field=all',
        expect.anything(),
      );
    });
  });

  describe('data endpoints', () => {
    it.each([
      ['getCategories', '/api/categories'],
      ['getQuickCategories', '/api/categories/quick'],
      ['getAccounts', '/api/accounts'],
      ['getMembers', '/api/members'],
      ['getProjects', '/api/projects'],
      ['getMerchants', '/api/merchants'],
    ])('%s calls %s', async (method, url) => {
      mockFetch.mockResolvedValue(mockResponse([]));
      await api[method]();
      expect(mockFetch).toHaveBeenCalledWith(url, expect.anything());
    });

    it('getBudgets with params', async () => {
      mockFetch.mockResolvedValue(mockResponse([]));
      await api.getBudgets({ year: 2024, month: 1 });
      expect(mockFetch).toHaveBeenCalledWith(
        '/api/budgets/check?year=2024&month=1',
        expect.anything(),
      );
    });

    it('setBudget sends POST', async () => {
      mockFetch.mockResolvedValue(mockResponse({ id: 1 }));
      await api.setBudget({ category: '餐饮', amount: 2000 });
      expect(mockFetch).toHaveBeenCalledWith(
        '/api/budgets',
        expect.objectContaining({ method: 'POST' }),
      );
    });

    it('getInfo', async () => {
      mockFetch.mockResolvedValue(mockResponse({ active_records: 100 }));
      const res = await api.getInfo();
      expect(res.data.active_records).toBe(100);
    });
  });
});
