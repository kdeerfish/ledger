package cli

import (
	"fmt"
	"strings"

	"github.com/kdeerfish/ledger/internal/domain"
	"github.com/spf13/cobra"
)

// txCmd is the umbrella command grouping all transaction operations.
func (a *App) txCmd() *cobra.Command {
	cmd := &cobra.Command{
		Use:   "tx",
		Short: "交易管理(增删改查、搜索、过滤、统计)",
	}
	cmd.AddCommand(
		a.txAddCmd(), a.txListCmd(), a.txUpdateCmd(), a.txDeleteCmd(),
		a.txRestoreCmd(), a.txHardDeleteCmd(), a.txGetCmd(),
	)
	return cmd
}

func (a *App) txAddCmd() *cobra.Command {
	var (
		typ, amount, date, category, subcategory, account, project,
		member, merchant, note string
		tagList []string
		force   bool
	)
	cmd := &cobra.Command{
		Use:   "add",
		Short: "添加一笔交易",
		Example: `  ledger tx add --type 支出 --amount 25.5 --category 食品 --account 微信
  ledger tx add -t 收入 -a 8000 -c 工资 -A 银行卡 --tag 工资 --tag 月薪`,
		RunE: func(cmd *cobra.Command, _ []string) error {
			amt, err := parseFloat(amount)
			if err != nil {
				a.Fail("金额格式错误: %v", err)
				return err
			}
			if err := parseDate(date); err != nil {
				a.Fail("日期格式错误: %v", err)
				return err
			}
			t, err := a.Tx.Add(AddInputFromCmd(domain.TxnType(typ), amt, date,
				category, subcategory, account, project, member, merchant, note, force, tagList))
			if err != nil {
				if err == domain.ErrDuplicate {
					a.Fail("检测到重复交易,使用 --force 强制添加")
				} else {
					a.Fail("添加失败: %v", err)
				}
				return err
			}
			a.OK("已添加交易 #%d (¥%s)", t.ID, formatAmount(t.Amount))
			return nil
		},
	}
	f := cmd.Flags()
	f.StringVarP(&typ, "type", "t", "", "交易类型: 支出 | 收入")
	f.StringVarP(&amount, "amount", "a", "", "金额 (必填)")
	f.StringVarP(&date, "date", "d", "", "日期 YYYY-MM-DD 或 YYYY-MM-DD HH:MM:SS")
	f.StringVarP(&category, "category", "c", "", "类别")
	f.StringVar(&subcategory, "subcategory", "", "子类别")
	f.StringVarP(&account, "account", "A", "", "账户")
	f.StringVarP(&project, "project", "p", "", "项目")
	f.StringVarP(&member, "member", "m", "", "成员")
	f.StringVar(&merchant, "merchant", "", "商家")
	f.StringVarP(&note, "note", "n", "", "备注")
	f.StringSliceVar(&tagList, "tag", nil, "标签(可多次使用)")
	f.BoolVar(&force, "force", false, "强制添加,跳过重复检测")
	_ = cmd.MarkFlagRequired("type")
	_ = cmd.MarkFlagRequired("amount")
	return cmd
}

func (a *App) txListCmd() *cobra.Command {
	var limit int
	var includeDeleted bool
	cmd := &cobra.Command{
		Use:   "list",
		Short: "列出最近交易",
		RunE: func(cmd *cobra.Command, _ []string) error {
			rows, total, err := a.Tx.List(domain.ListFilter{Limit: limit, IncludeDeleted: includeDeleted})
			if err != nil {
				a.Fail("查询失败: %v", err)
				return err
			}
			a.Print("共 %d 条记录,显示前 %d 条:", total, len(rows))
			renderTxnTable(rows, a.Out)
			return nil
		},
	}
	cmd.Flags().IntVarP(&limit, "limit", "l", 20, "限制条数")
	cmd.Flags().BoolVar(&includeDeleted, "include-deleted", false, "包含已软删记录")
	return cmd
}

