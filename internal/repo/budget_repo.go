package repo

import (
	"database/sql"
	"fmt"
	"strings"

	"github.com/kdeerfish/ledger/internal/domain"
)

// BudgetRepo handles the budgets and budget_templates tables.
type BudgetRepo struct{ db DB }

func NewBudgetRepo(d DB) *BudgetRepo { return &BudgetRepo{db: d} }

func (r *BudgetRepo) Set(b *domain.Budget) error {
	dimVal := derefString(b.DimensionValue)
	// SQLite UNIQUE treats NULLs as distinct. Coerce empty → '' so that a
	// second insert with the same (category, year, month, dimension_type,
	// dimension_value='') hits the conflict branch and updates the row.
	res, err := r.db.Exec(`INSERT INTO budgets
		(category, year, month, amount, dimension_type, dimension_value)
		VALUES (?, ?, ?, ?, ?, ?)
		ON CONFLICT(category, year, month, dimension_type, dimension_value)
		DO UPDATE SET amount = excluded.amount`,
		b.Category, b.Year, b.Month, b.Amount, b.DimensionType, dimVal)
	if err != nil {
		return err
	}
	id, _ := res.LastInsertId()
	b.ID = id
	return nil
}

func (r *BudgetRepo) List(year, month int) ([]domain.Budget, error) {
	var (
		rows *sql.Rows
		err  error
	)
	if year > 0 && month > 0 {
		rows, err = r.db.Query(`SELECT id, category, year, month, amount, dimension_type,
			dimension_value, IFNULL(created_at, '') FROM budgets
			WHERE year = ? AND month = ? ORDER BY category`, year, month)
	} else {
		rows, err = r.db.Query(`SELECT id, category, year, month, amount, dimension_type,
			dimension_value, IFNULL(created_at, '') FROM budgets ORDER BY year DESC, month DESC, category`)
	}
	if err != nil {
		return nil, err
	}
	defer rows.Close()
	var out []domain.Budget
	for rows.Next() {
		var b domain.Budget
		if err := rows.Scan(&b.ID, &b.Category, &b.Year, &b.Month, &b.Amount,
			&b.DimensionType, &b.DimensionValue, &b.CreatedAt); err != nil {
			return nil, err
		}
		out = append(out, b)
	}
	return out, rows.Err()
}

// Delete removes a single budget.
func (r *BudgetRepo) Delete(id int64) error {
	res, err := r.db.Exec(`DELETE FROM budgets WHERE id = ?`, id)
	if err != nil {
		return err
	}
	n, _ := res.RowsAffected()
	if n == 0 {
		return domain.ErrNotFound
	}
	return nil
}

// CheckMaterialises the spent amount per budget row for a given year/month.
// Returns the joined list of BudgetCheck ready for the API.
func (r *BudgetRepo) Check(year, month int) ([]domain.BudgetCheck, error) {
	bs, err := r.List(year, month)
	if err != nil {
		return nil, err
	}
	out := make([]domain.BudgetCheck, 0, len(bs))
	for _, b := range bs {
		spent, err := r.sumSpent(b, year, month)
		if err != nil {
			return nil, err
		}
		remaining := b.Amount - spent
		pct := 0.0
		if b.Amount > 0 {
			pct = (spent / b.Amount) * 100
		}
		out = append(out, domain.BudgetCheck{
			BudgetID:   b.ID,
			Category:   b.Category,
			Year:       b.Year,
			Month:      b.Month,
			Dimension:  b.DimensionType,
			DimValue:   derefString(b.DimensionValue),
			Budget:     b.Amount,
			Spent:      spent,
			Remaining:  remaining,
			Percentage: pct,
		})
	}
	return out, nil
}

// sumSpent aggregates the matching transactions for a budget. The original
// Python implementation only counts expenses (`type='支出'`).
func (r *BudgetRepo) sumSpent(b domain.Budget, year, month int) (float64, error) {
	dimCol := "category"
	switch b.DimensionType {
	case "account", "member", "project", "merchant":
		dimCol = b.DimensionType
	}
	q := `SELECT COALESCE(SUM(amount), 0) FROM transactions
		WHERE is_deleted = 0 AND type = '支出'
		  AND strftime('%Y', trans_date) = ? AND strftime('%m', trans_date) = ?`
	args := []any{fmt.Sprintf("%04d", year), fmt.Sprintf("%02d", month)}
	if dimCol == "category" {
		// Use the budget's category directly.
		q += ` AND category = ?`
		args = append(args, b.Category)
	} else {
		q += fmt.Sprintf(` AND %s = ?`, dimCol)
		args = append(args, derefString(b.DimensionValue))
	}
	var sum float64
	row := r.db.QueryRow(q, args...)
	if err := row.Scan(&sum); err != nil {
		return 0, err
	}
	return sum, nil
}

