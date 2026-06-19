// Package httpapi wires the chi router and serves both the JSON API and the
// embedded React SPA.
package httpapi

import (
	"encoding/json"
	"errors"
	"fmt"
	"io/fs"
	"log/slog"
	"net/http"
	"strconv"
	"strings"
	"time"

	"github.com/go-chi/chi/v5"
	"github.com/go-chi/chi/v5/middleware"

	"github.com/kdeerfish/ledger/internal/config"
	"github.com/kdeerfish/ledger/internal/domain"
	"github.com/kdeerfish/ledger/internal/service"
	"github.com/kdeerfish/ledger/internal/version"
)

// Server is the HTTP application surface. Use NewServer to construct.
type Server struct {
	cfg *config.Config
	srv *http.Server
	r   *chi.Mux
	log *slog.Logger
	tx  *service.TransactionService
	bdg *service.BudgetService
	tpl *service.TemplateService
	tag *service.TagService
}

// FS is populated in main.go by calling SetFS(). It defaults to nil so
// API-only builds (and tests) can omit the embedded SPA. When nil,
// handleSPA returns 404 for non-/api routes.
var FS fs.FS

// SetFS wires the embedded SPA into the handler. main.go calls this during
// startup; tests typically leave FS nil.
func SetFS(f fs.FS) { FS = f }

// NewServer builds an HTTP server. dist is the embed.FS root (may be nil for
// API-only deployments, e.g. tests).
func NewServer(cfg *config.Config, tx *service.TransactionService,
	bdg *service.BudgetService, tpl *service.TemplateService, tag *service.TagService,
) (*Server, error) {
	if cfg == nil {
		return nil, errors.New("nil config")
	}
	s := &Server{cfg: cfg, tx: tx, bdg: bdg, tpl: tpl, tag: tag, log: slog.Default()}
	s.r = s.buildRouter()
	s.srv = &http.Server{
		Addr:              fmt.Sprintf("%s:%d", cfg.WebHost, cfg.WebPort),
		Handler:           s.r,
		ReadHeaderTimeout: 10 * time.Second,
		ReadTimeout:       30 * time.Second,
		WriteTimeout:      30 * time.Second,
		IdleTimeout:       120 * time.Second,
	}
	return s, nil
}

// NewServerForTest is a thin wrapper used by external test packages. Kept
// here so we don't break the public NewServer signature.
func NewServerForTest(cfg *config.Config, tx *service.TransactionService,
	bdg *service.BudgetService, tpl *service.TemplateService, tag *service.TagService,
) (*Server, error) {
	return NewServer(cfg, tx, bdg, tpl, tag)
}

// Run blocks until the server stops. Use Start/Stop for tests.
func (s *Server) Run() error {
	s.log.Info("listening", "addr", s.srv.Addr, "db", s.cfg.DBPath)
	if err := s.srv.ListenAndServe(); err != nil && !errors.Is(err, http.ErrServerClosed) {
		return err
	}
	return nil
}

// Start launches ListenAndServe in a goroutine; returns when the listener is
// ready. Used by e2e tests.
func (s *Server) Start() (string, error) {
	ln, err := newListener(s.cfg.WebHost, s.cfg.WebPort)
	if err != nil {
		return "", err
	}
	// The http.Server doesn't expose the bound port when Port was 0; we use
	// the listener's address to construct the URL.
	go func() { _ = s.srv.Serve(ln) }()
	return ln.Addr().String(), nil
}

// Stop performs a graceful shutdown.
func (s *Server) Stop() error {
	return s.srv.Close()
}

// Handler exposes the underlying chi router for httptest.
func (s *Server) Handler() http.Handler { return s.r }

