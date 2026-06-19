// Package service_test hosts the *Benchmark tests for the service package.
// We use an external test package (not `package service`) so the tests
// can import the testutil fixture without creating a cycle: testutil
// already imports `internal/service`, so a test inside `package service`
// that imports testutil would form a loop.
package service_test

import (
	"fmt"
	"strings"
	"testing"

	"github.com/kdeerfish/ledger/internal/domain"
	"github.com/kdeerfish/ledger/internal/service"
	"github.com/kdeerfish/ledger/internal/testutil"
)

// BenchmarkImportCSV measures end-to-end CSV ingestion. Used to track
// regressions when we change the SQL path or the date parser.
//
// Run with:
//
//	make bench                       # all benchmarks, 3s each
//	go test -bench=ImportCSV -benchmem ./internal/service
func BenchmarkImportCSV(b *testing.B) {
	// Build a 1000-row CSV once and reuse it.
	var sb strings.Builder
	sb.WriteString("交易类型,金额,日期,类别,子类别,账户,项目,成员,商家,备注\n")
	for i := 0; i < 1000; i++ {
		fmt.Fprintf(&sb, "支出,%.2f,2026/06/19 12:00,食品,午餐%d,微信,日常,我,便利店%d,沙拉\n",
			float64(i+1), i, i)
	}
	csvData := sb.String()

	b.ResetTimer()
	b.ReportAllocs()
	for i := 0; i < b.N; i++ {
		b.StopTimer()
		// Fresh DB per iteration so the duplicate check has to scan.
		f := testutil.NewTestDBT(&benchB{b: b, td: b.TempDir()})
		tx := service.NewTransactionService(f.TxRepo, f.TagRepo)
		reader := strings.NewReader(csvData)
		b.StartTimer()

		res, err := tx.ImportCSV(reader)
		if err != nil {
			b.Fatalf("ImportCSV: %v", err)
		}
		if res.Imported != 1000 {
			b.Fatalf("expected 1000 imports, got %d", res.Imported)
		}
	}
}

// BenchmarkListTransactions measures the hot path for the Web dashboard.
func BenchmarkListTransactions(b *testing.B) {
	f := testutil.NewTestDBT(&benchB{b: b, td: b.TempDir()})
	tx := service.NewTransactionService(f.TxRepo, f.TagRepo)
	// Seed 5000 transactions.
	for i := 0; i < 5000; i++ {
		cat := "食品"
		if i%2 == 0 {
			cat = "交通"
		}
		_, _ = tx.Add(service.AddInput{
			Type:      "支出",
			Amount:    float64(i%100) + 1,
			Category:  cat,
			Account:   "微信",
			TransDate: "2026-06-19 12:00:00",
			Force:     true,
		})
	}
	b.ResetTimer()
	b.ReportAllocs()
	for i := 0; i < b.N; i++ {
		_, _, err := tx.List(benchFilter())
		if err != nil {
			b.Fatalf("List: %v", err)
		}
	}
}

// BenchmarkStatisticsByCategory measures the dashboard chart path.
func BenchmarkStatisticsByCategory(b *testing.B) {
	f := testutil.NewTestDBT(&benchB{b: b, td: b.TempDir()})
	tx := service.NewTransactionService(f.TxRepo, f.TagRepo)
	for i := 0; i < 1000; i++ {
		cat := "食品"
		if i%2 == 0 {
			cat = "交通"
		}
		_, _ = tx.Add(service.AddInput{
			Type: "支出", Amount: 10, Category: cat, TransDate: "2026-06-19 12:00:00", Force: true,
		})
	}
	b.ResetTimer()
	b.ReportAllocs()
	for i := 0; i < b.N; i++ {
		_, err := tx.Statistics("category", "", "", "")
		if err != nil {
			b.Fatalf("Statistics: %v", err)
		}
	}
}

// BenchmarkCheckDuplicate measures the hot path on every Add.
func BenchmarkCheckDuplicate(b *testing.B) {
	f := testutil.NewTestDBT(&benchB{b: b, td: b.TempDir()})
	tx := service.NewTransactionService(f.TxRepo, f.TagRepo)
	for i := 0; i < 1000; i++ {
		_, _ = tx.Add(service.AddInput{
			Type: "支出", Amount: 1, Category: "食品", TransDate: "2026-06-19 12:00:00", Force: true,
		})
	}
	b.ResetTimer()
	b.ReportAllocs()
	for i := 0; i < b.N; i++ {
		_, _ = f.TxRepo.CheckDuplicate("2026-06-19 12:00:00", "支出", 1, "食品")
	}
}

// benchB adapts *testing.B to the testutil.TB interface so benchmarks can
// share the same fixture as unit tests. We cache TempDir() per benchmark
// run so repeated calls return the same path (testutil's NewTestDBT only
// calls it once, but we keep it safe for future reuse).
type benchB struct {
	b  *testing.B
	td string
}

func (bb *benchB) Helper()           { bb.b.Helper() }
func (bb *benchB) TempDir() string   { return bb.td }
func (bb *benchB) Cleanup(fn func()) { bb.b.Cleanup(fn) }

// benchFilter is a tiny shared default used by all benchmarks.
func benchFilter() domain.ListFilter {
	return domain.ListFilter{Limit: 50}
}
