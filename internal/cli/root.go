// Package cli exposes BuildRoot, the entry point used by cmd/ledger/main.go
// to assemble the cobra command tree. This file must stay free of side
// effects so it can be imported in tests.
package cli

import (
	"github.com/kdeerfish/ledger/internal/version"
	"github.com/spf13/cobra"
)

// BuildRoot assembles the full command tree. The returned root can be
// executed via root.Execute().
func (a *App) BuildRoot() *cobra.Command {
	info := version.Get()
	root := &cobra.Command{
		Use:   "ledger",
		Short: "个人记账 CLI — 复刻 Python 版 ledger 全部功能",
		Long: "ledger — " + info.Version + " (" + info.GoVersion + ")\n" +
			"用法: ledger <command> [flags]\n" +
			"运行 `ledger <command> --help` 查看子命令帮助。\n\n" +
			"命令分组:\n" +
			"  tx        交易 (add / list / update / delete / restore / hard-delete)\n" +
			"  budget    预算与预算模板\n" +
			"  template  记账模板\n" +
			"  tag       标签\n" +
			"  misc      搜索 / 过滤 / 统计 / 导入 / 导出 / reconcile",
		Version: info.Version,
	}
	root.AddCommand(
		a.txCmd(), a.budgetCmd(), a.templateCmd(), a.tagCmd(), a.miscCmd(),
		a.initCmd(), a.versionCmd(), a.serveCmd(),
	)
	return root
}

func (a *App) initCmd() *cobra.Command {
	return &cobra.Command{
		Use:   "init",
		Short: "初始化数据库(已自动调用)",
		RunE: func(cmd *cobra.Command, _ []string) error {
			// Open() already ran during NewApp; nothing more to do.
			a.OK("数据库已就绪: %s", a.Cfg.DBPath)
			return nil
		},
	}
}

func (a *App) versionCmd() *cobra.Command {
	return &cobra.Command{
		Use:   "version",
		Short: "打印版本信息",
		Run: func(cmd *cobra.Command, _ []string) {
			info := version.Get()
			a.Print("ledger %s (commit %s, built %s, %s/%s, %s)",
				info.Version, info.Commit, info.BuildTime, info.OS, info.Arch, info.GoVersion)
		},
	}
}
