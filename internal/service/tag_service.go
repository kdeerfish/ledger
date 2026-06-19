package service

import (
	"github.com/kdeerfish/ledger/internal/domain"
	"github.com/kdeerfish/ledger/internal/repo"
)

// TagService handles tag CRUD.
type TagService struct {
	Repo *repo.TagRepo
	Tx   *repo.TransactionRepo
}

func NewTagService(r *repo.TagRepo, tx *repo.TransactionRepo) *TagService {
	return &TagService{Repo: r, Tx: tx}
}

func (s *TagService) List() ([]domain.Tag, error)              { return s.Repo.List() }
func (s *TagService) Create(name, color string) (int64, error) { return s.Repo.Create(name, color) }
func (s *TagService) Get(id int64) (*domain.Tag, error)        { return s.Repo.Get(id) }
func (s *TagService) Delete(id int64) error                    { return s.Repo.Delete(id) }
func (s *TagService) Count() (int, error)                      { return s.Repo.Count() }

// Transactions returns paginated transactions for a tag.
func (s *TagService) Transactions(tagID int64, limit, offset int) ([]domain.Transaction, error) {
	return s.Tx.TransactionsByTag(tagID, limit, offset)
}
