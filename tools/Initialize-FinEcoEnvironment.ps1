# 按项目锁定清单创建/补齐 .venv；不修改根依赖，不移动旧环境。
[CmdletBinding()]
param(
    [string]$BasePython = (
        Join-Path $env:USERPROFILE 'miniforge3/envs/py312/python.exe'
    ),
    [string]$UvExe = (
        Join-Path $env:USERPROFILE '.local/bin/uv.exe'
    ),
    [switch]$Offline
)

$ErrorActionPreference = 'Stop'
$finecoRoot = Split-Path -Parent $PSScriptRoot
$finecoVenv = Join-Path $finecoRoot '.venv'
$finecoPython = Join-Path $finecoVenv 'Scripts/python.exe'
$finecoLock = Join-Path $finecoRoot 'requirements-lock.txt'
$finecoCache = Join-Path $finecoRoot 'logs/environment/uv-cache'

foreach ($finecoFile in @($BasePython, $UvExe, $finecoLock)) {
    if (-not (Test-Path -LiteralPath $finecoFile -PathType Leaf)) {
        throw "找不到环境依赖入口：$finecoFile"
    }
}

if (-not (Test-Path -LiteralPath $finecoVenv)) {
    & $UvExe --cache-dir $finecoCache venv `
        --python $BasePython --no-managed-python --no-python-downloads `
        $finecoVenv
    if ($LASTEXITCODE -ne 0) { throw '创建 .venv 失败，保留日志与已有文件。' }
} elseif (-not (Test-Path -LiteralPath (Join-Path $finecoVenv 'pyvenv.cfg'))) {
    throw '.venv 已存在但不是已识别的虚拟环境；停止，不覆盖目录。'
}

$finecoVersion = & $finecoPython -I -c `
    'import sys; print(str(sys.version_info.major)+chr(46)+str(sys.version_info.minor))'
if ($LASTEXITCODE -ne 0 -or $finecoVersion -ne '3.12') {
    throw '此锁定清单按 Python 3.12 验收；当前解释器不匹配，未安装依赖。'
}

$finecoArgs = @(
    '--cache-dir', $finecoCache,
    'pip', 'install', '--python', $finecoPython,
    '--require-hashes', '--link-mode', 'copy', '-r', $finecoLock
)
if ($Offline) { $finecoArgs += '--offline' }
& $UvExe @finecoArgs
if ($LASTEXITCODE -ne 0) { throw '依赖安装失败；不改全局环境或锁定版本。' }

& $UvExe --cache-dir $finecoCache pip check --python $finecoPython
if ($LASTEXITCODE -ne 0) { throw '依赖一致性检查失败。' }
Write-Host 'FinEco .venv 已就绪；本脚本未运行课程案例或构建网站。'
