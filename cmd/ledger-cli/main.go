package main

import (
	"fmt"
	"os"

	"github.com/kdeerfish/ledger-cli/internal"
	"github.com/spf13/cobra"
)

func main() {
	c := internal.NewClient()

	root := &cobra.Command{
		Use:   "ledger-cli",
		Short: "Ledger 记账 CLI — 调用 Ledger HTTP API",
		Long: `ledger-cli 是 Ledger 记账系统的命令行客户端。
通过 HTTP API 与 Ledger 服务通信，支持交易管理、统计查询、预算管理等功能。

Base URL 通过环境变量 LEDGER_API_URL 设置，默认 http://127.0.0.1:5800`,
		SilenceUsage: true,
	}

	root.AddCommand(
		internal.TxCmd(c),
		internal.StatsCmd(c),
		internal.MetaCmd(c),
		internal.BudgetCmd(c),
		internal.TemplateCmd(c),
		internal.TagCmd(c),
		internal.ExportCmd(c),
		internal.MiscCmd(c),
	)

	if err := root.Execute(); err != nil {
		fmt.Fprintln(os.Stderr, err)
		os.Exit(1)
	}
}
