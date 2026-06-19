//go:build integration
// +build integration

// Package integration contains tests that exercise the full stack
// (db + repo + service) against a real, persisted SQLite file under
// t.TempDir(), but skip the HTTP layer (e2e does that).
//
// Run with: make test-integration
package integration_test

import (
	"bytes"
	"database/sql"
	"encoding/json"
	"path/filepath"
	"strings"
	"testing"

	"github.com/kdeerfish/ledger/internal/db"
	"github.com/kdeerfish/ledger/internal/domain"
	"github.com/kdeerfish/ledger/internal/repo"
	"github.com/kdeerfish/ledger/internal/service"
	"github.com/stretchr/testify/assert"
	"github.com/stretchr/testify/require"
)

// freshStack builds a complete app stack (db + repos + services) backed
// by a fresh SQLite file. Used by every integration test.
func freshStack(t *testing.T) *service.TransactionService {
	t.Helper()
	d, err := db.Open(filepath.Join(t.TempDir(), "integration.db"))
	require.NoError(t, err)
	t.Cleanup(func() { _ = d.Close() })
	txRepo := repo.NewTransactionRepo(d)
	tagRepo := repo.NewTagRepo(d)
	return service.NewTransactionService(txRepo, tagRepo)
}

func TestIntegration_DatabasePersistsAcrossConnections(t *testing.T) {
	dir := t.TempDir()
	path := filepath.Join(dir, "shared.db")

	// Connection 1: write.
	d1, err := db.Open(path)
	require.NoError(t, err)
	r1 := repo.NewTransactionRepo(d1)
	cat := "食品"
	id, err := r1.Insert(&domain.Transaction{
		Type: "支出", Amount: 30, Category: &cat, TransDate: "2026-06-19 12:00:00",
	})
	require.NoError(t, err)
	d1.Close()

	// Connection 2: read.
	d2, err := db.Open(path)
	require.NoError(t, err)
	defer d2.Close()
	r2 := repo.NewTransactionRepo(d2)
	got, err := r2.Get(id)
	require.NoError(t, err)
	assert.Equal(t, "食品", deref(got.Category))
	assert.InDelta(t, 30, got.Amount, 0.01)
}

func TestIntegration_MigrationRunsOnExistingDB(t *testing.T) {
	// Simulate an old v1 DB where every table is present EXCEPT the
	// is_deleted column on transactions, the tags column on
	// record_templates, and the three new indexes. This mirrors the
	// actual v0→v1→v2 state of the original Python project.
	dir := t.TempDir()
	path := filepath.Join(dir, "legacy.db")

	raw, err := sql.Open("sqlite", "file:"+path+"?_pragma=foreign_keys(1)")
	require.NoError(t, err)

	// Full v0 schema (no is_deleted, no idx_trans_*, no tags column).
	stmts := []string{
		`CREATE TABLE meta(key TEXT PRIMARY KEY, value TEXT NOT NULL)`,
		`INSERT INTO meta(key,value) VALUES('db_version','1')`,
		`CREATE TABLE transactions(
			id INTEGER PRIMARY KEY AUTOINCREMENT,
			type TEXT NOT NULL, amount REAL NOT NULL,
			category TEXT, subcategory TEXT, account TEXT,
			project TEXT, member TEXT, merchant TEXT, note TEXT,
			trans_date TEXT NOT NULL,
			created_at TEXT DEFAULT (datetime('now','localtime')))`,
		`INSERT INTO transactions(type, amount, category, trans_date) VALUES('支出', 10, '食品', '2026-06-19 12:00:00')`,
		`CREATE TABLE record_templates(
			id INTEGER PRIMARY KEY AUTOINCREMENT,
			name TEXT NOT NULL, description TEXT,
			template_type TEXT NOT NULL DEFAULT '通用',
			type TEXT, amount REAL DEFAULT 0,
			category TEXT, subcategory TEXT, account TEXT,
			project TEXT, member TEXT, merchant TEXT, note TEXT,
			usage_count INTEGER DEFAULT 0, last_used_at TEXT,
			created_at TEXT NOT NULL DEFAULT (datetime('now','localtime')))`,
	}
	for _, s := range stmts {
		_, err = raw.Exec(s)
		require.NoError(t, err)
	}
	require.NoError(t, raw.Close())

	// Reopen via the real path. Migrate should detect v1, apply v1
	// (add is_deleted + tags column + indexes), and bump db_version to 2.
	d, err := db.Open(path)
	require.NoError(t, err)
	defer d.Close()

	var v string
	require.NoError(t, d.QueryRow(`SELECT value FROM meta WHERE key='db_version'`).Scan(&v))
	assert.Equal(t, "2", v)

	// is_deleted column should now exist with default 0.
	var deleted int
	require.NoError(t, d.QueryRow(`SELECT is_deleted FROM transactions LIMIT 1`).Scan(&deleted))
	assert.Equal(t, 0, deleted)

	// New index should be present.
	var idxCount int
	require.NoError(t, d.QueryRow(`SELECT COUNT(*) FROM sqlite_master WHERE type='index' AND name='idx_trans_date'`).Scan(&idxCount))
	assert.Equal(t, 1, idxCount)
}

