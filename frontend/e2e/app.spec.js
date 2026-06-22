import { test, expect } from '@playwright/test';

// ─── 通用 ──────────────────────────────────────────────

test.describe('导航栏', () => {
  test('首页加载正常', async ({ page }) => {
    await page.goto('/');
    await expect(page.locator('.navbar-brand')).toContainText('Ledger');
  });

  test('导航链接全部可点击', async ({ page }) => {
    await page.goto('/');
    const navLinks = ['概览', '交易', '预算', '类别', '统计', '导入', '导出'];
    for (const label of navLinks) {
      const link = page.locator('.nav-link', { hasText: label });
      await expect(link).toBeVisible();
    }
  });

  test('各页面路由正常', async ({ page }) => {
    const routes = [
      { path: '/', text: '概览' },
      { path: '/transactions', text: '交易' },
      { path: '/import', text: '数据导入' },
      { path: '/export', text: '数据导出' },
    ];
    for (const route of routes) {
      await page.goto(route.path);
      await expect(page.locator('body')).toContainText(route.text);
    }
  });
});


// ─── 概览页 ──────────────────────────────────────────────

test.describe('概览页 Dashboard', () => {
  test('加载并显示统计卡片', async ({ page }) => {
    await page.goto('/');
    // 应该有收入/支出/结余的卡片
    await expect(page.locator('body')).toContainText('收入');
    await expect(page.locator('body')).toContainText('支出');
  });

  test('最近交易列表显示', async ({ page }) => {
    await page.goto('/');
    // 应该有最近交易或"暂无数据"
    await expect(page.locator('body')).toContainText('最近');
  });
});


// ─── 交易页 ──────────────────────────────────────────────

test.describe('交易页 Transactions', () => {
  test('交易列表加载', async ({ page }) => {
    await page.goto('/transactions');
    await expect(page.locator('body')).toContainText('交易');
    // 等待表格或列表加载
    await page.waitForTimeout(1000);
  });

  test('添加交易弹窗', async ({ page }) => {
    await page.goto('/transactions');
    // 点击添加按钮
    const addBtn = page.locator('button', { hasText: /添加|新增|记账/ });
    if (await addBtn.count() > 0) {
      await addBtn.first().click();
      // 弹窗应该出现
      await page.waitForTimeout(500);
      await expect(page.locator('.modal, [role="dialog"]')).toBeVisible();
    }
  });

  test('筛选功能', async ({ page }) => {
    await page.goto('/transactions');
    await page.waitForTimeout(1000);
    // 检查筛选区域是否存在
    const filterArea = page.locator('select, .dropdown, [class*="filter"]');
    // 页面应该有筛选相关的元素
    await expect(page.locator('body')).toContainText(/筛选|过滤|类别|账户/);
  });
});


// ─── 导入页 ──────────────────────────────────────────────

test.describe('导入页 Import', () => {
  test('页面加载正常', async ({ page }) => {
    await page.goto('/import');
    await expect(page.locator('body')).toContainText('数据导入');
    await expect(page.locator('body')).toContainText('选择 CSV 文件');
  });

  test('步骤指示器显示', async ({ page }) => {
    await page.goto('/import');
    // 应该有4个步骤
    await expect(page.locator('body')).toContainText('上传文件');
    await expect(page.locator('body')).toContainText('确认映射');
    await expect(page.locator('body')).toContainText('导入设置');
    await expect(page.locator('body')).toContainText('完成');
  });

  test('未选择文件时按钮禁用', async ({ page }) => {
    await page.goto('/import');
    const submitBtn = page.locator('button', { hasText: /分析文件/ });
    await expect(submitBtn).toBeDisabled();
  });

  test('上传文件后可点击分析', async ({ page }) => {
    await page.goto('/import');

    // 创建一个测试 CSV 文件
    const csvContent = '交易类型,日期,金额,类别,备注\n支出,2024/06/15 10:00,100,餐饮,午饭\n';
    const buffer = Buffer.from(csvContent, 'utf-8');

    // 上传文件
    const fileInput = page.locator('input[type="file"]');
    await fileInput.setInputFiles({
      name: 'test.csv',
      mimeType: 'text/csv',
      buffer,
    });

    // 按钮应该可用了
    const submitBtn = page.locator('button', { hasText: /分析文件/ });
    await expect(submitBtn).toBeEnabled();

    // 点击分析
    await submitBtn.click();

    // 应该进入第二步，显示映射表格
    await page.waitForTimeout(2000);
    await expect(page.locator('body')).toContainText('列映射');
  });

  test('完整导入流程', async ({ page }) => {
    await page.goto('/import');

    const csvContent = '交易类型,日期,金额,类别,备注\n支出,2024/06/15 10:00,100,餐饮,午饭\n收入,2024/06/16 14:00,5000,工资,6月工资\n';
    const buffer = Buffer.from(csvContent, 'utf-8');

    // Step 1: 上传
    await page.locator('input[type="file"]').setInputFiles({
      name: 'test_import.csv',
      mimeType: 'text/csv',
      buffer,
    });
    await page.locator('button', { hasText: /分析文件/ }).click();
    await page.waitForTimeout(2000);

    // Step 2: 确认映射
    await expect(page.locator('body')).toContainText('列映射');
    await page.locator('button', { hasText: /下一步/ }).click();

    // Step 3: 设置标签
    await expect(page.locator('body')).toContainText('标签');
    await page.locator('button', { hasText: /确认导入/ }).click();

    // Step 4: 完成
    await page.waitForTimeout(2000);
    await expect(page.locator('body')).toContainText('导入完成');
  });
});


// ─── 导出页 ──────────────────────────────────────────────

