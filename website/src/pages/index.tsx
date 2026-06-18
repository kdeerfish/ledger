import type {ReactNode} from 'react';
import Link from '@docusaurus/Link';
import useDocusaurusContext from '@docusaurus/useDocusaurusContext';
import Layout from '@theme/Layout';
import Heading from '@theme/Heading';
import styles from './index.module.css';

function Hero() {
  const {siteConfig} = useDocusaurusContext();
  return (
    <header className={styles.hero}>
      <div className="container">
        <Heading as="h1">📒 {siteConfig.title}</Heading>
        <p className={styles.heroTagline}>
          个人记账系统 — 收支管理 · 预算规划 · 多维度统计 · Web 界面 · AI Agent 集成
        </p>
        <p className={styles.heroDesc}>
          Python 3.10+ · SQLite · 86% test coverage · Multi-registry Docker
        </p>
        <div className={styles.buttons}>
          <Link className={styles.btnPrimary} to="/docs/intro">
            查看文档 →
          </Link>
          <Link className={styles.btnSecondary} to="/docs/quickstart">
            🚀 快速开始
          </Link>
          <Link className={styles.btnSecondary} to="/docs/docker">
            🐳 Docker 部署
          </Link>
        </div>
      </div>
    </header>
  );
}

function ValueProps() {
  return (
    <section className={styles.props}>
      <div className={styles.slimContainer}>
        <div className={styles.propsGrid}>
          <div className={styles.propCard}>
            <div className={styles.propIcon}>💻</div>
            <Heading as="h3" className={styles.propTitle}>
              终端优先
            </Heading>
            <p className={styles.propDesc}>
              命令行记账，快速高效。支持搜索、筛选、统计、导出，一切在终端完成。
            </p>
          </div>
          <div className={styles.propCard}>
            <div className={styles.propIcon}>🌐</div>
            <Heading as="h3" className={styles.propTitle}>
              开箱即用
            </Heading>
            <p className={styles.propDesc}>
              一条 Docker 命令启动 Web 界面，手机平板电脑均可访问。
            </p>
          </div>
          <div className={styles.propCard}>
            <div className={styles.propIcon}>🤖</div>
            <Heading as="h3" className={styles.propTitle}>
              AI Agent 就绪
            </Heading>
            <p className={styles.propDesc}>
              JSON 接口直通 AI Agent，用自然语言记账查账。
            </p>
          </div>
        </div>
      </div>
    </section>
  );
}

function CtaSection() {
  return (
    <section className={styles.cta}>
      <div className={styles.slimContainer}>
        <Heading as="h2" className={styles.ctaTitle}>
          开始记账
        </Heading>
        <p className={styles.ctaDesc}>
          CLI、Web、AI Agent 三种方式任你选择，总有一种适合你。
        </p>
        <div className={styles.ctaButtons}>
          <Link className={styles.btnPrimary} to="/docs/intro">
            阅读文档 →
          </Link>
          <Link className={styles.btnOutline} to="/docs/cli">
            📘 CLI 命令参考
          </Link>
          <Link className={styles.btnOutline} to="/docs/api">
            🔌 API 文档
          </Link>
          <Link className={styles.btnOutline} to="/docs/development">
            🛠 开发指南
          </Link>
        </div>
        <div className={styles.badgeRow}>
          <a href="https://github.com/kdeerfish/ledger/actions" target="_blank" rel="noopener">
            <img src="https://img.shields.io/github/actions/workflow/status/kdeerfish/ledger/docker-publish.yml?branch=master&label=CI%2FCD&logo=github" alt="CI/CD" />
          </a>
          <a href="https://www.python.org/" target="_blank" rel="noopener">
            <img src="https://img.shields.io/badge/python-3.10%2B-blue?logo=python" alt="Python" />
          </a>
          <a href="https://github.com/kdeerfish/ledger/actions" target="_blank" rel="noopener">
            <img src="https://img.shields.io/badge/coverage-86%25-brightgreen" alt="Coverage" />
          </a>
          <a href="https://github.com/kdeerfish/ledger/blob/master/LICENSE" target="_blank" rel="noopener">
            <img src="https://img.shields.io/github/license/kdeerfish/ledger" alt="License" />
          </a>
          <a href="https://github.com/kdeerfish/ledger" target="_blank" rel="noopener">
            <img src="https://img.shields.io/github/stars/kdeerfish/ledger?style=social" alt="Stars" />
          </a>
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
      description="Ledger 个人记账系统 - 收支管理、预算规划、多维度统计、Web 界面、AI Agent 集成">
      <Hero />
      <main>
        <ValueProps />
        <CtaSection />
        <div className={styles.footerNote}>
          <strong>Ledger</strong> · MIT · Python 3.10+ · SQLite ·{' '}
          <a href="https://github.com/kdeerfish/ledger">GitHub</a> ·{' '}
          <a href="https://hub.docker.com/r/zouzhenglu/ledger">Docker Hub</a>
        </div>
      </main>
    </Layout>
  );
}
