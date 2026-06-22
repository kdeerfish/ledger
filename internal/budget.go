package internal

import (
	"strconv"

	"github.com/spf13/cobra"
)

func BudgetCmd(c *Client) *cobra.Command {
	cmd := &cobra.Command{
		Use:   "budget",
		Short: "预算管理",
	}
	cmd.AddCommand(
		budgetSetCmd(c),
		budgetCheckCmd(c),
		budgetListCmd(c),
	)
	return cmd
}

func budgetSetCmd(c *Client) *cobra.Command {
	var category, amount, dimType, dimValue string
	var year, month int
	cmd := &cobra.Command{
		Use:   "set",
		Short: "设置预算",
		Example: `  ledger-cli budget set --category 食品酒水 --amount 2000 --year 2026 --month 6`,
		RunE: func(cmd *cobra.Command, args []string) error {
			data := map[string]any{
				"category": category,
				"amount":   amount,
				"year":     year,
				"month":    month,
			}
			if dimType != "" {
				data["dimension_type"] = dimType
			}
			if dimValue != "" {
				data["dimension_value"] = dimValue
			}
			body, err := c.PostJSON("/api/budgets", data)
			if err != nil {
				return err
			}
			PrintResponse(body)
			return nil
		},
	}
	f := cmd.Flags()
	f.StringVarP(&category, "category", "c", "", "类别 (必填)")
	f.StringVarP(&amount, "amount", "a", "", "金额 (必填)")
	f.IntVar(&year, "year", 0, "年份")
	f.IntVar(&month, "month", 0, "月份")
	f.StringVar(&dimType, "dim-type", "category", "维度类型: category/account/member/project/merchant")
	f.StringVar(&dimValue, "dim-value", "", "维度值")
	cmd.MarkFlagRequired("category")
	cmd.MarkFlagRequired("amount")
	return cmd
}

func budgetCheckCmd(c *Client) *cobra.Command {
	var year, month int
	cmd := &cobra.Command{
		Use:   "check",
		Short: "查看预算执行",
		RunE: func(cmd *cobra.Command, args []string) error {
			params := map[string]string{
				"year":  strconv.Itoa(year),
				"month": strconv.Itoa(month),
			}
			body, err := c.Get("/api/budgets/check", params)
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

func budgetListCmd(c *Client) *cobra.Command {
	var year, month int
	cmd := &cobra.Command{
		Use:   "list",
		Short: "预算列表",
		RunE: func(cmd *cobra.Command, args []string) error {
			params := map[string]string{
				"year":  strconv.Itoa(year),
				"month": strconv.Itoa(month),
			}
			body, err := c.Get("/api/budgets", params)
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
