# Ledger CLI Makefile

BINARY  := ledger-cli
VERSION := $(shell git describe --tags --always --dirty 2>/dev/null || echo dev)
LDFLAGS := -s -w -X main.version=$(VERSION)

.PHONY: build clean test cross

build:
	go build -ldflags "$(LDFLAGS)" -o bin/$(BINARY)$(if $(findstring windows,$(OS)),.exe) ./cmd/ledger-cli

clean:
	rm -rf bin/

test:
	go test ./...

# 交叉编译常用平台
cross: cross-linux-amd64 cross-linux-arm64 cross-windows

cross-linux-amd64:
	GOOS=linux GOARCH=amd64 go build -ldflags "$(LDFLAGS)" -o bin/$(BINARY)-linux-amd64 ./cmd/ledger-cli

cross-linux-arm64:
	GOOS=linux GOARCH=arm64 go build -ldflags "$(LDFLAGS)" -o bin/$(BINARY)-linux-arm64 ./cmd/ledger-cli

cross-windows:
	GOOS=windows GOARCH=amd64 go build -ldflags "$(LDFLAGS)" -o bin/$(BINARY)-windows-amd64.exe ./cmd/ledger-cli