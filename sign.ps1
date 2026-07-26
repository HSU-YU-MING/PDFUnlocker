<#  通用簽章腳本：sign.ps1（PDFUnlocker 專用實例）
    用法：
      powershell -ExecutionPolicy Bypass -File sign.ps1
    YubiKey 要插著，會跳 PIN / 觸碰提示。
    本專案為單檔 exe、zip/直接散布，無安裝檔 → 只簽內容物。
#>
[CmdletBinding()]
param([ValidateSet('content','installer','all')][string]$Target = 'content')

$ErrorActionPreference = 'Stop'
$root = $PSScriptRoot

# ===================== 只改這一區 =====================
$SignTool = 'C:\Program Files (x86)\Windows Kits\10\bin\10.0.26100.0\x64\signtool.exe'
$Thumb    = '5773AB1F9EB95258C45387CA166AD3D64A2EFDD5'
$TsUrl    = 'http://ts.ssl.com'

# 內容物：你的 exe + 自帶第三方 exe（相對本腳本位置）
$ContentFiles = @(
    'dist\PDFUnlocker.exe'
)

# 安裝檔檔名樣式（相對本腳本位置）；沒有安裝檔就設成 ''
$InstallerGlob = ''
# =====================================================

if (-not (Test-Path -LiteralPath $SignTool)) { throw "找不到 signtool：$SignTool" }

function Invoke-Sign {
    param([string]$File)
    if (-not (Test-Path -LiteralPath $File)) { throw "要簽的檔不存在：$File" }
    Write-Host "`n>> 簽章：$File" -ForegroundColor Yellow
    Write-Host "   （若跳 YubiKey PIN / 觸碰提示，請照做）" -ForegroundColor DarkGray
    & $SignTool sign /sha1 $Thumb /fd sha256 /tr $TsUrl /td sha256 /v $File
    if ($LASTEXITCODE -ne 0) { throw "簽章失敗（退出碼 $LASTEXITCODE）：$File" }
}

function Invoke-Verify {
    param([string]$File)
    Write-Host "`n>> 驗證：$File" -ForegroundColor Yellow
    $out = & $SignTool verify /pa /v $File 2>&1 | Out-String
    Write-Host $out
    if ($LASTEXITCODE -ne 0) { throw "驗證失敗（退出碼 $LASTEXITCODE）：$File" }
    if ($out -notmatch 'The signature is timestamped') {
        throw "★ 沒有時戳！$File —— 憑證到期後會變回未簽章，不可放行。"
    }
    Write-Host "   OK：已簽章且含 RFC3161 時戳。" -ForegroundColor Green
}

$targets = @()

if ($Target -in @('content','all')) {
    $targets += $ContentFiles | ForEach-Object { Join-Path $root $_ }
}

if ($Target -in @('installer','all')) {
    if (-not $InstallerGlob) { throw "此專案沒設 InstallerGlob，無安裝檔可簽。" }
    $dir  = Join-Path $root (Split-Path $InstallerGlob -Parent)
    $leaf = Split-Path $InstallerGlob -Leaf
    $setup = Get-ChildItem -LiteralPath $dir -Filter $leaf -File |
             Sort-Object LastWriteTime -Descending
    if (-not $setup) { throw "找不到安裝檔：$InstallerGlob（先編出安裝檔）" }
    if ($setup.Count -gt 1) {
        Write-Host "⚠ 多顆符合，取最新：" -ForegroundColor Yellow
        $setup | ForEach-Object { Write-Host "    $($_.Name)  $($_.LastWriteTime)" }
    }
    Write-Host "   將簽：$($setup[0].FullName)" -ForegroundColor Cyan
    $targets += $setup[0].FullName
}

Write-Host "`n=== 簽章（$Target），共 $($targets.Count) 支 ===" -ForegroundColor Cyan
foreach ($f in $targets) { Invoke-Sign  -File $f }
Write-Host "`n=== 驗證 ===" -ForegroundColor Cyan
foreach ($f in $targets) { Invoke-Verify -File $f }
Write-Host "`n全部完成：$($targets.Count) 支均已簽章且通過時戳驗證。" -ForegroundColor Green
