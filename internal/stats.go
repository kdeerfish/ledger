package internal

import (
	"strconv"

	"github.com/spf13/cobra"
)

func StatsCmd(c *Client) *cobra.Command {
	cmd := &cobra.Command{
		Use:   "stats",
		Short: "统计查询",
	}
	cmd.AddCommand(
		summaryCmd(c),
		groupStatsCmd(c),
		trendsCmd(c),
	)
	return cmd
}

// ─── summary ───

func summaryCmd(c *Client) *cobra.Command {
	var year, month int
	cmd := &cobra.Command{
		Use:   "summary",
		Short: "收支汇总",
		Example: `  ledger-cli stats summary --year 2026 --month 6`,
		RunE: func(cmd *cobra.Command, args []string) error {
			params := map[string]string{
				"year":  strconv.Itoa(year),
				"month": strconv.Itoa(month),
			}
			body, err := c.Get("/api/summary", params)
			if err != nil {
				return err
			}
			PrintResponse(body)
			return nil
		},
	}
	f := cmd.Flags()
	f.IntVar(&year, "year", 0, "年份")
	f.IntVar(&month, "month", 0, "月份")
	return cmd
}

// ─── group stats ───

func groupStatsCmd(c *Client) *cobra.Command {
	var groupBy, subGroup string
	var year, month int
	cmd := &cobra.Command{
		Use:   "group",
		Short: "分组统计",
		Example: `  ledger-cli stats group --by category --year 2026 --month 6
  ledger-cli stats group --by account --year 2026`,
		RunE: func(cmd *cobra.Command, args []string) error {
			params := map[string]string{
				"group_by":  groupBy,
				"sub_group": subGroup,
				"year":      strconv.Itoa(year),
				"month":     strconv.Itoa(month),
			}
			body, err := c.Get("/api/stats", params)
			if err != nil {
				return err
			}
			PrintResponse(body)
			return nil
		},
	}
	f := cmd.Flags()
	f.StringVar(&groupBy, "by", "category", "分组维度: category/subcategory/account/merchant/project/member/month/tag/type")
	f.StringVar(&subGroup, "sub-group", "", "二级分组 (如 subcategory)")
	f.IntVar(&year, "year", 0, "年份")
	f.IntVar(&month, "month", 0, "月份")
	return cmd
}

// ─── trends ───

func trendsCmd(c *Client) *cobra.Command {
	var year int
	var granularity string
	cmd := &cobra.Command{
		Use:   "trends",
		Short: "趋势分析",
		Example: `  ledger-cli stats trends --year 2026 --granularity month`,
		RunE: func(cmd *cobra.Command, args []string) error {
			params := map[string]string{
				"year":        strconv.Itoa(year),
				"granularity": granularity,
			}
			body, err := c.Get("/api/trends", params)
			if err != nil {
				return err
			}
			PrintResponse(body)
			return nil
		},
	}
	f := cmd.Flags()
	f.IntVar(&year, "year", 0, "年份")
	f.StringVar(&granularity, "granularity", "month", "粒度: day/week/month")
	return cmd
}
