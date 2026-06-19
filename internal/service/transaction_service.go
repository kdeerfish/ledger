// Package service contains the business logic that the HTTP and CLI layers
// share. Repos handle SQL; services translate user intent into repo calls and
// apply business rules (validation, deduplication, derived counts, etc.).
package service

import (
	"database/sql"
	"encoding/csv"
	"encoding/json"
	"fmt"
	"io"
	"sort"
	"strconv"
	"strings"
	"time"

	"github.com/kdeerfish/ledger/internal/domain"
	"github.com/kdeerfish/ledger/internal/repo"
)

// TransactionService exposes every transaction-related operation.
type TransactionService struct {
	Repo *repo.TransactionRepo
	Tags *repo.TagRepo
}

func NewTransactionService(t *repo.TransactionRepo, g *repo.TagRepo) *TransactionService {
	return &TransactionService{Repo: t, Tags: g}
}

// AddInput is the validated payload for Add.
type AddInput struct {
	Type        domain.TxnType
	Amount      float64
	Category    string
	Subcategory string
	Account     string
	Project     string
	Member      string
	Merchant    string
	Note        string
	TransDate   string // optional; default = now
	Force       bool   // bypass duplicate check
	TagNames    []string
}

// Add persists a new transaction. If a duplicate exists and Force is false,
// returns domain.ErrDuplicate.
func (s *TransactionService) Add(in AddInput) (*domain.Transaction, error) {
	if !in.Type.Valid() {
		return nil, domain.Wrap(domain.ErrInvalidInput, "type must be 支出 or 收入, got %q", in.Type)
	}
	if in.Amount <= 0 {
		return nil, domain.Wrap(domain.ErrInvalidInput, "amount must be > 0")
	}
	date := in.TransDate
	if date == "" {
		date = time.Now().Format("2006-01-02 15:04:05")
	} else if _, err := time.Parse("2006-01-02 15:04:05", date); err != nil {
		// Accept date-only as well.
		if _, err2 := time.Parse("2006-01-02", date); err2 != nil {
			return nil, domain.Wrap(domain.ErrInvalidInput, "trans_date must be YYYY-MM-DD or YYYY-MM-DD HH:MM:SS, got %q", date)
		}
	}
	if !in.Force {
		if existing, err := s.Repo.CheckDuplicate(date, in.Type, in.Amount, in.Category); err != nil {
			return nil, err
		} else if existing > 0 {
			return nil, domain.Wrap(domain.ErrDuplicate, "transaction #%d", existing)
		}
	}
	tagIDs, err := s.Tags.ResolveNames(in.TagNames)
	if err != nil {
		return nil, err
	}
	t := &domain.Transaction{
		Type: in.Type, Amount: in.Amount,
		Category:    ptrString(in.Category),
		Subcategory: ptrString(in.Subcategory),
		Account:     ptrString(in.Account),
		Project:     ptrString(in.Project),
		Member:      ptrString(in.Member),
		Merchant:    ptrString(in.Merchant),
		Note:        ptrString(in.Note),
		TransDate:   date,
		TagIDs:      tagIDs,
	}
	if _, err := s.Repo.Insert(t); err != nil {
		return nil, err
	}
	// Reload to populate TagNames (used by callers like TemplateService).
	if loaded, err := s.Repo.Get(t.ID); err == nil {
		return loaded, nil
	}
	return t, nil
}

// Get returns a single transaction with tag associations loaded.
func (s *TransactionService) Get(id int64) (*domain.Transaction, error) {
	return s.Repo.Get(id)
}

// List returns matching transactions (limit/offset honored) and the total
// match count for pagination.
func (s *TransactionService) List(f domain.ListFilter) ([]domain.Transaction, int, error) {
	if f.Limit <= 0 {
		f.Limit = 20
	}
	rows, err := s.Repo.List(f)
	if err != nil {
		return nil, 0, err
	}
	total, err := s.Repo.Count(f)
	if err != nil {
		return nil, 0, err
	}
	return rows, total, nil
}

