package service_test

import (
	"testing"

	"github.com/kdeerfish/ledger/internal/domain"
	"github.com/kdeerfish/ledger/internal/service"
	"github.com/stretchr/testify/assert"
	"github.com/stretchr/testify/require"
)

func TestBudget_SetAndCheck(t *testing.T) {
	h := newSvc(t)
	require.NoError(t, h.Budget.Set(service.SetInput{Category: "食品", Amount: 1000, Year: 2026, Month: 6}))
	checks, err := h.Budget.Check(2026, 6)
	require.NoError(t, err)
	require.Len(t, checks, 1)
	assert.Equal(t, "食品", checks[0].Category)
	assert.InDelta(t, 1000, checks[0].Budget, 0.01)
}

func TestBudget_Check_SpentMatches(t *testing.T) {
	h := newSvc(t)
	sampleData(t, h.Tx)
	require.NoError(t, h.Budget.Set(service.SetInput{Category: "食品", Amount: 1000, Year: 2026, Month: 6}))
	checks, _ := h.Budget.Check(2026, 6)
	require.Len(t, checks, 1)
	assert.InDelta(t, 145.5, checks[0].Spent, 0.01)
	assert.InDelta(t, 854.5, checks[0].Remaining, 0.01)
}

func TestBudget_Duplicate_UpdatesAmount(t *testing.T) {
	h := newSvc(t)
	require.NoError(t, h.Budget.Set(service.SetInput{Category: "食品", Amount: 1000, Year: 2026, Month: 6}))
	require.NoError(t, h.Budget.Set(service.SetInput{Category: "食品", Amount: 2000, Year: 2026, Month: 6}))
	bs, _ := h.Budget.List(2026, 6)
	assert.Len(t, bs, 1)
	assert.InDelta(t, 2000, bs[0].Amount, 0.01)
}

func TestBudgetTemplate_CreateAndApply(t *testing.T) {
	h := newSvc(t)
	tpl, err := h.Budget.CreateBudgetTemplate(service.CreateBudgetTemplateInput{
		Name: "月度餐饮", Category: "食品", Amount: 1500,
	})
	require.NoError(t, err)
	assert.Greater(t, tpl.ID, int64(0))
	bs, err := h.Budget.ApplyBudgetTemplate(tpl.ID)
	require.NoError(t, err)
	assert.Len(t, bs, 1)
	assert.InDelta(t, 1500, bs[0].Amount, 0.01)
}

func TestRecordTemplate_ApplyIncrementsUsage(t *testing.T) {
	h := newSvc(t)
	tpl, err := h.Template.CreateRecordTemplate(service.CreateRecordTemplateInput{
		Name: "早餐", Type: "支出", Amount: 8, Category: "食品", Account: "微信",
	})
	require.NoError(t, err)
	tx, err := h.Template.ApplyRecordTemplate(tpl.ID, 0)
	require.NoError(t, err)
	assert.Greater(t, tx.ID, int64(0))
	after, _ := h.Template.GetRecordTemplate(tpl.ID)
	assert.Equal(t, 1, after.UsageCount)
	_, _ = h.Template.ApplyRecordTemplate(tpl.ID, 0)
	after2, _ := h.Template.GetRecordTemplate(tpl.ID)
	assert.Equal(t, 2, after2.UsageCount)
	_ = tx
}

func TestRecordTemplate_Suggest(t *testing.T) {
	h := newSvc(t)
	_, _ = h.Template.CreateRecordTemplate(service.CreateRecordTemplateInput{Name: "a"})
	_, _ = h.Template.CreateRecordTemplate(service.CreateRecordTemplateInput{Name: "b"})
	ts, err := h.Template.SuggestRecordTemplates(1)
	require.NoError(t, err)
	assert.Len(t, ts, 1)
}

func TestTags_Lifecycle(t *testing.T) {
	h := newSvc(t)
	id, err := h.Tag.Create("常用", "")
	require.NoError(t, err)
	tags, _ := h.Tag.List()
	assert.GreaterOrEqual(t, len(tags), 1)
	assert.Equal(t, "常用", tags[0].Name)
	require.NoError(t, h.Tag.Delete(id))
	_, err = h.Tag.Get(id)
	assert.ErrorIs(t, err, domain.ErrNotFound)
}
