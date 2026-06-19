package config

import (
	"os"
	"path/filepath"
	"testing"

	"github.com/spf13/viper"
	"github.com/stretchr/testify/assert"
	"github.com/stretchr/testify/require"
)

func newViper(t *testing.T) *viper.Viper {
	t.Helper()
	v := viper.New()
	v.Set("LEDGER_DB_PATH", "ledger.db")
	v.Set("WEB_HOST", "0.0.0.0")
	v.Set("WEB_PORT", 5800)
	v.Set("WEB_DEBUG", false)
	v.Set("WEB_CORS_ORIGINS", "*")
	v.Set("LOG_LEVEL", "info")
	v.Set("LOG_FORMAT", "")
	return v
}

func TestFromViper_Defaults(t *testing.T) {
	cfg, err := FromViper(newViper(t))
	require.NoError(t, err)
	assert.Equal(t, 5800, cfg.WebPort)
	assert.False(t, cfg.WebDebug)
	assert.Contains(t, cfg.WebCorsOrigins, "*")
}

func TestFromViper_LogFormat_Auto(t *testing.T) {
	v := newViper(t)
	v.Set("WEB_DEBUG", true)
	cfg, err := FromViper(v)
	require.NoError(t, err)
	assert.Equal(t, "text", cfg.LogFormat)

	v.Set("WEB_DEBUG", false)
	cfg, err = FromViper(v)
	require.NoError(t, err)
	assert.Equal(t, "json", cfg.LogFormat)
}

func TestFromViper_CreatesDataDir(t *testing.T) {
	dir := t.TempDir()
	target := filepath.Join(dir, "nested", "ledger.db")
	v := newViper(t)
	v.Set("LEDGER_DB_PATH", target)
	cfg, err := FromViper(v)
	require.NoError(t, err)
	assert.Equal(t, target, cfg.DBPath)
	stat, err := os.Stat(filepath.Dir(target))
	require.NoError(t, err)
	assert.True(t, stat.IsDir())
}

func TestSplitCSV(t *testing.T) {
	assert.Equal(t, []string{"a", "b", "c"}, splitCSV("a,b,c"))
	assert.Equal(t, []string{"a", "b"}, splitCSV("  a , b "))
	assert.Nil(t, splitCSV(""))
	// Whitespace-only collapses to empty slice (not nil).
	assert.Equal(t, []string{}, splitCSV("   "))
}

func TestLoad_UsesEnv(t *testing.T) {
	t.Setenv("WEB_PORT", "9999")
	t.Setenv("WEB_DEBUG", "true")
	cfg, err := Load()
	require.NoError(t, err)
	assert.Equal(t, 9999, cfg.WebPort)
	assert.True(t, cfg.WebDebug)
}
