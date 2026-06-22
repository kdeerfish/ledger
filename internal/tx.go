package internal

import (
	"fmt"
	"strconv"

	"github.com/spf13/cobra"
)

func TxCmd(c *Client) *cobra.Command {
	cmd := &cobra.Command{
		Use:   "tx",
		Short: "交易管理",
	}
	cmd.AddCommand(
		txAddCmd(c),
		txListCmd(c),
		txGetCmd(c),
		txSearchCmd(c),
		txUpdateCmd(c),
		txDeleteCmd(c),
		txRestoreCmd(c),
	)
	return cmd
}

// ─── tx add ───

func txAddCmd(c *Client) *cobra.Command {
	var (
		typ, amount, category, subcategory, account string
		project, member, merchant, note, date        string
		force                                        bool
	)
	cmd := &cobra.Command{
		Use:   "add",
		Short: "添加一笔交易",
		Example: `  ledger-cli tx add --amount 30 --category 食品酒水 --note 早餐
  ledger-cli tx add -a 5000 -t 收入 -c 工资 -A 招商银行`,
		RunE: func(cmd *cobra.Command, args []string) error {
			data := map[string]any{"amount": amount}
			if typ != "" {
				data["type"] = typ
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
			if date != "" {
				data["date"] = date
			}
			if force {
				data["force"] = true
			}
			body, err := c.PostJSON("/api/transactions", data)
			if err != nil {
				return err
			}
			PrintResponse(body)
			return nil
		},
	}
	f := cmd.Flags()
	f.StringVarP(&typ, "type", "t", "", "类型: 支出/收入")
	f.StringVarP(&amount, "amount", "a", "", "金额 (必填)")
	f.StringVarP(&category, "category", "c", "", "类别")
	f.StringVarP(&subcategory, "subcategory", "s", "", "子类别")
	f.StringVarP(&account, "account", "A", "", "账户")
	f.StringVarP(&project, "project", "p", "", "项目")
	f.StringVarP(&member, "member", "m", "", "成员")
	f.StringVarP(&merchant, "merchant", "M", "", "商家")
	f.StringVarP(&note, "note", "n", "", "备注")
	f.StringVarP(&date, "date", "d", "", "日期 (YYYY-MM-DD HH:MM:SS)")
	f.BoolVarP(&force, "force", "f", false, "跳过重复检查")
	cmd.MarkFlagRequired("amount")
	return cmd
}

// ─── tx list ───

func txListCmd(c *Client) *cobra.Command {
	var (
		typ, category, subcategory, account string
		project, member, merchant, keyword  string
		limit, offset                       int
		includeDeleted                      bool
	)
	cmd := &cobra.Command{
		Use:   "list",
		Short: "查看交易记录",
		Example: `  ledger-cli tx list --limit 10
  ledger-cli tx list --category 食品酒水 --account 微信零钱`,
		RunE: func(cmd *cobra.Command, args []string) error {
			params := map[string]string{
				"type": typ, "category": category, "subcategory": subcategory,
				"account": account, "project": project, "member": member,
				"merchant": merchant, "keyword": keyword,
				"limit": strconv.Itoa(limit), "offset": strconv.Itoa(offset),
			}
			if includeDeleted {
				params["include_deleted"] = "true"
			}
			body, err := c.Get("/api/transactions", params)
			if err != nil {
				return err
			}
			PrintResponse(body)
			return nil
		},
	}
	f := cmd.Flags()
	f.StringVarP(&typ, "type", "t", "", "类型筛选")
	f.StringVarP(&category, "category", "c", "", "类别筛选")
	f.StringVarP(&subcategory, "subcategory", "s", "", "子类别筛选")
	f.StringVarP(&account, "account", "A", "", "账户筛选")
	f.StringVarP(&project, "project", "p", "", "项目筛选")
	f.StringVarP(&member, "member", "m", "", "成员筛选")
	f.StringVarP(&merchant, "merchant", "M", "", "商家筛选")
	f.StringVarP(&keyword, "keyword", "k", "", "关键词")
	f.IntVarP(&limit, "limit", "l", 20, "返回条数")
	f.IntVar(&offset, "offset", 0, "偏移量")
	f.BoolVar(&includeDeleted, "include-deleted", false, "包含已删除")
	return cmd
}

// ─── tx get ───

func txGetCmd(c *Client) *cobra.Command {
	return &cobra.Command{
		Use:   "get [id]",
		Short: "查看单条交易",
		Args:  cobra.ExactArgs(1),
		RunE: func(cmd *cobra.Command, args []string) error {
			body, err := c.Get("/api/transactions/"+args[0], nil)
			if err != nil {
				return err
			}
			PrintResponse(body)
			return nil
		},
	}
}

// ─── tx search ───

func txSearchCmd(c *Client) *cobra.Command {
	var searchType string
	var limit int
	cmd := &cobra.Command{
		Use:   "search [keyword]",
		Short: "搜索交易",
		Args:  cobra.ExactArgs(1),
		Example: `  ledger-cli tx search 早餐
  ledger-cli tx search 拼多多 --search-type merchant`,
		RunE: func(cmd *cobra.Command, args []string) error {
			body, err := c.Get("/api/transactions/search", map[string]string{
				"keyword":     args[0],
				"search_type": searchType,
				"limit":       strconv.Itoa(limit),
			})
			if err != nil {
				return err
			}
			PrintResponse(body)
			return nil
		},
	}
	f := cmd.Flags()
	f.StringVar(&searchType, "search-type", "all", "搜索范围: all/note/category/merchant")
	f.IntVarP(&limit, "limit", "l", 20, "返回条数")
	return cmd
}

// ─── tx update ───

func txUpdateCmd(c *Client) *cobra.Command {
	var (
		field, value                                      string
		amount, category, subcategory, account            string
		project, member, merchant, note, transDate, typ   string
	)
	cmd := &cobra.Command{
		Use:   "update [id]",
		Short: "修改交易",
		Args:  cobra.ExactArgs(1),
		Example: `  ledger-cli tx update 42 --amount 50
  ledger-cli tx update 42 --field amount --value 50
  ledger-cli tx update 42 --category 餐饮 --note 修改备注`,
		RunE: func(cmd *cobra.Command, args []string) error {
			tid := args[0]
			// 单字段模式
			if field != "" && value != "" {
				body, err := c.PutJSON("/api/transactions/"+tid, map[string]string{
					"field": field, "value": value,
				})
				if err != nil {
					return err
				}
				PrintResponse(body)
				return nil
			}
			// 多字段模式
			data := map[string]any{}
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
			if transDate != "" {
				data["trans_date"] = transDate
			}
			if typ != "" {
				data["type"] = typ
			}
			if len(data) == 0 {
				return fmt.Errorf("请指定要修改的字段")
			}
			body, err := c.PutJSON("/api/transactions/"+tid, data)
			if err != nil {
				return err
			}
			PrintResponse(body)
			return nil
		},
	}
	f := cmd.Flags()
	f.StringVar(&field, "field", "", "字段名 (单字段模式)")
	f.StringVar(&value, "value", "", "字段值 (单字段模式)")
	f.StringVarP(&amount, "amount", "a", "", "金额")
	f.StringVarP(&category, "category", "c", "", "类别")
	f.StringVarP(&subcategory, "subcategory", "s", "", "子类别")
	f.StringVarP(&account, "account", "A", "", "账户")
	f.StringVarP(&project, "project", "p", "", "项目")
	f.StringVarP(&member, "member", "m", "", "成员")
	f.StringVarP(&merchant, "merchant", "M", "", "商家")
	f.StringVarP(&note, "note", "n", "", "备注")
	f.StringVar(&transDate, "date", "", "日期")
	f.StringVarP(&typ, "type", "t", "", "类型")
	return cmd
}

// ─── tx delete ───

func txDeleteCmd(c *Client) *cobra.Command {
	return &cobra.Command{
		Use:   "delete [id]",
		Short: "删除交易 (软删除)",
		Args:  cobra.ExactArgs(1),
		RunE: func(cmd *cobra.Command, args []string) error {
			body, err := c.Delete("/api/transactions/" + args[0])
			if err != nil {
				return err
			}
			PrintResponse(body)
			return nil
		},
	}
}

// ─── tx restore ───

func txRestoreCmd(c *Client) *cobra.Command {
	return &cobra.Command{
		Use:   "restore [id]",
		Short: "恢复已删除的交易",
		Args:  cobra.ExactArgs(1),
		RunE: func(cmd *cobra.Command, args []string) error {
			body, err := c.PostJSON("/api/transactions/"+args[0]+"/restore", nil)
			if err != nil {
				return err
			}
			PrintResponse(body)
			return nil
		},
	}
}
