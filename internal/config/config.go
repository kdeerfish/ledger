// Package config loads runtime configuration from environment variables,
// .env files, and built-in defaults. Values are read once at process start.
package config

import (
	"fmt"
	"os"
	"path/filepath"
	"strings"

	"github.com/spf13/viper"
)

// Config holds all runtime configuration values.
type Config struct {
	// DBPath is the absolute path to the SQLite database file.
	DBPath string
	// WebDevProxyURL is the upstream Vite dev server URL, used when running in
	// "dev" mode. Empty in production builds.
	WebDevProxyURL string
	// WebHost is the HTTP listen address (e.g. "0.0.0.0").
	WebHost string
	// WebPort is the HTTP listen port (e.g. 5800).
	WebPort int
	// WebDebug toggles verbose logging and human-readable JSON.
	WebDebug bool
	// WebCorsOrigins is a comma-separated list of allowed CORS origins.
	WebCorsOrigins []string
	// LogLevel is one of: debug, info, warn, error.
	LogLevel string
	// LogFormat is "json" or "text".
	LogFormat string
	// DataDir is the directory that contains the database file.
	DataDir string
}

// FromViper materialises a Config from the given viper instance.
func FromViper(v *viper.Viper) (*Config, error) {
	cfg := &Config{
		DBPath:         v.GetString("LEDGER_DB_PATH"),
		WebDevProxyURL: v.GetString("WEB_DEV_PROXY_URL"),
		WebHost:        v.GetString("WEB_HOST"),
		WebPort:        v.GetInt("WEB_PORT"),
		WebDebug:       v.GetBool("WEB_DEBUG"),
		WebCorsOrigins: splitCSV(v.GetString("WEB_CORS_ORIGINS")),
		LogLevel:       v.GetString("LOG_LEVEL"),
		LogFormat:      v.GetString("LOG_FORMAT"),
	}

	// Default log format: text in dev, json in prod.
	if cfg.LogFormat == "" {
		if cfg.WebDebug {
			cfg.LogFormat = "text"
		} else {
			cfg.LogFormat = "json"
		}
	}

	// Resolve database path. Relative paths are anchored to the data directory
	// (which defaults to <repo>/data). Missing parent directories are created.
	if cfg.DBPath == "" {
		cfg.DBPath = "ledger.db"
	}
	if !filepath.IsAbs(cfg.DBPath) {
		anchor := resolveDataDir(v)
		cfg.DBPath = filepath.Join(anchor, cfg.DBPath)
	}
	cfg.DataDir = filepath.Dir(cfg.DBPath)
	if err := os.MkdirAll(cfg.DataDir, 0o755); err != nil {
		return nil, fmt.Errorf("create data dir %q: %w", cfg.DataDir, err)
	}

	return cfg, nil
}

// Load reads configuration from the current working directory and process
// environment. Existing environment variables always take precedence over
// file-based values, mirroring the original Python implementation.
func Load() (*Config, error) {
	v := viper.New()
	v.SetConfigName(".env")
	v.SetConfigType("env")
	v.AddConfigPath(".")
	v.AddConfigPath("..")
	v.AddConfigPath("../..")
	v.SetEnvPrefix("")
	v.SetEnvKeyReplacer(strings.NewReplacer(".", "_"))
	v.AutomaticEnv()

	// Built-in defaults. These are intentionally identical to the original
	// Python project so the migration is behaviour-preserving.
	v.SetDefault("LEDGER_DB_PATH", "ledger.db")
	v.SetDefault("WEB_HOST", "0.0.0.0")
	v.SetDefault("WEB_PORT", 5800)
	v.SetDefault("WEB_DEBUG", false)
	v.SetDefault("WEB_CORS_ORIGINS", "*")
	v.SetDefault("LOG_LEVEL", "info")
	v.SetDefault("LOG_FORMAT", "")
	v.SetDefault("WEB_DEV_PROXY_URL", "")

	// .env is optional; missing file is not an error.
	_ = v.ReadInConfig()

	return FromViper(v)
}

func resolveDataDir(v *viper.Viper) string {
	// LEDGER_PATH (rare, kept for compat) overrides the anchor.
	if p := v.GetString("LEDGER_PATH"); p != "" {
		if abs, err := filepath.Abs(p); err == nil {
			return abs
		}
		return p
	}
	// Default anchor: <repo>/data
	if abs, err := filepath.Abs("data"); err == nil {
		return abs
	}
	if cwd, err := os.Getwd(); err == nil {
		return cwd
	}
	return "."
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
