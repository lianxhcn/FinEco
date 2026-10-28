# 新电脑环境与任务预检

更新：2026-10-29。S3 环境、S4 代表性案例及 S5 本机提交/推送、Pages 部署和公开页面已验收。日常从 FinEco 主目录使用 `.venv`，不需要迁移目录解释器；下文保留 S3/S4 的历史状态。

## 1. 已核验的本机入口

| 项目 | 路径或版本 | 验证范围 |
|---|---|---|
| 项目 Python | `.venv/Scripts/python.exe`，3.12.16 | 禁用 user site，12 个根模块均从项目 site-packages 导入 |
| 根依赖 | `requirements.txt`，12 项固定版本 | 原文件未改，安装版本全部匹配 |
| 完整依赖锁 | `requirements-lock.txt`，84 个适用包，含 SHA256 | Windows x64 / Python 3.12 解析、安装及逐项核对 |
| 基础 Python | `C:/Users/admin36/miniforge3/envs/py312/python.exe` | 提供标准解释器，没有安装或降级日常环境的包 |
| uv | `C:/Users/admin36/.local/bin/uv.exe`，0.13.6 | 创建、解析、安装与检查；缓存写项目 logs |
| Quarto | `C:/Users/admin36/AppData/Local/Programs/Quarto/bin/quarto.exe`，1.10.19 | S4/S5 的 26 页静态构建通过，不执行代码 |
| Git | `C:/Users/admin36/AppData/Local/Programs/Git/cmd/git.exe`，2.56.0.windows.3 | 路径与版本通过；公开仓库 main 只读查询成功 |
| Stata | `D:/stata19/StataMP-64.exe` | S4 已通过 nbstata 在隔离副本执行 OLS，样本/系数/SE 与代数核对通过 |

本轮只读查询远端 main 为 `b6d0f766e67afaf3a41894ff248e190d6c78763c`，与当时本地 HEAD 一致。没有 fetch、登录检查或推送；公开读取成功不等于写入权限已验证。gh 未在当前常用入口找到，不作为 Python 环境就绪的前提。

`.venv` 仍使用正常安装的基础 Python 标准库，不是脱离操作系统的全打包；它不依赖迁移目录、旧 worktree 或旧聊天。软件路径变化时按实际安装位置调整。

## 2. 每个新终端的启动

在 PowerShell 中执行：

```powershell
Set-Location -LiteralPath 'D:/github_lianxh/FinEco'
. .\tools\Use-FinEcoEnvironment.ps1
```

入口只设置当前进程的 `PYTHON_EXE`、`QUARTO_PYTHON`、`STATA_EXE`、`FINECO_ROOT`、UTF-8 与项目缓存路径，并把项目 Python、Quarto 和 Git 加到当前进程 PATH 前部。不改用户/系统 PATH、注册表、Jupyter 用户内核或 Stata 配置，也不自动运行案例、构建或发布。点号表示在当前终端启用；关闭终端后这些设置结束。

如需环境自检：

```powershell
python -B tools/check_environment.py
```

结果默认写入 `logs/environment/preflight.json`。检查版本、导入来源和路径，不运行课程模型或取数。日常由 Agent 按需调用，教师无需每次手工运行。

软件位置改变时，可向启动脚本传入 `-StataExe`、`-QuartoExe`、`-GitExe`。脚本使用 USERPROFILE 下实际安装位置，不依赖可能被沙箱重定向的 LOCALAPPDATA；先验证程序路径再设置变量，缺项时停止。

## 3. 重建和依赖维护

本项目没有 `.venv` 或需要补齐锁定依赖时执行：

```powershell
powershell -NoProfile -ExecutionPolicy Bypass `
    -File tools/Initialize-FinEcoEnvironment.ps1
