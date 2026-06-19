package cli

import (
	"fmt"
	"strconv"

	"github.com/kdeerfish/ledger/internal/domain"
	"github.com/kdeerfish/ledger/internal/service"
	"github.com/spf13/cobra"
)

// AddInputFromCmd collects CLI flags into a service.AddInput.
func AddInputFromCmd(typ domain.TxnType, amount float64, date, category, subcategory,
	account, project, member, merchant, note string, force bool, tags []string,
) service.AddInput {
	return service.AddInput{
		Type: typ, Amount: amount, TransDate: date, Force: force, TagNames: tags,
		Category: category, Subcategory: subcategory, Account: account,
		Project: project, Member: member, Merchant: merchant, Note: note,
	}
}

// budgetCmd groups all budget operations.
func (a *App) budgetCmd() *cobra.Command {
	cmd := &cobra.Command{Use: "budget", Short: "预算管理"}
	cmd.AddCommand(
		a.budgetSetCmd(), a.budgetCheckCmd(), a.budgetListCmd(),
		a.budgetTplCreateCmd(), a.budgetTplListCmd(), a.budgetTplUpdateCmd(),
		a.budgetTplDeleteCmd(), a.budgetTplApplyCmd(), a.budgetTplSuggestCmd(),
	)
	return cmd
}

func (a *App) budgetSetCmd() *cobra.Command {
	var category, amount, year, month, dimType, dimVal string
	cmd := &cobra.Command{
		Use:   "set",
		Short: "设置(创建/更新)一笔预算",
		RunE: func(cmd *cobra.Command, _ []string) error {
			amt, err := parseFloat(amount)
			if err != nil {
				return err
			}
			y, m, err := parseYearMonth(joinYM(year, month))
			if err != nil {
				return err
			}
			if err := a.Budget.Set(service.SetInput{
				Category: category, Amount: amt, Year: y, Month: m,
				DimensionType: dimType, DimensionValue: dimVal,
			}); err != nil {
				a.Fail("设置失败: %v", err)
				return err
			}
			a.OK("预算已设置: %s ¥%.2f", category, amt)
			return nil
		},
	}
	f := cmd.Flags()
	f.StringVarP(&category, "category", "c", "", "类别 (必填)")
	f.StringVarP(&amount, "amount", "a", "", "金额 (必填)")
	f.StringVarP(&year, "year", "y", "", "年份 (默认今年)")
	f.StringVarP(&month, "month", "M", "", "月份 (默认本月)")
	f.StringVar(&dimType, "dimension-type", "category", "维度: category/account/member/project/merchant")
	f.StringVar(&dimVal, "dimension-value", "", "维度值")
	_ = cmd.MarkFlagRequired("category")
	_ = cmd.MarkFlagRequired("amount")
	return cmd
}

func (a *App) budgetCheckCmd() *cobra.Command {
	var year, month string
	cmd := &cobra.Command{
		Use:   "check",
		Short: "检查预算执行情况",
		RunE: func(cmd *cobra.Command, _ []string) error {
			y, m, err := parseYearMonth(joinYM(year, month))
			if err != nil {
				return err
			}
			checks, err := a.Budget.Check(y, m)
			if err != nil {
				return err
			}
			for _, c := range checks {
				fmt.Fprintf(a.Out, "%-12s 预算 ¥%.2f  已花 ¥%.2f  剩余 ¥%.2f  进度 %.1f%%\n",
					c.Category, c.Budget, c.Spent, c.Remaining, c.Percentage)
			}
			return nil
		},
	}
	cmd.Flags().StringVarP(&year, "year", "y", "", "年份")
	cmd.Flags().StringVarP(&month, "month", "M", "", "月份")
	return cmd
}

