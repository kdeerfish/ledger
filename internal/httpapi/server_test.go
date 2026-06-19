package httpapi_test

import (
	"bytes"
	"encoding/json"
	"net/http"
	"net/http/httptest"
	"path/filepath"
	"testing"

	"github.com/kdeerfish/ledger/internal/config"
	"github.com/kdeerfish/ledger/internal/db"
	"github.com/kdeerfish/ledger/internal/httpapi"
	"github.com/kdeerfish/ledger/internal/repo"
	"github.com/kdeerfish/ledger/internal/service"
	"github.com/stretchr/testify/assert"
	"github.com/stretchr/testify/require"
)

func newServer(t *testing.T) (*httptest.Server, *service.TransactionService) {
	t.Helper()
	d, err := db.Open(filepath.Join(t.TempDir(), "test.db"))
	require.NoError(t, err)
	t.Cleanup(func() { _ = d.Close() })
	txRepo := repo.NewTransactionRepo(d)
	tagRepo := repo.NewTagRepo(d)
	tx := service.NewTransactionService(txRepo, tagRepo)
	bdg := service.NewBudgetService(repo.NewBudgetRepo(d), repo.NewBudgetTemplateRepo(d))
	tpl := service.NewTemplateService(repo.NewRecordTemplateRepo(d), tagRepo, tx)
	tag := service.NewTagService(tagRepo, txRepo)
	cfg := &config.Config{WebHost: "127.0.0.1", WebPort: 0, WebCorsOrigins: []string{"*"}}
	srv, err := httpapi.NewServerForTest(cfg, tx, bdg, tpl, tag)
	require.NoError(t, err)
	ts := httptest.NewServer(srv.Handler())
	t.Cleanup(ts.Close)
	return ts, tx
}

// Helper to decode a success response.
func decodeOK(t *testing.T, resp *http.Response, into any) {
	t.Helper()
	defer resp.Body.Close()
	var env struct {
		Success bool            `json:"success"`
		Data    json.RawMessage `json:"data"`
		Error   string          `json:"error"`
	}
	require.NoError(t, json.NewDecoder(resp.Body).Decode(&env))
	assert.True(t, env.Success, "expected success, got error: %s", env.Error)
	if into != nil {
		require.NoError(t, json.Unmarshal(env.Data, into))
	}
}

func TestHTTP_Health(t *testing.T) {
	ts, _ := newServer(t)
	resp, err := http.Get(ts.URL + "/api/health")
	require.NoError(t, err)
	assert.Equal(t, http.StatusOK, resp.StatusCode)
	var body map[string]any
	decodeOK(t, resp, &body)
	assert.Equal(t, "ok", body["status"])
}

func TestHTTP_Transactions_RoundTrip(t *testing.T) {
	ts, _ := newServer(t)
	// POST a transaction.
	body := map[string]any{
		"type": "支出", "amount": 25.5, "category": "食品", "account": "微信",
		"trans_date": "2026-06-19 12:00:00",
	}
	buf := new(bytes.Buffer)
	_ = json.NewEncoder(buf).Encode(body)
	resp, err := http.Post(ts.URL+"/api/transactions", "application/json", buf)
	require.NoError(t, err)
	assert.Equal(t, http.StatusCreated, resp.StatusCode)
	var created struct{ ID int64 `json:"id"` }
	decodeOK(t, resp, &created)
	assert.Greater(t, created.ID, int64(0))

	// GET list.
	resp2, err := http.Get(ts.URL + "/api/transactions")
	require.NoError(t, err)
	assert.Equal(t, http.StatusOK, resp2.StatusCode)
	var list struct {
		Total        int `json:"total"`
		Transactions []map[string]any
	}
	decodeOK(t, resp2, &list)
	assert.Equal(t, 1, list.Total)
}

func TestHTTP_BadJSON_Returns400(t *testing.T) {
	ts, _ := newServer(t)
	resp, err := http.Post(ts.URL+"/api/transactions", "application/json", bytes.NewBufferString("{not json"))
	require.NoError(t, err)
	assert.Equal(t, http.StatusBadRequest, resp.StatusCode)
}

func TestHTTP_NotFound(t *testing.T) {
	ts, _ := newServer(t)
	resp, err := http.Get(ts.URL + "/api/transactions/9999")
	require.NoError(t, err)
	assert.Equal(t, http.StatusNotFound, resp.StatusCode)
}