```

默认使用本机已核实的 py312 和 uv，可传入 `-BasePython`、`-UvExe`。脚本只在 `.venv` 不存在时创建，已有环境先核对 Python 3.12，再按锁文件安装并检查；不删除环境、不改根版本、不安装到全局。`-Offline` 用于包已就绪或缓存足够时的离线复查；首次安装通常需要 PyPI。

根 `requirements.txt` 维护直接依赖；`requirements-lock.txt` 固定本次解析的传递依赖及分发文件哈希。确需更新依赖时先备份锁文件，按明确任务重新解析并复验，不在日常启动时自动升级。当前生成方式：

```powershell
$finecoUv = Join-Path $env:USERPROFILE '.local/bin/uv.exe'
& $finecoUv --cache-dir logs/environment/uv-cache `
    pip compile requirements.txt --python .venv/Scripts/python.exe `
    --generate-hashes --no-header --no-annotate `
    --output-file requirements-lock.txt
```

该命令用于经授权的依赖维护，不是每次写章的必跑步骤。其他系统或 Python 大版本不能直接视为已验收。CSMAR 的独立章级依赖继续暂缓，不混入根环境；不降级日常分析环境。

`.venv/`、缓存、运行日志和环境报告由 Git 排除。三个环境工具与锁文件进入后续精确候选，不把环境本体或整包执行证据公开。

## 4. 已验证边界

S3 证据位于 `logs/migration-20261028/s3-project-environment-20261028/`：

- 根依赖及 84 个锁定包安装成功，uv 一致性检查通过。
- 全新 Windows PowerShell 5.1 中启动和自检通过；12 个根模块从本项目导入，无迁移路径借包。
- 重建脚本在当前环境 `-Offline` 复查通过。
- 日常 py312 的包版本和原根 requirements 指纹前后保持；文件保全、候选与 Git 检查见 `verification.json`。

本轮未运行 OLS、MC、Bootstrap 或 CSMAR 案例，未启动 Stata 或构建网站。历史 26 页静态构建见 `00-temp-test-2026-10-27/render.log`，不替代 S4。共享环境入口另有 PicGo 与 OLS 副本专项记录，但不能替代当前 FinEco 版本的案例或图床验收。

上述未执行说明是 S3 的历史边界。后续 S4 已使用本项目环境，在副本运行 MC 66 个单元与 OLS/Stata 并核对结果；26 页隔离构建、4,579 项本地引用与七个代表页双视口通过。普通沙箱内核未进入首单元的尝试已终止，授权本地内核环境重试成功，不改全局配置。窄屏共享样式候选已验证，正式源文件/样式/docs 未接回；证据见 `logs/migration-20261028/s4-case-site-validation-20261028/S4_REPORT.md`。CSMAR、Bootstrap 全部重跑及其他全书案例不纳入本次代表性执行范围。

GitHub 写入权限、Pages 部署与公开页面归 S5；需要新图上传时再核验 PicGo。新章设计不等待上述发布环节或 CSMAR 整理。

2026-10-29 S5：本机 Git 初次缺少认证，协调官方浏览器登录后，试运行和普通快进推送均通过；未读取或转存凭据，未安装 gh。`83f2ac9` 与 `d06319c` 已推送；d06319c 的 Pages build/deploy 成功，13 项公开资源 HTTP 200 且与提交字节一致，代表页显示与实际搜索通过。运行、认证、推送和部署均有独立依据，证据位于 `logs/migration-20261028/s5-release-20261029/`。

## 5. 章节任务预检

1. 核对目录、规则、章级范围、Git 修改和共享占用，再启用项目环境。
2. 纯理论设计不重跑全书实验。代码或数值改动后从头执行对应实验，执行与渲染分开记录。
3. 使用冻结数据，不因安装环境刷新快照。CSMAR 由当前 dsed-data 整理，FinEco 相关执行暂缓，未来按确认版本和授权接入。
4. 网页预览使用隔离目录并保持 `execute.enabled: false`。`tools/build_book.ps1` 会覆盖 docs，不用于仅需隔离预览的任务。
5. 内容确认后按文件清单验收和发布。S2 候选是历史快照；本轮新增环境工具和更新文档以 S3 最新候选清单为准。
