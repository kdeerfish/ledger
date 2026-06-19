package main

import (
	"database/sql"
	"encoding/csv"
	"encoding/json"
	"fmt"
	"os"
	"path/filepath"
	"runtime"
	"strconv"
	"strings"
	"time"

	_ "modernc.org/sqlite"
	"github.com/spf13/cobra"
)

const version = "0.1.0"

var db *sql.DB

func dbPath() string {
	if p := os.Getenv("LEDGER_DB_PATH"); p != "" {
		return p
	}
	home, _ := os.UserHomeDir()
	return filepath.Join(home, ".ledger-cli", "ledger.db")
}

func ensureDir(p string) {
	os.MkdirAll(filepath.Dir(p), 0755)
}

func openDB() {
	p := dbPath()
	ensureDir(p)
	var err error
	db, err = sql.Open("sqlite", p+"?_journal_mode=WAL&_foreign_keys=ON")
	if err != nil {
		fmt.Fprintf(os.Stderr, "open db failed: %v\n", err)
		os.Exit(1)
	}
	migrate()
}

func migrate() {
	stmts := []string{
		`CREATE TABLE IF NOT EXISTS transactions (
			id INTEGER PRIMARY KEY AUTOINCREMENT,
			type TEXT NOT NULL CHECK(type IN ('expense','income')),
			amount REAL NOT NULL,
			category TEXT NOT NULL DEFAULT '',
			subcategory TEXT DEFAULT '',
			account TEXT DEFAULT '',
			project TEXT DEFAULT '',
			member TEXT DEFAULT '',
			merchant TEXT DEFAULT '',
			note TEXT DEFAULT '',
			trans_date TEXT NOT NULL,
			is_deleted INTEGER NOT NULL DEFAULT 0,
			created_at TEXT NOT NULL DEFAULT (datetime('now','localtime'))
		)`,
		`CREATE TABLE IF NOT EXISTS tags (
			id INTEGER PRIMARY KEY AUTOINCREMENT,
			name TEXT NOT NULL UNIQUE,
			color TEXT DEFAULT '#6c757d'
		)`,
		`CREATE TABLE IF NOT EXISTS transaction_tags (
			transaction_id INTEGER NOT NULL,
			tag_id INTEGER NOT NULL,
			PRIMARY KEY (transaction_id, tag_id),
			FOREIGN KEY (transaction_id) REFERENCES transactions(id) ON DELETE CASCADE,
			FOREIGN KEY (tag_id) REFERENCES tags(id) ON DELETE CASCADE
		)`,
		`CREATE TABLE IF NOT EXISTS budgets (
			id INTEGER PRIMARY KEY AUTOINCREMENT,
			year INTEGER NOT NULL,
			month INTEGER NOT NULL,
			category TEXT NOT NULL DEFAULT '',
			dimension_type TEXT DEFAULT '',
			dimension_value TEXT DEFAULT '',
			amount REAL NOT NULL,
			UNIQUE(year, month, category, dimension_type, dimension_value)
		)`,
		`CREATE TABLE IF NOT EXISTS budget_templates (
			id INTEGER PRIMARY KEY AUTOINCREMENT,
			name TEXT NOT NULL,
			category TEXT NOT NULL DEFAULT '',
			dimension_type TEXT DEFAULT '',
			dimension_value TEXT DEFAULT '',
			amount REAL NOT NULL
		)`,
		`CREATE TABLE IF NOT EXISTS record_templates (
			id INTEGER PRIMARY KEY AUTOINCREMENT,
			name TEXT NOT NULL,
			type TEXT NOT NULL CHECK(type IN ('expense','income')),
			amount REAL NOT NULL,
			category TEXT DEFAULT '',
			subcategory TEXT DEFAULT '',
			account TEXT DEFAULT '',
			merchant TEXT DEFAULT '',
			note TEXT DEFAULT '',
			usage_count INTEGER DEFAULT 0
		)`,
	}
	for _, s := range stmts {
		if _, err := db.Exec(s); err != nil {
			fmt.Fprintf(os.Stderr, "migrate failed: %v\n", err)
			os.Exit(1)
		}
	}
}

// JSON output helpers
type jsonOut struct {
	Success bool        `json:"success"`
	Data    interface{} `json:"data,omitempty"`
	Error   string      `json:"error,omitempty"`
}

var outputJSON bool

func printJSON(v interface{}) {
	json.NewEncoder(os.Stdout).Encode(jsonOut{Success: true, Data: v})
}

func printErr(msg string) {
	if outputJSON {
		json.NewEncoder(os.Stdout).Encode(jsonOut{Success: false, Error: msg})
	} else {
		fmt.Fprintf(os.Stderr, "error: %s\n", msg)
	}
}

func printOK(msg string) {
	if outputJSON {
		json.NewEncoder(os.Stdout).Encode(jsonOut{Success: true, Data: msg})
	} else {
		fmt.Println(msg)
	}
}

// Domain types
type Transaction struct {
	ID          int64    `json:"id"`
	Type        string   `json:"type"`
	Amount      float64  `json:"amount"`
	Category    string   `json:"category"`
	Subcategory string   `json:"subcategory,omitempty"`
	Account     string   `json:"account,omitempty"`
	Project     string   `json:"project,omitempty"`
	Member      string   `json:"member,omitempty"`
	Merchant    string   `json:"merchant,omitempty"`
	Note        string   `json:"note,omitempty"`
	Date        string   `json:"date"`
	CreatedAt   string   `json:"created_at,omitempty"`
	IsDeleted   bool     `json:"is_deleted,omitempty"`
	Tags        []string `json:"tags,omitempty"`
}

type Tag struct {
	ID    int64  `json:"id"`
	Name  string `json:"name"`
	Color string `json:"color"`
	Count int    `json:"count,omitempty"`
}

type Budget struct {
	ID             int64   `json:"id"`
	Year           int     `json:"year"`
	Month          int     `json:"month"`
	Category       string  `json:"category"`
	DimensionType  string  `json:"dimension_type,omitempty"`
	DimensionValue string  `json:"dimension_value,omitempty"`
	Amount         float64 `json:"amount"`
	Spent          float64 `json:"spent,omitempty"`
	Remaining      float64 `json:"remaining,omitempty"`
	Percent        float64 `json:"percent,omitempty"`
}

type BudgetTemplate struct {
	ID             int64   `json:"id"`
	Name           string  `json:"name"`
	Category       string  `json:"category"`
	DimensionType  string  `json:"dimension_type,omitempty"`
	DimensionValue string  `json:"dimension_value,omitempty"`
	Amount         float64 `json:"amount"`
}

