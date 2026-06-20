@echo off
REM package.bat - Cross-compile and package the skill for distribution (Windows)
REM Usage: package.bat

echo === Packaging ledger-cli ===

REM Extract version from main.go
for /f "tokens=3 delims= " %%a in ('findstr "const version" main.go') do set VERSION=%%~a
set VERSION=%VERSION:"=%
echo Version: %VERSION%

REM Clean previous builds
if exist bin rmdir /s /q bin
if exist dist rmdir /s /q dist
mkdir bin 2>$null
mkdir dist 2>$null

REM Build targets
echo   Building linux/amd64...
set GOOS=linux&& set GOARCH=amd64&& set CGO_ENABLED=0
go build -trimpath -ldflags "-s -w" -o bin\ledger-cli-linux-amd64 .

echo   Building linux/arm64...
set GOOS=linux&& set GOARCH=arm64&& set CGO_ENABLED=0
go build -trimpath -ldflags "-s -w" -o bin\ledger-cli-linux-arm64 .

echo   Building darwin/amd64...
set GOOS=darwin&& set GOARCH=amd64&& set CGO_ENABLED=0
go build -trimpath -ldflags "-s -w" -o bin\ledger-cli-darwin-amd64 .

echo   Building darwin/arm64...
set GOOS=darwin&& set GOARCH=arm64&& set CGO_ENABLED=0
go build -trimpath -ldflags "-s -w" -o bin\ledger-cli-darwin-arm64 .

echo   Building windows/amd64...
set GOOS=windows&& set GOARCH=amd64&& set CGO_ENABLED=0
go build -trimpath -ldflags "-s -w" -o bin\ledger-cli-windows-amd64.exe .

REM Package skill zip
set SKILL_DIR=dist\ledger-cli
if exist %SKILL_DIR% rmdir /s /q %SKILL_DIR%
mkdir %SKILL_DIR%\bin 2>$null

copy SKILL.md %SKILL_DIR%\ >$null
copy README.md %SKILL_DIR%\ >$null
copy main.go %SKILL_DIR%\ >$null
copy setup.sh %SKILL_DIR%\ >$null
copy bin\ledger-cli-* %SKILL_DIR%\bin\ >$null

REM Create zip using PowerShell
set ZIP_NAME=dist\ledger-cli-%VERSION%-skill.zip
if exist %ZIP_NAME% del %ZIP_NAME%
powershell -Command "Compress-Archive -Path '%SKILL_DIR%' -DestinationPath '%ZIP_NAME%'"
rmdir /s /q %SKILL_DIR%

echo.
echo === Done! ===
echo Binaries:   bin\
echo Skill zip:  %ZIP_NAME%
echo.
echo Upload %ZIP_NAME% to Reasonix Skills or GitHub Release.