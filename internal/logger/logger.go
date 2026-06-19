// Package logger configures the global slog handler. Call Setup once during
// process initialisation; the returned *slog.Logger is also installed as the
// process-wide default.
package logger

import (
	"log/slog"
	"os"
	"strings"
)

// Setup configures slog with the given level and format. format may be "json"
// (default) or "text". level is one of: debug, info, warn, error.
func Setup(level, format string) *slog.Logger {
	var lvl slog.Level
	switch strings.ToLower(level) {
	case "debug":
		lvl = slog.LevelDebug
	case "warn", "warning":
		lvl = slog.LevelWarn
	case "error":
		lvl = slog.LevelError
	default:
		lvl = slog.LevelInfo
	}

	opts := &slog.HandlerOptions{Level: lvl}

	var h slog.Handler
	switch strings.ToLower(format) {
	case "text":
		h = slog.NewTextHandler(os.Stdout, opts)
	default:
		h = slog.NewJSONHandler(os.Stdout, opts)
	}

	logger := slog.New(h)
	slog.SetDefault(logger)
	return logger
}
