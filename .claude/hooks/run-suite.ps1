# Stop hook: the structural suite must be green before Claude ends its turn.
# Contract: exit 0 = allow stopping; exit 2 = suite is red, stderr goes to Claude,
# Claude keeps working. The stop_hook_active guard limits enforcement to one pass
# per turn so this can never loop forever.
# Deliberately dormant (exit 0) when: no test files exist yet, or python/pytest missing.

Set-Location (Split-Path (Split-Path $PSScriptRoot))

$raw = [Console]::In.ReadToEnd()
try {
    $payload = $raw | ConvertFrom-Json
    if ($payload.stop_hook_active) { exit 0 }   # already continuing because of this hook
} catch { }

# Dormant until the suite exists.
$tests = Get-ChildItem -Path tests -Recurse -Filter 'test_*.py' -ErrorAction SilentlyContinue
if (-not $tests) { exit 0 }
if (-not (Get-Command python -ErrorAction SilentlyContinue)) { exit 0 }
python -m pytest --version *> $null
if ($LASTEXITCODE -ne 0) { exit 0 }             # pytest not installed yet

$out = python -m pytest tests -x -q 2>&1 | Out-String
if ($LASTEXITCODE -eq 0) { exit 0 }

# Red suite: feed the tail of the output back to Claude and refuse the stop.
$tail = if ($out.Length -gt 4000) { $out.Substring($out.Length - 4000) } else { $out }
[Console]::Error.WriteLine("Structural suite is RED. Do not finish - fix the failures. pytest output (tail):")
[Console]::Error.WriteLine($tail)
exit 2
