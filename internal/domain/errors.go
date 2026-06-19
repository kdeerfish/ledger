// Package domain contains pure data types shared by repo, service, and http
// layers. No business logic and no database/sql types live here.
package domain

import (
	"errors"
	"fmt"
)

// Sentinels used by every layer to classify failures. HTTP and CLI translate
// these into status codes or human-readable messages.
var (
	ErrNotFound        = errors.New("not found")
	ErrAlreadyExists   = errors.New("already exists")
	ErrInvalidInput    = errors.New("invalid input")
	ErrDuplicate       = errors.New("duplicate transaction")
	ErrNoUpdateField   = errors.New("no updateable field provided")
	ErrInvalidField    = errors.New("invalid field name")
	ErrNotImplemented  = errors.New("not implemented")
)

// Wrap attaches a context string to an error without losing the sentinel.
// Uses fmt.Errorf with %w so callers can use errors.Is to classify.
func Wrap(sentinel error, format string, args ...any) error {
	return fmt.Errorf("%w: %s", sentinel, fmt.Sprintf(format, args...))
}
