package internal

import (
	"fmt"

	"github.com/spf13/cobra"
)

func TemplateCmd(c *Client) *cobra.Command {
	cmd := &cobra.Command{
		Use:   "template",
		Short: "记账模板管理",
	}
	cmd.AddCommand(
		templateListCmd(c),
		templateAddCmd(c),
		templateUpdateCmd(c),
		templateDeleteCmd(c),
		templateUseCmd(c),
	)
	return cmd
}

func templateListCmd(c *Client) *cobra.Command {
	return &cobra.Command{
		Use:   "list",
		Short: "模板列表",
		RunE: func(cmd *cobra.Command, args []string) error {
			body, err := c.Get("/api/templates", nil)
			if err != nil {
				return err
			}
			PrintResponse(body)
			return nil
		},
	}
}

func templateAddCmd(c *Client) *cobra.Command {
	var (
		name, tplType, typ, category, subcategory string
		account, amount, note, project, member     string
		merchant                                   string
	)
	cmd := &cobra.Command{
		Use:   "add",
		Short: "创建模板",
		Example: `  ledger-cli template add --name 早餐 --amount 15 --category 食品酒水 --account 微信零钱`,
		RunE: func(cmd *cobra.Command, args []string) error {
			data := map[string]any{"name": name}
			if tplType != "" {
				data["template_type"] = tplType
			}
			if typ != "" {
				data["type"] = typ
			}
			if amount != "" {
				data["amount"] = amount
			}
			if category != "" {
				data["category"] = category
			}
			if subcategory != "" {
				data["subcategory"] = subcategory
			}
			if account != "" {
				data["account"] = account
			}
			if project != "" {
				data["project"] = project
			}
			if member != "" {
				data["member"] = member
			}
			if merchant != "" {
				data["merchant"] = merchant
			}
			if note != "" {
				data["note"] = note
			}
			body, err := c.PostJSON("/api/templates", data)
			if err != nil {
				return err
			}
			PrintResponse(body)
			return nil
		},
	}
	f := cmd.Flags()
	f.StringVar(&name, "name", "", "模板名称 (必填)")
	f.StringVar(&tplType, "template-type", "", "模板类型")
	f.StringVarP(&typ, "type", "t", "", "交易类型: 支出/收入")
	f.StringVarP(&amount, "amount", "a", "", "金额")
	f.StringVarP(&category, "category", "c", "", "类别")
	f.StringVarP(&subcategory, "subcategory", "s", "", "子类别")
	f.StringVarP(&account, "account", "A", "", "账户")
	f.StringVarP(&project, "project", "p", "", "项目")
	f.StringVarP(&member, "member", "m", "", "成员")
	f.StringVarP(&merchant, "merchant", "M", "", "商家")
	f.StringVarP(&note, "note", "n", "", "备注")
	cmd.MarkFlagRequired("name")
	return cmd
}

func templateUpdateCmd(c *Client) *cobra.Command {
	var (
		name, typ, category, subcategory string
		account, amount, note            string
	)
	cmd := &cobra.Command{
		Use:   "update [id]",
		Short: "修改模板",
		Args:  cobra.ExactArgs(1),
		RunE: func(cmd *cobra.Command, args []string) error {
			data := map[string]any{}
			if name != "" {
				data["name"] = name
			}
			if typ != "" {
				data["type"] = typ
			}
			if amount != "" {
				data["amount"] = amount
			}
			if category != "" {
				data["category"] = category
			}
			if subcategory != "" {
				data["subcategory"] = subcategory
			}
			if account != "" {
				data["account"] = account
			}
			if note != "" {
				data["note"] = note
			}
			if len(data) == 0 {
				return fmt.Errorf("请指定要修改的字段")
			}
			body, err := c.PutJSON("/api/templates/"+args[0], data)
			if err != nil {
				return err
			}
			PrintResponse(body)
			return nil
		},
	}
	f := cmd.Flags()
	f.StringVar(&name, "name", "", "模板名称")
	f.StringVarP(&typ, "type", "t", "", "交易类型")
	f.StringVarP(&amount, "amount", "a", "", "金额")
	f.StringVarP(&category, "category", "c", "", "类别")
	f.StringVarP(&subcategory, "subcategory", "s", "", "子类别")
	f.StringVarP(&account, "account", "A", "", "账户")
	f.StringVarP(&note, "note", "n", "", "备注")
	return cmd
}

func templateDeleteCmd(c *Client) *cobra.Command {
	return &cobra.Command{
		Use:   "delete [id]",
		Short: "删除模板",
		Args:  cobra.ExactArgs(1),
		RunE: func(cmd *cobra.Command, args []string) error {
			body, err := c.Delete("/api/templates/" + args[0])
			if err != nil {
				return err
			}
			PrintResponse(body)
			return nil
		},
	}
}

func templateUseCmd(c *Client) *cobra.Command {
	return &cobra.Command{
		Use:   "use [id]",
		Short: "使用模板 (增加使用次数)",
		Args:  cobra.ExactArgs(1),
		RunE: func(cmd *cobra.Command, args []string) error {
			body, err := c.PostJSON("/api/templates/"+args[0]+"/use", nil)
			if err != nil {
				return err
			}
			PrintResponse(body)
			return nil
		},
	}
}
