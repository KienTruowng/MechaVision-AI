param(
    [string]$Repository = 'MechaVision-AI',
    [ValidateSet('private','public')][string]$Visibility = 'private'
)
$ErrorActionPreference = 'Stop'
Set-Location (Resolve-Path (Join-Path $PSScriptRoot '..'))
if (-not (Get-Command git -ErrorAction SilentlyContinue)) { throw 'Hãy cài Git cho Windows trước.' }
if (-not (Get-Command gh -ErrorAction SilentlyContinue)) { throw 'Hãy cài GitHub CLI và chạy gh auth login trước.' }
gh auth status
if ($LASTEXITCODE -ne 0) { throw 'Đăng nhập bằng gh auth login.' }
$account = gh api user --jq .login
if ($account -ne 'KienTruowng') { throw "Đang đăng nhập bằng '$account', cần tài khoản 'KienTruowng'." }
if (-not (Test-Path '.git')) { git init -b main }
git add .
git diff --cached --quiet
if ($LASTEXITCODE -ne 0) {
    git commit -m 'Khởi tạo bộ công cụ nghiên cứu MechaVision AI'
    if ($LASTEXITCODE -ne 0) { throw 'Cấu hình git user.name và user.email rồi chạy lại.' }
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
if ($LASTEXITCODE -ne 0) { throw 'Xuất bản lên GitHub thất bại. Hãy xem thông báo ở trên.' }
Write-Host "Đã xuất bản: https://github.com/$full" -ForegroundColor Green
