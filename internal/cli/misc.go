package cli

import (
	"fmt"
	"os"
	"strings"
	"time"

	"github.com/spf13/cobra"

	"github.com/kdeerfish/ledger/internal/domain"
)

// miscCmd groups the lower-frequency commands (search/filter/summary/etc).
func (a *App) miscCmd() *cobra.Command {
	cmd := &cobra.Command{Use: "misc", Short: "查询 / 统计 / 导入导出"}
	cmd.AddCommand(
		a.searchCmd(), a.filterCmd(), a.summaryCmd(), a.statsCmd(),
		a.importCmd(), a.exportCmd(), a.analyzeCmd(), a.reconcileCmd(),
		a.accountsCmd(), a.categoriesCmd(), a.membersCmd(),
	)
	return cmd
}

func (a *App) searchCmd() *cobra.Command {
	var keyword, stype string
	var limit int
	cmd := &cobra.Command{
		Use:   "search",
		Short: "关键词搜索",
		RunE: func(_ *cobra.Command, _ []string) error {
			rows, err := a.Tx.Search(keyword, stype, limit)
			if err != nil {
				return err
			}
			a.Print("搜索 %q 命中 %d 条:", keyword, len(rows))
			renderTxnTable(rows, a.Out)
			return nil
		},
	}
	f := cmd.Flags()
	f.StringVarP(&keyword, "keyword", "k", "", "关键词 (必填)")
	f.StringVar(&stype, "search-type", "all", "all/note/category/merchant")
	f.IntVarP(&limit, "limit", "l", 50, "限制条数")
	_ = cmd.MarkFlagRequired("keyword")
	return cmd
}

func (a *App) filterCmd() *cobra.Command {
	var f domain.ListFilter
	cmd := &cobra.Command{
		Use:   "filter",
		Short: "多维过滤",
		RunE: func(_ *cobra.Command, _ []string) error {
			rows, err := a.Tx.Filter(f)
			if err != nil {
				return err
			}
			renderTxnTable(rows, a.Out)
			return nil
		},
	}
	flags := cmd.Flags()
	flags.StringVar(&f.Category, "category", "", "类别")
	flags.StringVar(&f.Subcategory, "subcategory", "", "子类别")
	flags.StringVar(&f.Account, "account", "", "账户")
	flags.StringVar(&f.Project, "project", "", "项目")
	flags.StringVar(&f.Member, "member", "", "成员")
	flags.StringVar(&f.Merchant, "merchant", "", "商家")
	flags.StringVar(&f.StartDate, "start-date", "", "起始 YYYY-MM-DD")
	flags.StringVar(&f.EndDate, "end-date", "", "结束 YYYY-MM-DD")
	flags.IntVarP(&f.Limit, "limit", "l", 100, "限制条数")
	return cmd
}

func (a *App) summaryCmd() *cobra.Command {
	var year, month string
	cmd := &cobra.Command{
		Use:   "summary",
		Short: "月度汇总",
		RunE: func(_ *cobra.Command, _ []string) error {
			y, m, err := parseYearMonth(joinYM(year, month))
			if err != nil {
				return err
			}
			start := fmt.Sprintf("%04d-%02d-01", safeYear(y), safeMonth(m))
			end := fmt.Sprintf("%04d-%02d-31", safeYear(y), safeMonth(m))
			sum, err := a.Tx.Summary(start, end)
			if err != nil {
				return err
			}
			fmt.Fprintf(a.Out, "收入 ¥%.2f  支出 ¥%.2f  结余 ¥%.2f  笔数 %d\n",
				sum.Income, sum.Expense, sum.Balance, sum.Count)
			return nil
		},
	}
	cmd.Flags().StringVarP(&year, "year", "y", "", "年")
	cmd.Flags().StringVarP(&month, "month", "M", "", "月")
	return cmd
}

func safeYear(y int) int {
	if y == 0 {
		return time.Now().Year()
	}
	return y
}
func safeMonth(m int) int {
	if m == 0 {
		return int(time.Now().Month())
	}
	return m
}