type RecordTemplate struct {
	ID          int64   `json:"id"`
	Name        string  `json:"name"`
	Type        string  `json:"type"`
	Amount      float64 `json:"amount"`
	Category    string  `json:"category"`
	Subcategory string  `json:"subcategory,omitempty"`
	Account     string  `json:"account,omitempty"`
	Merchant    string  `json:"merchant,omitempty"`
	Note        string  `json:"note,omitempty"`
	UsageCount  int     `json:"usage_count"`
}

func parseFlags(args []string) map[string]string {
	flags := map[string]string{}
	for i := 0; i < len(args); i++ {
		arg := args[i]
		if strings.HasPrefix(arg, "--") {
			key := strings.TrimPrefix(arg, "--")
			key = strings.ReplaceAll(key, "-", "_")
			if i+1 < len(args) && !strings.HasPrefix(args[i+1], "--") {
				flags[key] = args[i+1]
				i++
			} else {
				flags[key] = "true"
			}
		}
	}
	return flags
}

// ─── Transaction Commands ───────────────────────────────
func txAdd(args []string) error {
	flags := parseFlags(args)
	txn := Transaction{
		Type:     flags["type"],
		Date:     flags["date"],
		Category: flags["category"],
	}
	if txn.Type == "" {
		return fmt.Errorf("--type is required (expense/income)")
	}
	amt, err := strconv.ParseFloat(flags["amount"], 64)
	if err != nil || amt <= 0 {
		return fmt.Errorf("--amount must be positive")
	}
	txn.Amount = amt
	txn.Subcategory = flags["subcategory"]
	txn.Account = flags["account"]
	txn.Project = flags["project"]
	txn.Merchant = flags["merchant"]
	txn.Member = flags["member"]
	txn.Note = flags["note"]
	if txn.Date == "" {
		txn.Date = time.Now().Format("2006-01-02")
	}

	// Duplicate detection
	var dup int
	db.QueryRow(`SELECT COUNT(*) FROM transactions WHERE is_deleted=0 AND type=? AND amount=? AND category=? AND trans_date=?`,
		txn.Type, txn.Amount, txn.Category, txn.Date).Scan(&dup)
	if dup > 0 {
		printErr(fmt.Sprintf("warning: possible duplicate (%s %s %.2f [%s])", txn.Date, txn.Type, txn.Amount, txn.Category))
	}

	res, err := db.Exec(`INSERT INTO transactions (type,amount,category,subcategory,account,project,member,merchant,note,trans_date) VALUES (?,?,?,?,?,?,?,?,?,?)`,
		txn.Type, txn.Amount, txn.Category, txn.Subcategory, txn.Account, txn.Project, txn.Member, txn.Merchant, txn.Note, txn.Date)
	if err != nil {
		return err
	}
	id, _ := res.LastInsertId()

	if tags := flags["tags"]; tags != "" {
		for _, t := range strings.Split(tags, ",") {
			t = strings.TrimSpace(t)
			if t == "" {
				continue
			}
			tagID := getOrCreateTag(t)
			db.Exec(`INSERT OR IGNORE INTO transaction_tags (transaction_id, tag_id) VALUES (?,?)`, id, tagID)
		}
	}

	printOK(fmt.Sprintf("added #%d: %s %.2f %s/%s %s", id, txn.Type, txn.Amount, txn.Category, txn.Account, txn.Date))
	return nil
}

func txList(args []string) error {
	flags := parseFlags(args)
	limit := 20
	if v, ok := flags["limit"]; ok {
		limit, _ = strconv.Atoi(v)
	}
	query := `SELECT id,type,amount,category,subcategory,account,project,member,merchant,note,trans_date,is_deleted,created_at
		FROM transactions WHERE is_deleted=0`
	var params []interface{}

	if v := flags["category"]; v != "" {
		query += " AND category=?"
		params = append(params, v)
	}
	if v := flags["account"]; v != "" {
		query += " AND account=?"
		params = append(params, v)
	}
	if v := flags["type"]; v != "" {
		query += " AND type=?"
		params = append(params, v)
	}
	if v := flags["start"]; v != "" {
		query += " AND trans_date>=?"
		params = append(params, v)
	}
	if v := flags["end"]; v != "" {
		query += " AND trans_date<=?"
		params = append(params, v)
	}
	if v := flags["keyword"]; v != "" {
		query += " AND (note LIKE ? OR category LIKE ? OR merchant LIKE ?)"
		kw := "%" + v + "%"
		params = append(params, kw, kw, kw)
	}
	query += " ORDER BY trans_date DESC, id DESC LIMIT ?"
	params = append(params, limit)

	rows, err := db.Query(query, params...)
	if err != nil {
		return err
	}
	defer rows.Close()

	var txns []Transaction
	for rows.Next() {
		var t Transaction
		var deleted int
		err := rows.Scan(&t.ID, &t.Type, &t.Amount, &t.Category, &t.Subcategory, &t.Account,
			&t.Project, &t.Member, &t.Merchant, &t.Note, &t.Date, &deleted, &t.CreatedAt)
		if err != nil {
			return err
		}
		t.IsDeleted = deleted == 1
		tagRows, _ := db.Query(`SELECT t.name FROM tags t JOIN transaction_tags tt ON t.id=tt.tag_id WHERE tt.transaction_id=?`, t.ID)
		if tagRows != nil {
			for tagRows.Next() {
				var name string
				tagRows.Scan(&name)
				t.Tags = append(t.Tags, name)
			}
			tagRows.Close()
		}
		txns = append(txns, t)
	}

	if outputJSON {
		printJSON(txns)
	} else {
		if len(txns) == 0 {
			fmt.Println("no transactions found")
			return nil
		}
		fmt.Printf("%-6s %-8s %-10s %-10s %-8s %-12s %s\n", "ID", "Type", "Amount", "Category", "Account", "Date", "Note")
		fmt.Println(strings.Repeat("-", 70))
		for _, t := range txns {
			note := t.Note
			if len(note) > 10 {
				note = note[:10] + ".."
			}
			tagStr := ""
			if len(t.Tags) > 0 {
				tagStr = " [" + strings.Join(t.Tags, ",") + "]"
			}
			fmt.Printf("%-6d %-8s %10.2f %-10s %-8s %-12s %s%s\n",
				t.ID, t.Type, t.Amount, t.Category, t.Account, t.Date, note, tagStr)
		}
	}
	return nil
}

