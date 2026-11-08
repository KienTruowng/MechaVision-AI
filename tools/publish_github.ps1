param(
    [string]$Repository = 'MechaVision-AI',
    [ValidateSet('private','public')][string]$Visibility = 'private'
)
$ErrorActionPreference = 'Stop'
Set-Location (Resolve-Path (Join-Path $PSScriptRoot '..'))
if (-not (Get-Command git -ErrorAction SilentlyContinue)) { throw 'Install Git for Windows first.' }
if (-not (Get-Command gh -ErrorAction SilentlyContinue)) { throw 'Install GitHub CLI and run gh auth login first.' }
gh auth status
if ($LASTEXITCODE -ne 0) { throw 'Sign in with gh auth login.' }
$account = gh api user --jq .login
if ($account -ne 'KienTruowng') { throw "Signed in as '$account', expected 'KienTruowng'." }
if (-not (Test-Path '.git')) { git init -b main }
git add .
git diff --cached --quiet
if ($LASTEXITCODE -ne 0) {
    git commit -m 'Initial MechaVision AI research workbench'
    if ($LASTEXITCODE -ne 0) { throw 'Configure git user.name and user.email, then rerun.' }
}
git branch -M main
$full = "KienTruowng/$Repository"
gh repo view $full *> $null
if ($LASTEXITCODE -eq 0) {
    git remote get-url origin *> $null
    if ($LASTEXITCODE -ne 0) { git remote add origin "https://github.com/$full.git" }
    git push -u origin main
} else {
    gh repo create $full "--$Visibility" --source . --remote origin --push
}
if ($LASTEXITCODE -ne 0) { throw 'GitHub publish failed. Check the output above.' }
Write-Host "Published: https://github.com/$full" -ForegroundColor Green