// Search exposes a thin wrapper over List with a keyword and search_type.
func (s *TransactionService) Search(keyword, searchType string, limit int) ([]domain.Transaction, error) {
	f := domain.ListFilter{Keyword: keyword, SearchType: searchType, Limit: limit}
	rows, _, err := s.List(f)
	return rows, err
}

// Filter exposes a thin wrapper over List for the explicit filter endpoint.
func (s *TransactionService) Filter(f domain.ListFilter) ([]domain.Transaction, error) {
	rows, _, err := s.List(f)
	return rows, err
}

// Update applies a whitelist partial update.
func (s *TransactionService) Update(id int64, field, value string) error {
	if field == "" {
		return domain.ErrNoUpdateField
	}
	updates := map[string]any{field: value}
	if field == "amount" {
		v, err := strconv.ParseFloat(value, 64)
		if err != nil {
			return domain.Wrap(domain.ErrInvalidInput, "amount must be a number, got %q", value)
		}
		updates[field] = v
	}
	return s.Repo.UpdateFields(id, updates)
}

// SoftDelete marks a transaction as deleted.
func (s *TransactionService) SoftDelete(id int64) error {
	return s.Repo.SetDeleted(id, true)
}

// Restore undoes a soft delete.
func (s *TransactionService) Restore(id int64) error {
	return s.Repo.SetDeleted(id, false)
}

// HardDelete removes a row permanently.
func (s *TransactionService) HardDelete(id int64) error {
	return s.Repo.HardDelete(id)
}

// Summary computes aggregate income/expense for the given period.
func (s *TransactionService) Summary(startDate, endDate string) (domain.Summary, error) {
	return s.Repo.Summary(startDate, endDate)
}

// Statistics returns a grouped breakdown.
func (s *TransactionService) Statistics(groupBy, subGroup, startDate, endDate string) ([]repo.StatsResult, error) {
	column, err := mapStatsGroup(groupBy)
	if err != nil {
		return nil, err
	}
	sub := ""
	if subGroup != "" {
		sub, err = mapStatsGroup(subGroup)
		if err != nil {
			return nil, err
		}
	}
	return s.Repo.Statistics(column, sub, startDate, endDate)
}

func mapStatsGroup(s string) (string, error) {
	switch s {
	case "category", "account", "project", "member", "merchant", "type":
		return s, nil
	case "month":
		return "month", nil
	case "":
		return "category", nil
	default:
		return "", domain.Wrap(domain.ErrInvalidInput, "group_by %q not supported", s)
	}
}

// DistinctValues is a passthrough used by /api/accounts etc.
func (s *TransactionService) DistinctValues(column string) ([]string, error) {
	return s.Repo.DistinctValues(column, false)
}

// ListAccounts is a convenience wrapper.
func (s *TransactionService) ListAccounts() ([]string, error) {
	return s.Repo.DistinctValues("account", false)
}
func (s *TransactionService) ListCategories() ([]string, error) {
	return s.Repo.DistinctValues("category", false)
}
func (s *TransactionService) ListMembers() ([]string, error) {
	return s.Repo.DistinctValues("member", false)
}

// Suggestion returns auto-complete data.
func (s *TransactionService) Suggestion(field, keyword string) (domain.Suggestion, error) {
	out := domain.Suggestion{}
	cols := []string{"category", "subcategory", "account", "merchant", "project", "member"}
	for _, c := range cols {
		vals, err := s.Repo.DistinctValues(c, false)
		if err != nil {
			return out, err
		}
		var matched []string
		if keyword == "" {
			matched = vals
			if len(matched) > 20 {
				matched = matched[:20]
			}
		} else {
			for _, v := range vals {
				if strings.Contains(v, keyword) {
					matched = append(matched, v)
				}
			}
		}
		items := make([]domain.SuggestionItem, 0, len(matched))
		for _, m := range matched {
			items = append(items, domain.SuggestionItem{Value: m})
		}
		switch c {
		case "category":
			out.Categories = items
		case "subcategory":
			out.Subcategories = items
		case "account":
			out.Accounts = items
		case "merchant":
			out.Merchants = items
		case "project":
			out.Projects = items
		case "member":
			out.Members = items
		}
	}
	// Frequent: top 5 categories by usage.
	if field == "" || field == "category" {
		stats, err := s.Repo.Statistics("category", "", "", "")
		if err == nil {
			freq := make([]domain.SuggestionItem, 0, 5)
			for i, st := range stats {
				if i >= 5 {
					break
				}
				freq = append(freq, domain.SuggestionItem{Value: st.Group, Count: st.Count})
			}
			out.Frequent = freq
		}
	}
	return out, nil
}

