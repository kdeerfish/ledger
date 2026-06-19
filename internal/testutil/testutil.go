// Package testutil wires the in-memory equivalent of the Python project
// `tests/conftest.py` `temp_db` / `sample_db` fixtures. Every test that
// needs a real DB calls NewTestDB() (for *testing.T) or NewTestDBT()
// (for *testing.B benchmarks) to get an isolated SQLite file.
//
// Important: this package only depends on db + repo (no service) so it
// can be imported from inside the service package's *_test.go files
// without creating an import cycle.
package testutil

import (
	"database/sql"
	"path/filepath"

	"github.com/kdeerfish/ledger/internal/db"
	"github.com/kdeerfish/ledger/internal/repo"
)

// TB is the union of *testing.T and *testing.B that NewTestDBT accepts.
// It exists so benchmark code can reuse the same fixture as unit tests
// without duplicating the setup logic.
type TB interface {
	Helper()
	TempDir() string
	Cleanup(func())
}

// Fixture is the bag of dependencies every test needs. We expose the raw
// repos and *sql.DB so test code can wire up whatever services it needs;
// this avoids the import cycle that would arise from testutil importing
// internal/service directly.
type Fixture struct {
	DB      *sql.DB
	TxRepo  *repo.TransactionRepo
	TagRepo *repo.TagRepo
	BdgRepo *repo.BudgetRepo
	BTRepo  *repo.BudgetTemplateRepo
	RTRepo  *repo.RecordTemplateRepo
}

// NewTestDB is the historical API used by every service test. It returns
// a Fixture (raw repos), not pre-wired services. Tests that need services
// wire them inline:
//
//	h := testutil.NewTestDB(t)
//	tx := service.NewTransactionService(h.TxRepo, h.TagRepo)
func NewTestDB(tb TB) *Fixture {
	return NewTestDBT(tb)
}

// NewTestDBT is the generic constructor used by both *testing.T and *testing.B.
// The cleanup is handled by tb.TempDir() and the deferred Close().
//
// We avoid stretchr/testify assertions here (where they can't be used
// from a *testing.B) by panicking on db.Open failure: a temp dir that
// can't host a SQLite file means the host environment is broken in a
// way the test cannot recover from.
func NewTestDBT(tb TB) *Fixture {
	tb.Helper()
	d, err := db.Open(filepath.Join(tb.TempDir(), "test.db"))
	if err != nil {
		panic("testutil: db.Open: " + err.Error())
	}
	tb.Cleanup(func() { _ = d.Close() })
	return &Fixture{
		DB:      d,
		TxRepo:  repo.NewTransactionRepo(d),
		TagRepo: repo.NewTagRepo(d),
		BdgRepo: repo.NewBudgetRepo(d),
		BTRepo:  repo.NewBudgetTemplateRepo(d),
		RTRepo:  repo.NewRecordTemplateRepo(d),
	}
}
