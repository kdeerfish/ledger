import {themes as prismThemes} from 'prism-react-renderer';
import type {Config} from '@docusaurus/types';
import type * as Preset from '@docusaurus/preset-classic';

const config: Config = {
  title: 'Ledger',
  tagline: '个人记账系统 — 收支管理 · 预算规划 · 多维度统计 · Web 界面 · AI Agent 集成',
  favicon: 'img/favicon.ico',

  future: {
    v4: true,
  },

  url: 'https://kdeerfish.github.io',
  baseUrl: '/ledger/',

  organizationName: 'kdeerfish',
  projectName: 'ledger',

  onBrokenLinks: 'throw',
  onBrokenMarkdownLinks: 'warn',

  i18n: {
    defaultLocale: 'zh-Hans',
    locales: ['zh-Hans', 'en'],
    localeConfigs: {
      'zh-Hans': {
        label: '中文',
        direction: 'ltr',
      },
      en: {
        label: 'English',
        direction: 'ltr',
      },
    },
  },

  presets: [
    [
      'classic',
      {
        docs: {
          sidebarPath: './sidebars.ts',
          editUrl: 'https://github.com/kdeerfish/ledger/edit/master/website/',
          showLastUpdateTime: true,
        },
        blog: false,
        theme: {
          customCss: './src/css/custom.css',
        },
      } satisfies Preset.Options,
    ],
  ],

  themeConfig: {
    image: 'img/ledger-social-card.jpg',
    colorMode: {
      defaultMode: 'light',
      respectPrefersColorScheme: true,
    },
    navbar: {
      title: 'Ledger',
      logo: {
        alt: 'Ledger',
        src: 'img/logo.svg',
      },
      items: [
        {
          type: 'docSidebar',
          sidebarId: 'docs',
          position: 'left',
          label: '文档',
        },
        {to: '/docs/intro', label: '快速开始', position: 'left'},
        {
          type: 'localeDropdown',
          position: 'right',
        },
        {
          href: 'https://github.com/kdeerfish/ledger',
          position: 'right',
          className: 'header-github-link',
          'aria-label': 'GitHub',
        },
        {
          href: 'https://hub.docker.com/r/zouzhenglu/ledger',
          position: 'right',
          className: 'header-docker-link',
          'aria-label': 'Docker Hub',
        },
      ],
    },
    footer: {
      style: 'dark',
      links: [
        {
          title: '文档',
          items: [
            {label: '快速开始', to: '/docs/intro'},
            {label: 'CLI 命令参考', to: '/docs/cli'},
            {label: 'Web 界面', to: '/docs/web'},
            {label: 'API 文档', to: '/docs/api'},
            {label: 'Docker 部署', to: '/docs/docker'},
            {label: '开发指南', to: '/docs/development'},
          ],
        },
        {
          title: '项目',
          items: [
            {label: 'GitHub Issues', href: 'https://github.com/kdeerfish/ledger/issues'},
            {label: 'GitHub 仓库', href: 'https://github.com/kdeerfish/ledger'},
          ],
        },
        {
          title: '镜像仓库',
          items: [
            {label: 'Docker Hub', href: 'https://hub.docker.com/r/zouzhenglu/ledger'},
            {label: 'GitHub Container Registry', href: 'https://github.com/kdeerfish/ledger/pkgs/container/ledger'},
          ],
        },
      ],
      copyright: `Copyright © ${new Date().getFullYear()} zouzhenglu. Built with Docusaurus.`,
    },
    prism: {
      theme: prismThemes.github,
      darkTheme: prismThemes.dracula,
      defaultLanguage: 'bash',
    },
  } satisfies Preset.ThemeConfig,
};

export default config;
