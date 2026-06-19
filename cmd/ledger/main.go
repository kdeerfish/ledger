// Command ledger is the unified entry point for the Go rewrite of the
// personal accounting system. It exposes a cobra command tree (CLI) plus
// a sub-command to start the embedded web server.
package main

import (
	"fmt"
	"os"

	"github.com/kdeerfish/ledger/internal/cli"
	"github.com/kdeerfish/ledger/internal/config"
	"github.com/kdeerfish/ledger/internal/logger"
)

func main() {
	cfg, err := config.Load()
	if err != nil {
		fmt.Fprintf(os.Stderr, "❌ 配置加载失败: %v\n", err)
		os.Exit(1)
	}
	logger.Setup(cfg.LogLevel, cfg.LogFormat)

	app, err := cli.NewApp(cfg, os.Stdout, os.Stderr)
	if err != nil {
		fmt.Fprintf(os.Stderr, "❌ 初始化失败: %v\n", err)
		os.Exit(1)
	}
	defer app.Close()

	if err := app.BuildRoot().Execute(); err != nil {
		os.Exit(1)
	}
}
