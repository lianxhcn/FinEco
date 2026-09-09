# 在项目内保存 Quarto 缓存，避免沙箱访问全局缓存目录。
$ErrorActionPreference = 'Stop'
$bookRoot = Split-Path -Parent $PSScriptRoot
Push-Location $bookRoot
$previousCache = $env:LOCALAPPDATA
try {
    $env:LOCALAPPDATA = Join-Path $bookRoot '002-working/quarto-cache'
    New-Item -ItemType Directory -Force $env:LOCALAPPDATA | Out-Null
    quarto render
    if ($LASTEXITCODE -ne 0) { throw 'Quarto 渲染失败。' }
    New-Item -ItemType File -Force 'docs/.nojekyll' | Out-Null
} finally {
    $env:LOCALAPPDATA = $previousCache
    Pop-Location
}
