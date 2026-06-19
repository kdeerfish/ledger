// Package version exposes build-time metadata injected via -ldflags.
package version

import "runtime"

// These variables are overridden at build time via:
//
//	-ldflags "-X github.com/kdeerfish/ledger/internal/version.Version=v1.2.3 \
//	          -X github.com/kdeerfish/ledger/internal/version.Commit=$(git rev-parse --short HEAD) \
//	          -X github.com/kdeerfish/ledger/internal/version.BuildTime=$(date -u +%Y-%m-%dT%H:%M:%SZ)"
var (
	Version   = "0.2.0-dev"
	Commit    = "unknown"
	BuildTime = "unknown"
)

// Info aggregates build info for printing.
type Info struct {
	Version   string `json:"version"`
	Commit    string `json:"commit"`
	BuildTime string `json:"build_time"`
	GoVersion string `json:"go_version"`
	OS        string `json:"os"`
	Arch      string `json:"arch"`
}

// Get returns the current build info.
func Get() Info {
	return Info{
		Version:   Version,
		Commit:    Commit,
		BuildTime: BuildTime,
		GoVersion: runtime.Version(),
		OS:        runtime.GOOS,
		Arch:      runtime.GOARCH,
	}
}
