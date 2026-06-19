import type {SidebarsConfig} from '@docusaurus/plugin-content-docs';

const sidebars: SidebarsConfig = {
  docs: [
    'intro',
    {
      type: 'category',
      label: '🚀 快速开始',
      collapsed: false,
      items: [
        'getting-started/index',
        'getting-started/docker-wsl',
        'getting-started/docker-nas',
        'getting-started/source-code',
      ],
    },
    {
      type: 'category',
      label: '📖 使用手册',
      collapsed: false,
      items: [
        'user-guide/web-ui',
        'user-guide/cli',
      ],
    },
    {
      type: 'category',
      label: '🤖 AI Agent 集成',
      collapsed: false,
      items: [
        'ai-agent/index',
      ],
    },
    {
      type: 'category',
      label: '❓ FAQ',
      collapsed: false,
      items: [
        'faq/data',
        'faq/troubleshooting',
      ],
    },
    {
      type: 'category',
      label: '📚 参考',
      items: [
        'quickstart',
        'docker',
        'web',
        'api',
        {
          type: 'category',
          label: 'CLI 命令参考（详细）',
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
        'development',
      ],
    },
  ],
};

export default sidebars;