// Info returns database-wide metadata.
func (s *TransactionService) Info() (domain.Info, error) {
	var info domain.Info
	total, active, deleted, err := s.Repo.CountAll()
	if err != nil {
		return info, err
	}
	info.TotalRecords = total
	info.ActiveRecords = active
	info.DeletedRecords = deleted
	if lo, hi, err := s.Repo.MinMaxDate(); err == nil {
		info.DateRangeStart = lo
		info.DateRangeEnd = hi
	}
	if s.Tags != nil {
		if n, err := s.Tags.Count(); err == nil {
			info.TagCount = n
		}
	}
	return info, nil
}

// ImportCSV reads a "随手记" style CSV and inserts each valid row. Invalid
// rows are skipped silently (the original Python implementation does the same).
// The result counts are returned in ImportResult.
type ImportResult struct {
	Imported int      `json:"imported"`
	Skipped  int      `json:"skipped"`
	Errors   []string `json:"errors,omitempty"`
}

// ImportCSV imports a CSV stream. Expected headers (Chinese): 交易类型, 金额,
// 日期, 类别, 子类别, 账户, 项目, 成员, 商家, 备注.
func (s *TransactionService) ImportCSV(r io.Reader) (ImportResult, error) {
	cr := csv.NewReader(r)
	cr.FieldsPerRecord = -1
	header, err := cr.Read()
	if err != nil {
		return ImportResult{}, fmt.Errorf("%w: read header: %w", domain.ErrInvalidInput, err)
	}
	idx := map[string]int{}
	for i, h := range header {
		idx[strings.TrimSpace(h)] = i
	}
	required := []string{"交易类型", "金额", "日期", "类别"}
	for _, req := range required {
		if _, ok := idx[req]; !ok {
			return ImportResult{}, domain.Wrap(domain.ErrInvalidInput, "missing required column %q", req)
		}
	}
	var rows []AddInput
	res := ImportResult{}
	for {
		rec, err := cr.Read()
		if err == io.EOF {
			break
		}
		if err != nil {
			res.Skipped++
			res.Errors = append(res.Errors, err.Error())
			continue
		}
		typ := strings.TrimSpace(rec[idx["交易类型"]])
		if typ != string(domain.TxnExpense) && typ != string(domain.TxnIncome) {
			res.Skipped++
			continue
		}
		amtStr := strings.TrimSpace(rec[idx["金额"]])
		amt, err := strconv.ParseFloat(amtStr, 64)
		if err != nil || amt == 0 {
			res.Skipped++
			continue
		}
		dateStr := strings.TrimSpace(rec[idx["日期"]])
		date, err := parseCSVDate(dateStr)
		if err != nil {
			res.Skipped++
			res.Errors = append(res.Errors, err.Error())
			continue
		}
		rows = append(rows, AddInput{
			Type:        domain.TxnType(typ),
			Amount:      amt,
			Category:    strings.TrimSpace(rec[idx["类别"]]),
			Subcategory: safeCol(rec, idx, "子类别"),
			Account:     safeCol(rec, idx, "账户"),
			Project:     safeCol(rec, idx, "项目"),
			Member:      safeCol(rec, idx, "成员"),
			Merchant:    safeCol(rec, idx, "商家"),
			Note:        safeCol(rec, idx, "备注"),
			TransDate:   date,
		})
	}
	// Sort by date ascending to keep id order = time order.
	sort.Slice(rows, func(i, j int) bool { return rows[i].TransDate < rows[j].TransDate })
	for i := range rows {
		if _, err := s.Add(rows[i]); err != nil {
			res.Skipped++
			res.Errors = append(res.Errors, err.Error())
			continue
		}
		res.Imported++
	}
	return res, nil
}

