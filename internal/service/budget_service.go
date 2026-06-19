package service

import (
	"strings"
	"time"

	"github.com/kdeerfish/ledger/internal/domain"
	"github.com/kdeerfish/ledger/internal/repo"
)

// BudgetService handles budget / template CRUD and the check workflow.
type BudgetService struct {
	Repo     *repo.BudgetRepo
	Template *repo.BudgetTemplateRepo
}

func NewBudgetService(b *repo.BudgetRepo, t *repo.BudgetTemplateRepo) *BudgetService {
	return &BudgetService{Repo: b, Template: t}
}

// SetInput is the parameter object for Set.
type SetInput struct {
	Category       string
	Amount         float64
	Year           int
	Month          int
	DimensionType  string
	DimensionValue string
}

// Set creates or updates a budget row.
func (s *BudgetService) Set(in SetInput) error {
	if in.Category == "" {
		return domain.Wrap(domain.ErrInvalidInput, "category is required")
	}
	if in.Amount <= 0 {
		return domain.Wrap(domain.ErrInvalidInput, "amount must be > 0")
	}
	if in.Year == 0 {
		in.Year = time.Now().Year()
	}
	if in.Month == 0 {
		in.Month = int(time.Now().Month())
	}
	if in.DimensionType == "" {
		in.DimensionType = "category"
	}
	b := &domain.Budget{
		Category: in.Category, Amount: in.Amount, Year: in.Year, Month: in.Month,
		DimensionType:  in.DimensionType,
		DimensionValue: ptrString(in.DimensionValue),
	}
	return s.Repo.Set(b)
}

// List returns budgets for the period (year=0 means "all").
func (s *BudgetService) List(year, month int) ([]domain.Budget, error) {
	return s.Repo.List(year, month)
}

// Check computes the spent / remaining / percentage per budget for the period.
func (s *BudgetService) Check(year, month int) ([]domain.BudgetCheck, error) {
	if year == 0 {
		year = time.Now().Year()
	}
	if month == 0 {
		month = int(time.Now().Month())
	}
	return s.Repo.Check(year, month)
}

// Delete removes a budget row.
func (s *BudgetService) Delete(id int64) error { return s.Repo.Delete(id) }

// CreateBudgetTemplateInput is the payload for CreateBudgetTemplate.
type CreateBudgetTemplateInput struct {
	Name           string
	Description    string
	Category       string
	Amount         float64
	DimensionType  string
	DimensionValue string
	Account        string
	Project        string
	Member         string
	Merchant       string
	Note           string
	Year           *int
	Month          *int
}

func (s *BudgetService) CreateBudgetTemplate(in CreateBudgetTemplateInput) (*domain.BudgetTemplate, error) {
	if strings.TrimSpace(in.Name) == "" {
		return nil, domain.Wrap(domain.ErrInvalidInput, "name is required")
	}
	if in.DimensionType == "" {
		in.DimensionType = "category"
	}
	t := &domain.BudgetTemplate{
		Name: in.Name, Description: ptrString(in.Description),
		Category: ptrString(in.Category), Amount: in.Amount,
		DimensionType:  in.DimensionType,
		DimensionValue: ptrString(in.DimensionValue),
		Account: ptrString(in.Account), Project: ptrString(in.Project),
		Member: ptrString(in.Member), Merchant: ptrString(in.Merchant),
		Note: ptrString(in.Note), Year: in.Year, Month: in.Month,
	}
	if _, err := s.Template.Insert(t); err != nil {
		return nil, err
	}
	return t, nil
}

func (s *BudgetService) ListBudgetTemplates() ([]domain.BudgetTemplate, error) {
	return s.Template.List()
}

func (s *BudgetService) UpdateBudgetTemplate(id int64, fields map[string]any) error {
	return s.Template.UpdateFields(id, fields)
}

func (s *BudgetService) DeleteBudgetTemplate(id int64) error {
	return s.Template.Delete(id)
}

// ApplyBudgetTemplate materialises a template into one or more budget rows.
// If the template defines year/month, only that period is created; otherwise
// the current month is used.
func (s *BudgetService) ApplyBudgetTemplate(id int64) ([]domain.Budget, error) {
	t, err := s.Template.Get(id)
	if err != nil {
		return nil, err
	}
	year, month := time.Now().Year(), int(time.Now().Month())
	if t.Year != nil {
		year = *t.Year
	}
	if t.Month != nil {
		month = *t.Month
	}
	if t.Category == nil || *t.Category == "" {
		return nil, domain.Wrap(domain.ErrInvalidInput, "template has no category")
	}
	b := &domain.Budget{
		Category: *t.Category, Amount: t.Amount, Year: year, Month: month,
		DimensionType:  t.DimensionType,
		DimensionValue: t.DimensionValue,
	}
	if err := s.Repo.Set(b); err != nil {
		return nil, err
	}
	return []domain.Budget{*b}, nil
}

// SuggestBudgetTemplates ranks templates by amount desc, capped at 3.
func (s *BudgetService) SuggestBudgetTemplates(limit int) ([]domain.BudgetTemplate, error) {
	if limit <= 0 {
		limit = 3
	}
	all, err := s.Template.List()
	if err != nil {
		return nil, err
	}
	if len(all) > limit {
		all = all[:limit]
	}
	return all, nil
}
