package domain

// Budget mirrors a row in the `budgets` table.
type Budget struct {
	ID             int64   `json:"id"              db:"id"`
	Category       string  `json:"category"        db:"category"`
	Year           int     `json:"year"            db:"year"`
	Month          int     `json:"month"           db:"month"`
	Amount         float64 `json:"amount"          db:"amount"`
	DimensionType  string  `json:"dimension_type"  db:"dimension_type"` // category/account/member/project/merchant
	DimensionValue *string `json:"dimension_value" db:"dimension_value"`
	CreatedAt      string  `json:"created_at"      db:"created_at"`
}

// BudgetCheck is one row of the budget utilisation report.
type BudgetCheck struct {
	BudgetID   int64   `json:"budget_id"`
	Category   string  `json:"category"`
	Year       int     `json:"year"`
	Month      int     `json:"month"`
	Dimension  string  `json:"dimension_type"`
	DimValue   string  `json:"dimension_value"`
	Budget     float64 `json:"budget"`
	Spent      float64 `json:"spent"`
	Remaining  float64 `json:"remaining"`
	Percentage float64 `json:"percentage"`
}

// BudgetTemplate mirrors a row in the `budget_templates` table.
type BudgetTemplate struct {
	ID             int64   `json:"id"              db:"id"`
	Name           string  `json:"name"            db:"name"`
	Description    *string `json:"description"     db:"description"`
	Category       *string `json:"category"        db:"category"`
	Amount         float64 `json:"amount"          db:"amount"`
	DimensionType  string  `json:"dimension_type"  db:"dimension_type"`
	DimensionValue *string `json:"dimension_value" db:"dimension_value"`
	Account        *string `json:"account"         db:"account"`
	Project        *string `json:"project"         db:"project"`
	Member         *string `json:"member"          db:"member"`
	Merchant       *string `json:"merchant"        db:"merchant"`
	Note           *string `json:"note"            db:"note"`
	Year           *int    `json:"year"            db:"year"`
	Month          *int    `json:"month"           db:"month"`
	CreatedAt      string  `json:"created_at"      db:"created_at"`
}

// RecordTemplate mirrors a row in the `record_templates` table.
type RecordTemplate struct {
	ID           int64   `json:"id"             db:"id"`
	Name         string  `json:"name"           db:"name"`
	TemplateType string  `json:"template_type"  db:"template_type"` // 通用/支出/收入
	Type         *string `json:"type"           db:"type"`
	Amount       float64 `json:"amount"         db:"amount"`
	Category     *string `json:"category"       db:"category"`
	Subcategory  *string `json:"subcategory"    db:"subcategory"`
	Account      *string `json:"account"        db:"account"`
	Project      *string `json:"project"        db:"project"`
	Member       *string `json:"member"         db:"member"`
	Merchant     *string `json:"merchant"       db:"merchant"`
	Note         *string `json:"note"           db:"note"`
	Description  *string `json:"description"    db:"description"`
	UsageCount   int     `json:"usage_count"    db:"usage_count"`
	LastUsedAt   *string `json:"last_used_at"   db:"last_used_at"`
	CreatedAt    string  `json:"created_at"     db:"created_at"`
	Tags         string  `json:"tags"           db:"tags"` // comma-separated tag names
}