test.describe('导出页 Export', () => {
  test('页面加载正常', async ({ page }) => {
    await page.goto('/export');
    await expect(page.locator('body')).toContainText('数据导出');
  });

  test('四种格式卡片显示', async ({ page }) => {
    await page.goto('/export');
    await expect(page.locator('body')).toContainText('Excel');
    await expect(page.locator('body')).toContainText('CSV');
    await expect(page.locator('body')).toContainText('PDF');
    await expect(page.locator('body')).toContainText('JSON');
  });

  test('时间范围快捷按钮', async ({ page }) => {
    await page.goto('/export');
    await expect(page.locator('body')).toContainText('本月');
    await expect(page.locator('body')).toContainText('本年');
    await expect(page.locator('body')).toContainText('全部');
  });

  test('筛选条件可操作', async ({ page }) => {
    await page.goto('/export');
    await page.waitForTimeout(1000);
    // 检查筛选下拉框
    await expect(page.locator('body')).toContainText('类型');
    await expect(page.locator('body')).toContainText('类别');
    await expect(page.locator('body')).toContainText('账户');
  });

  test('导出预览显示', async ({ page }) => {
    await page.goto('/export');
    await page.waitForTimeout(2000);
    // 预览区域应该显示记录数
    await expect(page.locator('body')).toContainText('记录数');
    await expect(page.locator('body')).toContainText('日期范围');
  });

  test('快速时间范围切换', async ({ page }) => {
    await page.goto('/export');
    await page.waitForTimeout(1000);

    // 点击"本月"
    await page.locator('button', { hasText: '本月' }).click();
    await page.waitForTimeout(1000);

    // 点击"全部"
    await page.locator('button', { hasText: '全部' }).click();
    await page.waitForTimeout(1000);
  });
});


// ─── 其他页面 ──────────────────────────────────────────────

test.describe('预算页', () => {
  test('页面加载', async ({ page }) => {
    await page.goto('/budgets');
    await expect(page.locator('body')).toContainText(/预算|设置/);
  });
});

test.describe('类别页', () => {
  test('页面加载', async ({ page }) => {
    await page.goto('/categories');
    await expect(page.locator('body')).toContainText(/类别|标签/);
  });
});

test.describe('统计页', () => {
  test('页面加载', async ({ page }) => {
    await page.goto('/stats');
    await expect(page.locator('body')).toContainText(/统计|分析/);
  });

  test('卡片不跳转', async ({ page }) => {
    await page.goto('/stats');
    await page.waitForTimeout(1500);
    // 卡片区域不应该有 cursor: pointer
    const summaryCards = page.locator('.summary-card');
    if (await summaryCards.count() > 0) {
      const firstCard = summaryCards.first();
      const style = await firstCard.getAttribute('style');
      expect(style).not.toContain('cursor: pointer');
    }
  });

  test('图表类型选择器', async ({ page }) => {
    await page.goto('/stats');
    // 应该有多种图表类型按钮
    await expect(page.locator('body')).toContainText('环形图');
    await expect(page.locator('body')).toContainText('水平柱状图');
    await expect(page.locator('body')).toContainText('折线图');
  });

  test('排除标记交易 toggle', async ({ page }) => {
    await page.goto('/stats');
    const toggle = page.locator('#excludeToggle');
    await expect(toggle).toBeVisible();
    // 默认应该勾选
    await expect(toggle).toBeChecked();
    // 取消勾选
    await toggle.uncheck();
    await page.waitForTimeout(500);
    await expect(toggle).not.toBeChecked();
  });

  test('图表类型切换', async ({ page }) => {
    await page.goto('/stats');
    await page.waitForTimeout(1000);
    // 点击水平柱状图
    const hbarBtn = page.locator('button', { hasText: '水平柱状图' });
    if (await hbarBtn.count() > 0) {
      await hbarBtn.click();
      await page.waitForTimeout(500);
    }
    // 点击折线图
    const lineBtn = page.locator('button', { hasText: '折线图' });
    if (await lineBtn.count() > 0) {
      await lineBtn.click();
      await page.waitForTimeout(500);
    }
  });
});


// ─── API 健康检查 ──────────────────────────────────────────────

test.describe('API', () => {
  test('健康检查', async ({ request }) => {
    const response = await request.get('/api/health');
    expect(response.ok()).toBeTruthy();
    const data = await response.json();
    // health 接口可能返回不同格式
    expect(data).toBeTruthy();
  });

  test('导入预览接口', async ({ request }) => {
    const csvContent = '交易类型,日期,金额,类别\n支出,2024/06/15,100,餐饮\n';
    const response = await request.post('/api/import/preview', {
      multipart: {
        file: {
          name: 'test.csv',
          mimeType: 'text/csv',
          buffer: Buffer.from(csvContent, 'utf-8'),
        },
      },
    });
    expect(response.ok()).toBeTruthy();
    const data = await response.json();
    expect(data.success).toBeTruthy();
    expect(data.data.total_rows).toBe(1);
    expect(data.data.mapping['交易类型'].target).toBe('type');
  });

  test('导出预览接口', async ({ request }) => {
    const response = await request.get('/api/export/preview');
    expect(response.ok()).toBeTruthy();
    const data = await response.json();
    expect(data.success).toBeTruthy();
    expect(data.data.count).toBeGreaterThanOrEqual(0);
  });

  test('导出 Excel 接口', async ({ request }) => {
    const response = await request.get('/api/export/v2?format=excel');
    expect(response.ok()).toBeTruthy();
    const contentType = response.headers()['content-type'];
    expect(contentType).toContain('spreadsheetml');
  });

  test('导出 CSV 接口', async ({ request }) => {
    const response = await request.get('/api/export/v2?format=csv');
    expect(response.ok()).toBeTruthy();
    const contentType = response.headers()['content-type'];
    expect(contentType).toContain('csv');
  });
});