func txGet(args []string) error {
	if len(args) == 0 {
		return fmt.Errorf("transaction ID required")
	}
	id, _ := strconv.ParseInt(args[0], 10, 64)
	var t Transaction
	var deleted int
	err := db.QueryRow(`SELECT id,type,amount,category,subcategory,account,project,member,merchant,note,trans_date,is_deleted,created_at
		FROM transactions WHERE id=?`, id).Scan(&t.ID, &t.Type, &t.Amount, &t.Category, &t.Subcategory,
		&t.Account, &t.Project, &t.Member, &t.Merchant, &t.Note, &t.Date, &deleted, &t.CreatedAt)
	if err != nil {
		return fmt.Errorf("transaction #%d not found", id)
	}
	t.IsDeleted = deleted == 1
	tagRows, _ := db.Query(`SELECT t.name FROM tags t JOIN transaction_tags tt ON t.id=tt.tag_id WHERE tt.transaction_id=?`, id)
	if tagRows != nil {
		for tagRows.Next() {
			var name string
			tagRows.Scan(&name)
			t.Tags = append(t.Tags, name)
		}
		tagRows.Close()
	}
	if outputJSON {
		printJSON(t)
	} else {
		fmt.Printf("Transaction #%d\n", t.ID)
		fmt.Printf("  Type:     %s\n", t.Type)
		fmt.Printf("  Amount:   %.2f\n", t.Amount)
		fmt.Printf("  Category: %s / %s\n", t.Category, t.Subcategory)
		fmt.Printf("  Account:  %s\n", t.Account)
		fmt.Printf("  Merchant: %s\n", t.Merchant)
		fmt.Printf("  Member:   %s\n", t.Member)
		fmt.Printf("  Project:  %s\n", t.Project)
		fmt.Printf("  Date:     %s\n", t.Date)
		fmt.Printf("  Note:     %s\n", t.Note)
		if len(t.Tags) > 0 {
			fmt.Printf("  Tags:     %s\n", strings.Join(t.Tags, ", "))
		}
		fmt.Printf("  Created:  %s\n", t.CreatedAt)
	}
	return nil
}

func txUpdate(args []string) error {
	if len(args) == 0 {
		return fmt.Errorf("transaction ID required")
	}
	id, _ := strconv.ParseInt(args[0], 10, 64)
	flags := parseFlags(args[1:])
	sets := []string{}
	params := []interface{}{}
	for _, f := range []struct{ key, col string }{
		{"type", "type"}, {"amount", "amount"}, {"category", "category"},
		{"subcategory", "subcategory"}, {"account", "account"}, {"project", "project"},
		{"member", "member"}, {"merchant", "merchant"}, {"note", "note"}, {"date", "trans_date"},
	} {
		if v, ok := flags[f.key]; ok {
			sets = append(sets, f.col+"=?")
			if f.key == "amount" {
				amt, _ := strconv.ParseFloat(v, 64)
				params = append(params, amt)
			} else {
				params = append(params, v)
			}
		}
	}
	if len(sets) == 0 {
		return fmt.Errorf("no fields to update")
	}
	params = append(params, id)
	_, err := db.Exec("UPDATE transactions SET "+strings.Join(sets, ",")+" WHERE id=?", params...)
	if err != nil {
		return err
	}
	printOK(fmt.Sprintf("updated #%d", id))
	return nil
}

func txDelete(args []string) error {
	if len(args) == 0 {
		return fmt.Errorf("transaction ID required")
	}
	id, _ := strconv.ParseInt(args[0], 10, 64)
	_, err := db.Exec("UPDATE transactions SET is_deleted=1 WHERE id=?", id)
	if err != nil {
		return err
	}
	printOK(fmt.Sprintf("soft-deleted #%d", id))
	return nil
}

func txRestore(args []string) error {
	if len(args) == 0 {
		return fmt.Errorf("transaction ID required")
	}
	id, _ := strconv.ParseInt(args[0], 10, 64)
	_, err := db.Exec("UPDATE transactions SET is_deleted=0 WHERE id=?", id)
	if err != nil {
		return err
	}
	printOK(fmt.Sprintf("restored #%d", id))
	return nil
}

func txHardDelete(args []string) error {
	if len(args) == 0 {
		return fmt.Errorf("transaction ID required")
	}
	id, _ := strconv.ParseInt(args[0], 10, 64)
	_, err := db.Exec("DELETE FROM transactions WHERE id=?", id)
	if err != nil {
		return err
	}
	printOK(fmt.Sprintf("permanently deleted #%d", id))
	return nil
}

// ─── Summary / Stats / Analyze ──────────────────────────
func cmdSummary(args []string) error {
	flags := parseFlags(args)
	now := time.Now()
	year, _ := strconv.Atoi(flags["year"])
	month, _ := strconv.Atoi(flags["month"])
	if year == 0 {
		year = now.Year()
	}
	if month == 0 {
		month = int(now.Month())
	}
	start := fmt.Sprintf("%04d-%02d-01", year, month)
	end := fmt.Sprintf("%04d-%02d-31", year, month)

	type summary struct {
		Income  float64 `json:"income"`
		Expense float64 `json:"expense"`
		Balance float64 `json:"balance"`
		Count   int     `json:"count"`
	}
	var s summary
	db.QueryRow(`SELECT COALESCE(SUM(amount),0) FROM transactions WHERE type='income' AND is_deleted=0 AND trans_date>=? AND trans_date<=?`,
		start, end).Scan(&s.Income)
	db.QueryRow(`SELECT COALESCE(SUM(amount),0) FROM transactions WHERE type='expense' AND is_deleted=0 AND trans_date>=? AND trans_date<=?`,
		start, end).Scan(&s.Expense)
	db.QueryRow(`SELECT COUNT(*) FROM transactions WHERE is_deleted=0 AND trans_date>=? AND trans_date<=?`,
		start, end).Scan(&s.Count)
	s.Balance = s.Income - s.Expense

	if outputJSON {
		printJSON(s)
	} else {
		fmt.Printf("=== %d-%02d Summary ===\n", year, month)
		fmt.Printf("  Income:  %12.2f\n", s.Income)
		fmt.Printf("  Expense: %12.2f\n", s.Expense)
		fmt.Printf("  Balance: %12.2f\n", s.Balance)
		fmt.Printf("  Count:   %d\n", s.Count)
	}
	return nil
}

