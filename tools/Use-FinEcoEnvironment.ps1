# 在当前 PowerShell 进程启用 FinEco 环境；不运行案例或修改系统设置。
# 用法：. .\tools\Use-FinEcoEnvironment.ps1
[CmdletBinding()]
param(
    [string]$StataExe = 'D:/stata19/StataMP-64.exe',
    [string]$QuartoExe = (
        Join-Path $env:USERPROFILE 'AppData/Local/Programs/Quarto/bin/quarto.exe'
    ),
    [string]$GitExe = (
        Join-Path $env:USERPROFILE 'AppData/Local/Programs/Git/cmd/git.exe'
    )
)

$finecoRoot = Split-Path -Parent $PSScriptRoot
$finecoPython = Join-Path $finecoRoot '.venv/Scripts/python.exe'

# 先核对完整范围，缺少软件时不留下半套环境变量。
foreach ($finecoTool in @($finecoPython, $StataExe, $QuartoExe, $GitExe)) {
    if (-not (Test-Path -LiteralPath $finecoTool -PathType Leaf)) {
        throw "找不到程序：$finecoTool。请按环境说明创建 .venv 或传入实际路径。"
    }
}

$env:PYTHON_EXE = $finecoPython
$env:QUARTO_PYTHON = $finecoPython
$env:STATA_EXE = (Resolve-Path -LiteralPath $StataExe).Path
$env:FINECO_ROOT = $finecoRoot
$env:VIRTUAL_ENV = Join-Path $finecoRoot '.venv'
$env:PYTHONUTF8 = '1'
$env:PYTHONIOENCODING = 'utf-8'
$env:PYTHONNOUSERSITE = '1'
$env:PYTHONDONTWRITEBYTECODE = '1'
$env:MPLCONFIGDIR = Join-Path $finecoRoot 'logs/environment/matplotlib'
$env:IPYTHONDIR = Join-Path $finecoRoot 'logs/environment/ipython'
$env:JUPYTER_RUNTIME_DIR = Join-Path $finecoRoot 'logs/environment/jupyter-runtime'
$env:JUPYTER_CONFIG_DIR = Join-Path $finecoRoot 'logs/environment/jupyter-config'

# 仅当前进程的 PATH；重复启用不会累积重复目录。
$finecoBins = @(
    (Split-Path -Parent $finecoPython),
    (Split-Path -Parent $QuartoExe),
    (Split-Path -Parent $GitExe)
)
$finecoOldBins = @($env:PATH -split ';' | Where-Object {
    $_ -and $_ -notin $finecoBins
})
$env:PATH = (@($finecoBins) + @($finecoOldBins)) -join ';'

Write-Host "FinEco Python: $finecoPython"
Write-Host "Stata: $env:STATA_EXE"
Write-Host '仅当前终端生效；未执行 Notebook、Stata、构建或发布。'
