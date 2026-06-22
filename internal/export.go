package internal

import "github.com/spf13/cobra"

func ExportCmd(c *Client) *cobra.Command {
	var format, category, startDate, endDate string
	cmd := &cobra.Command{
		Use:   "export",
		Short: "数据导出",
		Example: `  ledger-cli export --format json --category 食品酒水
  ledger-cli export --format csv --start-date 2026-01-01 --end-date 2026-06-30`,
		RunE: func(cmd *cobra.Command, args []string) error {
			params := map[string]string{
				"format":     format,
				"category":   category,
				"start_date": startDate,
				"end_date":   endDate,
			}
			body, err := c.Get("/api/export", params)
			if err != nil {
				return err
			}
			PrintResponse(body)
			return nil
		},
	}
	f := cmd.Flags()
	f.StringVar(&format, "format", "json", "格式: json/csv")
	f.StringVarP(&category, "category", "c", "", "类别筛选")
	f.StringVar(&startDate, "start-date", "", "开始日期")
	f.StringVar(&endDate, "end-date", "", "结束日期")
	return cmd
}