func (a *App) txGetCmd() *cobra.Command {
	var id int64
	cmd := &cobra.Command{
		Use:   "get",
		Short: "查询单条交易",
		RunE: func(cmd *cobra.Command, _ []string) error {
			t, err := a.Tx.Get(id)
			if err != nil {
				a.Fail("未找到 #%d", id)
				return err
			}
			renderTxnTable([]domain.Transaction{*t}, a.Out)
			return nil
		},
	}
	cmd.Flags().Int64Var(&id, "id", 0, "交易 ID")
	_ = cmd.MarkFlagRequired("id")
	return cmd
}

func (a *App) txUpdateCmd() *cobra.Command {
	var id int64
	var field, value string
	cmd := &cobra.Command{
		Use:   "update",
		Short: "更新单字段(白名单)",
		RunE: func(cmd *cobra.Command, _ []string) error {
			if err := a.Tx.Update(id, field, value); err != nil {
				a.Fail("更新失败: %v", err)
				return err
			}
			a.OK("已更新交易 #%d 的 %s", id, field)
			return nil
		},
	}
	cmd.Flags().Int64Var(&id, "id", 0, "交易 ID")
	cmd.Flags().StringVarP(&field, "field", "f", "", "字段(amount/category/subcategory/account/project/member/merchant/note/trans_date/type)")
	cmd.Flags().StringVarP(&value, "value", "v", "", "新值")
	_ = cmd.MarkFlagRequired("id")
	_ = cmd.MarkFlagRequired("field")
	_ = cmd.MarkFlagRequired("value")
	return cmd
}

func (a *App) txDeleteCmd() *cobra.Command {
	var id int64
	cmd := &cobra.Command{
		Use:   "delete",
		Short: "软删除一笔交易",
		RunE: func(cmd *cobra.Command, _ []string) error {
			if err := a.Tx.SoftDelete(id); err != nil {
				a.Fail("删除失败: %v", err)
				return err
			}
			a.OK("已软删除 #%d", id)
			return nil
		},
	}
	cmd.Flags().Int64Var(&id, "id", 0, "交易 ID")
	_ = cmd.MarkFlagRequired("id")
	return cmd
}

func (a *App) txRestoreCmd() *cobra.Command {
	var id int64
	cmd := &cobra.Command{
		Use:   "restore",
		Short: "恢复一笔已软删的交易",
		RunE: func(cmd *cobra.Command, _ []string) error {
			if err := a.Tx.Restore(id); err != nil {
				a.Fail("恢复失败: %v", err)
				return err
			}
			a.OK("已恢复 #%d", id)
			return nil
		},
	}
	cmd.Flags().Int64Var(&id, "id", 0, "交易 ID")
	_ = cmd.MarkFlagRequired("id")
	return cmd
}

func (a *App) txHardDeleteCmd() *cobra.Command {
	var id int64
	var confirm bool
	cmd := &cobra.Command{
		Use:   "hard-delete",
		Short: "永久删除一笔交易(需 --confirm)",
		RunE: func(cmd *cobra.Command, _ []string) error {
			if isNoConfirm(confirm) {
				a.Fail("请传 --confirm 以确认永久删除")
				return fmt.Errorf("missing --confirm")
			}
			if err := a.Tx.HardDelete(id); err != nil {
				a.Fail("删除失败: %v", err)
				return err
			}
			a.OK("已永久删除 #%d", id)
			return nil
		},
	}
	cmd.Flags().Int64Var(&id, "id", 0, "交易 ID")
	cmd.Flags().BoolVar(&confirm, "confirm", false, "确认永久删除")
	_ = cmd.MarkFlagRequired("id")
	return cmd
}

func renderTxnTable(rows []domain.Transaction, w interface{ Write(p []byte) (int, error) }) {
	for _, t := range rows {
		fmt.Fprintf(w, "#%-6d  %-3s  ¥%-10s  %-6s  %-12s  %-10s  %s  %s\n",
			t.ID, string(t.Type), formatAmount(t.Amount),
			derefStr(t.Category), derefStr(t.Subcategory),
			derefStr(t.Account), t.TransDate, derefStr(t.Note))
		if len(t.TagNames) > 0 {
			fmt.Fprintf(w, "        tags: %s\n", strings.Join(t.TagNames, ", "))
		}
	}
}

func formatAmount(v float64) string {
	return fmt.Sprintf("%.2f", v)
}