func (a *App) budgetListCmd() *cobra.Command {
	var year, month string
	cmd := &cobra.Command{
		Use:   "list",
		Short: "列出预算",
		RunE: func(cmd *cobra.Command, _ []string) error {
			y, m, err := parseYearMonth(joinYM(year, month))
			if err != nil {
				return err
			}
			bs, err := a.Budget.List(y, m)
			if err != nil {
				return err
			}
			for _, b := range bs {
				fmt.Fprintf(a.Out, "#%-4d  %-4d-%-2d  %-12s  ¥%.2f  dim=%s:%s\n",
					b.ID, b.Year, b.Month, b.Category, b.Amount, b.DimensionType, derefStr(b.DimensionValue))
			}
			return nil
		},
	}
	cmd.Flags().StringVarP(&year, "year", "y", "", "年份")
	cmd.Flags().StringVarP(&month, "month", "M", "", "月份")
	return cmd
}

func (a *App) budgetTplCreateCmd() *cobra.Command {
	var in service.CreateBudgetTemplateInput
	cmd := &cobra.Command{
		Use:   "template-create",
		Short: "创建预算模板",
		RunE: func(cmd *cobra.Command, _ []string) error {
			t, err := a.Budget.CreateBudgetTemplate(in)
			if err != nil {
				a.Fail("创建失败: %v", err)
				return err
			}
			a.OK("已创建预算模板 #%d: %s", t.ID, t.Name)
			return nil
		},
	}
	f := cmd.Flags()
	f.StringVar(&in.Name, "name", "未命名模板", "模板名")
	f.StringVar(&in.Description, "description", "", "描述")
	f.StringVar(&in.Category, "category", "", "类别")
	f.Float64Var(&in.Amount, "amount", 0, "金额")
	f.StringVar(&in.DimensionType, "dimension-type", "category", "维度")
	f.StringVar(&in.DimensionValue, "dimension-value", "", "维度值")
	f.StringVar(&in.Account, "account", "", "账户")
	f.StringVar(&in.Project, "project", "", "项目")
	f.StringVar(&in.Member, "member", "", "成员")
	f.StringVar(&in.Merchant, "merchant", "", "商家")
	f.StringVar(&in.Note, "note", "", "备注")
	return cmd
}

func (a *App) budgetTplListCmd() *cobra.Command {
	return &cobra.Command{
		Use:   "template-list",
		Short: "列出预算模板",
		RunE: func(cmd *cobra.Command, _ []string) error {
			ts, err := a.Budget.ListBudgetTemplates()
			if err != nil {
				return err
			}
			for _, t := range ts {
				fmt.Fprintf(a.Out, "#%-4d  %s  amount=%.2f  cat=%s\n",
					t.ID, t.Name, t.Amount, derefStr(t.Category))
			}
			return nil
		},
	}
}

func (a *App) budgetTplUpdateCmd() *cobra.Command {
	var id int64
	var fields []string
	cmd := &cobra.Command{
		Use:   "template-update",
		Short: "更新预算模板字段",
		RunE: func(cmd *cobra.Command, _ []string) error {
			m, err := parseKVFields(fields)
			if err != nil {
				return err
			}
			if err := a.Budget.UpdateBudgetTemplate(id, m); err != nil {
				a.Fail("更新失败: %v", err)
				return err
			}
			a.OK("已更新模板 #%d", id)
			return nil
		},
	}
	cmd.Flags().Int64Var(&id, "id", 0, "模板 ID")
	cmd.Flags().StringSliceVar(&fields, "set", nil, "字段更新 key=value,可多次使用")
	_ = cmd.MarkFlagRequired("id")
	return cmd
}

func (a *App) budgetTplDeleteCmd() *cobra.Command {
	var id int64
	cmd := &cobra.Command{
		Use:   "template-delete",
		Short: "删除预算模板",
		RunE: func(cmd *cobra.Command, _ []string) error {
			if err := a.Budget.DeleteBudgetTemplate(id); err != nil {
				return err
			}
			a.OK("已删除模板 #%d", id)
			return nil
		},
	}
	cmd.Flags().Int64Var(&id, "id", 0, "模板 ID")
	_ = cmd.MarkFlagRequired("id")
	return cmd
}

