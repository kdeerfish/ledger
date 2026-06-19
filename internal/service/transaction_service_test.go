package service_test

import (
	"strings"
	"testing"

	"github.com/stretchr/testify/assert"
	"github.com/stretchr/testify/require"

	"github.com/kdeerfish/ledger/internal/domain"
	"github.com/kdeerfish/ledger/internal/repo"
	"github.com/kdeerfish/ledger/internal/service"
)

func TestAdd_Normal(t *testing.T) {
	h := newSvc(t)
	txn, err := h.Tx.Add(service.AddInput{
		Type: "支出", Amount: 30, Category: "食品", Account: "微信",
		TransDate: "2026-06-19 12:00:00", Force: true,
	})
	require.NoError(t, err)
	assert.Greater(t, txn.ID, int64(0))
	assert.Equal(t, "食品", deref(txn.Category))
}

func TestAdd_RejectsZeroAmount(t *testing.T) {
	h := newSvc(t)
	_, err := h.Tx.Add(service.AddInput{Type: "支出", Amount: 0, TransDate: "2026-06-19"})
	require.Error(t, err)
}

func TestAdd_RejectsInvalidType(t *testing.T) {
	h := newSvc(t)
	_, err := h.Tx.Add(service.AddInput{Type: "其他", Amount: 10})
	require.Error(t, err)
}

func TestAdd_Duplicate(t *testing.T) {
	h := newSvc(t)
	in := service.AddInput{
		Type: "支出", Amount: 30, Category: "食品", Account: "微信",
		TransDate: "2026-06-19 12:00:00",
	}
	_, err := h.Tx.Add(in)
	require.NoError(t, err)
	_, err = h.Tx.Add(in)
	require.ErrorIs(t, err, domain.ErrDuplicate)
}

func TestAdd_ForceBypassesDuplicate(t *testing.T) {
	h := newSvc(t)
	in := service.AddInput{
		Type: "支出", Amount: 30, Category: "食品", Account: "微信",
		TransDate: "2026-06-19 12:00:00", Force: true,
	}
	_, err := h.Tx.Add(in)
	require.NoError(t, err)
	_, err = h.Tx.Add(in)
	require.NoError(t, err)
}

func TestList_FilterByCategory(t *testing.T) {
	h := newSvc(t)
	sampleData(t, h.Tx)
	rows, total, err := h.Tx.List(domain.ListFilter{Category: "食品"})
	require.NoError(t, err)
	assert.Equal(t, 2, total)
	for _, r := range rows {
		assert.Equal(t, "食品", deref(r.Category))
	}
}

func TestSearch(t *testing.T) {
	h := newSvc(t)
	sampleData(t, h.Tx)
	rows, err := h.Tx.Search("午餐", "all", 50)
	require.NoError(t, err)
	assert.Len(t, rows, 1)
	assert.Equal(t, "午餐", deref(rows[0].Note))
}

func TestSoftDeleteAndRestore(t *testing.T) {
	h := newSvc(t)
	sampleData(t, h.Tx)
	rows, _, _ := h.Tx.List(domain.ListFilter{})
	first := rows[0].ID
	require.NoError(t, h.Tx.SoftDelete(first))
	rows2, total, _ := h.Tx.List(domain.ListFilter{})
	assert.Equal(t, 4, total)
	assert.NotContains(t, ids(rows2), first)
	rowsAll, _, _ := h.Tx.List(domain.ListFilter{IncludeDeleted: true})
	assert.Contains(t, ids(rowsAll), first)
	require.NoError(t, h.Tx.Restore(first))
	rows3, _, _ := h.Tx.List(domain.ListFilter{})
	assert.Contains(t, ids(rows3), first)
}

func TestHardDelete(t *testing.T) {
	h := newSvc(t)
	sampleData(t, h.Tx)
	rows, _, _ := h.Tx.List(domain.ListFilter{})
	first := rows[0].ID
	require.NoError(t, h.Tx.HardDelete(first))
	rowsAll, _, _ := h.Tx.List(domain.ListFilter{IncludeDeleted: true})
	assert.NotContains(t, ids(rowsAll), first)
}

func TestUpdate_Whitelist(t *testing.T) {
	h := newSvc(t)
	sampleData(t, h.Tx)
	rows, _, _ := h.Tx.List(domain.ListFilter{})
	first := rows[0].ID
	require.NoError(t, h.Tx.Update(first, "category", "娱乐"))
	got, _ := h.Tx.Get(first)
	assert.Equal(t, "娱乐", deref(got.Category))
}

