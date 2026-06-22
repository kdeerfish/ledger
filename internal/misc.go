package internal

import "github.com/spf13/cobra"

func MiscCmd(c *Client) *cobra.Command {
	cmd := &cobra.Command{
		Use:   "misc",
		Short: "其他命令",
	}
	cmd.AddCommand(
		healthCmd(c),
		infoCmd(c),
		analyzeCmd(c),
	)
	return cmd
}

func healthCmd(c *Client) *cobra.Command {
	return &cobra.Command{
		Use:   "health",
		Short: "健康检查",
		RunE: func(cmd *cobra.Command, args []string) error {
			body, err := c.Get("/api/health", nil)
			if err != nil {
				return err
			}
			PrintResponse(body)
			return nil
		},
	}
}

func infoCmd(c *Client) *cobra.Command {
	return &cobra.Command{
		Use:   "info",
		Short: "数据库信息",
		RunE: func(cmd *cobra.Command, args []string) error {
			body, err := c.Get("/api/info", nil)
			if err != nil {
				return err
			}
			PrintResponse(body)
			return nil
		},
	}
}

func analyzeCmd(c *Client) *cobra.Command {
	return &cobra.Command{
		Use:   "analyze",
		Short: "消费分析报告",
		RunE: func(cmd *cobra.Command, args []string) error {
			body, err := c.Get("/api/analyze", nil)
			if err != nil {
				return err
			}
			PrintResponse(body)
			return nil
		},
	}
}
