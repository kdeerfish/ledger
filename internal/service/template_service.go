package service

import (
	"strings"

	"github.com/kdeerfish/ledger/internal/domain"
	"github.com/kdeerfish/ledger/internal/repo"
)

// TemplateService handles the record_templates table.
type TemplateService struct {
	Repo *repo.RecordTemplateRepo
	Tags *repo.TagRepo
	Tx   *TransactionService
}

func NewTemplateService(r *repo.RecordTemplateRepo, g *repo.TagRepo, tx *TransactionService) *TemplateService {
	return &TemplateService{Repo: r, Tags: g, Tx: tx}
}

// CreateRecordTemplateInput is the payload for CreateRecordTemplate.
type CreateRecordTemplateInput struct {
	Name         string
	Description  string
	TemplateType string
	Type         string
	Amount       float64
	Category     string
	Subcategory  string
	Account      string
	Project      string
	Member       string
	Merchant     string
	Note         string
	Tags         []string
}

func (s *TemplateService) CreateRecordTemplate(in CreateRecordTemplateInput) (*domain.RecordTemplate, error) {
	if strings.TrimSpace(in.Name) == "" {
		return nil, domain.Wrap(domain.ErrInvalidInput, "name is required")
	}
	if in.TemplateType == "" {
		in.TemplateType = "通用"
	}
	tagNames := strings.Join(in.Tags, ",")
	t := &domain.RecordTemplate{
		Name: in.Name, Description: ptrString(in.Description),
		TemplateType: in.TemplateType, Type: ptrString(in.Type),
		Amount: in.Amount, Category: ptrString(in.Category),
		Subcategory: ptrString(in.Subcategory), Account: ptrString(in.Account),
		Project: ptrString(in.Project), Member: ptrString(in.Member),
		Merchant: ptrString(in.Merchant), Note: ptrString(in.Note),
		Tags: tagNames,
	}
	if _, err := s.Repo.Insert(t); err != nil {
		return nil, err
	}
	return t, nil
}

func (s *TemplateService) ListRecordTemplates(templateType string) ([]domain.RecordTemplate, error) {
	return s.Repo.List(templateType)
}

func (s *TemplateService) GetRecordTemplate(id int64) (*domain.RecordTemplate, error) {
	return s.Repo.Get(id)
}

func (s *TemplateService) UpdateRecordTemplate(id int64, fields map[string]any) error {
	return s.Repo.UpdateFields(id, fields)
}

func (s *TemplateService) DeleteRecordTemplate(id int64) error {
	return s.Repo.Delete(id)
}

// ApplyRecordTemplate creates a new transaction from a template and bumps
// usage_count. amountOverride may override the stored amount.
func (s *TemplateService) ApplyRecordTemplate(id int64, amountOverride float64) (*domain.Transaction, error) {
	t, err := s.Repo.Get(id)
	if err != nil {
		return nil, err
	}
	amount := t.Amount
	if amountOverride > 0 {
		amount = amountOverride
	}
	tagNames := splitCSV(t.Tags)
	in := AddInput{
		Type:        domain.TxnType(derefString(t.Type)),
		Amount:      amount,
		Category:    derefString(t.Category),
		Subcategory: derefString(t.Subcategory),
		Account:     derefString(t.Account),
		Project:     derefString(t.Project),
		Member:      derefString(t.Member),
		Merchant:    derefString(t.Merchant),
		Note:        derefString(t.Note),
		Force:       true, // templates are user-confirmed
		TagNames:    tagNames,
	}
	if in.Type == "" {
		in.Type = domain.TxnExpense
	}
	tx, err := s.Tx.Add(in)
	if err != nil {
		return nil, err
	}
	if err := s.Repo.IncrementUsage(id); err != nil {
		return tx, err
	}
	return tx, nil
}

// SuggestRecordTemplates returns the top N templates by usage count.
func (s *TemplateService) SuggestRecordTemplates(limit int) ([]domain.RecordTemplate, error) {
	if limit <= 0 {
		limit = 3
	}
	all, err := s.Repo.List("")
	if err != nil {
		return nil, err
	}
	if len(all) > limit {
		all = all[:limit]
	}
	return all, nil
}

func splitCSV(s string) []string {
	if s == "" {
		return nil
	}
	parts := strings.Split(s, ",")
	out := make([]string, 0, len(parts))
	for _, p := range parts {
		p = strings.TrimSpace(p)
		if p != "" {
			out = append(out, p)
		}
	}
	return out
}