func (s *Server) buildRouter() *chi.Mux {
	r := chi.NewRouter()
	r.Use(middleware.RealIP)
	r.Use(middleware.RequestID)
	r.Use(middleware.Recoverer)
	r.Use(s.corsMiddleware)
	r.Use(s.loggingMiddleware)
	if s.cfg.WebDebug {
		r.Use(middleware.NoCache)
	}
	r.Route("/api", func(r chi.Router) {
		r.Get("/health", s.handleHealth)
		r.Get("/info", s.handleInfo)
		// Transactions
		r.Get("/transactions", s.handleListTx)
		r.Post("/transactions", s.handleAddTx)
		r.Get("/transactions/search", s.handleSearch)
		r.Get("/transactions/{id}", s.handleGetTx)
		r.Put("/transactions/{id}", s.handleUpdateTx)
		r.Delete("/transactions/{id}", s.handleDeleteTx)
		r.Post("/transactions/{id}/restore", s.handleRestoreTx)
		r.Get("/transactions/{id}/hard-delete", s.handleHardDeleteTx) // GET so it works without form body; CLI uses POST internally
		// Tags
		r.Get("/tags", s.handleListTags)
		r.Post("/tags", s.handleCreateTag)
		r.Delete("/tags/{id}", s.handleDeleteTag)
		r.Get("/tags/{id}/transactions", s.handleTagTx)
		// Templates
		r.Get("/templates", s.handleListTpl)
		r.Post("/templates", s.handleCreateTpl)
		r.Put("/templates/{id}", s.handleUpdateTpl)
		r.Delete("/templates/{id}", s.handleDeleteTpl)
		r.Post("/templates/{id}/use", s.handleUseTpl)
		// Suggestions
		r.Get("/suggestions", s.handleSuggestions)
		// Aggregates
		r.Get("/summary", s.handleSummary)
		r.Get("/stats", s.handleStats)
		// Distinct
		r.Get("/accounts", s.handleAccounts)
		r.Get("/categories", s.handleCategories)
		r.Get("/members", s.handleMembers)
		// Budgets
		r.Get("/budgets", s.handleListBudgets)
		r.Post("/budgets", s.handleSetBudget)
		r.Get("/budgets/check", s.handleCheckBudget)
		// Export / analyze
		r.Get("/export", s.handleExport)
		r.Get("/analyze", s.handleAnalyze)
	})
	// Static / SPA fallback
	r.HandleFunc("/*", s.handleSPA)
	return r
}

// ─── Response helpers ────────────────────────────────────────────────────────

type apiResponse struct {
	Success bool   `json:"success"`
	Data    any    `json:"data,omitempty"`
	Error   string `json:"error,omitempty"`
}

func writeJSON(w http.ResponseWriter, status int, payload any) {
	w.Header().Set("Content-Type", "application/json; charset=utf-8")
	w.WriteHeader(status)
	_ = json.NewEncoder(w).Encode(payload)
}

func writeOK(w http.ResponseWriter, data any) {
	writeJSON(w, http.StatusOK, apiResponse{Success: true, Data: data})
}

func writeErr(w http.ResponseWriter, status int, err error) {
	msg := ""
	if err != nil {
		msg = err.Error()
	}
	writeJSON(w, status, apiResponse{Success: false, Error: msg})
}

// mapDomainError returns the HTTP status for a domain sentinel error.
func mapDomainError(err error) int {
	switch {
	case errors.Is(err, domain.ErrNotFound):
		return http.StatusNotFound
	case errors.Is(err, domain.ErrInvalidInput), errors.Is(err, domain.ErrInvalidField), errors.Is(err, domain.ErrNoUpdateField):
		return http.StatusBadRequest
	case errors.Is(err, domain.ErrDuplicate):
		return http.StatusConflict
	default:
		return http.StatusInternalServerError
	}
}

// ─── Middleware ──────────────────────────────────────────────────────────────

func (s *Server) corsMiddleware(next http.Handler) http.Handler {
	return http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		origin := "*"
		if len(s.cfg.WebCorsOrigins) > 0 {
			origin = strings.Join(s.cfg.WebCorsOrigins, ",")
		}
		w.Header().Set("Access-Control-Allow-Origin", origin)
		w.Header().Set("Access-Control-Allow-Methods", "GET, POST, PUT, DELETE, OPTIONS")
		w.Header().Set("Access-Control-Allow-Headers", "Content-Type, X-Request-ID")
		if r.Method == http.MethodOptions {
			w.WriteHeader(http.StatusNoContent)
			return
		}
		next.ServeHTTP(w, r)
	})
}

