package service

import (
	"strings"
	"testing"
)

// FuzzParseCSVDate stress-tests the CSV date parser. The original Python
// implementation only accepted "2006/01/02 15:04" and "2006/01/02"; Go's
// version uses time.Parse under the hood, so this fuzz target mainly
// verifies the function never panics and rejects garbage gracefully.
//
// Run with:
//
//	make fuzz-quick         # 5s smoke test
//	make fuzz               # 60s default
//	go test -run=^$ -fuzz=ParseCSVDate -fuzztime=10s ./internal/service
func FuzzParseCSVDate(f *testing.F) {
	// Seed corpus: the formats we know work + a handful of common typos.
	f.Add("2026/06/19 12:00")
	f.Add("2026/06/19")
	f.Add("2026-06-19 12:00:00")
	f.Add("2026-06-19")
	f.Add("2026/13/40 25:99")        // impossible values
	f.Add("not a date")
	f.Add("")
	f.Add(" ")
	f.Add("2026/6/9 1:2")             // short
	f.Add("2026/06/19T12:00:00Z")     // ISO 8601
	f.Add("19/06/2026")               // dd/mm/yyyy
	f.Add("2026_06_19")
	f.Add("\x00\x00\x00")             // null bytes
	f.Add(strings.Repeat("9", 1000))  // very long
	f.Add("2026/06/19 12:00:00.000")  // with subseconds

	f.Fuzz(func(t *testing.T, s string) {
		out, err := parseCSVDate(s)
		// Two invariants: never panic, and either error or non-empty
		// result when err is nil.
		if err == nil && out == "" {
			t.Errorf("parseCSVDate(%q) returned empty string with nil error", s)
		}
		// If we claimed to parse, the result must be a valid time.
		if err == nil {
			if len(out) != len("2006-01-02 15:04:05") {
				t.Errorf("parseCSVDate(%q) returned wrong-length %q", s, out)
			}
		}
	})
}

// FuzzSplitCSV fuzzes the template-tag CSV splitter. Many real-world bugs
// hide in "comma + whitespace" handling.
func FuzzSplitCSV(f *testing.F) {
	f.Add("a,b,c")
	f.Add("")
	f.Add(",,,")
	f.Add(" a , b , c ")
	f.Add("a,")
	f.Add(",a")
	f.Add("a||b||c")
	f.Add("\"quoted, value\"")
	f.Add(strings.Repeat("x,", 1000))

	f.Fuzz(func(t *testing.T, s string) {
		out := splitCSV(s)
		// Invariant: output contains no empty strings (we filter them).
		for _, p := range out {
			if p == "" {
				t.Errorf("splitCSV(%q) returned empty part: %v", s, out)
			}
		}
		// Invariant: result length ≤ number of commas + 1.
		if len(out) > strings.Count(s, ",")+1 {
			t.Errorf("splitCSV(%q) returned %d parts but only %d commas", s, len(out), strings.Count(s, ","))
		}
	})
}
