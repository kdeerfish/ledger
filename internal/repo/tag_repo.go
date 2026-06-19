package repo

import (
	"database/sql"
	"fmt"

	"github.com/kdeerfish/ledger/internal/domain"
)

// TagRepo handles the tags and transaction_tags tables.
type TagRepo struct{ db DB }

func NewTagRepo(d DB) *TagRepo { return &TagRepo{db: d} }

// List returns all tags with their usage count.
func (r *TagRepo) List() ([]domain.Tag, error) {
	rows, err := r.db.Query(`SELECT t.id, t.name, IFNULL(t.color, '#6366f1'),
		IFNULL(t.created_at, ''),
		(SELECT COUNT(*) FROM transaction_tags tt WHERE tt.tag_id = t.id) AS usage_count
		FROM tags t ORDER BY t.name`)
	if err != nil {
		return nil, err
	}
	defer rows.Close()
	var out []domain.Tag
	for rows.Next() {
		var t domain.Tag
		if err := rows.Scan(&t.ID, &t.Name, &t.Color, &t.CreatedAt, &t.UsageCount); err != nil {
			return nil, err
		}
		out = append(out, t)
	}
	return out, rows.Err()
}

// Create inserts a tag and returns its id.
func (r *TagRepo) Create(name, color string) (int64, error) {
	if color == "" {
		color = "#6366f1"
	}
	res, err := r.db.Exec(`INSERT INTO tags(name, color) VALUES(?, ?)
		ON CONFLICT(name) DO UPDATE SET color = excluded.color`, name, color)
	if err != nil {
		return 0, err
	}
	id, _ := res.LastInsertId()
	if id == 0 {
		// Already existed - look it up.
		row := r.db.QueryRow(`SELECT id FROM tags WHERE name = ?`, name)
		if err := row.Scan(&id); err != nil {
			return 0, err
		}
	}
	return id, nil
}

// Get fetches a single tag by id.
func (r *TagRepo) Get(id int64) (*domain.Tag, error) {
	row := r.db.QueryRow(`SELECT id, name, IFNULL(color, '#6366f1'),
		IFNULL(created_at, '') FROM tags WHERE id = ?`, id)
	var t domain.Tag
	if err := row.Scan(&t.ID, &t.Name, &t.Color, &t.CreatedAt); err != nil {
		if err == sql.ErrNoRows {
			return nil, domain.ErrNotFound
		}
		return nil, err
	}
	return &t, nil
}

// Delete removes a tag (and its joins via ON DELETE CASCADE).
func (r *TagRepo) Delete(id int64) error {
	res, err := r.db.Exec(`DELETE FROM tags WHERE id = ?`, id)
	if err != nil {
		return err
	}
	n, _ := res.RowsAffected()
	if n == 0 {
		return domain.ErrNotFound
	}
	return nil
}

// Count returns the total tag count.
func (r *TagRepo) Count() (int, error) {
	var n int
	row := r.db.QueryRow(`SELECT COUNT(*) FROM tags`)
	return n, row.Scan(&n)
}

// FindOrCreate returns the id for name, creating the row when missing.
func (r *TagRepo) FindOrCreate(name string) (int64, error) {
	var id int64
	row := r.db.QueryRow(`SELECT id FROM tags WHERE name = ?`, name)
	if err := row.Scan(&id); err == nil {
		return id, nil
	} else if err != sql.ErrNoRows {
		return 0, err
	}
	return r.Create(name, "#6366f1")
}

// ResolveNames converts tag names to ids, creating missing ones. Used when
// persisting a record template's tag list.
func (r *TagRepo) ResolveNames(names []string) ([]int64, error) {
	out := make([]int64, 0, len(names))
	for _, n := range names {
		if n == "" {
			continue
		}
		id, err := r.FindOrCreate(n)
		if err != nil {
			return nil, fmt.Errorf("resolve tag %q: %w", n, err)
		}
		out = append(out, id)
	}
	return out, nil
}
