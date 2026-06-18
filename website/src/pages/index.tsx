import type {ReactNode} from 'react';
import Link from '@docusaurus/Link';
import useDocusaurusContext from '@docusaurus/useDocusaurusContext';
import Layout from '@theme/Layout';
import Heading from '@theme/Heading';
import Translate, {translate} from '@docusaurus/Translate';
import styles from './index.module.css';

const features = [
  {
    num: '01', icon: '💰',
    titleKey: 'features.transactions',
    titleDefault: '收支管理',
    descKey: 'features.transactions.desc',
    descDefault: '添加、编辑、软删除、恢复、搜索、筛选，覆盖完整记账流程。支持随手记 CSV 一键导入，自动去重。',
    link: '/docs/cli/transactions',
    linkTextKey: 'features.transactions.link',
    linkTextDefault: '查看 CLI 用法 →',
  },
  {
    num: '02', icon: '📊',
    titleKey: 'features.budgets',
    titleDefault: '预算规划',
    descKey: 'features.budgets.desc',
    descDefault: '按月 / 类别 / 账户 / 成员 / 项目设置预算，实时计算已用额度，进度条展示，超支自动预警。',
    link: '/docs/cli/budgets',
    linkTextKey: 'features.budgets.link',
    linkTextDefault: '查看预算功能 →',
  },
  {
    num: '03', icon: '📈',
    titleKey: 'features.stats',
    titleDefault: '多维度统计',
    descKey: 'features.stats.desc',
    descDefault: '按类别、账户、月份分组聚合统计，支持商家→类别、账户→商家交叉分析，CSV / JSON 导出。',
    link: '/docs/cli/statistics',
    linkTextKey: 'features.stats.link',
    linkTextDefault: '查看统计功能 →',
  },
  {
    num: '04', icon: '🌐',
    titleKey: 'features.web',
    titleDefault: 'Web 界面',
    descKey: 'features.web.desc',
    descDefault: 'Flask + Bootstrap 5 响应式管理面板，手机 / 平板 / 电脑均可用。概览 Dashboard + 预算仪表盘 + 图表。',
    link: '/docs/web',
    linkTextKey: 'features.web.link',
    linkTextDefault: '查看 Web 界面 →',
  },
  {
    num: '05', icon: '🤖',
    titleKey: 'features.ai',
    titleDefault: 'AI Agent 集成',
    descKey: 'features.ai.desc',
    descDefault: '提供 JSON 接口，支持 picoclaw 等 AI Agent 直接调用。analyze 命令输出结构化数据摘要供 Agent 学习。',
    link: '/docs/cli/ai-agent',
    linkTextKey: 'features.ai.link',
    linkTextDefault: '查看 Agent 集成 →',
  },
  {
    num: '06', icon: '🐳',
    titleKey: 'features.docker',
    titleDefault: 'Docker 部署',
    descKey: 'features.docker.desc',
    descDefault: '三仓库推送（Docker Hub / ghcr.io / 阿里云），push master 自动构建，健康检查，非 root 安全运行。',
    link: '/docs/docker',
    linkTextKey: 'features.docker.link',
    linkTextDefault: '查看部署指南 →',
  },
];

function Hero() {
  const {siteConfig} = useDocusaurusContext();
  return (
    <header className={styles.hero}>
      <div className="container">
        <Heading as="h1">📒 {siteConfig.title}</Heading>
        <p className={styles.heroTagline}>
          <Translate>个人记账系统 — 收支管理 · 预算规划 · 多维度统计 · Web 界面 · AI Agent 集成</Translate>
        </p>
        <p className={styles.heroDesc}>
          Python 3.10+ · SQLite · pytest <Translate>覆盖率</Translate> 86% · <Translate>三仓库 Docker 镜像</Translate>
        </p>
        <div className={styles.buttons}>
          <Link className={styles.btnPrimary} to="/docs/intro">
            🚀 <Translate>快速开始</Translate>
          </Link>
          <Link className={styles.btnSecondary} to="/docs/cli">
            📘 <Translate>CLI 参考</Translate>
          </Link>
          <Link className={styles.btnSecondary} to="/docs/docker">
            🐳 <Translate>Docker 部署</Translate>
          </Link>
        </div>
      </div>
    </header>
  );
}

function FeaturesSection() {
  return (
    <section className={styles.section}>
      <div className={styles.slimContainer}>
        <Heading as="h2" className={styles.sectionTitle}>
          ✨ <Translate>功能一览</Translate>
        </Heading>
        <p className={styles.sectionSub}>
          <Translate>命令行、Web 界面、AI Agent 三种交互方式，覆盖记账全场景。</Translate>
        </p>
        <div className={styles.featureGrid}>
          {features.map((f) => (
            <div key={f.num} className={styles.featureCard}>
              <div className={styles.featureNum}>{f.num}</div>
              <div className={styles.featureIcon}>{f.icon}</div>
              <Heading as="h3" className={styles.featureTitle}>
                {translate({message: f.titleDefault, id: f.titleKey})}
              </Heading>
              <p className={styles.featureDesc}>
                {translate({message: f.descDefault, id: f.descKey})}
              </p>
              <div className={styles.featureLink}>
                <Link to={f.link}>
                  {translate({message: f.linkTextDefault, id: f.linkTextKey})}
                </Link>
              </div>
            </div>
          ))}
        </div>
      </div>
    </section>
  );
}