func (s *Server) loggingMiddleware(next http.Handler) http.Handler {
	return http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		ww := middleware.NewWrapResponseWriter(w, r.ProtoMajor)
		start := time.Now()
		next.ServeHTTP(ww, r)
		s.log.Debug("http",
			"method", r.Method, "path", r.URL.Path,
			"status", ww.Status(), "bytes", ww.BytesWritten(),
			"dur_ms", time.Since(start).Milliseconds(),
		)
	})
}

// ─── Handlers ────────────────────────────────────────────────────────────────

func (s *Server) handleHealth(w http.ResponseWriter, r *http.Request) {
	info := version.Get()
	writeOK(w, map[string]any{
		"status":  "ok",
		"db_path": s.cfg.DBPath,
		"version": info.Version,
	})
}

func (s *Server) handleInfo(w http.ResponseWriter, r *http.Request) {
	info, err := s.tx.Info()
	if err != nil {
		writeErr(w, http.StatusInternalServerError, err)
		return
	}
	info.DBPath = s.cfg.DBPath
	writeOK(w, info)
}

// ─── Transactions ────────────────────────────────────────────────────────────

func (s *Server) handleListTx(w http.ResponseWriter, r *http.Request) {
	f, err := parseListFilter(r)
	if err != nil {
		writeErr(w, http.StatusBadRequest, err)
		return
	}
	rows, total, err := s.tx.List(f)
	if err != nil {
		writeErr(w, http.StatusInternalServerError, err)
		return
	}
	writeOK(w, map[string]any{"transactions": rows, "total": total})
}

func (s *Server) handleAddTx(w http.ResponseWriter, r *http.Request) {
	var body struct {
		Type        string   `json:"type"`
		Amount      float64  `json:"amount"`
		Category    string   `json:"category"`
		Subcategory string   `json:"subcategory"`
		Account     string   `json:"account"`
		Project     string   `json:"project"`
		Member      string   `json:"member"`
		Merchant    string   `json:"merchant"`
		Note        string   `json:"note"`
		TransDate   string   `json:"trans_date"`
		Tags        []string `json:"tags"`
		Force       bool     `json:"force"`
	}
	if err := json.NewDecoder(r.Body).Decode(&body); err != nil {
		writeErr(w, http.StatusBadRequest, err)
		return
	}
	t, err := s.tx.Add(service.AddInput{
		Type:        domain.TxnType(body.Type),
		Amount:      body.Amount,
		Category:    body.Category,
		Subcategory: body.Subcategory,
		Account:     body.Account,
		Project:     body.Project,
		Member:      body.Member,
		Merchant:    body.Merchant,
		Note:        body.Note,
		TransDate:   body.TransDate,
		TagNames:    body.Tags,
		Force:       body.Force,
	})
	if err != nil {
		writeErr(w, mapDomainError(err), err)
		return
	}
	writeJSON(w, http.StatusCreated, apiResponse{Success: true, Data: t})
}

func (s *Server) handleGetTx(w http.ResponseWriter, r *http.Request) {
	id, err := strconv.ParseInt(chi.URLParam(r, "id"), 10, 64)
	if err != nil {
		writeErr(w, http.StatusBadRequest, err)
		return
	}
	t, err := s.tx.Get(id)
	if err != nil {
		writeErr(w, mapDomainError(err), err)
		return
	}
	writeOK(w, t)
}

func (s *Server) handleUpdateTx(w http.ResponseWriter, r *http.Request) {
	id, err := strconv.ParseInt(chi.URLParam(r, "id"), 10, 64)
	if err != nil {
		writeErr(w, http.StatusBadRequest, err)
		return
	}
	var body map[string]any
	if err := json.NewDecoder(r.Body).Decode(&body); err != nil {
		writeErr(w, http.StatusBadRequest, err)
		return
	}
	if err := s.tx.Repo.UpdateFields(id, body); err != nil {
		writeErr(w, mapDomainError(err), err)
		return
	}
	writeOK(w, map[string]any{"id": id})
}

func (s *Server) handleDeleteTx(w http.ResponseWriter, r *http.Request) {
	id, err := strconv.ParseInt(chi.URLParam(r, "id"), 10, 64)
	if err != nil {
		writeErr(w, http.StatusBadRequest, err)
		return
	}
	if err := s.tx.SoftDelete(id); err != nil {
		writeErr(w, mapDomainError(err), err)
		return
	}
	writeOK(w, map[string]any{"id": id, "deleted": true})
}

