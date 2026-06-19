package repo_test

import (
	"path/filepath"
	"testing"

	"github.com/kdeerfish/ledger/internal/db"
	"github.com/kdeerfish/ledger/internal/domain"
	"github.com/kdeerfish/ledger/internal/repo"
	"github.com/stretchr/testify/assert"
	"github.com/stretchr/testify/require"
)

func newRepo(t *testing.T) (*repo.TransactionRepo, *repo.TagRepo) {
	t.Helper()
	d, err := db.Open(filepath.Join(t.TempDir(), "test.db"))
	require.NoError(t, err)
	t.Cleanup(func() { _ = d.Close() })
	return repo.NewTransactionRepo(d), repo.NewTagRepo(d)
}

func TestRepo_InsertAndGet(t *testing.T) {
	tx, _ := newRepo(t)
	cat := "食品"
	got, err := tx.Insert(&domain.Transaction{
		Type: "支出", Amount: 30, Category: &cat, TransDate: "2026-06-19 12:00:00",
	})
	require.NoError(t, err)
	t2, err := tx.Get(got)
	require.NoError(t, err)
	assert.Equal(t, "食品", deref(t2.Category))
}

func TestRepo_UpdateFields(t *testing.T) {
	tx, _ := newRepo(t)
	cat := "食品"
	id, _ := tx.Insert(&domain.Transaction{
		Type: "支出", Amount: 30, Category: &cat, TransDate: "2026-06-19 12:00:00",
	})
	require.NoError(t, tx.UpdateFields(id, map[string]any{"amount": 50.0, "category": "娱乐"}))
	got, _ := tx.Get(id)
	assert.InDelta(t, 50, got.Amount, 0.01)
	assert.Equal(t, "娱乐", deref(got.Category))
}

func TestRepo_UpdateFields_RejectsBogus(t *testing.T) {
	tx, _ := newRepo(t)
	cat := "食品"
	id, _ := tx.Insert(&domain.Transaction{
		Type: "支出", Amount: 30, Category: &cat, TransDate: "2026-06-19 12:00:00",
	})
	err := tx.UpdateFields(id, map[string]any{"is_deleted": 1})
	assert.Error(t, err)
}

func TestRepo_Duplicate(t *testing.T) {
	tx, _ := newRepo(t)
	cat := "食品"
	tx.Insert(&domain.Transaction{Type: "支出", Amount: 30, Category: &cat, TransDate: "2026-06-19 12:00:00"})
	id, err := tx.CheckDuplicate("2026-06-19 12:30:00", "支出", 30, "食品")
	require.NoError(t, err)
	assert.Greater(t, id, int64(0))
	id2, _ := tx.CheckDuplicate("2026-06-19 12:30:00", "支出", 999, "食品")
	assert.Equal(t, int64(0), id2)
}

func TestRepo_Distinct(t *testing.T) {
	tx, _ := newRepo(t)
	cat1, cat2 := "食品", "交通"
	tx.Insert(&domain.Transaction{Type: "支出", Amount: 10, Category: &cat1, TransDate: "2026-06-19 12:00:00"})
	tx.Insert(&domain.Transaction{Type: "支出", Amount: 20, Category: &cat2, TransDate: "2026-06-19 12:01:00"})
	tx.Insert(&domain.Transaction{Type: "支出", Amount: 30, Category: &cat1, TransDate: "2026-06-19 12:02:00"})
	vals, err := tx.DistinctValues("category", false)
	require.NoError(t, err)
	assert.ElementsMatch(t, []string{"食品", "交通"}, vals)
}

func TestTagRepo_Lifecycle(t *testing.T) {
	_, tag := newRepo(t)
	id, err := tag.Create("常用", "#fff")
	require.NoError(t, err)
	assert.Greater(t, id, int64(0))
	t2, err := tag.Get(id)
	require.NoError(t, err)
	assert.Equal(t, "常用", t2.Name)
	require.NoError(t, tag.Delete(id))
	_, err = tag.Get(id)
	assert.ErrorIs(t, err, domain.ErrNotFound)
}

func deref(p *string) string {
	if p == nil {
		return ""
	}
	return *p
}
