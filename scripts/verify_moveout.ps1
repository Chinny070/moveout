# Full offline verification for MoveOut, including deterministic regressions and Stage 2–4 direct tests.
$ErrorActionPreference = 'Stop'
$scriptPath = Join-Path $PSScriptRoot 'verify_stage1.ps1'
& powershell -NoProfile -ExecutionPolicy Bypass -File $scriptPath
if ($LASTEXITCODE -ne 0) {
    throw "MoveOut verification failed with exit code $LASTEXITCODE"
}
