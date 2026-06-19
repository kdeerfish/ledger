// Package webui embeds the built React SPA at compile time. The actual files
// live under ../../frontend/dist. The //go:embed directive below is matched
// at package build time and is the single source of truth for the SPA.
//
// We split embed and API concerns so unit tests can build without the SPA
// (and we don't pay the binary size cost in non-Web builds).
package webui

import (
	"embed"
	"io/fs"
)

//go:embed all:dist
var distFS embed.FS

// FS returns an fs.FS rooted at the dist/ directory.
func FS() fs.FS {
	sub, err := fs.Sub(distFS, "dist")
	if err != nil {
		// distFS always contains "dist" because of the //go:embed pattern.
		panic(err)
	}
	return sub
}
