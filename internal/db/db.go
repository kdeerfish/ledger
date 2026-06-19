// Package db owns the SQLite connection pool and schema migrations.
package db

import (
	"context"
	"database/sql"
	"fmt"
	"time"

	_ "modernc.org/sqlite" // pure-Go SQLite driver, registers as "sqlite"
)

// Current schema version. Bump and add a migration in migrations.go when the
// schema changes.
const CurrentVersion = 2

// Open opens (or creates) the SQLite database at path, applies pragmas
// matching the original Python project, and runs pending migrations.
func Open(path string) (*sql.DB, error) {
	// DSN: enable foreign keys, use WAL for better concurrency, set busy
	// timeout to 5s. Foreign keys were also enabled in the Python schema
	// (only transaction_tags actually relies on the cascade).
	dsn := fmt.Sprintf("file:%s?_pragma=foreign_keys(1)&_pragma=journal_mode(WAL)&_pragma=busy_timeout(5000)", path)
	d, err := sql.Open("sqlite", dsn)
	if err != nil {
		return nil, fmt.Errorf("open sqlite: %w", err)
	}
	// SQLite serializes writes; a small connection pool keeps the reader
	// fast without exhausting the lock.
	d.SetMaxOpenConns(1)
	d.SetMaxIdleConns(1)
	d.SetConnMaxLifetime(time.Hour)

	ctx, cancel := context.WithTimeout(context.Background(), 5*time.Second)
	defer cancel()
	if err := d.PingContext(ctx); err != nil {
		return nil, fmt.Errorf("ping sqlite: %w", err)
	}
	if err := Migrate(d); err != nil {
		_ = d.Close()
		return nil, fmt.Errorf("migrate: %w", err)
	}
	return d, nil
}
