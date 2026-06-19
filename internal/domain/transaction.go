package domain

import "time"

// TxnType is a strict Chinese enum for transaction direction.
type TxnType string

const (
	TxnExpense TxnType = "支出"
	TxnIncome  TxnType = "收入"
)

// Valid reports whether the type is one of the supported values.
func (t TxnType) Valid() bool {
	return t == TxnExpense || t == TxnIncome
}

// Transaction mirrors a row in the `transactions` table. Nullable columns are
// represented by *string; IsDeleted is *bool so a missing column reads as false.
type Transaction struct {
	ID          int64     `json:"id"          db:"id"`
	Type        TxnType   `json:"type"        db:"type"`
	Amount      float64   `json:"amount"      db:"amount"`
	Category    *string   `json:"category"    db:"category"`
	Subcategory *string   `json:"subcategory" db:"subcategory"`
	Account     *string   `json:"account"     db:"account"`
	Project     *string   `json:"project"     db:"project"`
	Member      *string   `json:"member"      db:"member"`
	Merchant    *string   `json:"merchant"    db:"merchant"`
	Note        *string   `json:"note"        db:"note"`
	TransDate   string    `json:"trans_date"  db:"trans_date"` // YYYY-MM-DD HH:MM:SS
	IsDeleted   bool      `json:"is_deleted"  db:"is_deleted"`
	TagIDs      []int64   `json:"tag_ids,omitempty"     db:"-"`
	TagNames    []string  `json:"tags,omitempty"        db:"-"`
	CreatedAt   time.Time `json:"-"           db:"-"`
}

// ListFilter holds the query parameters for List / Search / Filter.
// Zero values mean "no constraint".
type ListFilter struct {
	Limit          int
	Offset         int
	IncludeDeleted bool
	Type           TxnType
	Category       string
	Subcategory    string
	Account        string
	Project        string
	Member         string
	Merchant       string
	Keyword        string
	StartDate      string // YYYY-MM-DD
	EndDate        string // YYYY-MM-DD
	Year           int
	Month          int
	TagIDs         []int64
	SearchType     string // all/note/category/merchant
}

// Summary is the per-period aggregate returned by Summary().
type Summary struct {
	Income    float64 `json:"income"`
	Expense   float64 `json:"expense"`
	Balance   float64 `json:"balance"`
	Count     int     `json:"count"`
	IncomeN   int     `json:"income_count"`
	ExpenseN  int     `json:"expense_count"`
	DailyAvg  float64 `json:"daily_avg"`
	StartDate string  `json:"start_date"`
	EndDate   string  `json:"end_date"`
}

// StatRow is one row of a GetStatistics result.
type StatRow struct {
	Group     string  `json:"group"`
	Income    float64 `json:"income"`
	Expense   float64 `json:"expense"`
	Balance   float64 `json:"balance"`
	Count     int     `json:"count"`
	SubGroups []StatRow `json:"sub_groups,omitempty"`
}

// Suggestion groups auto-complete hints for the front-end.
type Suggestion struct {
	Categories    []SuggestionItem `json:"categories"`
	Subcategories []SuggestionItem `json:"subcategories"`
	Accounts      []SuggestionItem `json:"accounts"`
	Merchants     []SuggestionItem `json:"merchants"`
	Projects      []SuggestionItem `json:"projects"`
	Members       []SuggestionItem `json:"members"`
	Frequent      []SuggestionItem `json:"frequent"`
}

// SuggestionItem is one auto-complete entry with a usage count.
type SuggestionItem struct {
	Value string `json:"value"`
	Count int    `json:"count"`
}

// Info aggregates database metadata returned by /api/info.
type Info struct {
	TotalRecords    int    `json:"total_records"`
	ActiveRecords   int    `json:"active_records"`
	DeletedRecords  int    `json:"deleted_records"`
	DateRangeStart  string `json:"date_range_start"`
	DateRangeEnd    string `json:"date_range_end"`
	TagCount        int    `json:"tag_count"`
	DBPath          string `json:"db_path"`
}
