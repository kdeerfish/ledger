package cli

import (
	"github.com/kdeerfish/ledger/internal/httpapi"
	"github.com/spf13/cobra"
)

// serveCmd is the Web UI entry point. Kept in a separate file so that the
// HTTP layer can be imported in tests without dragging cobra.
func (a *App) serveCmd() *cobra.Command {
	var (
		host  string
		port  int
		debug bool
	)
	cmd := &cobra.Command{
		Use:   "serve",
		Short: "启动 Web 服务(http://0.0.0.0:5800)",
		RunE: func(_ *cobra.Command, _ []string) error {
			cfg := *a.Cfg
			if host != "" {
				cfg.WebHost = host
			}
			if port > 0 {
				cfg.WebPort = port
			}
			if debug {
				cfg.WebDebug = true
			}
			srv, err := httpapi.NewServer(&cfg, a.Tx, a.Budget, a.Template, a.Tag)
			if err != nil {
				return err
			}
			return srv.Run()
		},
	}
	f := cmd.Flags()
	f.StringVar(&host, "host", "", "绑定地址")
	f.IntVarP(&port, "port", "p", 0, "端口")
	f.BoolVar(&debug, "debug", false, "调试模式")
	return cmd
}
