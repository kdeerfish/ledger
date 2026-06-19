package repo

import (
	"database/sql"
	"fmt"
	"strings"
	"time"

	"github.com/kdeerfish/ledger/internal/domain"
)

// TransactionRepo handles CRUD on the transactions table plus the
// transaction_tags join table.
type TransactionRepo struct{ db DB }

func NewTransactionRepo(d DB) *TransactionRepo { return &TransactionRepo{db: d} }

// DB exposes the underlying connection so callers (e.g. service tests) can
// run ad-hoc queries without re-opening a handle.
func (r *TransactionRepo) DB() DB { return r.db }

// scanTxn populates a Transaction from one row of the standard column order.
func scanTxn(scan func(dest ...any) error, t *domain.Transaction) error {
	var typ, date string
	if err := scan(&t.ID, &typ, &t.Amount,
		&t.Category, &t.Subcategory, &t.Account, &t.Project, &t.Member,
		&t.Merchant, &t.Note, &date, &t.IsDeleted); err != nil {
		return err
	}
	t.Type = domain.TxnType(typ)
	t.TransDate = date
	return nil
}

const txnCols = `id, type, amount, category, subcategory, account, project, member,
	merchant, note, trans_date, is_deleted`

// Insert adds a new transaction. Tags (if any) are persisted in the same call.
func (r *TransactionRepo) Insert(t *domain.Transaction) (int64, error) {
	if t.TransDate == "" {
		t.TransDate = nowString()
	}
	res, err := r.db.Exec(`INSERT INTO transactions
		(type, amount, category, subcategory, account, project, member, merchant, note, trans_date, is_deleted)
		VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 0)`,
		string(t.Type), t.Amount,
		emptyAsNull(derefString(t.Category)),
		emptyAsNull(derefString(t.Subcategory)),
		emptyAsNull(derefString(t.Account)),
		emptyAsNull(derefString(t.Project)),
		emptyAsNull(derefString(t.Member)),
		emptyAsNull(derefString(t.Merchant)),
		emptyAsNull(derefString(t.Note)),
		t.TransDate)
	if err != nil {
		return 0, fmt.Errorf("insert transaction: %w", err)
	}
	id, _ := res.LastInsertId()
	t.ID = id
	if len(t.TagIDs) > 0 {
		if err := r.SetTags(id, t.TagIDs); err != nil {
			return id, err
		}
	}
	return id, nil
}

// Get fetches a single transaction by ID. Returns domain.ErrNotFound if absent.
func (r *TransactionRepo) Get(id int64) (*domain.Transaction, error) {
	row := r.db.QueryRow(`SELECT `+txnCols+` FROM transactions WHERE id = ?`, id)
	var t domain.Transaction
	if err := scanTxn(row.Scan, &t); err != nil {
		if err == sql.ErrNoRows {
			return nil, domain.ErrNotFound
		}
		return nil, fmt.Errorf("get transaction: %w", err)
	}
	if err := r.loadTags(&t); err != nil {
		return nil, err
	}
	return &t, nil
}

// List returns transactions matching the filter, ordered by date desc.
// limit/offset <= 0 mean no limit.
func (r *TransactionRepo) List(f domain.ListFilter) ([]domain.Transaction, error) {
	where, args := buildWhere(f)
	q := `SELECT ` + txnCols + ` FROM transactions` + where + ` ORDER BY trans_date DESC, id DESC`
	if f.Limit > 0 {
		q += fmt.Sprintf(" LIMIT %d OFFSET %d", f.Limit, f.Offset)
	}
	rows, err := r.db.Query(q, args...)
	if err != nil {
		return nil, fmt.Errorf("list transactions: %w", err)
	}
	defer rows.Close()
	var out []domain.Transaction
	for rows.Next() {
		var t domain.Transaction
		if err := scanTxn(rows.Scan, &t); err != nil {
			return nil, err
		}
		out = append(out, t)
	}
	return out, rows.Err()
}

// Count returns the row count for a filter (useful for pagination totals).
func (r *TransactionRepo) Count(f domain.ListFilter) (int, error) {
	where, args := buildWhere(f)
	var n int
	row := r.db.QueryRow(`SELECT COUNT(*) FROM transactions`+where, args...)
	if err := row.Scan(&n); err != nil {
		return 0, err
	}
	return n, nil
}

