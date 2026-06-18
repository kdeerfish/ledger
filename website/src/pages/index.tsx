import type {ReactNode} from 'react';
import clsx from 'clsx';
import Link from '@docusaurus/Link';
import useDocusaurusContext from '@docusaurus/useDocusaurusContext';
import Layout from '@theme/Layout';
import Heading from '@theme/Heading';
import styles from './index.module.css';

function HomepageHeader() {
  const {siteConfig} = useDocusaurusContext();
  return (
    <header className={clsx('hero hero--primary', styles.heroBanner)}>
      <div className="container">
        <Heading as="h1" className="hero__title">
          📒 {siteConfig.title}
        </Heading>
        <p className="hero__subtitle">{siteConfig.tagline}</p>
        <div className={styles.buttons}>
          <Link className="button button--secondary button--lg" to="/docs/intro">
            🚀 快速开始
          </Link>
          <Link className="button button--secondary button--lg" to="/docs/cli">
            📘 CLI 参考
          </Link>
          <Link className="button button--secondary button--lg" to="/docs/docker">
            🐳 Docker 部署
          </Link>
        </div>
      </div>
    </header>
  );
}

function Feature({icon, title, description}: {icon: string; title: string; description: ReactNode}) {
  return (
    <div className={clsx('col col--4')}>
      <div className="text--center padding-horiz--md padding-vert--lg">
        <div style={{fontSize: '3rem', marginBottom: '1rem'}}>{icon}</div>
        <Heading as="h3">{title}</Heading>
        <p>{description}</p>
      </div>
    </div>
  );
}

export default function Home(): ReactNode {
  const {siteConfig} = useDocusaurusContext();
  return (
    <Layout
      title={siteConfig.title}
      description="Ledger 个人记账系统 - 收支管理、预算规划、多维度统计、Web 界面、AI Agent 集成">
      <HomepageHeader />
      <main className="container">
        <div className="row" style={{marginTop: '3rem', marginBottom: '3rem', maxWidth: 1200, margin: '0 auto'}}>
          <Feature
            icon="💰"
            title="收支管理"
            description={
              <>
                完整的记账功能：添加、编辑、软删除、恢复、搜索、筛选。
                <br />
                <Link to="/docs/cli/transactions">查看 CLI 用法 →</Link>
              </>
            }
          />
          <Feature
            icon="📊"
            title="预算规划"
            description={
              <>
                按月/类别/账户/成员设置预算，实时进度跟踪，超支预警。
                <br />
                <Link to="/docs/cli/budgets">查看预算功能 →</Link>
              </>
            }
          />
          <Feature
            icon="📈"
            title="多维度统计"
            description={
              <>
                按类别、账户、月份分组统计，交叉分析，数据导出。
                <br />
                <Link to="/docs/cli/statistics">查看统计功能 →</Link>
              </>
            }
          />
          <Feature
            icon="🌐"
            title="Web 界面"
            description={
              <>
                Flask + Bootstrap 5 响应式管理界面，支持手机/平板/电脑。
                <br />
                <Link to="/docs/web">查看 Web 界面 →</Link>
              </>
            }
          />
          <Feature
            icon="🤖"
            title="AI Agent 集成"
            description={
              <>
                提供 JSON API 接口，支持 picoclaw 等 AI Agent 调用。
                <br />
                <Link to="/docs/cli/ai-agent">查看 Agent 集成 →</Link>
              </>
            }
          />
          <Feature
            icon="🐳"
            title="Docker 部署"
            description={
              <>
                三仓库推送（Docker Hub / ghcr.io / 阿里云），一键部署。
                <br />
                <Link to="/docs/docker">查看部署指南 →</Link>
              </>
            }
          />
        </div>

        {/* Docker Quick Start */}
        <div className="row" style={{marginBottom: '3rem'}}>
          <div className="col col--8 col--offset-2">
            <div className="card">
              <div className="card__header">
                <Heading as="h3">🐳 快速部署</Heading>
              </div>
              <div className="card__body">
                <pre>
                  <code>
                    {`# 国内用户推荐阿里云
docker pull crpi-1bkinvfgt16i5pgx.cn-shenzhen.personal.cr.aliyuncs.com/deerfish/ledger:latest

# 启动容器
docker run -d \\
  --name ledger \\
  -p 5800:5800 \\
  -v $(pwd)/data:/data \\
  --restart unless-stopped \\
  zouzhenglu/ledger:latest

# 访问
open http://localhost:5800`}
                  </code>
                </pre>
              </div>
              <div className="card__footer">
                <Link to="/docs/docker" className="button button--primary button--sm">
                  完整部署指南 →
                </Link>
              </div>
            </div>
          </div>
        </div>

        {/* Image Registry Table */}
        <div className="row" style={{marginBottom: '3rem'}}>
          <div className="col col--8 col--offset-2">
            <Heading as="h3" className="text--center">📦 镜像仓库</Heading>
            <table>
              <thead>
                <tr>
                  <th>仓库</th>
                  <th>拉取命令</th>
                  <th>速度</th>
                </tr>
              </thead>
              <tbody>
                <tr>
                  <td><a href="https://hub.docker.com/r/zouzhenglu/ledger">Docker Hub</a></td>
                  <td><code>docker pull zouzhenglu/ledger:latest</code></td>
                  <td>🌍 全球</td>
                </tr>
                <tr>
                  <td><a href="https://github.com/kdeerfish/ledger/pkgs/container/ledger">ghcr.io</a></td>
                  <td><code>docker pull ghcr.io/kdeerfish/ledger:latest</code></td>
                  <td>🌍 全球</td>
                </tr>
                <tr>
                  <td>阿里云容器镜像服务</td>
                  <td><code>docker pull crpi-1bkinvfgt16i5pgx.cn-shenzhen.personal.cr.aliyuncs.com/deerfish/ledger:latest</code></td>
                  <td>🇨🇳 国内最快</td>
                </tr>
              </tbody>
            </table>
          </div>
        </div>

        {/* Stats / Badges */}
        <div className="row" style={{marginBottom: '3rem'}}>
          <div className="col col--8 col--offset-2 text--center">
            <p>
              <img src="https://img.shields.io/github/actions/workflow/status/kdeerfish/ledger/docker-publish.yml?branch=master&label=CI%2FCD&logo=github" alt="CI/CD" />
              &nbsp;
              <img src="https://img.shields.io/badge/python-3.10%2B-blue?logo=python" alt="Python" />
              &nbsp;
              <img src="https://img.shields.io/badge/coverage-86%25-brightgreen" alt="Coverage" />
              &nbsp;
              <img src="https://img.shields.io/github/license/kdeerfish/ledger" alt="License" />
              &nbsp;
              <img src="https://img.shields.io/github/stars/kdeerfish/ledger?style=social" alt="Stars" />
            </p>
          </div>
        </div>
      </main>
    </Layout>
  );
}