function InstallSection() {
  return (
    <section className={styles.sectionAlt}>
      <div className={styles.slimContainer}>
        <Heading as="h2" className={styles.sectionTitle}>
          🐳 <Translate>快速部署</Translate>
        </Heading>
        <p className={styles.sectionSub}>
          <Translate>一条命令启动。支持 Docker 及本地 Python 运行。</Translate>
        </p>
        <div className={styles.installGrid}>
          <div className={styles.installCard}>
            <div className={styles.installLabel}><Translate>Docker（推荐）</Translate></div>
            <pre className={styles.installCode}>
              <code>
                {`docker run -d \\
  --name ledger \\
  -p 5800:5800 \\
  -v $(pwd)/data:/data \\
  --restart unless-stopped \\
  zouzhenglu/ledger:latest`}
              </code>
            </pre>
          </div>
          <div className={styles.installCard}>
            <div className={styles.installLabel}><Translate>国内用户（阿里云）</Translate></div>
            <pre className={styles.installCode}>
              <code>
                {`docker pull crpi-1bkinvfgt16i5pgx.cn-shenzhen\\
  .personal.cr.aliyuncs.com/deerfish/ledger:latest

docker run -d \\
  -p 5800:5800 \\
  -v $(pwd)/data:/data \\
  --restart unless-stopped \\
  crpi-xxx/deerfish/ledger:latest`}
              </code>
            </pre>
          </div>
          <div className={styles.installCard}>
            <div className={styles.installLabel}><Translate>本地运行</Translate></div>
            <pre className={styles.installCode}>
              <code>
                {`pip install -e ".[dev,lint]"
python web/run.py

# 访问 http://localhost:5800`}
              </code>
            </pre>
          </div>
          <div className={styles.installCard}>
            <div className={styles.installLabel}>docker-compose</div>
            <pre className={styles.installCode}>
              <code>
                {`git clone https://github.com/kdeerfish/ledger.git
cd ledger
docker compose up -d

# 访问 http://localhost:5800`}
              </code>
            </pre>
          </div>
        </div>

        <div className={styles.badgeRow}>
          <img src="https://img.shields.io/github/actions/workflow/status/kdeerfish/ledger/docker-publish.yml?branch=master&label=CI%2FCD&logo=github" alt="CI/CD" />
          <img src="https://img.shields.io/badge/python-3.10%2B-blue?logo=python" alt="Python" />
          <img src="https://img.shields.io/badge/coverage-86%25-brightgreen" alt="Coverage" />
          <img src="https://img.shields.io/github/license/kdeerfish/ledger" alt="License" />
          <img src="https://img.shields.io/github/stars/kdeerfish/ledger?style=social" alt="Stars" />
        </div>
      </div>
    </section>
  );
}

function RegistrySection() {
  return (
    <section className={styles.section}>
      <div className={styles.slimContainer}>
        <Heading as="h2" className={styles.sectionTitle}>
          📦 <Translate>镜像仓库</Translate>
        </Heading>
        <p className={styles.sectionSub}>
          <Translate>每次 push master 自动构建并推送到全球 3 个镜像仓库。</Translate>
        </p>
        <div className={styles.installGrid}>
          <div className={styles.installCard}>
            <div className={styles.installLabel}>Docker Hub</div>
            <pre className={styles.installCode}>
              <code>{'docker pull zouzhenglu/ledger:latest'}</code>
            </pre>
            <div style={{marginTop: '0.5rem', fontSize: '0.8rem', color: 'var(--ifm-color-emphasis-500)'}}>🌍 <Translate>全球</Translate></div>
          </div>
          <div className={styles.installCard}>
            <div className={styles.installLabel}>ghcr.io</div>
            <pre className={styles.installCode}>
              <code>{'docker pull ghcr.io/kdeerfish/ledger:latest'}</code>
            </pre>
            <div style={{marginTop: '0.5rem', fontSize: '0.8rem', color: 'var(--ifm-color-emphasis-500)'}}>🌍 <Translate>全球</Translate></div>
          </div>
          <div className={styles.installCard}>
            <div className={styles.installLabel}><Translate>阿里云（国内最快）</Translate></div>
            <pre className={styles.installCode}>
              <code>
                {'docker pull crpi-1bkinvfgt16i5pgx\\\n.cn-shenzhen.personal.cr.aliyuncs.com\\\n/deerfish/ledger:latest'}
              </code>
            </pre>
            <div style={{marginTop: '0.5rem', fontSize: '0.8rem', color: 'var(--ifm-color-emphasis-500)'}}>🇨🇳 <Translate>国内无需代理</Translate></div>
          </div>
        </div>
      </div>
    </section>
  );
}

export default function Home(): ReactNode {
  const {siteConfig} = useDocusaurusContext();
  return (
    <Layout
      title={siteConfig.title}
      description={translate({
        message: 'Ledger 个人记账系统 - 收支管理、预算规划、多维度统计、Web 界面、AI Agent 集成',
      })}>
      <Hero />
      <main>
        <FeaturesSection />
        <InstallSection />
        <RegistrySection />
        <div className={styles.footerNote}>
          <strong>Ledger</strong> · MIT · Python 3.10+ · SQLite ·{' '}
          <a href="https://github.com/kdeerfish/ledger"><Translate>GitHub</Translate></a> ·{' '}
          <a href="https://hub.docker.com/r/zouzhenglu/ledger">Docker Hub</a>
        </div>
      </main>
    </Layout>
  );
}