func safeCol(rec []string, idx map[string]int, name string) string {
	if i, ok := idx[name]; ok && i < len(rec) {
		return strings.TrimSpace(rec[i])
	}
	return ""
}

func parseCSVDate(s string) (string, error) {
	layouts := []string{"2006/01/02 15:04", "2006/01/02"}
	for _, l := range layouts {
		if t, err := time.Parse(l, s); err == nil {
			return t.Format("2006-01-02 15:04:05"), nil
		}
	}
	return "", fmt.Errorf("unrecognized date %q", s)
}

// ExportFormat is the on-disk format for Export.
type ExportFormat string

const (
	FormatCSV  ExportFormat = "csv"
	FormatJSON ExportFormat = "json"
)

// Export writes the filtered transactions to w in the requested format.
func (s *TransactionService) Export(f domain.ListFilter, w io.Writer, format ExportFormat) error {
	rows, err := s.Repo.List(f)
	if err != nil {
		return err
	}
	switch format {
	case FormatJSON:
		enc := json.NewEncoder(w)
		enc.SetIndent("", "  ")
		return enc.Encode(rows)
	default:
		cw := csv.NewWriter(w)
		defer cw.Flush()
		header := []string{"id", "type", "amount", "category", "subcategory",
			"account", "project", "member", "merchant", "note", "trans_date", "is_deleted"}
		if err := cw.Write(header); err != nil {
			return err
		}
		for i := range rows {
			r := &rows[i]
			row := []string{
				strconv.FormatInt(r.ID, 10),
				string(r.Type),
				strconv.FormatFloat(r.Amount, 'f', -1, 64),
				derefString(r.Category),
				derefString(r.Subcategory),
				derefString(r.Account),
				derefString(r.Project),
				derefString(r.Member),
				derefString(r.Merchant),
				derefString(r.Note),
				r.TransDate,
				strconv.FormatBool(r.IsDeleted),
			}
			if err := cw.Write(row); err != nil {
				return err
			}
		}
		return nil
	}
}

// AnalyzeData is the human-readable cross-stats report used by
// `analyze` and /api/analyze. It returns a slice of sections.
func (s *TransactionService) AnalyzeData() ([]string, error) {
	stats, err := s.Repo.Statistics("category", "", "", "")
	if err != nil {
		return nil, err
	}
	monthly, err := s.Repo.Statistics("month", "", "", "")
	if err != nil {
		return nil, err
	}
	accountStats, err := s.Repo.Statistics("account", "", "", "")
	if err != nil {
		return nil, err
	}
	out := []string{"## 类别统计", sectionFromStats(stats), "## 月度统计", sectionFromStats(monthly),
		"## 账户统计", sectionFromStats(accountStats)}
	return out, nil
}

func sectionFromStats(in []repo.StatsResult) string {
	var sb strings.Builder
	for _, s := range in {
		fmt.Fprintf(&sb, "%s: 收入 %.2f 支出 %.2f 笔数 %d\n", s.Group, s.Income, s.Expense, s.Count)
	}
	return sb.String()
}

// ReconcileGuide returns the static "对账指南" text.
func (s *TransactionService) ReconcileGuide() string {
	return "对账指南:\n1. 导出 CSV/JSON\n2. 与银行/支付宝对账单比对\n3. 标注差异\n4. 添加备注修正"
}

// Ensure SQL is used to silence import-only warnings when this file is
// compiled without the sql import. The variable is never executed.
var _ = sql.ErrNoRows
