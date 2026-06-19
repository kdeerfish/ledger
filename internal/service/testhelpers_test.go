package service_test

import (
	"testing"

	"github.com/kdeerfish/ledger/internal/service"
	"github.com/kdeerfish/ledger/internal/testutil"
)

// svc is a tiny wrapper around testutil.Fixture that pre-wires the four
// services every test uses. It exists to keep existing test bodies short
// (`svc.Tx.Add(...)` instead of `service.NewTransactionService(h.TxRepo, h.TagRepo).Add(...)`).
type svc struct {
	*testutil.Fixture
	Tx       *service.TransactionService
	Budget   *service.BudgetService
	Template *service.TemplateService
	Tag      *service.TagService
}

func newSvc(t *testing.T) *svc {
	t.Helper()
	f := testutil.NewTestDB(t)
	tx := service.NewTransactionService(f.TxRepo, f.TagRepo)
	return &svc{
		Fixture:  f,
		Tx:       tx,
		Budget:   service.NewBudgetService(f.BdgRepo, f.BTRepo),
		Template: service.NewTemplateService(f.RTRepo, f.TagRepo, tx),
		Tag:      service.NewTagService(f.TagRepo, f.TxRepo),
	}
}

// sampleData seeds the standard 5-row fixture into the Tx service.
func sampleData(t *testing.T, tx *service.TransactionService) {
	t.Helper()
	rows := []service.AddInput{
		{Type: "支出", Amount: 25.5, Category: "食品", Account: "微信", Note: "午餐", TransDate: "2026-06-19 12:00:00", Force: true},
		{Type: "支出", Amount: 8, Category: "交通", Subcategory: "地铁", Account: "支付宝", TransDate: "2026-06-19 09:00:00", Force: true},
		{Type: "收入", Amount: 8000, Category: "工资", Account: "银行卡", TransDate: "2026-06-01 09:00:00", Force: true},
		{Type: "支出", Amount: 120, Category: "食品", Account: "微信", TransDate: "2026-06-15 19:00:00", Force: true},
		{Type: "支出", Amount: 50, Category: "娱乐", Account: "微信", Member: "我", TransDate: "2026-06-18 20:00:00", Force: true},
	}
	for _, r := range rows {
		if _, err := tx.Add(r); err != nil {
			t.Fatalf("sampleData seed: %v", err)
		}
	}
}