// UpdateFields applies a partial update with a whitelist of allowed columns.
func (r *TransactionRepo) UpdateFields(id int64, fields map[string]any) error {
	if len(fields) == 0 {
		return domain.ErrNoUpdateField
	}
	allowed := map[string]bool{
		"amount": true, "category": true, "subcategory": true, "account": true,
		"project": true, "member": true, "merchant": true, "note": true,
		"trans_date": true, "type": true,
	}
	var setParts []string
	var args []any
	for k, v := range fields {
		if !allowed[k] {
			return domain.Wrap(domain.ErrInvalidField, "field %q is not updateable", k)
		}
		setParts = append(setParts, fmt.Sprintf("%s = ?", k))
		args = append(args, v)
	}
	args = append(args, id)
	q := "UPDATE transactions SET " + strings.Join(setParts, ", ") + " WHERE id = ?"
	res, err := r.db.Exec(q, args...)
	if err != nil {
		return fmt.Errorf("update transaction: %w", err)
	}
	n, _ := res.RowsAffected()
	if n == 0 {
		return domain.ErrNotFound
	}
	return nil
}

// SetDeleted flips the is_deleted flag.
func (r *TransactionRepo) SetDeleted(id int64, deleted bool) error {
	val := 0
	if deleted {
		val = 1
	}
	res, err := r.db.Exec(`UPDATE transactions SET is_deleted = ? WHERE id = ?`, val, id)
	if err != nil {
		return err
	}
	n, _ := res.RowsAffected()
	if n == 0 {
		return domain.ErrNotFound
	}
	return nil
}

// HardDelete removes a row permanently.
func (r *TransactionRepo) HardDelete(id int64) error {
	_, err := r.db.Exec(`DELETE FROM transactions WHERE id = ?`, id)
	return err
}

// CheckDuplicate returns the id of an existing transaction that matches
// date+type+amount+category (same day), or 0 when no match exists.
func (r *TransactionRepo) CheckDuplicate(date string, typ domain.TxnType, amount float64, category string) (int64, error) {
	var id int64
	day := date[:10] // YYYY-MM-DD prefix
	row := r.db.QueryRow(`SELECT id FROM transactions
		WHERE date(trans_date) = ?
		  AND type = ?
		  AND amount = ?
		  AND IFNULL(category, '') = ?
		LIMIT 1`, day, string(typ), amount, category)
	if err := row.Scan(&id); err != nil {
		if err == sql.ErrNoRows {
			return 0, nil
		}
		return 0, err
	}
	return id, nil
}

// SetTags replaces the tag set for a transaction.
func (r *TransactionRepo) SetTags(txnID int64, tagIDs []int64) error {
	if _, err := r.db.Exec(`DELETE FROM transaction_tags WHERE transaction_id = ?`, txnID); err != nil {
		return err
	}
	for _, id := range tagIDs {
		if _, err := r.db.Exec(`INSERT OR IGNORE INTO transaction_tags(transaction_id, tag_id) VALUES (?, ?)`, txnID, id); err != nil {
			return err
		}
	}
	return nil
}

// GetTagIDs returns the tag ids associated with a transaction.
func (r *TransactionRepo) GetTagIDs(txnID int64) ([]int64, error) {
	rows, err := r.db.Query(`SELECT tag_id FROM transaction_tags WHERE transaction_id = ?`, txnID)
	if err != nil {
		return nil, err
	}
	defer rows.Close()
	var out []int64
	for rows.Next() {
		var id int64
		if err := rows.Scan(&id); err != nil {
			return nil, err
		}
		out = append(out, id)
	}
	return out, rows.Err()
}

// loadTags populates t.TagIDs and t.TagNames (via a join on tags).
func (r *TransactionRepo) loadTags(t *domain.Transaction) error {
	rows, err := r.db.Query(`SELECT t.id, t.name FROM tags t
		JOIN transaction_tags tt ON tt.tag_id = t.id
		WHERE tt.transaction_id = ? ORDER BY t.name`, t.ID)
	if err != nil {
		return err
	}
	defer rows.Close()
	for rows.Next() {
		var id int64
		var name string
		if err := rows.Scan(&id, &name); err != nil {
			return err
		}
		t.TagIDs = append(t.TagIDs, id)
		t.TagNames = append(t.TagNames, name)
	}
	return rows.Err()
}

