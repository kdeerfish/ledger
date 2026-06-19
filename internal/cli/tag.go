package cli

import (
	"github.com/kdeerfish/ledger/internal/service"
	"github.com/spf13/cobra"
)

// tagCmd groups tag CRUD operations.
func (a *App) tagCmd() *cobra.Command {
	cmd := &cobra.Command{Use: "tag", Short: "标签管理"}
	cmd.AddCommand(a.tagListCmd(), a.tagCreateCmd(), a.tagDeleteCmd())
	return cmd
}

func (a *App) tagListCmd() *cobra.Command {
	return &cobra.Command{
		Use:   "list",
		Short: "列出所有标签",
		RunE: func(_ *cobra.Command, _ []string) error {
			tags, err := a.Tag.List()
			if err != nil {
				return err
			}
			for _, t := range tags {
				a.Print("#%-4d  %-20s  %s  使用 %d", t.ID, t.Name, t.Color, t.UsageCount)
			}
			return nil
		},
	}
}

func (a *App) tagCreateCmd() *cobra.Command {
	var name, color string
	cmd := &cobra.Command{
		Use:   "create",
		Short: "创建标签",
		RunE: func(_ *cobra.Command, _ []string) error {
			id, err := a.Tag.Create(name, color)
			if err != nil {
				return err
			}
			a.OK("已创建标签 #%d: %s", id, name)
			return nil
		},
	}
	cmd.Flags().StringVar(&name, "name", "", "标签名 (必填)")
	cmd.Flags().StringVar(&color, "color", "#6366f1", "颜色 hex")
	_ = cmd.MarkFlagRequired("name")
	return cmd
}

func (a *App) tagDeleteCmd() *cobra.Command {
	var id int64
	cmd := &cobra.Command{
		Use:   "delete",
		Short: "删除标签",
		RunE: func(_ *cobra.Command, _ []string) error {
			if err := a.Tag.Delete(id); err != nil {
				return err
			}
			a.OK("已删除标签 #%d", id)
			return nil
		},
	}
	cmd.Flags().Int64Var(&id, "id", 0, "标签 ID")
	_ = cmd.MarkFlagRequired("id")
	return cmd
}

// importCSVFn is re-exported from service to keep public surface clean.
var _ service.ExportFormat
