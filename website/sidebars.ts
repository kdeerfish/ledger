import type {SidebarsConfig} from '@docusaurus/plugin-content-docs';

const sidebars: SidebarsConfig = {
  docs: [
    'intro',
    {
      type: 'category',
      label: '快速开始',
      items: ['quickstart', 'docker'],
    },
    {
      type: 'category',
      label: 'CLI 命令参考',
      items: [
        'cli/index',
        'cli/transactions',
        'cli/search',
        'cli/statistics',
        'cli/budgets',
        'cli/templates',
        'cli/import-export',
        'cli/ai-agent',
        'cli/database',
      ],
    },
    'web',
    'api',
    'development',
  ],
};

export default sidebars;
