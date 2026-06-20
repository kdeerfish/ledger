SHELL := powershell.exe
GO    ?= go
BIN   ?= bin/ledger
PKG   := ./...
VER   := $(shell $(GO) run ./internal/version 2>$null; if ($$LASTEXITCODE -ne 0) { "0.2.0-dev" })

# GOPATH/GOMODCACHE must be set before go commands; VSCode tasks handle this
# automatically via settings.json. For plain `make`, export them once:
#   export GOPATH=$HOME/go-pkg  export GOMODCACHE=$GOPATH/mod

.PHONY: help all build run test test-unit test-integration test-e2e \
        test-race fuzz fuzz-quick bench coverage coverage-html lint fmt vet \
        clean clean-db docker docker-run snapshot release check pre-commit \
        test-frontend test-frontend-coverage coverage-all

all: fmt vet test build

help:
	@Write-Host ""
	@Write-Host "Ledger (Go) - build / test / deploy targets"
	@Write-Host "============================================"
	@Write-Host ""
	@Write-Host "  BUILD"
	@Write-Host "    make build            build single binary ($(BIN))"
	@Write-Host "    make run              build + run CLI (./$(BIN) --help)"
	@Write-Host ""
	@Write-Host "  TEST"
	@Write-Host "    make test             run ALL unit tests"
	@Write-Host "    make test-unit        same as 'make test'"
	@Write-Host "    make test-integration integration tests (real SQLite, -tags=integration)"
	@Write-Host "    make test-e2e         end-to-end HTTP tests (-tags=e2e)"
	@Write-Host "    make test-all         unit + integration + e2e (full suite)"
	@Write-Host "    make test-race        unit tests with race detector (needs CGO/gcc)"
	@Write-Host "    make fuzz-quick       5s fuzz smoke test"
	@Write-Host "    make fuzz             60s fuzz on all fuzz targets"
	@Write-Host "    make bench            run all benchmarks (3s each)"
	@Write-Host "    make coverage         unit tests + coverage report"
	@Write-Host "    make coverage-html    unit tests + HTML coverage report"
	@Write-Host "    make test-frontend   frontend unit tests (vitest)"
	@Write-Host "    make test-frontend-coverage  frontend tests + coverage report"
	@Write-Host "    make coverage-all     Go + frontend combined coverage"
	@Write-Host "    make check            fmt + vet + test (pre-commit gate)"
	@Write-Host "    make pre-commit       same as check (git hook alias)"
	@Write-Host ""
	@Write-Host "  LINT / FORMAT"
	@Write-Host "    make fmt              gofmt -s -w ."
	@Write-Host "    make vet              go vet ./..."
	@Write-Host "    make lint             golangci-lint run (needs install)"
	@Write-Host ""
	@Write-Host "  DOCKER"
	@Write-Host "    make docker           build container image"
	@Write-Host "    make docker-run       run container, expose 5800"
	@Write-Host ""
	@Write-Host "  RELEASE"
	@Write-Host "    make snapshot         goreleaser --snapshot --clean (local dry-run)"
	@Write-Host "    make release          goreleaser release (needs GITHUB_TOKEN)"
	@Write-Host "    make install          go install ./cmd/ledger"
	@Write-Host ""
	@Write-Host "  CLEAN"
	@Write-Host "    make clean            remove build artefacts"
	@Write-Host "    make clean-db         remove ledger.db"
	@Write-Host ""

# ─── Build ────────────────────────────────────────────────────────────────

build:
	$(GO) build -trimpath -ldflags "-s -w" -o $(BIN) ./cmd/ledger

run: build
	./$(BIN) --help

install:
	$(GO) install ./cmd/ledger

# ─── Test: Unit (default) ─────────────────────────────────────────────────

test: test-unit

test-unit:
	$(GO) test -count=1 $(PKG)

test-race:
	$(GO) test -race -count=1 $(PKG)

# ─── Test: Integration ───────────────────────────────────────────────────

test-integration:
	$(GO) test -tags=integration -count=1 ./integration/...

# ─── Test: End-to-End ────────────────────────────────────────────────────

test-e2e:
	$(GO) test -tags=e2e -count=1 ./e2e/...

# ─── Test: Full suite ────────────────────────────────────────────────────

test-all: test-unit test-integration test-e2e
	@Write-Host ""
	@Write-Host "=== ALL TEST LAYERS PASSED ==="
	@Write-Host ""

# ─── Fuzz ─────────────────────────────────────────────────────────────────

fuzz-quick:
	$(GO) test -run "^$$" -fuzz ParseCSVDate -fuzztime 5s ./internal/service/
	$(GO) test -run "^$$" -fuzz SplitCSV -fuzztime 5s ./internal/service/

fuzz:
	$(GO) test -run "^$$" -fuzz ParseCSVDate -fuzztime 60s ./internal/service/
	$(GO) test -run "^$$" -fuzz SplitCSV -fuzztime 60s ./internal/service/

# ─── Benchmarks ──────────────────────────────────────────────────────────

bench:
	$(GO) test -run "NoMatch" -bench "." -benchtime 1s ./internal/service/

# ─── Coverage ─────────────────────────────────────────────────────────────

coverage:
	$(GO) test -coverprofile=coverage.out -covermode=atomic -count=1 $(PKG)
	$(GO) tool cover -func=coverage.out | Select-Object -Last 1

coverage-html: coverage
	$(GO) tool cover -html=coverage.out -o coverage.html
	@Write-Host "Open coverage.html in browser"

# ─── Frontend Test ────────────────────────────────────────────────────

test-frontend:
	cd frontend; npm run test

test-frontend-coverage:
	cd frontend; npm run test:coverage

# ─── Combined Coverage ────────────────────────────────────────────────

coverage-all: coverage test-frontend-coverage
	@Write-Host ""
	@Write-Host "=== ALL COVERAGE REPORTS GENERATED ==="
	@Write-Host "  Go:        coverage.out"
	@Write-Host "  Frontend:  frontend/coverage/"
	@Write-Host ""

# ─── Lint / Format ───────────────────────────────────────────────────────

fmt:
	$(GO) fmt ./...

vet:
	$(GO) vet ./...

lint:
	golangci-lint run

# ─── Pre-commit gate ────────────────────────────────────────────────────
# Run from VSCode task or git hook.

check: fmt vet test
	@Write-Host ""
	@Write-Host "=== PRE-COMMIT CHECK PASSED ==="
	@Write-Host ""

pre-commit: check

# ─── Docker ──────────────────────────────────────────────────────────────

docker:
	docker build -t ledger:dev -f Dockerfile .

docker-run: docker
	docker run --rm -p 5800:5800 -v $${PWD}/data:/data ledger:dev

# ─── Release ─────────────────────────────────────────────────────────────

snapshot:
	goreleaser release --snapshot --clean

release:
	goreleaser release --clean

# ─── Clean ───────────────────────────────────────────────────────────────

clean:
	Remove-Item -Recurse -Force bin, dist, deploy, coverage.out, coverage.html -ErrorAction SilentlyContinue

clean-db:
	Remove-Item -Force ledger.db, data/ledger.db, data/ledger-go.db -ErrorAction SilentlyContinue
	@Write-Host "Database removed"

# ─── Git hooks setup ─────────────────────────────────────────────────────

pre-commit-setup:
	git config core.hooksPath .githooks
	@Write-Host "pre-commit hook installed (will run gofmt + go vet + go test)"
