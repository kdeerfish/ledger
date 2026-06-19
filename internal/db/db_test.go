package db

import (
	"path/filepath"
	"testing"

	"github.com/stretchr/testify/assert"
	"github.com/stretchr/testify/require"
)

func TestOpen_CreatesDB(t *testing.T) {
	dir := t.TempDir()
	d, err := Open(filepath.Join(dir, "test.db"))
	require.NoError(t, err)
	defer d.Close()

	// Schema applied; we can query meta.
	var v string
	err = d.QueryRow(`SELECT value FROM meta WHERE key='db_version'`).Scan(&v)
	require.NoError(t, err)
	assert.Equal(t, "2", v)
}

func TestOpen_AppliesIdempotently(t *testing.T) {
	dir := t.TempDir()
	p := filepath.Join(dir, "test.db")
	d1, err := Open(p)
	require.NoError(t, err)
	d1.Close()
	d2, err := Open(p)
	require.NoError(t, err)
	d2.Close()
}

func TestOpen_TablesPresent(t *testing.T) {
	dir := t.TempDir()
	d, err := Open(filepath.Join(dir, "test.db"))
	require.NoError(t, err)
	defer d.Close()
	tables := []string{"meta", "transactions", "budgets", "budget_templates",
		"record_templates", "tags", "transaction_tags"}
	for _, tbl := range tables {
		var n int
		err := d.QueryRow(`SELECT COUNT(*) FROM sqlite_master WHERE type='table' AND name=?`, tbl).Scan(&n)
		require.NoError(t, err)
		assert.Equal(t, 1, n, "table %s missing", tbl)
	}
}

func TestOpen_IndexesCreated(t *testing.T) {
	dir := t.TempDir()
	d, err := Open(filepath.Join(dir, "test.db"))
	require.NoError(t, err)
	defer d.Close()
	idx := []string{"idx_trans_date", "idx_trans_category", "idx_trans_type"}
	for _, name := range idx {
		var n int
		err := d.QueryRow(`SELECT COUNT(*) FROM sqlite_master WHERE type='index' AND name=?`, name).Scan(&n)
		require.NoError(t, err)
		assert.GreaterOrEqual(t, n, 1, "index %s missing", name)
	}
}

func TestHasColumn(t *testing.T) {
	dir := t.TempDir()
	d, err := Open(filepath.Join(dir, "test.db"))
	require.NoError(t, err)
	defer d.Close()
	assert.True(t, hasColumn(d, "transactions", "is_deleted"))
	assert.True(t, hasColumn(d, "transactions", "amount"))
	assert.False(t, hasColumn(d, "transactions", "nonexistent"))
}
