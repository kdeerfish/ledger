package internal

import (
	"strconv"

	"github.com/spf13/cobra"
)

func TagCmd(c *Client) *cobra.Command {
	cmd := &cobra.Command{
		Use:   "tag",
		Short: "标签管理",
	}
	cmd.AddCommand(
		tagListCmd(c),
		tagAddCmd(c),
		tagDeleteCmd(c),
		tagTxCmd(c),
	)
	return cmd
}

func tagListCmd(c *Client) *cobra.Command {
	return &cobra.Command{
		Use:   "list",
		Short: "标签列表",
		RunE: func(cmd *cobra.Command, args []string) error {
			body, err := c.Get("/api/tags", nil)
			if err != nil {
				return err
			}
			PrintResponse(body)
			return nil
		},
	}
}

func tagAddCmd(c *Client) *cobra.Command {
	var name, color string
	cmd := &cobra.Command{
		Use:   "add",
		Short: "创建标签",
		Example: `  ledger-cli tag add --name 报销 --color "#ef4444"`,
		RunE: func(cmd *cobra.Command, args []string) error {
			data := map[string]any{"name": name}
			if color != "" {
				data["color"] = color
			}
			body, err := c.PostJSON("/api/tags", data)
			if err != nil {
				return err
			}
			PrintResponse(body)
			return nil
		},
	}
	f := cmd.Flags()
	f.StringVar(&name, "name", "", "标签名称 (必填)")
	f.StringVar(&color, "color", "", "颜色 (如 #ef4444)")
	cmd.MarkFlagRequired("name")
	return cmd
}

func tagDeleteCmd(c *Client) *cobra.Command {
	return &cobra.Command{
		Use:   "delete [id]",
		Short: "删除标签",
		Args:  cobra.ExactArgs(1),
		RunE: func(cmd *cobra.Command, args []string) error {
			body, err := c.Delete("/api/tags/" + args[0])
			if err != nil {
				return err
			}
			PrintResponse(body)
			return nil
		},
	}
}

func tagTxCmd(c *Client) *cobra.Command {
	var limit int
	cmd := &cobra.Command{
		Use:   "tx [tag_id]",
		Short: "按标签查记录",
		Args:  cobra.ExactArgs(1),
		RunE: func(cmd *cobra.Command, args []string) error {
			body, err := c.Get("/api/tags/"+args[0]+"/transactions", map[string]string{
				"limit": strconv.Itoa(limit),
			})
			if err != nil {
				return err
			}
			PrintResponse(body)
			return nil
		},
	}
	f := cmd.Flags()
	f.IntVarP(&limit, "limit", "l", 20, "返回条数")
	return cmd
}