func TestIntegration_BulkInsertPerformance(t *testing.T) {
	if testing.Short() {
		t.Skip("bulk insert skipped in -short mode")
	}
	h := freshStack(t)
	const N = 5000
	for i := 0; i < N; i++ {
		cat := "食品"
		if i%2 == 0 {
			cat = "交通"
		}
		_, err := h.Add(service.AddInput{
			Type:      "支出",
			Amount:    float64(i%100) + 1,
			Category:  cat,
			Account:   "微信",
			TransDate: "2026-06-19 12:00:00",
			Force:     true,
		})
		require.NoError(t, err)
	}

	// Verify counts and stats round-trip.
	stats, err := h.Statistics("category", "", "", "")
	require.NoError(t, err)
	assert.Len(t, stats, 2)
	total := 0
	for _, s := range stats {
		total += s.Count
	}
	assert.Equal(t, N, total)
}

func TestIntegration_CSVImportRoundTrip(t *testing.T) {
	h := freshStack(t)
	csv := strings.NewReader(strings.Join([]string{
		"交易类型,金额,日期,类别,子类别,账户,项目,成员,商家,备注",
		"支出,12.5,2026/06/19 12:00,食品,午餐,微信,,,便利店,沙拉",
		"收入,8000,2026/06/01 09:00,工资,,银行卡,,,公司,月薪",
		"支出,8,2026/06/19 09:00,交通,地铁,支付宝,,,地铁站,通勤",
	}, "\n"))
	res, err := h.ImportCSV(csv)
	require.NoError(t, err)
	assert.Equal(t, 3, res.Imported)
	assert.Equal(t, 0, res.Skipped)

	sum, err := h.Summary("2026-06-01", "2026-06-30")
	require.NoError(t, err)
	assert.InDelta(t, 8000, sum.Income, 0.01)
	assert.InDelta(t, 20.5, sum.Expense, 0.01)
}

func TestIntegration_JSONExportIsValidJSON(t *testing.T) {
	h := freshStack(t)
	_, _ = h.Add(service.AddInput{
		Type: "支出", Amount: 5, Category: "测试", TransDate: "2026-06-19 12:00:00", Force: true,
	})
	var buf bytes.Buffer
	require.NoError(t, h.Export(domain.ListFilter{Limit: 10}, &buf, service.FormatJSON))
	var rows []domain.Transaction
	require.NoError(t, json.Unmarshal(buf.Bytes(), &rows))
	assert.Len(t, rows, 1)
	assert.Equal(t, "测试", deref(rows[0].Category))
}

func deref(p *string) string {
	if p == nil {
		return ""
	}
	return *p
}
