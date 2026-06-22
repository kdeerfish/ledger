package internal

import "github.com/spf13/cobra"

func MetaCmd(c *Client) *cobra.Command {
	cmd := &cobra.Command{
		Use:   "meta",
		Short: "枚举查询 (类别/账户/成员/项目/商家)",
	}
	cmd.AddCommand(
		metaListCmd(c, "categories", "所有类别", "/api/categories"),
		metaListCmd(c, "quick-categories", "常用子类别 TOP20", "/api/categories/quick"),
		metaListCmd(c, "accounts", "所有账户", "/api/accounts"),
		metaListCmd(c, "members", "所有成员", "/api/members"),
		metaListCmd(c, "projects", "所有项目", "/api/projects"),
		metaListCmd(c, "merchants", "所有商家", "/api/merchants"),
		suggestCmd(c),
	)
	return cmd
}

func metaListCmd(c *Client, name, short, path string) *cobra.Command {
	return &cobra.Command{
		Use:   name,
		Short: short,
		RunE: func(cmd *cobra.Command, args []string) error {
			body, err := c.Get(path, nil)
			if err != nil {
				return err
			}
			PrintResponse(body)
			return nil
		},
	}
}

func suggestCmd(c *Client) *cobra.Command {
	var field, keyword string
	cmd := &cobra.Command{
		Use:   "suggest",
		Short: "自动建议",
		Example: `  ledger-cli meta suggest --field all --keyword 早`,
		RunE: func(cmd *cobra.Command, args []string) error {
			body, err := c.Get("/api/suggestions", map[string]string{
				"field":   field,
				"keyword": keyword,
			})
			if err != nil {
				return err
			}
			PrintResponse(body)
			return nil
		},
	}
	f := cmd.Flags()
	f.StringVar(&field, "field", "all", "字段: all/categories/subcategories/accounts/merchants/projects/members")
	f.StringVar(&keyword, "keyword", "", "关键词")
	return cmd
}