// DistinctValues returns the list of distinct non-null values in column.
func (r *TransactionRepo) DistinctValues(column string, includeDeleted bool) ([]string, error) {
	allowed := map[string]bool{
		"category": true, "subcategory": true, "account": true,
		"project": true, "member": true, "merchant": true,
	}
	if !allowed[column] {
		return nil, domain.Wrap(domain.ErrInvalidField, "distinct on %q not supported", column)
	}
	q := fmt.Sprintf(`SELECT DISTINCT %s FROM transactions WHERE %s IS NOT NULL AND %s != ''`,
		column, column, column)
	if !includeDeleted {
		q += ` AND is_deleted = 0`
	}
	q += ` ORDER BY ` + column
	rows, err := r.db.Query(q)
	if err != nil {
		return nil, err
	}
	defer rows.Close()
	var out []string
	for rows.Next() {
		var s string
		if err := rows.Scan(&s); err != nil {
			return nil, err
		}
		out = append(out, s)
	}
	return out, rows.Err()
}

// StatsResult groups one row returned by GetStatistics.
type StatsResult struct {
	Group   string
	Income  float64
	Expense float64
	Count   int
	// sub holds per-row sub-grouping results.
	Sub []StatsResult
}

// Statistics aggregates transactions by the requested column. When
// subColumn is non-empty, a second-level breakdown is included.
func (r *TransactionRepo) Statistics(column, subColumn, startDate, endDate string) ([]StatsResult, error) {
	col, err := r.distinctAllowed(column)
	if err != nil {
		return nil, err
	}
	if subColumn != "" {
		if _, err := r.distinctAllowed(subColumn); err != nil {
			return nil, err
		}
	}
	where, args := r.buildStatsWhere(startDate, endDate)

	// Main grouping.
	mainSQL := fmt.Sprintf(`SELECT COALESCE(NULLIF(%s, ''), '(空)') AS grp,
		SUM(CASE WHEN type='收入' THEN amount ELSE 0 END) AS income,
		SUM(CASE WHEN type='支出' THEN amount ELSE 0 END) AS expense,
		COUNT(*) AS cnt
		FROM transactions %s
		GROUP BY grp ORDER BY (income + expense) DESC`, col, where)
	rows, err := r.db.Query(mainSQL, args...)
	if err != nil {
		return nil, err
	}
	defer rows.Close()
	var out []StatsResult
	for rows.Next() {
		var s StatsResult
		if err := rows.Scan(&s.Group, &s.Income, &s.Expense, &s.Count); err != nil {
			return nil, err
		}
		out = append(out, s)
	}
	if err := rows.Err(); err != nil {
		return nil, err
	}
	if subColumn == "" {
		return out, nil
	}

	// Sub-grouping: one extra query per main group.
	for i, g := range out {
		subSQL := fmt.Sprintf(`SELECT COALESCE(NULLIF(%s, ''), '(空)') AS grp,
			SUM(CASE WHEN type='收入' THEN amount ELSE 0 END),
			SUM(CASE WHEN type='支出' THEN amount ELSE 0 END),
			COUNT(*)
			FROM transactions
			WHERE %s = ? %s
			GROUP BY grp ORDER BY (SUM(CASE WHEN type='收入' THEN amount ELSE 0 END) + SUM(CASE WHEN type='支出' THEN amount ELSE 0 END)) DESC`,
			subColumn, column, where)
		subArgs := append([]any{g.Group}, args...)
		sr, err := r.db.Query(subSQL, subArgs...)
		if err != nil {
			return nil, err
		}
		for sr.Next() {
			var sub StatsResult
			if err := sr.Scan(&sub.Group, &sub.Income, &sub.Expense, &sub.Count); err != nil {
				sr.Close()
				return nil, err
			}
			out[i].Sub = append(out[i].Sub, sub)
		}
		sr.Close()
	}
	return out, nil
}

