param(
  [Parameter(ValueFromRemainingArguments = $true)]
  [string[]]$AppArgs
)

$ErrorActionPreference = "Stop"
$RepoRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
$VenvPython = Join-Path $RepoRoot ".venv\Scripts\python.exe"
$VenvScripts = Join-Path $RepoRoot ".venv\Scripts"
$BundledPython = "C:\Users\User\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe"

Set-Location -LiteralPath $RepoRoot

if (Test-Path -LiteralPath $VenvScripts) {
  $env:PATH = "$VenvScripts;$env:PATH"
}

if (Test-Path -LiteralPath $VenvPython) {
  & $VenvPython -m app @AppArgs
} elseif (Get-Command python -ErrorAction SilentlyContinue) {
  & python -m app @AppArgs
} elseif (Test-Path -LiteralPath $BundledPython) {
  & $BundledPython -m app @AppArgs
} else {
  Write-Error "Python was not found. Install Python or run with the bundled Codex Python path."
}
