// Package cli implements the cobra command tree that mirrors the original
// Python scripts/cli.py surface area.
package cli

import (
	"fmt"
	"io"
	"os"
	"path/filepath"
	"strconv"
	"strings"
	"time"

	"github.com/kdeerfish/ledger/internal/config"
	"github.com/kdeerfish/ledger/internal/db"
	"github.com/kdeerfish/ledger/internal/domain"
	"github.com/kdeerfish/ledger/internal/repo"
	"github.com/kdeerfish/ledger/internal/service"
)

// App holds the wired-up dependencies shared by every command.
type App struct {
	Cfg        *config.Config
	DB         *dbHandle
	Tx         *service.TransactionService
	Budget     *service.BudgetService
	Template   *service.TemplateService
	Tag        *service.TagService
	Out        io.Writer
	Err        io.Writer
	suppressOK bool
}

// dbHandle keeps the *sql.DB alive for the duration of the process.
type dbHandle struct{ inner interface{ Close() error } }

func (h *dbHandle) Close() error { return h.inner.Close() }

// NewApp builds an App with the given config, ready for Execute.
func NewApp(cfg *config.Config, out, errOut io.Writer) (*App, error) {
	if out == nil {
		out = os.Stdout
	}
	if errOut == nil {
		errOut = os.Stderr
	}
	if cfg == nil {
		var err error
		cfg, err = config.Load()
		if err != nil {
			return nil, err
		}
	}
	d, err := db.Open(cfg.DBPath)
	if err != nil {
		return nil, err
	}
	txRepo := repo.NewTransactionRepo(d)
	tagRepo := repo.NewTagRepo(d)
	budgetRepo := repo.NewBudgetRepo(d)
	btRepo := repo.NewBudgetTemplateRepo(d)
	rtRepo := repo.NewRecordTemplateRepo(d)
	tx := service.NewTransactionService(txRepo, tagRepo)
	tpl := service.NewTemplateService(rtRepo, tagRepo, tx)
	return &App{
		Cfg:      cfg,
		DB:       &dbHandle{inner: d},
		Tx:       tx,
		Budget:   service.NewBudgetService(budgetRepo, btRepo),
		Template: tpl,
		Tag:      service.NewTagService(tagRepo, txRepo),
		Out:      out,
		Err:      errOut,
	}, nil
}

// Close releases the database connection.
func (a *App) Close() {
	if a.DB != nil {
		_ = a.DB.Close()
	}
}

// Print writes a success/info line to stdout.
func (a *App) Print(format string, args ...any) {
	if a.suppressOK {
		return
	}
	fmt.Fprintf(a.Out, format+"\n", args...)
}

// ErrPrint writes a failure line to stderr.
func (a *App) ErrPrint(format string, args ...any) {
	fmt.Fprintf(a.Err, format+"\n", args...)
}

// OK is a convenience for printing ✅ success messages.
func (a *App) OK(format string, args ...any) { a.Print("✅ "+format, args...) }

// Fail is a convenience for printing ❌ failure messages.
func (a *App) Fail(format string, args ...any) { a.ErrPrint("❌ "+format, args...) }



// parseFloat parses a string flag into a float64.
func parseFloat(s string) (float64, error) {
	if s == "" {
		return 0, nil
	}
	return strconv.ParseFloat(s, 64)
}

// parseDate validates a YYYY-MM-DD or YYYY-MM-DD HH:MM:SS input. Empty means
// "use now" (handled by the service layer).
func parseDate(s string) error {
	if s == "" {
		return nil
	}
	if _, err := time.Parse("2006-01-02 15:04:05", s); err == nil {
		return nil
	}
	if _, err := time.Parse("2006-01-02", s); err == nil {
		return nil
	}
	return fmt.Errorf("invalid date %q (expected YYYY-MM-DD or YYYY-MM-DD HH:MM:SS)", s)
}

// parseYearMonth validates "YYYY" or "YYYY-MM" inputs.
func parseYearMonth(s string) (year, month int, err error) {
	if s == "" {
		return 0, 0, nil
	}
	parts := strings.Split(s, "-")
	if len(parts) == 1 {
		y, e := strconv.Atoi(parts[0])
		if e != nil {
			return 0, 0, e
		}
		return y, 0, nil
	}
	if len(parts) == 2 {
		y, e := strconv.Atoi(parts[0])
		if e != nil {
			return 0, 0, e
		}
		m, e := strconv.Atoi(parts[1])
		if e != nil {
			return 0, 0, e
		}
		return y, m, nil
	}
	return 0, 0, fmt.Errorf("invalid period %q", s)
}

// pathAbs resolves a relative path against cwd, used by import/export.
func pathAbs(p string) (string, error) {
	if filepath.IsAbs(p) {
		return p, nil
	}
	cwd, err := os.Getwd()
	if err != nil {
		return "", err
	}
	return filepath.Join(cwd, p), nil
}

// derefStr is a small helper for printing optional columns.
func derefStr(p *string) string {
	if p == nil {
		return ""
	}
	return *p
}


// isNoConfirm returns true when the user did NOT pass --confirm.
func isNoConfirm(confirm bool) bool { return !confirm }

// exportData wraps the service.Export call with file handling.
func (a *App) exportData(filter domain.ListFilter, outPath, format string) error {
	if outPath == "" {
		return fmt.Errorf("--output is required")
	}
	abs, err := pathAbs(outPath)
	if err != nil {
		return err
	}
	f, err := os.Create(abs)
	if err != nil {
		return err
	}
	defer f.Close()
	return a.Tx.Export(filter, f, service.ExportFormat(format))
}