func (a *App) statsCmd() *cobra.Command {
	var groupBy, subGroup, startDate, endDate string
	cmd := &cobra.Command{
		Use:   "stats",
		Short: "按维度统计",
		RunE: func(_ *cobra.Command, _ []string) error {
			rows, err := a.Tx.Statistics(groupBy, subGroup, startDate, endDate)
			if err != nil {
				return err
			}
			for _, r := range rows {
				fmt.Fprintf(a.Out, "%-20s  收 %.2f  支 %.2f  笔 %d\n",
					r.Group, r.Income, r.Expense, r.Count)
				for _, s := range r.Sub {
					fmt.Fprintf(a.Out, "  └─%-18s  收 %.2f  支 %.2f  笔 %d\n",
						s.Group, s.Income, s.Expense, s.Count)
				}
			}
			return nil
		},
	}
	f := cmd.Flags()
	f.StringVarP(&groupBy, "group-by", "g", "category", "category/account/project/member/merchant/month")
	f.StringVar(&subGroup, "sub-group", "", "二级分组")
	f.StringVar(&startDate, "start-date", "", "起始 YYYY-MM-DD")
	f.StringVar(&endDate, "end-date", "", "结束 YYYY-MM-DD")
	return cmd
}

func (a *App) importCmd() *cobra.Command {
	var file string
	cmd := &cobra.Command{
		Use:   "import",
		Short: "从 CSV 导入交易",
		RunE: func(_ *cobra.Command, _ []string) error {
			abs, err := pathAbs(file)
			if err != nil {
				return err
			}
			f, err := os.Open(abs)
			if err != nil {
				return err
			}
			defer f.Close()
			res, err := a.Tx.ImportCSV(f)
			if err != nil {
				return err
			}
			a.OK("导入完成: 成功 %d 条, 跳过 %d 条", res.Imported, res.Skipped)
			if len(res.Errors) > 0 {
				a.Print("错误明细:")
				for _, e := range res.Errors {
					a.Print("  - %s", e)
				}
			}
			return nil
		},
	}
	cmd.Flags().StringVarP(&file, "file", "f", "", "CSV 文件路径")
	_ = cmd.MarkFlagRequired("file")
	return cmd
}

func (a *App) exportCmd() *cobra.Command {
	var out, format, startDate, endDate, category string
	cmd := &cobra.Command{
		Use:   "export",
		Short: "导出 CSV / JSON",
		RunE: func(_ *cobra.Command, _ []string) error {
			if format == "" {
				format = "csv"
			}
			f := domain.ListFilter{StartDate: startDate, EndDate: endDate, Category: category, Limit: 100000}
			if err := a.exportData(f, out, format); err != nil {
				return err
			}
			a.OK("已导出到 %s", out)
			return nil
		},
	}
	flags := cmd.Flags()
	flags.StringVarP(&out, "output", "o", "", "输出文件")
	flags.StringVarP(&format, "format", "f", "csv", "csv|json")
	flags.StringVar(&startDate, "start-date", "", "起始 YYYY-MM-DD")
	flags.StringVar(&endDate, "end-date", "", "结束 YYYY-MM-DD")
	flags.StringVar(&category, "category", "", "按类别过滤")
	_ = cmd.MarkFlagRequired("output")
	return cmd
}

func (a *App) analyzeCmd() *cobra.Command {
	return &cobra.Command{
		Use:   "analyze",
		Short: "交叉统计分析报告",
		RunE: func(_ *cobra.Command, _ []string) error {
			sections, err := a.Tx.AnalyzeData()
			if err != nil {
				return err
			}
			for _, s := range sections {
				fmt.Fprintln(a.Out, s)
			}
			return nil
		},
	}
}

func (a *App) reconcileCmd() *cobra.Command {
	return &cobra.Command{
		Use:   "reconcile",
		Short: "对账指南",
		Run: func(_ *cobra.Command, _ []string) {
			fmt.Fprintln(a.Out, a.Tx.ReconcileGuide())
		},
	}
}

func (a *App) accountsCmd() *cobra.Command {
	return &cobra.Command{
		Use:   "accounts",
		Short: "所有账户",
		RunE: func(_ *cobra.Command, _ []string) error {
			xs, err := a.Tx.ListAccounts()
			if err != nil {
				return err
			}
			a.Print(strings.Join(xs, "\n"))
			return nil
		},
	}
}

func (a *App) categoriesCmd() *cobra.Command {
	return &cobra.Command{
		Use:   "categories",
		Short: "所有类别",
		RunE: func(_ *cobra.Command, _ []string) error {
			xs, err := a.Tx.ListCategories()
			if err != nil {
				return err
			}
			a.Print(strings.Join(xs, "\n"))
			return nil
		},
	}
}

func (a *App) membersCmd() *cobra.Command {
	return &cobra.Command{
		Use:   "members",
		Short: "所有成员",
		RunE: func(_ *cobra.Command, _ []string) error {
			xs, err := a.Tx.ListMembers()
			if err != nil {
				return err
			}
			a.Print(strings.Join(xs, "\n"))
			return nil
		},
	}
}
