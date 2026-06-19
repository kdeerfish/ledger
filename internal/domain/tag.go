package domain

// Tag mirrors a row in the `tags` table.
type Tag struct {
	ID         int64  `json:"id"          db:"id"`
	Name       string `json:"name"        db:"name"`
	Color      string `json:"color"       db:"color"`
	CreatedAt  string `json:"created_at"  db:"created_at"`
	UsageCount int    `json:"usage_count" db:"-"`
}