func (a *App) budgetTplApplyCmd() *cobra.Command {
	var id int64
	cmd := &cobra.Command{
		Use:   "template-apply",
		Short: "应用预算模板(生成一笔预算)",
		RunE: func(cmd *cobra.Command, _ []string) error {
			bs, err := a.Budget.ApplyBudgetTemplate(id)
			if err != nil {
				return err
			}
			for _, b := range bs {
				a.OK("已应用模板: %s ¥%.2f", b.Category, b.Amount)
			}
			return nil
		},
	}
	cmd.Flags().Int64Var(&id, "id", 0, "模板 ID")
	_ = cmd.MarkFlagRequired("id")
	return cmd
}

func (a *App) budgetTplSuggestCmd() *cobra.Command {
	var limit int
	cmd := &cobra.Command{
		Use:   "template-suggest",
		Short: "智能推荐预算模板",
		RunE: func(cmd *cobra.Command, _ []string) error {
			ts, err := a.Budget.SuggestBudgetTemplates(limit)
			if err != nil {
				return err
			}
			for _, t := range ts {
				fmt.Fprintf(a.Out, "%s (¥%.2f)\n", t.Name, t.Amount)
			}
			return nil
		},
	}
	cmd.Flags().IntVarP(&limit, "limit", "l", 3, "推荐条数")
	return cmd
}

// templateCmd groups record template operations.
func (a *App) templateCmd() *cobra.Command {
	cmd := &cobra.Command{Use: "template", Short: "记账模板"}
	cmd.AddCommand(
		a.tplCreateCmd(), a.tplListCmd(), a.tplUpdateCmd(),
		a.tplDeleteCmd(), a.tplApplyCmd(), a.tplSuggestCmd(),
	)
	return cmd
}

func (a *App) tplCreateCmd() *cobra.Command {
	var in service.CreateRecordTemplateInput
	var tags []string
	cmd := &cobra.Command{
		Use:   "create",
		Short: "创建记账模板",
		RunE: func(cmd *cobra.Command, _ []string) error {
			in.Tags = tags
			t, err := a.Template.CreateRecordTemplate(in)
			if err != nil {
				return err
			}
			a.OK("已创建模板 #%d: %s", t.ID, t.Name)
			return nil
		},
	}
	f := cmd.Flags()
	f.StringVar(&in.Name, "name", "", "模板名 (必填)")
	f.StringVar(&in.Description, "description", "", "描述")
	f.StringVar(&in.TemplateType, "type-mode", "通用", "模板类型: 通用|支出|收入")
	f.StringVar(&in.Type, "type", "", "交易类型")
	f.Float64Var(&in.Amount, "amount", 0, "金额")
	f.StringVar(&in.Category, "category", "", "类别")
	f.StringVar(&in.Subcategory, "subcategory", "", "子类别")
	f.StringVar(&in.Account, "account", "", "账户")
	f.StringVar(&in.Project, "project", "", "项目")
	f.StringVar(&in.Member, "member", "", "成员")
	f.StringVar(&in.Merchant, "merchant", "", "商家")
	f.StringVar(&in.Note, "note", "", "备注")
	f.StringSliceVar(&tags, "tag", nil, "标签(可多次)")
	_ = cmd.MarkFlagRequired("name")
	return cmd
}

func (a *App) tplListCmd() *cobra.Command {
	var typ string
	cmd := &cobra.Command{
		Use:   "list",
		Short: "列出记账模板",
		RunE: func(cmd *cobra.Command, _ []string) error {
			ts, err := a.Template.ListRecordTemplates(typ)
			if err != nil {
				return err
			}
			for _, t := range ts {
				fmt.Fprintf(a.Out, "#%-4d used=%-3d  %s  cat=%s  amt=%.2f\n",
					t.ID, t.UsageCount, t.Name, derefStr(t.Category), t.Amount)
			}
			return nil
		},
	}
	cmd.Flags().StringVar(&typ, "type-mode", "", "按模板类型过滤")
	return cmd
}

