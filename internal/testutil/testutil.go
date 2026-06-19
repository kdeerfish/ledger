// Package testutil wires the in-memory equivalent of the Python project
// `tests/conftest.py` `temp_db` / `sample_db` fixtures. Every test that
// needs a real DB calls NewTestDB() to get an isolated SQLite file under
// t.TempDir().
package testutil

import (
	"path/filepath"
	"testing"

	"github.com/kdeerfish/ledger/internal/db"
	"github.com/kdeerfish/ledger/internal/repo"
	"github.com/kdeerfish/ledger/internal/service"
	"github.com/stretchr/testify/require"
)

// TestDB is the bag of dependencies every service test needs.
type TestDB struct {
	Tx       *service.TransactionService
	Budget   *service.BudgetService
	Template *service.TemplateService
	Tag      *service.TagService
	TxRepo   *repo.TransactionRepo
	TagRepo  *repo.TagRepo
	BdgRepo  *repo.BudgetRepo
}

// NewTestDB returns a fresh, fully migrated test database. The cleanup is
// handled by t.TempDir() and the deferred Close().
func NewTestDB(t *testing.T) *TestDB {
	t.Helper()
	d, err := db.Open(filepath.Join(t.TempDir(), "test.db"))
	require.NoError(t, err)
	t.Cleanup(func() { _ = d.Close() })
	txRepo := repo.NewTransactionRepo(d)
	tagRepo := repo.NewTagRepo(d)
	budgetRepo := repo.NewBudgetRepo(d)
	btRepo := repo.NewBudgetTemplateRepo(d)
	rtRepo := repo.NewRecordTemplateRepo(d)
	tx := service.NewTransactionService(txRepo, tagRepo)
	tpl := service.NewTemplateService(rtRepo, tagRepo, tx)
	return &TestDB{
		Tx:       tx,
		Budget:   service.NewBudgetService(budgetRepo, btRepo),
		Template: tpl,
		Tag:      service.NewTagService(tagRepo, txRepo),
		TxRepo:   txRepo,
		TagRepo:  tagRepo,
		BdgRepo:  budgetRepo,
	}
}

// SampleData seeds a few transactions covering the major use cases.
func SampleData(t *testing.T, h *TestDB) {
	t.Helper()
	now := "2026-06-19 12:00:00"
	_, err := h.Tx.Add(service.AddInput{
		Type: "支出", Amount: 25.5, Category: "食品", Account: "微信",
		Note: "午餐", TransDate: now, Force: true,
	})
	require.NoError(t, err)
	_, err = h.Tx.Add(service.AddInput{
		Type: "支出", Amount: 8, Category: "交通", Subcategory: "地铁",
		Account: "支付宝", TransDate: "2026-06-19 09:00:00", Force: true,
	})
	require.NoError(t, err)
	_, err = h.Tx.Add(service.AddInput{
		Type: "收入", Amount: 8000, Category: "工资", Account: "银行卡",
		TransDate: "2026-06-01 09:00:00", Force: true,
	})
	require.NoError(t, err)
	_, err = h.Tx.Add(service.AddInput{
		Type: "支出", Amount: 120, Category: "食品", Account: "微信",
		TransDate: "2026-06-15 19:00:00", Force: true,
	})
	require.NoError(t, err)
	_, err = h.Tx.Add(service.AddInput{
		Type: "支出", Amount: 50, Category: "娱乐", Account: "微信",
		Member: "我", TransDate: "2026-06-18 20:00:00", Force: true,
	})
	require.NoError(t, err)
}
