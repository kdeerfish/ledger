SHELL := powershell.exe
GO    ?= go
BIN   ?= bin/ledger
PKG   := ./...

.PHONY: help all build run test test-race coverage lint fmt vet clean clean-db docker docker-run release snapshot install deps tidy check

all: fmt vet lint test build

help:
	@Write-Host ""
	@Write-Host "Ledger (Go) - build / test / deploy targets"
	@Write-Host "==========================================="
	@Write-Host "  make build        build single binary ($(BIN))"
	@Write-Host "  make run          build + run CLI (./$(BIN) --help)"
	@Write-Host "  make test         run all unit tests"
	@Write-Host "  make test-race    run tests with -race detector"
	@Write-Host "  make coverage     run tests with coverage report"
	@Write-Host "  make fmt          gofmt -s -w ."
	@Write-Host "  make vet          go vet $(PKG)"
	@Write-Host "  make lint         golangci-lint run (needs golangci-lint)"
	@Write-Host "  make tidy         go mod tidy"
	@Write-Host "  make clean        remove build artefacts"
	@Write-Host "  make docker       build container image"
	@Write-Host "  make docker-run   run container, expose 5800"
	@Write-Host "  make snapshot     goreleaser --snapshot --clean"
	@Write-Host ""

deps:
	$(GO) mod download

tidy:
	$(GO) mod tidy

build:
	$(GO) build -trimpath -ldflags "-s -w" -o $(BIN) ./cmd/ledger

run: build
	./$(BIN) --help

test:
	$(GO) test $(PKG)

test-race:
	$(GO) test -race $(PKG)

coverage:
	$(GO) test -coverprofile=coverage.out -covermode=atomic $(PKG)
	$(GO) tool cover -func=coverage.out
	@if (Test-Path coverage.out) { Write-Host "HTML report: file:///$$(Resolve-Path coverage.out | Split-Path -Parent)\coverage.html" }

fmt:
	$(GO) fmt ./...

vet:
	$(GO) vet $(PKG)

lint:
	golangci-lint run

check: fmt vet test

clean:
	Remove-Item -Recurse -Force bin, dist, deploy, coverage.out, coverage.html -ErrorAction SilentlyContinue

clean-db:
	Remove-Item -Force ledger.db -ErrorAction SilentlyContinue
	Write-Host "ledger.db removed"

docker:
	docker build -t ledger:dev -f Dockerfile .

docker-run: docker
	docker run --rm -p 5800:5800 -v $${PWD}/data:/data ledger:dev

snapshot:
	goreleaser release --snapshot --clean

install:
	$(GO) install $$(Get-Content tools.go | Select-String '_ "github\.com/golangci/golangci-lint/cmd/golangci-lint@' | ForEach-Object { $$_ -split '"' | Select-Object -Index 1 })
