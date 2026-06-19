package db

import (
	"database/sql"
	"fmt"
)

// Migrate creates the meta table (if missing), inspects the current schema
// version, and applies any pending migrations. The result is idempotent and
// safe to run on every startup.
func Migrate(d *sql.DB) error {
	if _, err := d.Exec(`CREATE TABLE IF NOT EXISTS meta (
		key   TEXT PRIMARY KEY,
		value TEXT NOT NULL
	)`); err != nil {
		return fmt.Errorf("create meta: %w", err)
	}

	current, err := readVersion(d)
	if err != nil {
		return err
	}

	// Base schema (v0). created unconditionally when current < 1.
	if current < 1 {
		if err := applyV0(d); err != nil {
			return err
		}
	}
	// v1: add is_deleted column + indexes (matches Python db.py v2 migration).
	if current < 2 {
		if err := applyV1(d); err != nil {
			return err
		}
	}
	return setVersion(d, CurrentVersion)
}

func readVersion(d *sql.DB) (int, error) {
	var v sql.NullString
	row := d.QueryRow(`SELECT value FROM meta WHERE key = 'db_version'`)
	if err := row.Scan(&v); err != nil {
		if err == sql.ErrNoRows {
			return 0, nil
		}
		return 0, fmt.Errorf("read version: %w", err)
	}
	if !v.Valid {
		return 0, nil
	}
	var n int
	if _, err := fmt.Sscanf(v.String, "%d", &n); err != nil {
		return 0, fmt.Errorf("parse version %q: %w", v.String, err)
	}
	return n, nil
}

func setVersion(d *sql.DB, v int) error {
	_, err := d.Exec(`INSERT INTO meta(key, value) VALUES('db_version', ?)
		ON CONFLICT(key) DO UPDATE SET value = excluded.value`, fmt.Sprintf("%d", v))
	return err
}

// applyV0 creates every table from scratch. Identical layout to the original
// Python project (ledger_modules/db.py v1).
func applyV0(d *sql.DB) error {
	stmts := []string{
		`CREATE TABLE IF NOT EXISTS transactions (
			id           INTEGER PRIMARY KEY AUTOINCREMENT,
			type         TEXT    NOT NULL,
			amount       REAL    NOT NULL,
			category     TEXT,
			subcategory  TEXT,
			account      TEXT,
			project      TEXT,
			member       TEXT,
			merchant     TEXT,
			note         TEXT,
			trans_date   TEXT    NOT NULL,
			created_at   TEXT    DEFAULT (datetime('now','localtime'))
		)`,
		`CREATE TABLE IF NOT EXISTS budgets (
			id              INTEGER PRIMARY KEY AUTOINCREMENT,
			category        TEXT NOT NULL,
			year            INTEGER NOT NULL,
			month           INTEGER NOT NULL,
			amount          REAL NOT NULL,
			dimension_type  TEXT DEFAULT 'category',
			dimension_value TEXT,
			created_at      TEXT DEFAULT (datetime('now','localtime')),
			UNIQUE(category, year, month, dimension_type, dimension_value)
		)`,
		`CREATE TABLE IF NOT EXISTS budget_templates (
			id              INTEGER PRIMARY KEY AUTOINCREMENT,
			name            TEXT NOT NULL,
			description     TEXT,
			category        TEXT,
			amount          REAL DEFAULT 0,
			dimension_type  TEXT DEFAULT 'category',
			dimension_value TEXT,
			account         TEXT,
			project         TEXT,
			member          TEXT,
			merchant        TEXT,
			note            TEXT,
			year            INTEGER,
			month           INTEGER,
			created_at      TEXT NOT NULL DEFAULT (datetime('now','localtime'))
		)`,
		`CREATE TABLE IF NOT EXISTS record_templates (
			id             INTEGER PRIMARY KEY AUTOINCREMENT,
			name           TEXT NOT NULL,
			description    TEXT,
			template_type  TEXT NOT NULL DEFAULT '通用',
			type           TEXT,
			amount         REAL DEFAULT 0,
			category       TEXT,
			subcategory    TEXT,
			account        TEXT,
			project        TEXT,
			member         TEXT,
			merchant       TEXT,
			note           TEXT,
			usage_count    INTEGER DEFAULT 0,
			last_used_at   TEXT,
			created_at     TEXT NOT NULL DEFAULT (datetime('now','localtime'))
		)`,
		`CREATE TABLE IF NOT EXISTS tags (
			id         INTEGER PRIMARY KEY AUTOINCREMENT,
			name       TEXT NOT NULL UNIQUE,
			color      TEXT DEFAULT '#6366f1',
			created_at TEXT DEFAULT (datetime('now','localtime'))
		)`,
		`CREATE TABLE IF NOT EXISTS transaction_tags (
			transaction_id INTEGER NOT NULL,
			tag_id         INTEGER NOT NULL,
			PRIMARY KEY (transaction_id, tag_id),
			FOREIGN KEY (transaction_id) REFERENCES transactions(id) ON DELETE CASCADE,
			FOREIGN KEY (tag_id)         REFERENCES tags(id)         ON DELETE CASCADE
		)`,
	}
	for _, s := range stmts {
		if _, err := d.Exec(s); err != nil {
			return fmt.Errorf("create table: %w (%s)", err, firstLine(s))
		}
	}
	return nil
}

// applyV1 adds the is_deleted column (if missing) and three indexes. Mirrors
// the lazy migrations in Python db.py:145-165.
func applyV1(d *sql.DB) error {
	if !hasColumn(d, "transactions", "is_deleted") {
		if _, err := d.Exec(`ALTER TABLE transactions ADD COLUMN is_deleted INTEGER DEFAULT 0`); err != nil {
			return fmt.Errorf("add is_deleted: %w", err)
		}
	}
	if !hasColumn(d, "record_templates", "tags") {
		if _, err := d.Exec(`ALTER TABLE record_templates ADD COLUMN tags TEXT DEFAULT ''`); err != nil {
			return fmt.Errorf("add tags: %w", err)
		}
	}
	stmts := []string{
		`CREATE INDEX IF NOT EXISTS idx_trans_date     ON transactions(trans_date)`,
		`CREATE INDEX IF NOT EXISTS idx_trans_category ON transactions(category)`,
		`CREATE INDEX IF NOT EXISTS idx_trans_type     ON transactions(type)`,
	}
	for _, s := range stmts {
		if _, err := d.Exec(s); err != nil {
			return fmt.Errorf("create index: %w", err)
		}
	}
	return nil
}

func hasColumn(d *sql.DB, table, column string) bool {
	rows, err := d.Query(fmt.Sprintf(`PRAGMA table_info(%s)`, table))
	if err != nil {
		return false
	}
	defer rows.Close()
	for rows.Next() {
		var cid int
		var name, ctype string
		var notnull, dflt, pk sql.NullString
		var nn int
		if err := rows.Scan(&cid, &name, &ctype, &notnull, &dflt, &pk); err != nil {
			return false
		}
		_ = nn
		if name == column {
			return true
		}
	}
	return false
}

func firstLine(s string) string {
	for i, c := range s {
		if c == '\n' {
			return s[:i]
		}
	}
	return s
}
