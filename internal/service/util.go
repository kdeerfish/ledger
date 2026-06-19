package service

// ptrString returns a pointer to s, or nil if s is empty.
func ptrString(s string) *string {
	if s == "" {
		return nil
	}
	return &s
}

// derefString returns the dereferenced value of p, or empty if nil.
func derefString(p *string) string {
	if p == nil {
		return ""
	}
	return *p
}