func cmdStats(args []string) error {
	flags := parseFlags(args)
	groupBy := flags["group-by"]
	if groupBy == "" {
		groupBy = "category"
	}
	validGroups := map[string]bool{
		"category": true, "subcategory": true, "account": true,
		"project": true, "member": true, "merchant": true,
	}
	if !validGroups[groupBy] {
		return fmt.Errorf("unsupported group-by: %s", groupBy)
	}

	query := fmt.Sprintf(`SELECT %s, type, COALESCE(SUM(amount),0), COUNT(*)
		FROM transactions WHERE is_deleted=0`, groupBy)
	var params []interface{}
	if v := flags["start"]; v != "" {
		query += " AND trans_date>=?"
		params = append(params, v)
	}
	if v := flags["end"]; v != "" {
		query += " AND trans_date<=?"
		params = append(params, v)
	}
	query += fmt.Sprintf(` GROUP BY %s, type ORDER BY %s`, groupBy, groupBy)

	rows, err := db.Query(query, params...)
	if err != nil {
		return err
	}
	defer rows.Close()

	type statRow struct {
		Value  string  `json:"value"`
		Type   string  `json:"type"`
		Amount float64 `json:"amount"`
		Count  int     `json:"count"`
	}
	var stats []statRow
	for rows.Next() {
		var s statRow
		rows.Scan(&s.Value, &s.Type, &s.Amount, &s.Count)
		if s.Value == "" {
			s.Value = "(empty)"
		}
		stats = append(stats, s)
	}

	if outputJSON {
		printJSON(stats)
	} else {
		fmt.Printf("=== Stats by %s ===\n", groupBy)
		fmt.Printf("%-16s %-8s %12s %6s\n", "Value", "Type", "Amount", "Count")
		fmt.Println(strings.Repeat("-", 46))
		for _, s := range stats {
			fmt.Printf("%-16s %-8s %12.2f %6d\n", s.Value, s.Type, s.Amount, s.Count)
		}
	}
	return nil
}

func cmdAnalyze(args []string) error {
	flags := parseFlags(args)
	year, _ := strconv.Atoi(flags["year"])
	month, _ := strconv.Atoi(flags["month"])
	now := time.Now()
	if year == 0 {
		year = now.Year()
	}
	if month == 0 {
		month = int(now.Month())
	}
	start := fmt.Sprintf("%04d-%02d-01", year, month)
	end := fmt.Sprintf("%04d-%02d-31", year, month)

	type catStat struct {
		Category string  `json:"category"`
		Amount   float64 `json:"amount"`
		Percent  float64 `json:"percent"`
	}
	var total float64
	db.QueryRow(`SELECT COALESCE(SUM(amount),0) FROM transactions WHERE type='expense' AND is_deleted=0 AND trans_date>=? AND trans_date<=?`,
		start, end).Scan(&total)

	rows, err := db.Query(`SELECT category, SUM(amount) FROM transactions
		WHERE type='expense' AND is_deleted=0 AND trans_date>=? AND trans_date<=?
		GROUP BY category ORDER BY SUM(amount) DESC`, start, end)
	if err != nil {
		return err
	}
	defer rows.Close()

	var stats []catStat
	for rows.Next() {
		var s catStat
		rows.Scan(&s.Category, &s.Amount)
		if total > 0 {
			s.Percent = s.Amount / total * 100
		}
		stats = append(stats, s)
	}

	if outputJSON {
		printJSON(map[string]interface{}{"year": year, "month": month, "total": total, "breakdown": stats})
	} else {
		fmt.Printf("=== %d-%02d Expense Analysis ===\n", year, month)
		fmt.Printf("Total: %.2f\n\n", total)
		fmt.Printf("%-16s %12s %8s\n", "Category", "Amount", "Percent")
		fmt.Println(strings.Repeat("-", 38))
		for _, s := range stats {
			fmt.Printf("%-16s %12.2f %7.1f%%\n", s.Category, s.Amount, s.Percent)
		}
	}
	return nil
}

func cmdSuggest(args []string) error {
	flags := parseFlags(args)
	field := flags["field"]
	keyword := flags["keyword"]

	validFields := map[string]bool{
		"category": true, "account": true, "merchant": true,
		"project": true, "member": true,
	}
	if !validFields[field] {
		return fmt.Errorf("unsupported field: %s", field)
	}

	query := fmt.Sprintf("SELECT DISTINCT %s FROM transactions WHERE is_deleted=0 AND %s!=''", field, field)
	var params []interface{}
	if keyword != "" {
		query += fmt.Sprintf(" AND %s LIKE ?", field)
		params = append(params, "%"+keyword+"%")
	}
	query += fmt.Sprintf(" ORDER BY %s LIMIT 20", field)

	rows, err := db.Query(query, params...)
	if err != nil {
		return err
	}
	defer rows.Close()

	var items []string
	for rows.Next() {
		var v string
		rows.Scan(&v)
		items = append(items, v)
	}
	if outputJSON {
		printJSON(items)
	} else {
		for _, v := range items {
			fmt.Println(v)
		}
	}
	return nil
}

func cmdAccounts(args []string) error {
	rows, err := db.Query("SELECT DISTINCT account FROM transactions WHERE is_deleted=0 AND account!='' ORDER BY account")
	if err != nil {
		return err
	}
	defer rows.Close()
	var items []string
	for rows.Next() {
		var v string
		rows.Scan(&v)
		items = append(items, v)
	}
	if outputJSON {
		printJSON(items)
	} else {
		for _, v := range items {
			fmt.Println(v)
		}
	}
	return nil
}

func cmdCategories(args []string) error {
	rows, err := db.Query("SELECT DISTINCT category FROM transactions WHERE is_deleted=0 ORDER BY category")
	if err != nil {
		return err
	}
	defer rows.Close()
	var items []string
	for rows.Next() {
		var v string
		rows.Scan(&v)
		items = append(items, v)
	}
	if outputJSON {
		printJSON(items)
	} else {
		for _, v := range items {
			fmt.Println(v)
		}
	}
	return nil
}

// ─── Tag Commands ───────────────────────────────────────
func getOrCreateTag(name string) int64 {
	var id int64
	err := db.QueryRow("SELECT id FROM tags WHERE name=?", name).Scan(&id)
	if err == nil {
		return id
	}
	res, _ := db.Exec("INSERT INTO tags (name) VALUES (?)", name)
	id, _ = res.LastInsertId()
	return id
}

