param(
  [string]$Python = "python",
  [string]$VendorRoot = ".v4_external"
)
$ErrorActionPreference = "Stop"
$KronosCommit = "67b630e67f6a18c9e9be918d9b4337c960db1e9a"
$MomentCommit = "38f7310ad594100747ca2a8357e9c7ca7d323e0e"
New-Item -ItemType Directory -Force -Path $VendorRoot | Out-Null
$Kronos = Join-Path $VendorRoot "Kronos"
if (-not (Test-Path $Kronos)) {
  git clone https://github.com/shiyu-coder/Kronos.git $Kronos
}
git -C $Kronos fetch --all --tags
git -C $Kronos checkout $KronosCommit
& $Python -m pip install -r (Join-Path $Kronos "requirements.txt")
# MOMENT's released package is sufficient; record the upstream code commit in the V4 manifest.
& $Python -m pip install "momentfm==0.1.5"
Write-Host "EXTERNAL MODEL INSTALL PASS"
Write-Host "Kronos pinned:" $KronosCommit
Write-Host "MOMENT reference commit:" $MomentCommit