func (s *Server) handleRestoreTx(w http.ResponseWriter, r *http.Request) {
	id, err := strconv.ParseInt(chi.URLParam(r, "id"), 10, 64)
	if err != nil {
		writeErr(w, http.StatusBadRequest, err)
		return
	}
	if err := s.tx.Restore(id); err != nil {
		writeErr(w, mapDomainError(err), err)
		return
	}
	writeOK(w, map[string]any{"id": id, "restored": true})
}

func (s *Server) handleHardDeleteTx(w http.ResponseWriter, r *http.Request) {
	id, err := strconv.ParseInt(chi.URLParam(r, "id"), 10, 64)
	if err != nil {
		writeErr(w, http.StatusBadRequest, err)
		return
	}
	confirm := r.URL.Query().Get("confirm") == "true"
	if !confirm {
		writeErr(w, http.StatusBadRequest, errors.New("missing confirm=true"))
		return
	}
	if err := s.tx.HardDelete(id); err != nil {
		writeErr(w, mapDomainError(err), err)
		return
	}
	writeOK(w, map[string]any{"id": id, "deleted": "hard"})
}

func (s *Server) handleSearch(w http.ResponseWriter, r *http.Request) {
	q := r.URL.Query()
	keyword := q.Get("keyword")
	limit := atoiDefault(q.Get("limit"), 50)
	rows, err := s.tx.Search(keyword, q.Get("search_type"), limit)
	if err != nil {
		writeErr(w, http.StatusInternalServerError, err)
		return
	}
	writeOK(w, map[string]any{"transactions": rows, "total": len(rows)})
}

func parseListFilter(r *http.Request) (domain.ListFilter, error) {
	q := r.URL.Query()
	f := domain.ListFilter{
		Limit:          atoiDefault(q.Get("limit"), 50),
		Offset:         atoiDefault(q.Get("offset"), 0),
		IncludeDeleted: q.Get("include_deleted") == "true" || q.Get("include_deleted") == "1",
		Type:           domain.TxnType(q.Get("type")),
		Category:       q.Get("category"),
		Subcategory:    q.Get("subcategory"),
		Account:        q.Get("account"),
		Project:        q.Get("project"),
		Member:         q.Get("member"),
		Merchant:       q.Get("merchant"),
		Keyword:        q.Get("keyword"),
		StartDate:      q.Get("start_date"),
		EndDate:        q.Get("end_date"),
		Year:           atoiDefault(q.Get("year"), 0),
		Month:          atoiDefault(q.Get("month"), 0),
		SearchType:     q.Get("search_type"),
	}
	if tids := q.Get("tag_ids"); tids != "" {
		for _, p := range strings.Split(tids, ",") {
			if id, err := strconv.ParseInt(strings.TrimSpace(p), 10, 64); err == nil {
				f.TagIDs = append(f.TagIDs, id)
			}
		}
	}
	return f, nil
}

func atoiDefault(s string, def int) int {
	if s == "" {
		return def
	}
	n, err := strconv.Atoi(s)
	if err != nil {
		return def
	}
	return n
}

// ─── Tags ────────────────────────────────────────────────────────────────────

func (s *Server) handleListTags(w http.ResponseWriter, r *http.Request) {
	tags, err := s.tag.List()
	if err != nil {
		writeErr(w, http.StatusInternalServerError, err)
		return
	}
	writeOK(w, map[string]any{"tags": tags})
}

func (s *Server) handleCreateTag(w http.ResponseWriter, r *http.Request) {
	var body struct{ Name, Color string }
	if err := json.NewDecoder(r.Body).Decode(&body); err != nil {
		writeErr(w, http.StatusBadRequest, err)
		return
	}
	id, err := s.tag.Create(body.Name, body.Color)
	if err != nil {
		writeErr(w, http.StatusInternalServerError, err)
		return
	}
	writeOK(w, map[string]any{"id": id, "name": body.Name})
}

