$ErrorActionPreference = "Stop"

$bundledPython = "C:\Users\awind\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe"
$systemPython = (Get-Command python -ErrorAction SilentlyContinue).Source
$python = if ($systemPython) {
    $systemPython
} elseif (Test-Path -LiteralPath $bundledPython) {
    $bundledPython
} else {
    throw "Python runtime was not found."
}

$cacheRoot = "C:\tmp\trading-python-cache"
New-Item -ItemType Directory -Path $cacheRoot -Force | Out-Null
$env:PYTHONPYCACHEPREFIX = $cacheRoot

& $python @args
exit $LASTEXITCODE
