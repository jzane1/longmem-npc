# PostToolUse hook: format AND lint any Python file Claude just edited or wrote.
# Contract: exit 0 = fine; exit 2 = problem, stderr is fed back to Claude.
# Deliberately dormant (exit 0) when: no file path, not a .py file, or ruff not installed
# (neither on PATH nor as a module of the global python).
#
# `ruff check` joined the gate 2026-07-28. Before that only `format` ran, and
# CLAUDE.md's "enforced mechanically" was half true: a dead local sat in a
# floor-verified file because nothing ever linted. Rules and per-file ignores
# live in ruff.toml; ruff itself is pinned in requirements.txt so formatter
# output cannot drift between releases.

# Run from the project root regardless of the caller's working directory.
if ($env:CLAUDE_PROJECT_DIR) {
    Set-Location $env:CLAUDE_PROJECT_DIR
} else {
    Set-Location (Split-Path (Split-Path $PSScriptRoot))
}

$raw = [Console]::In.ReadToEnd()
try { $payload = $raw | ConvertFrom-Json } catch { exit 0 }

$path = $payload.tool_input.file_path
if (-not $path) { $path = $payload.inputs.file_path }   # older payload shape
if (-not $path) { exit 0 }
if ($path -notmatch '\.py$') { exit 0 }
if (-not (Test-Path $path)) { exit 0 }
# Resolve ruff: prefer the PATH executable, fall back to the module install
# (ruff is pip-installed on this machine but its Scripts dir is not on PATH).
$ruffExe = $null
$ruffPrefix = @()
if (Get-Command ruff -ErrorAction SilentlyContinue) {
    $ruffExe = 'ruff'
} elseif (Get-Command python -ErrorAction SilentlyContinue) {
    python -m ruff --version *> $null
    if ($LASTEXITCODE -eq 0) { $ruffExe = 'python'; $ruffPrefix = @('-m', 'ruff') }
}
if (-not $ruffExe) { exit 0 }

$out = & $ruffExe @($ruffPrefix + @('format', $path)) 2>&1 | Out-String
if ($LASTEXITCODE -ne 0) {
    [Console]::Error.WriteLine("ruff format failed on $path - almost certainly a syntax error in what was just written. Fix it. ruff says:")
    [Console]::Error.WriteLine($out)
    exit 2
}

# Lint the formatted file. Never --fix: the hook reports, Claude decides.
$out = & $ruffExe @($ruffPrefix + @('check', $path)) 2>&1 | Out-String
if ($LASTEXITCODE -ne 0) {
    [Console]::Error.WriteLine("ruff check found lint violations in $path. Fix them (do not add a blanket noqa). ruff says:")
    [Console]::Error.WriteLine($out)
    exit 2
}
exit 0