// BudgetTemplateRepo handles the budget_templates table.
type BudgetTemplateRepo struct{ db DB }

func NewBudgetTemplateRepo(d DB) *BudgetTemplateRepo { return &BudgetTemplateRepo{db: d} }

const btCols = `id, name, description, category, amount, dimension_type, dimension_value,
	account, project, member, merchant, note, year, month, IFNULL(created_at, '')`

func scanBT(scan func(dest ...any) error, b *domain.BudgetTemplate) error {
	return scan(&b.ID, &b.Name, &b.Description, &b.Category, &b.Amount, &b.DimensionType,
		&b.DimensionValue, &b.Account, &b.Project, &b.Member, &b.Merchant, &b.Note,
		&b.Year, &b.Month, &b.CreatedAt)
}

func (r *BudgetTemplateRepo) Insert(t *domain.BudgetTemplate) (int64, error) {
	res, err := r.db.Exec(`INSERT INTO budget_templates
		(name, description, category, amount, dimension_type, dimension_value,
		 account, project, member, merchant, note, year, month)
		VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)`,
		t.Name, emptyAsNull(derefString(t.Description)),
		emptyAsNull(derefString(t.Category)), t.Amount,
		t.DimensionType, emptyAsNull(derefString(t.DimensionValue)),
		emptyAsNull(derefString(t.Account)), emptyAsNull(derefString(t.Project)),
		emptyAsNull(derefString(t.Member)), emptyAsNull(derefString(t.Merchant)),
		emptyAsNull(derefString(t.Note)), t.Year, t.Month)
	if err != nil {
		return 0, err
	}
	id, _ := res.LastInsertId()
	t.ID = id
	return id, nil
}

func (r *BudgetTemplateRepo) Get(id int64) (*domain.BudgetTemplate, error) {
	row := r.db.QueryRow(`SELECT `+btCols+` FROM budget_templates WHERE id = ?`, id)
	var t domain.BudgetTemplate
	if err := scanBT(row.Scan, &t); err != nil {
		if err == sql.ErrNoRows {
			return nil, domain.ErrNotFound
		}
		return nil, err
	}
	return &t, nil
}

func (r *BudgetTemplateRepo) List() ([]domain.BudgetTemplate, error) {
	rows, err := r.db.Query(`SELECT ` + btCols + ` FROM budget_templates ORDER BY id DESC`)
	if err != nil {
		return nil, err
	}
	defer rows.Close()
	var out []domain.BudgetTemplate
	for rows.Next() {
		var t domain.BudgetTemplate
		if err := scanBT(rows.Scan, &t); err != nil {
			return nil, err
		}
		out = append(out, t)
	}
	return out, rows.Err()
}

func (r *BudgetTemplateRepo) UpdateFields(id int64, fields map[string]any) error {
	allowed := map[string]bool{
		"name": true, "description": true, "category": true, "amount": true,
		"dimension_type": true, "dimension_value": true, "account": true,
		"project": true, "member": true, "merchant": true, "note": true,
		"year": true, "month": true,
	}
	var setParts []string
	var args []any
	for k, v := range fields {
		if !allowed[k] {
			return domain.Wrap(domain.ErrInvalidField, "field %q not updateable", k)
		}
		setParts = append(setParts, k+" = ?")
		args = append(args, v)
	}
	if len(setParts) == 0 {
		return domain.ErrNoUpdateField
	}
	args = append(args, id)
	res, err := r.db.Exec("UPDATE budget_templates SET "+strings.Join(setParts, ", ")+" WHERE id = ?", args...)
	if err != nil {
		return err
	}
	n, _ := res.RowsAffected()
	if n == 0 {
		return domain.ErrNotFound
	}
	return nil
}

func (r *BudgetTemplateRepo) Delete(id int64) error {
	res, err := r.db.Exec(`DELETE FROM budget_templates WHERE id = ?`, id)
	if err != nil {
		return err
	}
	n, _ := res.RowsAffected()
	if n == 0 {
		return domain.ErrNotFound
	}
	return nil
}

// RecordTemplateRepo handles the record_templates table.
type RecordTemplateRepo struct{ db DB }

func NewRecordTemplateRepo(d DB) *RecordTemplateRepo { return &RecordTemplateRepo{db: d} }

