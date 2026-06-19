//go:build e2e
// +build e2e

// Package e2e contains end-to-end tests that exercise the real HTTP server.
// Run with: go test -tags=e2e ./e2e/...
package e2e_test

import (
	"bytes"
	"encoding/json"
	"fmt"
	"net/http"
	"net/http/httptest"
	"os"
	"path/filepath"
	"strings"
	"testing"

	"github.com/kdeerfish/ledger/internal/config"
	"github.com/kdeerfish/ledger/internal/db"
	"github.com/kdeerfish/ledger/internal/httpapi"
	"github.com/kdeerfish/ledger/internal/repo"
	"github.com/kdeerfish/ledger/internal/service"
	"github.com/stretchr/testify/assert"
	"github.com/stretchr/testify/require"
)

func newE2EServer(t *testing.T) *httptest.Server {
	t.Helper()
	d, err := db.Open(filepath.Join(t.TempDir(), "e2e.db"))
	require.NoError(t, err)
	t.Cleanup(func() { _ = d.Close() })
	txRepo := repo.NewTransactionRepo(d)
	tagRepo := repo.NewTagRepo(d)
	budgetRepo := repo.NewBudgetRepo(d)
	btRepo := repo.NewBudgetTemplateRepo(d)
	rtRepo := repo.NewRecordTemplateRepo(d)
	tx := service.NewTransactionService(txRepo, tagRepo)
	tpl := service.NewTemplateService(rtRepo, tagRepo, tx)
	cfg := &config.Config{WebHost: "127.0.0.1", WebPort: 0, WebCorsOrigins: []string{"*"}}
	srv, err := httpapi.NewServerForTest(cfg, tx,
		service.NewBudgetService(budgetRepo, btRepo), tpl,
		service.NewTagService(tagRepo, txRepo))
	require.NoError(t, err)
	ts := httptest.NewServer(srv.Handler())
	t.Cleanup(ts.Close)
	return ts
}

func post(t *testing.T, url string, body any) (int, map[string]any) {
	t.Helper()
	buf, _ := json.Marshal(body)
	resp, err := http.Post(url, "application/json", bytes.NewReader(buf))
	require.NoError(t, err)
	defer resp.Body.Close()
	var out map[string]any
	require.NoError(t, json.NewDecoder(resp.Body).Decode(&out))
	return resp.StatusCode, out
}

func get(t *testing.T, url string) (int, map[string]any) {
	t.Helper()
	resp, err := http.Get(url)
	require.NoError(t, err)
	defer resp.Body.Close()
	var out map[string]any
	require.NoError(t, json.NewDecoder(resp.Body).Decode(&out))
	return resp.StatusCode, out
}

func TestE2E_HealthEndpoint(t *testing.T) {
	ts := newE2EServer(t)
	status, body := get(t, ts.URL+"/api/health")
	assert.Equal(t, http.StatusOK, status)
	assert.True(t, body["success"].(bool))
}

func TestE2E_AddListSummary(t *testing.T) {
	ts := newE2EServer(t)
	for i := 0; i < 5; i++ {
		// Vary category to avoid duplicate-detection false positives.
		status, _ := post(t, ts.URL+"/api/transactions", map[string]any{
			"type": "支出", "amount": 10 + float64(i), "category": fmt.Sprintf("类别-%d", i),
			"account": "微信", "trans_date": fmt.Sprintf("2026-06-19 1%d:00:00", i),
		})
		assert.Equal(t, http.StatusCreated, status, "add #%d failed", i)
	}
	// List
	status, body := get(t, ts.URL+"/api/transactions")
	assert.Equal(t, http.StatusOK, status)
	data := body["data"].(map[string]any)
	assert.Equal(t, float64(5), data["total"])
}

func TestE2E_TagsAttach(t *testing.T) {
	ts := newE2EServer(t)
	post(t, ts.URL+"/api/tags", map[string]any{"name": "测试", "color": "#fff"})
	post(t, ts.URL+"/api/transactions", map[string]any{
		"type": "支出", "amount": 5, "category": "食品", "trans_date": "2026-06-19 12:00:00",
		"tags": []string{"测试"},
	})
	_, body := get(t, ts.URL+"/api/tags")
	data := body["data"].(map[string]any)
	tags := data["tags"].([]any)
	assert.GreaterOrEqual(t, len(tags), 1)
}

func TestE2E_BudgetSetAndCheck(t *testing.T) {
	ts := newE2EServer(t)
	post(t, ts.URL+"/api/transactions", map[string]any{
		"type": "支出", "amount": 100, "category": "食品", "trans_date": "2026-06-15 12:00:00",
	})
	post(t, ts.URL+"/api/budgets", map[string]any{
		"category": "食品", "amount": 500, "year": 2026, "month": 6,
	})
	_, body := get(t, ts.URL+"/api/budgets/check?year=2026&month=6")
	data := body["data"].(map[string]any)
	checks := data["checks"].([]any)
	require.GreaterOrEqual(t, len(checks), 1)
	first := checks[0].(map[string]any)
	assert.InDelta(t, 100, first["spent"], 0.01)
}

func TestE2E_ExportCSV(t *testing.T) {
	ts := newE2EServer(t)
	post(t, ts.URL+"/api/transactions", map[string]any{
		"type": "支出", "amount": 5, "category": "测试类别", "trans_date": "2026-06-19 12:00:00",
	})
	resp, err := http.Get(ts.URL + "/api/export?format=csv")
	require.NoError(t, err)
	defer resp.Body.Close()
	tmp := make([]byte, 4096)
	var buf strings.Builder
	for {
		n, err := resp.Body.Read(tmp)
		if n > 0 {
			buf.Write(tmp[:n])
		}
		if err != nil {
			break
		}
	}
	assert.Contains(t, buf.String(), "id,type,amount")
	assert.Contains(t, buf.String(), "测试类别")
}

func TestE2E_InfoEndpoint(t *testing.T) {
	ts := newE2EServer(t)
	resp, err := http.Get(ts.URL + "/api/info")
	require.NoError(t, err)
	defer resp.Body.Close()
	tmp := make([]byte, 4096)
	var buf strings.Builder
	for {
		n, err := resp.Body.Read(tmp)
		if n > 0 {
			buf.Write(tmp[:n])
		}
		if err != nil {
			break
		}
	}
	t.Logf("info response: %s", buf.String())
	assert.Contains(t, buf.String(), "db_path")
}

func TestMain(m *testing.M) {
	os.Exit(m.Run())
}