func (s *Server) handleDeleteTag(w http.ResponseWriter, r *http.Request) {
	id, err := strconv.ParseInt(chi.URLParam(r, "id"), 10, 64)
	if err != nil {
		writeErr(w, http.StatusBadRequest, err)
		return
	}
	if err := s.tag.Delete(id); err != nil {
		writeErr(w, mapDomainError(err), err)
		return
	}
	writeOK(w, map[string]any{"id": id, "deleted": true})
}

func (s *Server) handleTagTx(w http.ResponseWriter, r *http.Request) {
	id, err := strconv.ParseInt(chi.URLParam(r, "id"), 10, 64)
	if err != nil {
		writeErr(w, http.StatusBadRequest, err)
		return
	}
	limit := atoiDefault(r.URL.Query().Get("limit"), 50)
	offset := atoiDefault(r.URL.Query().Get("offset"), 0)
	rows, err := s.tag.Transactions(id, limit, offset)
	if err != nil {
		writeErr(w, http.StatusInternalServerError, err)
		return
	}
	writeOK(w, map[string]any{"transactions": rows, "total": len(rows)})
}

// ─── Templates ───────────────────────────────────────────────────────────────

func (s *Server) handleListTpl(w http.ResponseWriter, r *http.Request) {
	typ := r.URL.Query().Get("template_type")
	ts, err := s.tpl.ListRecordTemplates(typ)
	if err != nil {
		writeErr(w, http.StatusInternalServerError, err)
		return
	}
	writeOK(w, map[string]any{"templates": ts})
}

func (s *Server) handleCreateTpl(w http.ResponseWriter, r *http.Request) {
	var in service.CreateRecordTemplateInput
	if err := json.NewDecoder(r.Body).Decode(&in); err != nil {
		writeErr(w, http.StatusBadRequest, err)
		return
	}
	t, err := s.tpl.CreateRecordTemplate(in)
	if err != nil {
		writeErr(w, mapDomainError(err), err)
		return
	}
	writeJSON(w, http.StatusCreated, apiResponse{Success: true, Data: t})
}

func (s *Server) handleUpdateTpl(w http.ResponseWriter, r *http.Request) {
	id, err := strconv.ParseInt(chi.URLParam(r, "id"), 10, 64)
	if err != nil {
		writeErr(w, http.StatusBadRequest, err)
		return
	}
	var body map[string]any
	if err := json.NewDecoder(r.Body).Decode(&body); err != nil {
		writeErr(w, http.StatusBadRequest, err)
		return
	}
	if err := s.tpl.UpdateRecordTemplate(id, body); err != nil {
		writeErr(w, mapDomainError(err), err)
		return
	}
	writeOK(w, map[string]any{"id": id})
}

func (s *Server) handleDeleteTpl(w http.ResponseWriter, r *http.Request) {
	id, err := strconv.ParseInt(chi.URLParam(r, "id"), 10, 64)
	if err != nil {
		writeErr(w, http.StatusBadRequest, err)
		return
	}
	if err := s.tpl.DeleteRecordTemplate(id); err != nil {
		writeErr(w, mapDomainError(err), err)
		return
	}
	writeOK(w, map[string]any{"id": id, "deleted": true})
}

func (s *Server) handleUseTpl(w http.ResponseWriter, r *http.Request) {
	id, err := strconv.ParseInt(chi.URLParam(r, "id"), 10, 64)
	if err != nil {
		writeErr(w, http.StatusBadRequest, err)
		return
	}
	var body struct {
		Amount float64 `json:"amount"`
	}
	_ = json.NewDecoder(r.Body).Decode(&body)
	t, err := s.tpl.ApplyRecordTemplate(id, body.Amount)
	if err != nil {
		writeErr(w, mapDomainError(err), err)
		return
	}
	writeJSON(w, http.StatusCreated, apiResponse{Success: true, Data: t})
}

// ─── Aggregates / helpers ────────────────────────────────────────────────────

func (s *Server) handleSuggestions(w http.ResponseWriter, r *http.Request) {
	q := r.URL.Query()
	out, err := s.tx.Suggestion(q.Get("field"), q.Get("keyword"))
	if err != nil {
		writeErr(w, http.StatusInternalServerError, err)
		return
	}
	writeOK(w, out)
}

