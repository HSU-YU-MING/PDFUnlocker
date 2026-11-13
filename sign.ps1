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
# 憑證指紋、signtool 路徑、時戳伺服器:五個 App 共用,收在 D:\應用程式\codesign.psd1 一份。
# ⚠ 不要在這裡寫回實際的指紋。以前這三行在五份 sign.ps1 裡各寫一次(加上 Kindling\docs\
#   兩份文件共七處),而憑證 2027/10/25 到期 —— 換證時漏掉一處,那個 App 就在發版當下簽不出來。
# 往上找而不是寫死相對路徑:五支腳本在不同深度(有的在專案根、有的在 專案\專案\)。
$cfgDir = $PSScriptRoot
while ($cfgDir -and -not (Test-Path -LiteralPath (Join-Path $cfgDir 'codesign.psd1'))) {
    $cfgDir = Split-Path $cfgDir -Parent
}
if (-not $cfgDir) {
    throw "找不到 codesign.psd1(應在 D:\應用程式\)——簽章設定的單一真相源不見了,不要改用寫死的指紋。"
}
$CodeSign = Import-PowerShellDataFile -LiteralPath (Join-Path $cfgDir 'codesign.psd1')
$SignTool = $CodeSign.SignTool
$Thumb    = $CodeSign.Thumbprint
$TsUrl    = $CodeSign.TimestampUrl

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
