$ErrorActionPreference = 'Stop'
$repoRoot = Split-Path -Parent $PSScriptRoot
Set-Location -LiteralPath $repoRoot
$env:PYTHONIOENCODING = 'utf-8'

function Invoke-RequiredCheck([string]$Label, [string]$Executable, [string[]]$Arguments) {
    Write-Host "`n== $Label =="
    & $Executable @Arguments
    if ($LASTEXITCODE -ne 0) {
        throw "$Label failed with exit code $LASTEXITCODE"
    }
}

Invoke-RequiredCheck 'Complete suite (Stage 1, historical regressions, Stages 2–4 direct tests)' 'gltest' @('tests', '-q')
Invoke-RequiredCheck 'GenVM lint' 'genvm-lint' @('lint', 'contracts/moveout_protocol_v1.py')
Invoke-RequiredCheck 'GenVM SDK validation' 'genvm-lint' @('check', 'contracts/moveout_protocol_v1.py')
Invoke-RequiredCheck 'Python syntax compilation' 'python' @('-m', 'compileall', '-q', 'contracts', 'tests')

Write-Host "`n== Stage 4 nondeterministic scope scan =="
& python 'scripts/check_stage4_scope.py'
if ($LASTEXITCODE -ne 0) { throw "Stage 4 scope scan failed with exit code $LASTEXITCODE" }

Write-Host "`n== Benchmark-specific production logic scan =="
$benchmarkSelectors = 'MOV-SYN|expected_label|benchmark_manifest'
& rg -n $benchmarkSelectors 'contracts/moveout_protocol_v1.py'
if ($LASTEXITCODE -eq 0) { throw 'Benchmark-specific contract reference found' }
if ($LASTEXITCODE -ne 1) { throw "Benchmark source scan failed with exit code $LASTEXITCODE" }

$sensitive = '-----BEGIN (RSA |OPENSSH |EC )?PRIVATE KEY-----|mnemonic|seed phrase|wallet\.json|api[_-]?key|access[_-]?token|password\s*='
& rg -n -i -- $sensitive 'contracts/moveout_protocol_v1.py' 'docs/MOVEOUT_STAGE_1_1_HARDENING.md'
if ($LASTEXITCODE -eq 0) { throw 'Secret-like material found in reviewed production/documentation files' }
if ($LASTEXITCODE -ne 1) { throw "Secret scan failed with exit code $LASTEXITCODE" }

Write-Host "`n== Diff whitespace check =="
& git diff --check
if ($LASTEXITCODE -ne 0) { throw "git diff --check failed with exit code $LASTEXITCODE" }
& git diff --cached --check
if ($LASTEXITCODE -ne 0) { throw "git diff --cached --check failed with exit code $LASTEXITCODE" }

Write-Host "`nAll MoveOut offline verification checks passed."
