// Command ledger is the unified entry point for the Go rewrite of the
// personal accounting system. It exposes a cobra command tree (CLI) plus
// a sub-command to start the embedded web server.
package main

import (
	"fmt"
	"os"

	"github.com/kdeerfish/ledger/internal/cli"
	"github.com/kdeerfish/ledger/internal/config"
	"github.com/kdeerfish/ledger/internal/httpapi"
	"github.com/kdeerfish/ledger/internal/logger"
	"github.com/kdeerfish/ledger/internal/webui"
)

func main() {
	if err := run(); err != nil {
		fmt.Fprintf(os.Stderr, "❌ %v\n", err)
		os.Exit(1)
	}
}

func run() error {
	cfg, err := config.Load()
	if err != nil {
		return fmt.Errorf("配置加载失败: %w", err)
	}
	logger.Setup(cfg.LogLevel, cfg.LogFormat)

	app, err := cli.NewApp(cfg, os.Stdout, os.Stderr)
	if err != nil {
		return fmt.Errorf("初始化失败: %w", err)
	}
	defer app.Close()

	// Hand the embedded SPA to the HTTP server. main is the only place that
	// knows about the webui package, so the rest of the code stays SPA-agnostic.
	httpapi.SetFS(webui.FS())

	return app.BuildRoot().Execute()
}