const rtCols = `id, name, description, template_type, type, amount, category, subcategory,
	account, project, member, merchant, note, usage_count,
	IFNULL(last_used_at, ''), IFNULL(created_at, ''), IFNULL(tags, '')`

func scanRT(scan func(dest ...any) error, t *domain.RecordTemplate) error {
	return scan(&t.ID, &t.Name, &t.Description, &t.TemplateType, &t.Type, &t.Amount,
		&t.Category, &t.Subcategory, &t.Account, &t.Project, &t.Member, &t.Merchant,
		&t.Note, &t.UsageCount, &t.LastUsedAt, &t.CreatedAt, &t.Tags)
}

func (r *RecordTemplateRepo) Insert(t *domain.RecordTemplate) (int64, error) {
	res, err := r.db.Exec(`INSERT INTO record_templates
		(name, description, template_type, type, amount, category, subcategory,
		 account, project, member, merchant, note, tags)
		VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)`,
		t.Name, emptyAsNull(derefString(t.Description)), t.TemplateType,
		emptyAsNull(derefString(t.Type)), t.Amount,
		emptyAsNull(derefString(t.Category)), emptyAsNull(derefString(t.Subcategory)),
		emptyAsNull(derefString(t.Account)), emptyAsNull(derefString(t.Project)),
		emptyAsNull(derefString(t.Member)), emptyAsNull(derefString(t.Merchant)),
		emptyAsNull(derefString(t.Note)), emptyAsNull(t.Tags))
	if err != nil {
		return 0, err
	}
	id, _ := res.LastInsertId()
	t.ID = id
	return id, nil
}

func (r *RecordTemplateRepo) Get(id int64) (*domain.RecordTemplate, error) {
	row := r.db.QueryRow(`SELECT `+rtCols+` FROM record_templates WHERE id = ?`, id)
	var t domain.RecordTemplate
	if err := scanRT(row.Scan, &t); err != nil {
		if err == sql.ErrNoRows {
			return nil, domain.ErrNotFound
		}
		return nil, err
	}
	return &t, nil
}

func (r *RecordTemplateRepo) List(templateType string) ([]domain.RecordTemplate, error) {
	q := `SELECT ` + rtCols + ` FROM record_templates`
	var args []any
	if templateType != "" {
		q += ` WHERE template_type = ?`
		args = append(args, templateType)
	}
	q += ` ORDER BY usage_count DESC, id DESC`
	rows, err := r.db.Query(q, args...)
	if err != nil {
		return nil, err
	}
	defer rows.Close()
	var out []domain.RecordTemplate
	for rows.Next() {
		var t domain.RecordTemplate
		if err := scanRT(rows.Scan, &t); err != nil {
			return nil, err
		}
		out = append(out, t)
	}
	return out, rows.Err()
}

func (r *RecordTemplateRepo) UpdateFields(id int64, fields map[string]any) error {
	allowed := map[string]bool{
		"name": true, "description": true, "template_type": true, "type": true,
		"amount": true, "category": true, "subcategory": true, "account": true,
		"project": true, "member": true, "merchant": true, "note": true, "tags": true,
	}
	var setParts []string
	var args []any
	for k, v := range fields {
		if !allowed[k] {
			return domain.Wrap(domain.ErrInvalidField, "field %q not updateable", k)
		}
		setParts = append(setParts, k+" = ?")
		args = append(args, v)
	}
	if len(setParts) == 0 {
		return domain.ErrNoUpdateField
	}
	args = append(args, id)
	res, err := r.db.Exec("UPDATE record_templates SET "+strings.Join(setParts, ", ")+" WHERE id = ?", args...)
	if err != nil {
		return err
	}
	n, _ := res.RowsAffected()
	if n == 0 {
		return domain.ErrNotFound
	}
	return nil
}

func (r *RecordTemplateRepo) Delete(id int64) error {
	res, err := r.db.Exec(`DELETE FROM record_templates WHERE id = ?`, id)
	if err != nil {
		return err
	}
	n, _ := res.RowsAffected()
	if n == 0 {
		return domain.ErrNotFound
	}
	return nil
}

// IncrementUsage bumps usage_count and last_used_at atomically.
func (r *RecordTemplateRepo) IncrementUsage(id int64) error {
	_, err := r.db.Exec(`UPDATE record_templates
		SET usage_count = usage_count + 1, last_used_at = datetime('now', 'localtime')
		WHERE id = ?`, id)
	return err
}
