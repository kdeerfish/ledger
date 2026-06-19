// Package repo provides thin database accessors. Each repo exposes only SQL
// operations: business rules live in the service layer.
package repo

import (
	"database/sql"
	"fmt"
	"strings"
	"time"

	"github.com/kdeerfish/ledger/internal/domain"
)

// DB is the minimal handle repos need.
type DB interface {
	QueryRow(query string, args ...any) *sql.Row
	Query(query string, args ...any) (*sql.Rows, error)
	Exec(query string, args ...any) (sql.Result, error)
}


// derefString returns the dereferenced value of p, or empty if nil.
func derefString(p *string) string {
	if p == nil {
		return ""
	}
	return *p
}

func nowString() string {
	return time.Now().Format("2006-01-02 15:04:05")
}

// emptyAsNull is a small helper that turns "" into SQL NULL during inserts.
func emptyAsNull(s string) any {
	if s == "" {
		return nil
	}
	return s
}

// buildWhere assembles a WHERE clause + args from a ListFilter. Returns
// ("", nil) when there are no constraints.
func buildWhere(f domain.ListFilter) (string, []any) {
	var clauses []string
	var args []any

	if !f.IncludeDeleted {
		clauses = append(clauses, "is_deleted = 0")
	}
	if f.Type != "" {
		clauses = append(clauses, "type = ?")
		args = append(args, string(f.Type))
	}
	if f.Category != "" {
		clauses = append(clauses, "category = ?")
		args = append(args, f.Category)
	}
	if f.Subcategory != "" {
		clauses = append(clauses, "subcategory = ?")
		args = append(args, f.Subcategory)
	}
	if f.Account != "" {
		clauses = append(clauses, "account = ?")
		args = append(args, f.Account)
	}
	if f.Project != "" {
		clauses = append(clauses, "project = ?")
		args = append(args, f.Project)
	}
	if f.Member != "" {
		clauses = append(clauses, "member = ?")
		args = append(args, f.Member)
	}
	if f.Merchant != "" {
		clauses = append(clauses, "merchant = ?")
		args = append(args, f.Merchant)
	}
	if f.Keyword != "" {
		// Search scope depends on SearchType: all (default) covers note+category+merchant
		kw := "%" + f.Keyword + "%"
		switch f.SearchType {
		case "note":
			clauses = append(clauses, "note LIKE ?")
			args = append(args, kw)
		case "category":
			clauses = append(clauses, "category LIKE ?")
			args = append(args, kw)
		case "merchant":
			clauses = append(clauses, "merchant LIKE ?")
			args = append(args, kw)
		default:
			clauses = append(clauses, "(note LIKE ? OR category LIKE ? OR merchant LIKE ? OR subcategory LIKE ?)")
			args = append(args, kw, kw, kw, kw)
		}
	}
	if f.StartDate != "" {
		clauses = append(clauses, "trans_date >= ?")
		args = append(args, f.StartDate)
	}
	if f.EndDate != "" {
		clauses = append(clauses, "trans_date <= ?")
		args = append(args, f.EndDate+" 23:59:59")
	}
	if f.Year > 0 {
		clauses = append(clauses, "strftime('%Y', trans_date) = ?")
		args = append(args, fmt.Sprintf("%04d", f.Year))
	}
	if f.Month > 0 {
		clauses = append(clauses, "strftime('%m', trans_date) = ?")
		args = append(args, fmt.Sprintf("%02d", f.Month))
	}
	if len(f.TagIDs) > 0 {
		// Subquery to ensure ALL specified tags match (intersection).
		placeholders := strings.Repeat("?,", len(f.TagIDs))
		placeholders = placeholders[:len(placeholders)-1]
		clauses = append(clauses, fmt.Sprintf(`id IN (
			SELECT transaction_id FROM transaction_tags
			WHERE tag_id IN (%s)
			GROUP BY transaction_id
			HAVING COUNT(DISTINCT tag_id) = ?
		)`, placeholders))
		for _, id := range f.TagIDs {
			args = append(args, id)
		}
		args = append(args, len(f.TagIDs))
	}
	if len(clauses) == 0 {
		return "", nil
	}
	return " WHERE " + strings.Join(clauses, " AND "), args
}