func (s *Server) handleSummary(w http.ResponseWriter, r *http.Request) {
	q := r.URL.Query()
	year := atoiDefault(q.Get("year"), 0)
	month := atoiDefault(q.Get("month"), 0)
	start, end := periodRange(year, month, q.Get("start_date"), q.Get("end_date"))
	sum, err := s.tx.Summary(start, end)
	if err != nil {
		writeErr(w, http.StatusInternalServerError, err)
		return
	}
	writeOK(w, sum)
}

func (s *Server) handleStats(w http.ResponseWriter, r *http.Request) {
	q := r.URL.Query()
	rows, err := s.tx.Statistics(q.Get("group_by"), q.Get("sub_group"),
		q.Get("start_date"), q.Get("end_date"))
	if err != nil {
		writeErr(w, mapDomainError(err), err)
		return
	}
	writeOK(w, map[string]any{"stats": rows})
}

func (s *Server) handleAccounts(w http.ResponseWriter, r *http.Request) {
	xs, err := s.tx.ListAccounts()
	if err != nil {
		writeErr(w, http.StatusInternalServerError, err)
		return
	}
	writeOK(w, map[string]any{"accounts": xs})
}

func (s *Server) handleCategories(w http.ResponseWriter, r *http.Request) {
	xs, err := s.tx.ListCategories()
	if err != nil {
		writeErr(w, http.StatusInternalServerError, err)
		return
	}
	writeOK(w, map[string]any{"categories": xs})
}

func (s *Server) handleMembers(w http.ResponseWriter, r *http.Request) {
	xs, err := s.tx.ListMembers()
	if err != nil {
		writeErr(w, http.StatusInternalServerError, err)
		return
	}
	writeOK(w, map[string]any{"members": xs})
}

// ─── Budgets ────────────────────────────────────────────────────────────────

func (s *Server) handleListBudgets(w http.ResponseWriter, r *http.Request) {
	q := r.URL.Query()
	bs, err := s.bdg.List(atoiDefault(q.Get("year"), 0), atoiDefault(q.Get("month"), 0))
	if err != nil {
		writeErr(w, http.StatusInternalServerError, err)
		return
	}
	writeOK(w, map[string]any{"budgets": bs})
}

func (s *Server) handleSetBudget(w http.ResponseWriter, r *http.Request) {
	var body struct {
		Category       string  `json:"category"`
		Amount         float64 `json:"amount"`
		Year           int     `json:"year"`
		Month          int     `json:"month"`
		DimensionType  string  `json:"dimension_type"`
		DimensionValue string  `json:"dimension_value"`
	}
	if err := json.NewDecoder(r.Body).Decode(&body); err != nil {
		writeErr(w, http.StatusBadRequest, err)
		return
	}
	if err := s.bdg.Set(service.SetInput{
		Category: body.Category, Amount: body.Amount, Year: body.Year, Month: body.Month,
		DimensionType: body.DimensionType, DimensionValue: body.DimensionValue,
	}); err != nil {
		writeErr(w, mapDomainError(err), err)
		return
	}
	writeOK(w, map[string]any{"status": "ok"})
}

func (s *Server) handleCheckBudget(w http.ResponseWriter, r *http.Request) {
	q := r.URL.Query()
	year := atoiDefault(q.Get("year"), 0)
	month := atoiDefault(q.Get("month"), 0)
	checks, err := s.bdg.Check(year, month)
	if err != nil {
		writeErr(w, http.StatusInternalServerError, err)
		return
	}
	writeOK(w, map[string]any{"checks": checks})
}

// ─── Export / Analyze ──────────────────────────────────────────────────────

func (s *Server) handleExport(w http.ResponseWriter, r *http.Request) {
	q := r.URL.Query()
	f := domain.ListFilter{
		StartDate: q.Get("start_date"), EndDate: q.Get("end_date"),
		Category: q.Get("category"), Account: q.Get("account"),
		Limit: 100000,
	}
	format := q.Get("format")
	if format == "" {
		format = "csv"
	}
	w.Header().Set("Content-Type", "text/csv; charset=utf-8")
	if format == "json" {
		w.Header().Set("Content-Type", "application/json; charset=utf-8")
	}
	if err := s.tx.Export(f, w, service.ExportFormat(format)); err != nil {
		writeErr(w, http.StatusInternalServerError, err)
		return
	}
}