func tagList(args []string) error {
	rows, err := db.Query(`SELECT t.id, t.name, t.color, COUNT(tt.transaction_id) as cnt
		FROM tags t LEFT JOIN transaction_tags tt ON t.id=tt.tag_id
		GROUP BY t.id ORDER BY t.name`)
	if err != nil {
		return err
	}
	defer rows.Close()

	var tags []Tag
	for rows.Next() {
		var t Tag
		rows.Scan(&t.ID, &t.Name, &t.Color, &t.Count)
		tags = append(tags, t)
	}
	if outputJSON {
		printJSON(tags)
	} else {
		if len(tags) == 0 {
			fmt.Println("no tags")
			return nil
		}
		fmt.Printf("%-6s %-12s %-10s %s\n", "ID", "Name", "Color", "Count")
		fmt.Println(strings.Repeat("-", 40))
		for _, t := range tags {
			fmt.Printf("%-6d %-12s %-10s %d\n", t.ID, t.Name, t.Color, t.Count)
		}
	}
	return nil
}

func tagCreate(args []string) error {
	flags := parseFlags(args)
	name := flags["name"]
	if name == "" {
		return fmt.Errorf("--name is required")
	}
	color := flags["color"]
	if color == "" {
		color = "#6c757d"
	}
	_, err := db.Exec("INSERT INTO tags (name, color) VALUES (?,?)", name, color)
	if err != nil {
		return fmt.Errorf("tag already exists or failed: %v", err)
	}
	printOK(fmt.Sprintf("tag '%s' created", name))
	return nil
}

func tagDelete(args []string) error {
	if len(args) == 0 {
		return fmt.Errorf("tag ID required")
	}
	id, _ := strconv.ParseInt(args[0], 10, 64)
	_, err := db.Exec("DELETE FROM tags WHERE id=?", id)
	if err != nil {
		return err
	}
	printOK(fmt.Sprintf("tag #%d deleted", id))
	return nil
}

func tagTxns(args []string) error {
	if len(args) == 0 {
		return fmt.Errorf("tag name or ID required")
	}
	id, err := strconv.ParseInt(args[0], 10, 64)
	var tagID int64
	if err != nil {
		err = db.QueryRow("SELECT id FROM tags WHERE name=?", args[0]).Scan(&tagID)
		if err != nil {
			return fmt.Errorf("tag '%s' not found", args[0])
		}
	} else {
		tagID = id
	}

	rows, err := db.Query(`SELECT t.id,t.type,t.amount,t.category,t.account,t.trans_date,t.note
		FROM transactions t JOIN transaction_tags tt ON t.id=tt.transaction_id
		WHERE tt.tag_id=? AND t.is_deleted=0 ORDER BY t.trans_date DESC LIMIT 20`, tagID)
	if err != nil {
		return err
	}
	defer rows.Close()

	type tagTx struct {
		ID       int64   `json:"id"`
		Type     string  `json:"type"`
		Amount   float64 `json:"amount"`
		Category string  `json:"category"`
		Account  string  `json:"account"`
		Date     string  `json:"date"`
		Note     string  `json:"note"`
	}
	var txns []tagTx
	for rows.Next() {
		var t tagTx
		rows.Scan(&t.ID, &t.Type, &t.Amount, &t.Category, &t.Account, &t.Date, &t.Note)
		txns = append(txns, t)
	}
	if outputJSON {
		printJSON(txns)
	} else {
		if len(txns) == 0 {
			fmt.Println("no transactions for this tag")
			return nil
		}
		for _, t := range txns {
			fmt.Printf("#%-4d %s %s %8.2f %s/%s %s\n", t.ID, t.Date, t.Type, t.Amount, t.Category, t.Account, t.Note)
		}
	}
	return nil
}

// ─── Budget Commands ────────────────────────────────────
func budgetSet(args []string) error {
	flags := parseFlags(args)
	year, _ := strconv.Atoi(flags["year"])
	month, _ := strconv.Atoi(flags["month"])
	amt, _ := strconv.ParseFloat(flags["amount"], 64)
	if year == 0 || month == 0 || amt <= 0 {
		return fmt.Errorf("--year --month --amount required and amount>0")
	}
	cat := flags["category"]
	dimType := flags["dimension_type"]
	dimVal := flags["dimension_value"]

	_, err := db.Exec(`INSERT INTO budgets (year,month,category,dimension_type,dimension_value,amount) VALUES (?,?,?,?,?,?)
		ON CONFLICT(year,month,category,dimension_type,dimension_value) DO UPDATE SET amount=excluded.amount`,
		year, month, cat, dimType, dimVal, amt)
	if err != nil {
		return err
	}
	printOK(fmt.Sprintf("budget set: %d-%02d %s %.2f", year, month, cat, amt))
	return nil
}

func budgetList(args []string) error {
	flags := parseFlags(args)
	year, _ := strconv.Atoi(flags["year"])
	month, _ := strconv.Atoi(flags["month"])
	now := time.Now()
	if year == 0 {
		year = now.Year()
	}
	if month == 0 {
		month = int(now.Month())
	}
	start := fmt.Sprintf("%04d-%02d-01", year, month)
	end := fmt.Sprintf("%04d-%02d-31", year, month)

	rows, err := db.Query(`SELECT b.id,b.year,b.month,b.category,b.dimension_type,b.dimension_value,b.amount
		FROM budgets b WHERE b.year=? AND b.month=? ORDER BY b.category`, year, month)
	if err != nil {
		return err
	}
	defer rows.Close()

	var budgets []Budget
	for rows.Next() {
		var b Budget
		rows.Scan(&b.ID, &b.Year, &b.Month, &b.Category, &b.DimensionType, &b.DimensionValue, &b.Amount)
		spentQ := `SELECT COALESCE(SUM(amount),0) FROM transactions WHERE type='expense' AND is_deleted=0 AND trans_date>=? AND trans_date<=?`
		spentP := []interface{}{start, end}
		if b.Category != "" {
			spentQ += " AND category=?"
			spentP = append(spentP, b.Category)
		}
		db.QueryRow(spentQ, spentP...).Scan(&b.Spent)
		b.Remaining = b.Amount - b.Spent
		if b.Amount > 0 {
			b.Percent = b.Spent / b.Amount * 100
		}
		budgets = append(budgets, b)
	}

	if outputJSON {
		printJSON(budgets)
	} else {
		if len(budgets) == 0 {
			fmt.Printf("no budgets for %d-%02d\n", year, month)
			return nil
		}
		fmt.Printf("=== Budgets %d-%02d ===\n", year, month)
		fmt.Printf("%-16s %10s %10s %10s %8s\n", "Category", "Budget", "Spent", "Left", "Pct")
		fmt.Println(strings.Repeat("-", 58))
		for _, b := range budgets {
			cat := b.Category
			if cat == "" {
				cat = "(total)"
			}
			fmt.Printf("%-16s %10.2f %10.2f %10.2f %7.0f%%\n", cat, b.Amount, b.Spent, b.Remaining, b.Percent)
		}
	}
	return nil
}