func TestUpdate_RejectsBogusField(t *testing.T) {
	h := newSvc(t)
	sampleData(t, h.Tx)
	rows, _, _ := h.Tx.List(domain.ListFilter{})
	first := rows[0].ID
	err := h.Tx.Update(first, "is_deleted", "1")
	assert.Error(t, err)
}

func TestSummary(t *testing.T) {
	h := newSvc(t)
	sampleData(t, h.Tx)
	sum, err := h.Tx.Summary("2026-06-01", "2026-06-30")
	require.NoError(t, err)
	assert.InDelta(t, 8000, sum.Income, 0.01)
	assert.InDelta(t, 203.5, sum.Expense, 0.01)
	assert.Equal(t, 5, sum.Count)
}

func TestStatistics_ByCategory(t *testing.T) {
	h := newSvc(t)
	sampleData(t, h.Tx)
	rows, err := h.Tx.Statistics("category", "", "2026-06-01", "2026-06-30")
	require.NoError(t, err)
	m := statsByGroup(rows)
	assert.InDelta(t, 8000, m["工资"].Income, 0.01)
	assert.InDelta(t, 145.5, m["食品"].Expense, 0.01)
}

func TestStatistics_ByMonth(t *testing.T) {
	h := newSvc(t)
	sampleData(t, h.Tx)
	rows, err := h.Tx.Statistics("month", "", "2026-06-01", "2026-06-30")
	require.NoError(t, err)
	assert.Greater(t, len(rows), 0)
}

func TestAccountsAndCategories(t *testing.T) {
	h := newSvc(t)
	sampleData(t, h.Tx)
	acc, err := h.Tx.ListAccounts()
	require.NoError(t, err)
	assert.Contains(t, acc, "微信")
	cat, err := h.Tx.ListCategories()
	require.NoError(t, err)
	assert.Contains(t, cat, "食品")
}

func TestImportCSV(t *testing.T) {
	h := newSvc(t)
	csv := strings.NewReader(strings.Join([]string{
		"交易类型,金额,日期,类别,子类别,账户,项目,成员,商家,备注",
		"支出,12.5,2026/06/19 12:00,食品,午餐,微信,,,便利店,沙拉",
		"收入,8000,2026/06/01 09:00,工资,,银行卡,,,公司,月薪",
		"支出,无效,2026/06/19 12:00,食品,午餐,微信,,,便利店,沙拉",
		"未知类型,5,2026/06/19 12:00,食品,午餐,微信,,,便利店,沙拉",
		"", "", "", "", "", "", "", "", "", "",
	}, "\n"))
	res, err := h.Tx.ImportCSV(csv)
	require.NoError(t, err)
	assert.Equal(t, 2, res.Imported)
	assert.GreaterOrEqual(t, res.Skipped, 2)
}

func TestExport_CSV(t *testing.T) {
	h := newSvc(t)
	sampleData(t, h.Tx)
	var sb strings.Builder
	require.NoError(t, h.Tx.Export(domain.ListFilter{Limit: 1000}, &sb, service.FormatCSV))
	out := sb.String()
	assert.Contains(t, out, "id,type,amount,category")
	assert.Contains(t, out, "食品")
}

func TestExport_JSON(t *testing.T) {
	h := newSvc(t)
	sampleData(t, h.Tx)
	var sb strings.Builder
	require.NoError(t, h.Tx.Export(domain.ListFilter{Limit: 1000}, &sb, service.FormatJSON))
	assert.Contains(t, sb.String(), `"type": "支出"`)
}

func TestSuggestion(t *testing.T) {
	h := newSvc(t)
	sampleData(t, h.Tx)
	s, err := h.Tx.Suggestion("", "")
	require.NoError(t, err)
	assert.NotEmpty(t, s.Categories)
}

func TestTags_CreateAndAttach(t *testing.T) {
	h := newSvc(t)
	id, err := h.Tag.Create("日常", "#abcdef")
	require.NoError(t, err)
	assert.Greater(t, id, int64(0))
	txn, err := h.Tx.Add(service.AddInput{
		Type: "支出", Amount: 5, Category: "食品", TransDate: "2026-06-19 12:00:00",
		TagNames: []string{"日常"}, Force: true,
	})
	require.NoError(t, err)
	assert.Contains(t, txn.TagNames, "日常")
}

func deref(p *string) string {
	if p == nil {
		return ""
	}
	return *p
}

func ids(rows []domain.Transaction) []int64 {
	out := make([]int64, 0, len(rows))
	for _, r := range rows {
		out = append(out, r.ID)
	}
	return out
}

func statsByGroup(rows []repo.StatsResult) map[string]repo.StatsResult {
	m := make(map[string]repo.StatsResult, len(rows))
	for _, r := range rows {
		m[r.Group] = r
	}
	return m
}
