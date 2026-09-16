# 金融数据章：学生数据与运行说明

本目录只保存来源、规则、字段映射与汇总，不包含 CSMAR ZIP、解压记录或公司级派生数据。教师提供的坚果云下载入口、校验值和解压说明见 [CSMAR 数据获取](DATA_ACCESS.md)。源文件标注仅供中山大学使用，请在已有授权范围内使用，勿将原始记录或完整派生数据上传个人公共仓库。

四章单元依次为流程与获取、数据管理、清洗与审计、CSMAR 实战。学生可 clone `https://github.com/lianxhcn/FinEco.git` 后运行；已有教师仓库副本时，先保存自己的修改，再更新仓库。`financial-data-source.ipynb` 是供网页下载的执行副本，由汇总发布脚本生成，不单独编辑。

独立学生项目的规则模板、项目计划、决策记录模板和 P00–P07 提示词位于 [agent-project/](agent-project/PROMPTS.md)。模板不覆盖课程仓库根规则。没有 CSMAR 数据时，可独立运行 `tools/financial-data/teaching_examples.py` 学习前三章的小表操作。

## 1. 准备目录

将教师提供的原始 ZIP 放入本地授权目录的 `raw-zip/`。保留原文件名、TXT 字段说明和版权文件，不把原始数据上传个人公共仓库。使用外部授权目录时，自行确保该目录不被云盘公开同步或 Git 跟踪。

```text
授权数据根目录/
  raw-zip/                  原始 ZIP，只读
  financial-data-v2/
    raw-extracted/          原样解压，按数据集分目录
    runs/运行时间戳/
      interim/              全行标准化 Parquet
      processed/            支持层、候选年度表与受限待审行
      audit/                本次运行汇总与元数据
```

## 2. 运行实验

在 PowerShell 中设置本次会话的数据位置，示例路径请换成自己的授权目录：

```powershell
$env:FINECO_CSMAR_ROOT = 'D:/course-private/csmar'
& $env:PYTHON_EXE 'tools/financial-data/run_notebook.py'
```

也可以从 Jupyter 打开 `notebooks/financial-data/financial-data.ipynb`，使用已安装所需依赖的 Python 内核，Restart Kernel 后 Run All。环境变量应在启动 Jupyter 前设置。完整运行不访问实时 API。

先运行小型验证：

```powershell
& $env:PYTHON_EXE 'tools/financial-data/test_pipeline.py'
```

只运行数据流水线时使用 `tools/financial-data/pipeline.py`。依赖列表和教师已测试版本见 `tools/financial-data/requirements-chapter.txt`。本章未修改课程公共依赖。

## 3. 怎样判断运行成功

Notebook 全部代码单元格有执行编号且没有报错；本地生成新的 runs 子目录；`audit/summary.json` 和各汇总表存在。随后阅读 [审计报告](AUDIT_REPORT.md) 和 [数据缺口](DATA_GAPS.md)。程序完成与研究库验收是两件事。

现有 `master_2015_2025.parquet` 是历史兼容的程序文件名，实际状态是**按证券年度键组织的候选视图**，存在公司身份及上市日期待审事项。不要把它直接当作最终 firm-year 数据。

## 4. 常见问题

- 找不到 raw-zip：检查环境变量是否指向 ZIP 的上一级目录；不要指向单个 ZIP。
- 缺少 pyarrow：使用教师说明的课程环境；本章不会自动修改全局 Python。
- 键不唯一而停止：查看重复组含义，不使用 `drop_duplicates` 绕过验证。
- ZIP 数量或字段改变：输入版本已改变，先更新来源审计，再修改映射。
- Notebook 输出较旧：代码改变后重新 Run All；网页渲染不会执行代码。

提交作业只提交自己的代码、说明和审计汇总，不提交原始记录、完整 master 或真实公司行的 Notebook 输出。清除输出本身也不等于移除了已进入 Git 历史的数据，因此应在提交前检查。