// ─── Budget Template Commands ───────────────────────────
func budgetTemplateCreate(args []string) error {
	flags := parseFlags(args)
	name := flags["name"]
	amt, _ := strconv.ParseFloat(flags["amount"], 64)
	if name == "" || amt <= 0 {
		return fmt.Errorf("--name and --amount required")
	}
	cat := flags["category"]
	dimType := flags["dimension_type"]
	dimVal := flags["dimension_value"]
	_, err := db.Exec(`INSERT INTO budget_templates (name,category,dimension_type,dimension_value,amount) VALUES (?,?,?,?,?)`,
		name, cat, dimType, dimVal, amt)
	if err != nil {
		return err
	}
	printOK(fmt.Sprintf("budget template '%s' created", name))
	return nil
}

func budgetTemplateList(args []string) error {
	rows, err := db.Query("SELECT id,name,category,dimension_type,dimension_value,amount FROM budget_templates ORDER BY name")
	if err != nil {
		return err
	}
	defer rows.Close()

	var templates []BudgetTemplate
	for rows.Next() {
		var t BudgetTemplate
		rows.Scan(&t.ID, &t.Name, &t.Category, &t.DimensionType, &t.DimensionValue, &t.Amount)
		templates = append(templates, t)
	}
	if outputJSON {
		printJSON(templates)
	} else {
		if len(templates) == 0 {
			fmt.Println("no budget templates")
			return nil
		}
		for _, t := range templates {
			fmt.Printf("#%-4d %-16s %-10s %.2f\n", t.ID, t.Name, t.Category, t.Amount)
		}
	}
	return nil
}

func budgetTemplateApply(args []string) error {
	if len(args) == 0 {
		return fmt.Errorf("template ID required")
	}
	id, _ := strconv.ParseInt(args[0], 10, 64)
	flags := parseFlags(args[1:])
	year, _ := strconv.Atoi(flags["year"])
	month, _ := strconv.Atoi(flags["month"])
	if year == 0 || month == 0 {
		return fmt.Errorf("--year and --month required")
	}

	var t BudgetTemplate
	err := db.QueryRow("SELECT name,category,dimension_type,dimension_value,amount FROM budget_templates WHERE id=?", id).
		Scan(&t.Name, &t.Category, &t.DimensionType, &t.DimensionValue, &t.Amount)
	if err != nil {
		return fmt.Errorf("template #%d not found", id)
	}
	_, err = db.Exec(`INSERT INTO budgets (year,month,category,dimension_type,dimension_value,amount) VALUES (?,?,?,?,?,?)
		ON CONFLICT(year,month,category,dimension_type,dimension_value) DO UPDATE SET amount=excluded.amount`,
		year, month, t.Category, t.DimensionType, t.DimensionValue, t.Amount)
	if err != nil {
		return err
	}
	printOK(fmt.Sprintf("template '%s' applied to %d-%02d", t.Name, year, month))
	return nil
}

func budgetTemplateDelete(args []string) error {
	if len(args) == 0 {
		return fmt.Errorf("template ID required")
	}
	id, _ := strconv.ParseInt(args[0], 10, 64)
	_, err := db.Exec("DELETE FROM budget_templates WHERE id=?", id)
	if err != nil {
		return err
	}
	printOK(fmt.Sprintf("budget template #%d deleted", id))
	return nil
}

// ─── Record Template Commands ───────────────────────────
func templateCreate(args []string) error {
	flags := parseFlags(args)
	name := flags["name"]
	txnType := flags["type"]
	amt, _ := strconv.ParseFloat(flags["amount"], 64)
	if name == "" || txnType == "" || amt <= 0 {
		return fmt.Errorf("--name --type --amount required")
	}
	cat := flags["category"]
	sub := flags["subcategory"]
	account := flags["account"]
	merchant := flags["merchant"]
	note := flags["note"]
	_, err := db.Exec(`INSERT INTO record_templates (name,type,amount,category,subcategory,account,merchant,note) VALUES (?,?,?,?,?,?,?,?)`,
		name, txnType, amt, cat, sub, account, merchant, note)
	if err != nil {
		return err
	}
	printOK(fmt.Sprintf("template '%s' created", name))
	return nil
}

func templateList(args []string) error {
	rows, err := db.Query("SELECT id,name,type,amount,category,subcategory,account,merchant,note,usage_count FROM record_templates ORDER BY usage_count DESC")
	if err != nil {
		return err
	}
	defer rows.Close()

	var templates []RecordTemplate
	for rows.Next() {
		var t RecordTemplate
		rows.Scan(&t.ID, &t.Name, &t.Type, &t.Amount, &t.Category, &t.Subcategory, &t.Account, &t.Merchant, &t.Note, &t.UsageCount)
		templates = append(templates, t)
	}
	if outputJSON {
		printJSON(templates)
	} else {
		if len(templates) == 0 {
			fmt.Println("no record templates")
			return nil
		}
		fmt.Printf("%-4s %-16s %-6s %8s %-10s %-8s %s\n", "ID", "Name", "Type", "Amount", "Category", "Account", "Uses")
		fmt.Println(strings.Repeat("-", 65))
		for _, t := range templates {
			fmt.Printf("%-4d %-16s %-6s %8.2f %-10s %-8s %d\n",
				t.ID, t.Name, t.Type, t.Amount, t.Category, t.Account, t.UsageCount)
		}
	}
	return nil
}

func templateApply(args []string) error {
	if len(args) == 0 {
		return fmt.Errorf("template ID required")
	}
	id, _ := strconv.ParseInt(args[0], 10, 64)
	flags := parseFlags(args[1:])
	date := flags["date"]
	if date == "" {
		date = time.Now().Format("2006-01-02")
	}

	var t RecordTemplate
	err := db.QueryRow("SELECT name,type,amount,category,subcategory,account,merchant,note FROM record_templates WHERE id=?", id).
		Scan(&t.Name, &t.Type, &t.Amount, &t.Category, &t.Subcategory, &t.Account, &t.Merchant, &t.Note)
	if err != nil {
		return fmt.Errorf("template #%d not found", id)
	}

	res, err := db.Exec(`INSERT INTO transactions (type,amount,category,subcategory,account,merchant,note,trans_date) VALUES (?,?,?,?,?,?,?,?)`,
		t.Type, t.Amount, t.Category, t.Subcategory, t.Account, t.Merchant, t.Note, date)
	if err != nil {
		return err
	}
	txID, _ := res.LastInsertId()
	db.Exec("UPDATE record_templates SET usage_count=usage_count+1 WHERE id=?", id)

	printOK(fmt.Sprintf("template '%s' applied -> #%d: %s %.2f %s/%s", t.Name, txID, t.Type, t.Amount, t.Category, t.Account))
	return nil
}