func (a *App) tplUpdateCmd() *cobra.Command {
	var id int64
	var fields []string
	cmd := &cobra.Command{
		Use:   "update",
		Short: "更新记账模板",
		RunE: func(cmd *cobra.Command, _ []string) error {
			m, err := parseKVFields(fields)
			if err != nil {
				return err
			}
			if err := a.Template.UpdateRecordTemplate(id, m); err != nil {
				return err
			}
			a.OK("已更新模板 #%d", id)
			return nil
		},
	}
	cmd.Flags().Int64Var(&id, "id", 0, "模板 ID")
	cmd.Flags().StringSliceVar(&fields, "set", nil, "字段更新 key=value")
	_ = cmd.MarkFlagRequired("id")
	return cmd
}

func (a *App) tplDeleteCmd() *cobra.Command {
	var id int64
	cmd := &cobra.Command{
		Use:   "delete",
		Short: "删除记账模板",
		RunE: func(cmd *cobra.Command, _ []string) error {
			if err := a.Template.DeleteRecordTemplate(id); err != nil {
				return err
			}
			a.OK("已删除模板 #%d", id)
			return nil
		},
	}
	cmd.Flags().Int64Var(&id, "id", 0, "模板 ID")
	_ = cmd.MarkFlagRequired("id")
	return cmd
}

func (a *App) tplApplyCmd() *cobra.Command {
	var id int64
	var amount string
	cmd := &cobra.Command{
		Use:   "apply",
		Short: "应用模板生成一笔交易",
		RunE: func(cmd *cobra.Command, _ []string) error {
			amt, err := parseFloat(amount)
			if err != nil {
				return err
			}
			t, err := a.Template.ApplyRecordTemplate(id, amt)
			if err != nil {
				return err
			}
			a.OK("已应用模板 #%d 生成交易 #%d", id, t.ID)
			return nil
		},
	}
	cmd.Flags().Int64Var(&id, "id", 0, "模板 ID")
	cmd.Flags().StringVarP(&amount, "amount", "a", "", "覆盖金额")
	_ = cmd.MarkFlagRequired("id")
	return cmd
}

func (a *App) tplSuggestCmd() *cobra.Command {
	var limit int
	cmd := &cobra.Command{
		Use:   "suggest",
		Short: "智能推荐模板(按使用频次)",
		RunE: func(cmd *cobra.Command, _ []string) error {
			ts, err := a.Template.SuggestRecordTemplates(limit)
			if err != nil {
				return err
			}
			for _, t := range ts {
				fmt.Fprintf(a.Out, "%s (使用 %d 次)\n", t.Name, t.UsageCount)
			}
			return nil
		},
	}
	cmd.Flags().IntVarP(&limit, "limit", "l", 3, "推荐条数")
	return cmd
}

func parseKVFields(kvs []string) (map[string]any, error) {
	out := make(map[string]any, len(kvs))
	for _, kv := range kvs {
		eq := -1
		for i, c := range kv {
			if c == '=' {
				eq = i
				break
			}
		}
		if eq < 0 {
			return nil, fmt.Errorf("invalid key=value: %q", kv)
		}
		k := kv[:eq]
		v := kv[eq+1:]
		// Try int / float for numeric fields.
		if n, err := strconv.Atoi(v); err == nil {
			out[k] = n
		} else if f, err := strconv.ParseFloat(v, 64); err == nil {
			out[k] = f
		} else {
			out[k] = v
		}
	}
	return out, nil
}

func joinYM(y, m string) string {
	if y == "" {
		return ""
	}
	if m == "" {
		return y
	}
	return y + "-" + m
}