func (s *Server) handleAnalyze(w http.ResponseWriter, _ *http.Request) {
	sections, err := s.tx.AnalyzeData()
	if err != nil {
		writeErr(w, http.StatusInternalServerError, err)
		return
	}
	writeOK(w, map[string]any{"sections": sections})
}

// ─── Static / SPA ───────────────────────────────────────────────────────────

func (s *Server) handleSPA(w http.ResponseWriter, r *http.Request) {
	if FS == nil {
		http.NotFound(w, r)
		return
	}
	path := strings.TrimPrefix(r.URL.Path, "/")
	if path == "" {
		path = "index.html"
	}
	f, err := FS.Open(path)
	if err != nil {
		// SPA fallback: serve index.html for any non-asset route.
		if !strings.Contains(path, ".") {
			f, err = FS.Open("index.html")
		}
		if err != nil {
			http.NotFound(w, r)
			return
		}
	}
	defer f.Close()
	stat, err := f.Stat()
	if err != nil {
		http.NotFound(w, r)
		return
	}
	if d, ok := f.(fs.ReadDirFile); ok {
		_ = d
	}
	// Best-effort content type.
	switch {
	case strings.HasSuffix(path, ".html"):
		w.Header().Set("Content-Type", "text/html; charset=utf-8")
	case strings.HasSuffix(path, ".js"):
		w.Header().Set("Content-Type", "application/javascript; charset=utf-8")
	case strings.HasSuffix(path, ".css"):
		w.Header().Set("Content-Type", "text/css; charset=utf-8")
	case strings.HasSuffix(path, ".svg"):
		w.Header().Set("Content-Type", "image/svg+xml")
	}
	http.ServeContent(w, r, path, stat.ModTime(), readSeeker(f))
}

// readSeeker is a tiny adapter so http.ServeContent can serve from an
// embed.FS entry. embed.FS files are *embed.openFile which implements
// io.ReadSeeker via Stat/Read on the inner reader — but the concrete type
// also implements io.Seeker on most platforms. We try a type assertion and
// fall back to io.Copy.
type seekFiler interface {
	Read(p []byte) (int, error)
	Seek(offset int64, whence int) (int64, error)
}

func readSeeker(f fs.File) interface {
	Read(p []byte) (int, error)
	Seek(offset int64, whence int) (int64, error)
} {
	if s, ok := f.(seekFiler); ok {
		return s
	}
	// Last resort: read all and return a bytes.Reader.
	buf := make([]byte, 0, 4096)
	tmp := make([]byte, 4096)
	for {
		n, err := f.Read(tmp)
		if n > 0 {
			buf = append(buf, tmp[:n]...)
		}
		if err != nil {
			break
		}
	}
	return readSeekerFromBytes(buf)
}

// readSeekerFromBytes wraps a byte slice in a seekable in-memory reader.
type bytesSeeker struct {
	b   []byte
	pos int64
}

func (r *bytesSeeker) Read(p []byte) (int, error) {
	if r.pos >= int64(len(r.b)) {
		return 0, fmt.Errorf("EOF")
	}
	n := copy(p, r.b[r.pos:])
	r.pos += int64(n)
	return n, nil
}

func (r *bytesSeeker) Seek(offset int64, whence int) (int64, error) {
	switch whence {
	case 0:
		r.pos = offset
	case 1:
		r.pos += offset
	case 2:
		r.pos = int64(len(r.b)) + offset
	}
	return r.pos, nil
}

func readSeekerFromBytes(b []byte) *bytesSeeker { return &bytesSeeker{b: b} }

// periodRange resolves (year, month, startDate, endDate) to a (start, end)
// pair suitable for the Summary service.
func periodRange(year, month int, startDate, endDate string) (string, string) {
	if startDate != "" && endDate != "" {
		return startDate, endDate
	}
	if year == 0 {
		year = time.Now().Year()
	}
	if month == 0 {
		month = int(time.Now().Month())
	}
	return fmt.Sprintf("%04d-%02d-01", year, month), fmt.Sprintf("%04d-%02d-31", year, month)
}