func templateDelete(args []string) error {
	if len(args) == 0 {
		return fmt.Errorf("template ID required")
	}
	id, _ := strconv.ParseInt(args[0], 10, 64)
	_, err := db.Exec("DELETE FROM record_templates WHERE id=?", id)
	if err != nil {
		return err
	}
	printOK(fmt.Sprintf("template #%d deleted", id))
	return nil
}

func templateUpdate(args []string) error {
	if len(args) == 0 {
		return fmt.Errorf("template ID required")
	}
	id, _ := strconv.ParseInt(args[0], 10, 64)
	flags := parseFlags(args[1:])
	sets := []string{}
	params := []interface{}{}
	for _, f := range []struct{ key, col string }{
		{"name", "name"}, {"type", "type"}, {"amount", "amount"},
		{"category", "category"}, {"subcategory", "subcategory"},
		{"account", "account"}, {"merchant", "merchant"}, {"note", "note"},
	} {
		if v, ok := flags[f.key]; ok {
			sets = append(sets, f.col+"=?")
			if f.key == "amount" {
				amt, _ := strconv.ParseFloat(v, 64)
				params = append(params, amt)
			} else {
				params = append(params, v)
			}
		}
	}
	if len(sets) == 0 {
		return fmt.Errorf("no fields to update")
	}
	params = append(params, id)
	_, err := db.Exec("UPDATE record_templates SET "+strings.Join(sets, ",")+" WHERE id=?", params...)
	if err != nil {
		return err
	}
	printOK(fmt.Sprintf("template #%d updated", id))
	return nil
}

func templateSuggest(args []string) error {
	rows, err := db.Query("SELECT id,name,type,amount,category,account,usage_count FROM record_templates ORDER BY usage_count DESC LIMIT 5")
	if err != nil {
		return err
	}
	defer rows.Close()

	type suggest struct {
		ID         int64   `json:"id"`
		Name       string  `json:"name"`
		Type       string  `json:"type"`
		Amount     float64 `json:"amount"`
		Category   string  `json:"category"`
		Account    string  `json:"account"`
		UsageCount int     `json:"usage_count"`
	}
	var items []suggest
	for rows.Next() {
		var s suggest
		rows.Scan(&s.ID, &s.Name, &s.Type, &s.Amount, &s.Category, &s.Account, &s.UsageCount)
		items = append(items, s)
	}
	if outputJSON {
		printJSON(items)
	} else {
		if len(items) == 0 {
			fmt.Println("no template suggestions")
			return nil
		}
		fmt.Println("suggested templates:")
		for _, s := range items {
			fmt.Printf("  #%d %-12s %s %.2f (%s/%s) used %d times\n",
				s.ID, s.Name, s.Type, s.Amount, s.Category, s.Account, s.UsageCount)
		}
	}
	return nil
}

// ─── Import / Export ────────────────────────────────────
func cmdImport(args []string) error {
	flags := parseFlags(args)
	file := flags["file"]
	if file == "" {
		return fmt.Errorf("--file is required")
	}

	f, err := os.Open(file)
	if err != nil {
		return fmt.Errorf("open file failed: %v", err)
	}
	defer f.Close()

	reader := csv.NewReader(f)
	records, err := reader.ReadAll()
	if err != nil {
		return fmt.Errorf("read CSV failed: %v", err)
	}

	imported := 0
	skipped := 0
	for i, row := range records {
		if i == 0 {
			continue
		}
		if len(row) < 3 {
			skipped++
			continue
		}
		date := strings.TrimSpace(row[0])
		txnType := strings.TrimSpace(row[1])
		subcat := strings.TrimSpace(row[2])
		cat := ""
		if len(row) > 3 {
			cat = strings.TrimSpace(row[3])
		}
		account := ""
		if len(row) > 4 {
			account = strings.TrimSpace(row[4])
		}
		amountStr := ""
		if len(row) > 5 {
			amountStr = strings.TrimSpace(row[5])
		}
		note := ""
		if len(row) > 6 {
			note = strings.TrimSpace(row[6])
		}

		amount, err := strconv.ParseFloat(amountStr, 64)
		if err != nil || amount == 0 {
			skipped++
			continue
		}
		if txnType != "expense" && txnType != "income" {
			skipped++
			continue
		}
		var dup int
		db.QueryRow(`SELECT COUNT(*) FROM transactions WHERE type=? AND amount=? AND category=? AND trans_date=? AND is_deleted=0`,
			txnType, amount, cat, date).Scan(&dup)
		if dup > 0 {
			skipped++
			continue
		}

		db.Exec(`INSERT INTO transactions (type,amount,category,subcategory,account,note,trans_date) VALUES (?,?,?,?,?,?,?)`,
			txnType, amount, cat, subcat, account, note, date)
		imported++
	}

	printOK(fmt.Sprintf("imported %d, skipped %d", imported, skipped))
	return nil
}

func cmdExport(args []string) error {
	flags := parseFlags(args)
	format := flags["format"]
	if format == "" {
		format = "csv"
	}
	output := flags["output"]
	if output == "" {
		output = "export." + format
	}

	query := `SELECT type,amount,category,subcategory,account,project,member,merchant,note,trans_date,created_at
		FROM transactions WHERE is_deleted=0`
	var params []interface{}
	if v := flags["start"]; v != "" {
		query += " AND trans_date>=?"
		params = append(params, v)
	}
	if v := flags["end"]; v != "" {
		query += " AND trans_date<=?"
		params = append(params, v)
	}
	query += " ORDER BY trans_date DESC"

	rows, err := db.Query(query, params...)
	if err != nil {
		return err
	}
	defer rows.Close()

	if format == "json" {
		type exportTx struct {
			Type        string  `json:"type"`
			Amount      float64 `json:"amount"`
			Category    string  `json:"category"`
			Subcategory string  `json:"subcategory"`
			Account     string  `json:"account"`
			Project     string  `json:"project"`
			Member      string  `json:"member"`
			Merchant    string  `json:"merchant"`
			Note        string  `json:"note"`
			Date        string  `json:"date"`
			CreatedAt   string  `json:"created_at"`
		}
		var txns []exportTx
		for rows.Next() {
			var t exportTx
			rows.Scan(&t.Type, &t.Amount, &t.Category, &t.Subcategory, &t.Account,
				&t.Project, &t.Member, &t.Merchant, &t.Note, &t.Date, &t.CreatedAt)
			txns = append(txns, t)
		}
		f, _ := os.Create(output)
		defer f.Close()
		json.NewEncoder(f).Encode(txns)
	} else {
		f, _ := os.Create(output)
		defer f.Close()
		w := csv.NewWriter(f)
		w.Write([]string{"type", "amount", "category", "subcategory", "account", "project", "member", "merchant", "note", "date"})
		for rows.Next() {
			var t Transaction
			rows.Scan(&t.Type, &t.Amount, &t.Category, &t.Subcategory, &t.Account,
				&t.Project, &t.Member, &t.Merchant, &t.Note, &t.Date, &t.CreatedAt)
			w.Write([]string{t.Type, fmt.Sprintf("%.2f", t.Amount), t.Category, t.Subcategory, t.Account,
				t.Project, t.Member, t.Merchant, t.Note, t.Date})
		}
		w.Flush()
	}
	printOK(fmt.Sprintf("exported to %s", output))
	return nil
}

