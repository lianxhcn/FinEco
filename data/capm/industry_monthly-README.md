# 行业月收益

固定文件：`industry_monthly.dta`。真实金融数据，一行对应一个月，共 432 行；1990 年 1 月至 2025 年 12 月连续，无重复月份和缺失值。用途是本章的市场回归、行业比较、固定权重组合和滚动 β 演示。

## 来源与冻结

来源为 [Kenneth R. French Data Library](https://mba.tuck.dartmouth.edu/pages/faculty/ken.french/data_library.html) 的 [10 Industry Portfolios](https://mba.tuck.dartmouth.edu/pages/faculty/ken.french/Data_Library/det_10_ind_port.html) 和 [Fama/French 因子](https://mba.tuck.dartmouth.edu/pages/faculty/ken.french/Data_Library/f-f_factors.html)。2026-10-29 下载，文件头记录 CRSP 数据库版本为 202609。行业文件选取第一个 Average Value Weighted Returns — Monthly 区块，含股息，保留十行业；与同源因子的 Mkt-RF、RF 按月份内连接，截取上述固定期间。

本次更名逐字节复制已经执行核验的 `monthly.dta`，没有重新下载、筛选、改变数值或填补缺失。旧名和原 CSV 的私有备份在本轮返修目录。来源记录及文件指纹见 `industry_monthly-source.json`；两份教学输入的统一清单为 `source.json`。

## 变量与单位

| 变量 | 含义 |
|---|---|
| month | 年月字符串，例如 1990-01 |
| mdate | Stata 月日期，1960 年 1 月为零，显示格式为 %tm |
| mktrf | 美国市场代理的月超额收益，已扣 RF |
| rf | 同月无风险收益 |
| nodur | 非耐用消费品行业组合收益 |
| durbl | 耐用消费品行业组合收益 |
| manuf | 制造业组合收益 |
| enrgy | 能源行业组合收益 |
| hitec | 高科技行业组合收益 |
| telcm | 电信行业组合收益 |
| shops | 商业及服务行业组合收益 |
| hlth | 医疗保健行业组合收益 |
| utils | 公用事业行业组合收益 |
| other | 其他行业组合收益 |

所有收益均以**每月百分数**存储，数值 1 表示月收益 1%，不是小数 0.01。行业收益尚未扣 RF；构造超额收益时减同月 rf 一次。mktrf 不再扣 rf。β 无单位，α 的单位为每月百分数。行业范围按来源 SIC 规则定义，不是代表个股，也不是首讲的 A 股篮子或 CSMAR。

## 调用

从 FinEco 根目录：

```stata
use data/capm/industry_monthly.dta, clear
format mdate %tm
tsset mdate, monthly
generate double ex_hitec = hitec - rf
regress ex_hitec mktrf
```

分析、网页渲染和课堂演示均只读，不联网取数。需重新取得来源时，显式使用来源获取工具；`prepare_data.py` 生成新的行业输入及单独来源记录，已有文件存在时拒绝覆盖。更新版本后重新核验统一指纹清单与全部结果。

## 解释与权利边界

来源会修订历史数据。2025 年起供应商使用 CRSP CIZ 格式生成研究收益；RF 从 2024 年 6 月起改用 ICE BofA US 1-Month Treasury Bill Index，之前为 Ibbotson 来源。本文件是下载时的历史版本，没有重建每个历史时点的信息集，不能据此声称投资策略没有前视偏误。

第三方数据保留来源权利，本章不另授开放数据许可。公开再分发或出版前核验原来源使用条件。来源 ZIP 和取得记录私有保存在 logs/capm/sources，正常执行不依赖这些原始下载。
