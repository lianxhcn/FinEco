# 从复现代码提取数据规则

案例：Chen and Zimmermann (2022)，*Open Source Cross-Sectional Asset Pricing*。retrieved_date: 2026-09-16。仅阅读公开代码，不运行 WRDS 数据流程。

## 1. 已核验的来源

- [论文 DOI](https://doi.org/10.1561/104.00000112)：2022，Critical Finance Review，11(2)，207–264。
- [项目 README](https://github.com/OpenSourceAP/CrossSection/)：区分信号构造、组合和发布模块。
- [AssetGrowth.py](https://github.com/OpenSourceAP/CrossSection/blob/master/Signals/pyCode/Predictors/AssetGrowth.py)：资产增长信号。
- [CompustatAnnual.py](https://github.com/OpenSourceAP/CrossSection/blob/master/Signals/pyCode/DataDownloads/CompustatAnnual.py)：年度输入与连接、月度展开。

这是当前仓库的局部代码阅读，未锁定发表时版本。未将本次读取结果冒充已经复现论文。

## 2. 课堂规则提取表

| 项目 | 已找到的规则或下一步 |
|---|---|
| Population | 论文涉及横截面股票信号；精确全体证券范围需查组合与主表模块，pending |
| Sample | 本段年度代码选择合并、标准格式、USD 和 INDL 等条件 |
| Data source | Compustat 年度数据和 CRSP–Compustat 历史连接，经 WRDS |
| Unit | 年度财务输入，展开为月度信号输入 |
| Key | 公司键与证券键分开；连接有效期不可省略 |
| Variable definitions | 资产增长使用本期与 12 行前资产之差除以后者 |
| Exclusions | 年度流程要求资产、价格、净利润非缺失 |
| Missing-value rules | 指定字段有填零处理，不能移植为所有字段通用规则 |
| Outlier rules | 未在所读 AssetGrowth 片段确认完整缩尾规则，pending |
| Merge rules | 使用历史连接的类型、优先级和有效期 |
| Timing | 年度信息作六个月滞后，再展开月度；不等于每家公司实际公告日 |
| Final sample | 未执行整套包，最终样本数 unknown |

## 3. 学生应做出的判断

同一段 shift 代码在规则完整的月度表和有断档的年度表上含义不同。阅读者应追查上游日期结构，而不是只复制公式。缺失处理、滞后、键冲突处理也应追查依据；公开代码仍需要审计。

课程只用这一局部案例练习读规则。若将其作为正式论文复现，应另行固定版本、核查全部上游模块、数据权限与运行结果。