// Summary returns aggregate income/expense for a period.
func (r *TransactionRepo) Summary(startDate, endDate string) (domain.Summary, error) {
	where, args := r.buildStatsWhere(startDate, endDate)
	q := `SELECT
		SUM(CASE WHEN type='收入' THEN amount ELSE 0 END),
		SUM(CASE WHEN type='支出' THEN amount ELSE 0 END),
		COUNT(*),
		SUM(CASE WHEN type='收入' THEN 1 ELSE 0 END),
		SUM(CASE WHEN type='支出' THEN 1 ELSE 0 END)
		FROM transactions ` + where
	var s domain.Summary
	row := r.db.QueryRow(q, args...)
	if err := row.Scan(&s.Income, &s.Expense, &s.Count, &s.IncomeN, &s.ExpenseN); err != nil {
		return s, err
	}
	s.Balance = s.Income - s.Expense
	s.StartDate = startDate
	s.EndDate = endDate
	// Daily average: expense / days in period (capped to 1).
	if startDate != "" && endDate != "" {
		s.DailyAvg = dailyAvg(s.Expense, startDate, endDate)
	}
	return s, nil
}

func (r *TransactionRepo) buildStatsWhere(startDate, endDate string) (string, []any) {
	var clauses []string
	var args []any
	clauses = append(clauses, "is_deleted = 0")
	if startDate != "" {
		clauses = append(clauses, "trans_date >= ?")
		args = append(args, startDate)
	}
	if endDate != "" {
		clauses = append(clauses, "trans_date <= ?")
		args = append(args, endDate+" 23:59:59")
	}
	return " WHERE " + strings.Join(clauses, " AND "), args
}

func (r *TransactionRepo) distinctAllowed(column string) (string, error) {
	allowed := map[string]bool{
		"category": true, "subcategory": true, "account": true,
		"project": true, "member": true, "merchant": true, "type": true,
		"month": true,
	}
	if !allowed[column] {
		return "", domain.Wrap(domain.ErrInvalidField, "stats by %q not supported", column)
	}
	if column == "month" {
		return "strftime('%Y-%m', trans_date)", nil
	}
	return column, nil
}

// MinMaxDate returns the [min, max] trans_date among non-deleted rows.
func (r *TransactionRepo) MinMaxDate() (string, string, error) {
	var lo, hi sql.NullString
	row := r.db.QueryRow(`SELECT MIN(trans_date), MAX(trans_date) FROM transactions WHERE is_deleted = 0`)
	if err := row.Scan(&lo, &hi); err != nil {
		return "", "", err
	}
	return lo.String, hi.String, nil
}

func dailyAvg(expense float64, start, end string) float64 {
	a, errA := parseDay(start)
	b, errB := parseDay(end)
	if errA != nil || errB != nil {
		return 0
	}
	days := int(b.Sub(a).Hours()/24) + 1
	if days < 1 {
		days = 1
	}
	return expense / float64(days)
}

func parseDay(s string) (time.Time, error) {
	return time.Parse("2006-01-02", s)
}

// CountAll returns total, active, and deleted counts.
func (r *TransactionRepo) CountAll() (total, active, deleted int, err error) {
	row := r.db.QueryRow(`SELECT
		COUNT(*),
		COALESCE(SUM(CASE WHEN is_deleted = 0 THEN 1 ELSE 0 END), 0),
		COALESCE(SUM(CASE WHEN is_deleted = 1 THEN 1 ELSE 0 END), 0)
		FROM transactions`)
	err = row.Scan(&total, &active, &deleted)
	return
}

// TagUsageCount returns the number of transactions linked to a given tag.
func (r *TransactionRepo) TagUsageCount(tagID int64) (int, error) {
	var n int
	row := r.db.QueryRow(`SELECT COUNT(*) FROM transaction_tags WHERE tag_id = ?`, tagID)
	err := row.Scan(&n)
	return n, err
}

// TransactionsByTag returns paginated transactions for a tag.
func (r *TransactionRepo) TransactionsByTag(tagID int64, limit, offset int) ([]domain.Transaction, error) {
	q := `SELECT ` + txnCols + ` FROM transactions
		WHERE is_deleted = 0 AND id IN (SELECT transaction_id FROM transaction_tags WHERE tag_id = ?)
		ORDER BY trans_date DESC, id DESC`
	if limit > 0 {
		q += fmt.Sprintf(" LIMIT %d OFFSET %d", limit, offset)
	}
	rows, err := r.db.Query(q, tagID)
	if err != nil {
		return nil, err
	}
	defer rows.Close()
	var out []domain.Transaction
	for rows.Next() {
		var t domain.Transaction
		if err := scanTxn(rows.Scan, &t); err != nil {
			return nil, err
		}
		out = append(out, t)
	}
	return out, rows.Err()
}
