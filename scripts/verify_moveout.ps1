# Full offline verification for the deterministic MoveOut protocol, including Stage 1 regressions and Stage 2 tests.
$ErrorActionPreference = 'Stop'
$scriptPath = Join-Path $PSScriptRoot 'verify_stage1.ps1'
& powershell -NoProfile -ExecutionPolicy Bypass -File $scriptPath
if ($LASTEXITCODE -ne 0) {
    throw "MoveOut verification failed with exit code $LASTEXITCODE"
}