func cmdInfo(args []string) error {
	var count int
	db.QueryRow("SELECT COUNT(*) FROM transactions WHERE is_deleted=0").Scan(&count)

	type info struct {
		Version      string `json:"version"`
		DBPath       string `json:"db_path"`
		Transactions int    `json:"transactions"`
		Platform     string `json:"platform"`
	}
	inf := info{
		Version:      version,
		DBPath:       dbPath(),
		Transactions: count,
		Platform:     runtime.GOOS + "/" + runtime.GOARCH,
	}
	if outputJSON {
		printJSON(inf)
	} else {
		fmt.Printf("ledger-cli v%s\n", inf.Version)
		fmt.Printf("Platform:    %s\n", inf.Platform)
		fmt.Printf("DB Path:     %s\n", inf.DBPath)
		fmt.Printf("Transactions: %d\n", inf.Transactions)
	}
	return nil
}

// ─── CLI Entry ──────────────────────────────────────────

func makeCmd(use, short string, fn func([]string) error) *cobra.Command {
	return &cobra.Command{
		Use:                use,
		Short:              short,
		FParseErrWhitelist: cobra.FParseErrWhitelist{UnknownFlags: true},
		DisableFlagParsing: true,
		RunE: func(cmd *cobra.Command, args []string) error {
			// Skip our global --json flag from args
			var cleanArgs []string
			skipNext := false
			for _, a := range args {
				if skipNext {
					skipNext = false
					continue
				}
				if a == "--json" || a == "-j" {
					outputJSON = true
					continue
				}
				if (a == "--json" || a == "-j") && len(args) > 1 {
					// handled above
					continue
				}
				cleanArgs = append(cleanArgs, a)
			}
			return fn(cleanArgs)
		},
	}
}

func main() {
	openDB()
	defer db.Close()

	root := &cobra.Command{
		Use:     "ledger-cli",
		Short:   "Super simple ledger CLI - Agent friendly",
		Version: version,
	}

	// Global --json flag via root PersistentPreRun
	root.PersistentFlags().BoolP("json", "j", false, "JSON output")
	root.PersistentPreRun = func(cmd *cobra.Command, args []string) {
		outputJSON, _ = cmd.Flags().GetBool("json")
	}

	// tx
	tx := &cobra.Command{Use: "tx", Short: "Transaction management", DisableFlagParsing: true}
	tx.AddCommand(
		makeCmd("add", "Add transaction", txAdd),
		makeCmd("list", "List transactions", txList),
		makeCmd("get", "Get transaction", txGet),
		makeCmd("update", "Update transaction", txUpdate),
		makeCmd("delete", "Soft delete", txDelete),
		makeCmd("restore", "Restore deleted", txRestore),
		makeCmd("hard-delete", "Permanently delete", txHardDelete),
	)
	root.AddCommand(tx)

	// tag
	tag := &cobra.Command{Use: "tag", Short: "Tag management", DisableFlagParsing: true}
	tag.AddCommand(
		makeCmd("list", "List tags", tagList),
		makeCmd("create", "Create tag", tagCreate),
		makeCmd("delete", "Delete tag", tagDelete),
		makeCmd("transactions", "Transactions by tag", tagTxns),
	)
	root.AddCommand(tag)

	// budget
	budget := &cobra.Command{Use: "budget", Short: "Budget management", DisableFlagParsing: true}
	budget.AddCommand(
		makeCmd("set", "Set budget", budgetSet),
		makeCmd("list", "List budgets", budgetList),
		makeCmd("check", "Check budget usage", budgetList),
	)
	root.AddCommand(budget)

	// budget-template
	bt := &cobra.Command{Use: "budget-template", Short: "Budget templates", DisableFlagParsing: true}
	bt.AddCommand(
		makeCmd("create", "Create template", budgetTemplateCreate),
		makeCmd("list", "List templates", budgetTemplateList),
		makeCmd("apply", "Apply template", budgetTemplateApply),
		makeCmd("delete", "Delete template", budgetTemplateDelete),
	)
	root.AddCommand(bt)

	// template
	tpl := &cobra.Command{Use: "template", Short: "Record templates", DisableFlagParsing: true}
	tpl.AddCommand(
		makeCmd("create", "Create template", templateCreate),
		makeCmd("list", "List templates", templateList),
		makeCmd("update", "Update template", templateUpdate),
		makeCmd("apply", "Apply template", templateApply),
		makeCmd("delete", "Delete template", templateDelete),
		makeCmd("suggest", "Suggest templates", templateSuggest),
	)
	root.AddCommand(tpl)

	// summary / stats / analyze
	root.AddCommand(
		makeCmd("summary", "Monthly summary", cmdSummary),
		makeCmd("stats", "Grouped stats", cmdStats),
		makeCmd("analyze", "Expense analysis", cmdAnalyze),
	)

	// suggest / accounts / categories
	root.AddCommand(
		makeCmd("suggest", "Auto-complete hints", cmdSuggest),
		makeCmd("accounts", "List accounts", cmdAccounts),
		makeCmd("categories", "List categories", cmdCategories),
	)

	// import / export
	root.AddCommand(
		makeCmd("import", "Import CSV", cmdImport),
		makeCmd("export", "Export data", cmdExport),
	)

	// info
	root.AddCommand(
		makeCmd("info", "System info", cmdInfo),
	)

	// tags alias
	root.AddCommand(
		makeCmd("tags", "List tags (alias)", tagList),
	)

	if err := root.Execute(); err != nil {
		os.Exit(1)
	}
}