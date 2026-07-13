# PostToolUse hook: format any Python file Claude just edited or wrote.
# Contract: exit 0 = fine; exit 2 = problem, stderr is fed back to Claude.
# Deliberately dormant (exit 0) when: no file path, not a .py file, or ruff not installed.

# Run from the project root regardless of the caller's working directory.
Set-Location (Split-Path (Split-Path $PSScriptRoot))

$raw = [Console]::In.ReadToEnd()
try { $payload = $raw | ConvertFrom-Json } catch { exit 0 }

$path = $payload.tool_input.file_path
if (-not $path) { $path = $payload.inputs.file_path }   # older payload shape
if (-not $path) { exit 0 }
if ($path -notmatch '\.py$') { exit 0 }
if (-not (Test-Path $path)) { exit 0 }
if (-not (Get-Command ruff -ErrorAction SilentlyContinue)) { exit 0 }

$out = ruff format $path 2>&1 | Out-String
if ($LASTEXITCODE -ne 0) {
    [Console]::Error.WriteLine("ruff format failed on $path - almost certainly a syntax error in what was just written. Fix it. ruff says:")
    [Console]::Error.WriteLine($out)
    exit 2
}
exit 0
