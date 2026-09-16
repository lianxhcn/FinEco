# 字段字典与映射

依据：各 ZIP 配套 TXT 和基本信息数据库说明。此处提供字段标签、处理与边界；完整原说明仅保留在受限目录。

| 表 | 原字段 | 标准字段 | 含义 |
|---|---|---|---|
| annual_info | `Symbol` | `stock_code` | 股票代码 |
| annual_info | `ShortName` | `ShortName` | 股票简称 |
| annual_info | `EndDate` | `EndDate` | 统计截止日期 |
| annual_info | `ListedCoID` | `firm_id` | 上市公司ID |
| annual_info | `SecurityID` | `security_id` | 证券ID |
| annual_info | `IndustryName` | `industry_name` | 行业名称 |
| annual_info | `IndustryCode` | `industry_code` | 行业代码 |
| annual_info | `Crcd` | `Crcd` | ABH股交叉码 |
| annual_info | `LISTINGDATE` | `listing_date` | 首次上市日期 |
| annual_info | `PROVINCECODE` | `PROVINCECODE` | 所属省份代码 |
| annual_info | `PROVINCE` | `PROVINCE` | 所属省份 |
| annual_info | `CITYCODE` | `CITYCODE` | 所属城市代码 |
| annual_info | `CITY` | `CITY` | 所属城市 |
| annual_info | `LISTINGSTATE` | `listing_state_source` | 上市状态 |
| ownership | `Symbol` | `stock_code` | 证券代码 |
| ownership | `ShortName` | `ShortName` | 证券简称 |
| ownership | `EndDate` | `EndDate` | 截止日期 |
| ownership | `LargestHolder` | `LargestHolder` | 第一大控股股东 |
| ownership | `LargestHolderRate` | `top1_ownership_pct` | 第一大股东持股比率(%) |
| ownership | `TopTenHoldersRate` | `TopTenHoldersRate` | 前十大股东持股比例(%) |
| ownership | `ActualControllerName` | `ultimate_controller` | 实际控制人名称 |
| ownership | `ActualControllerNatureID` | `ActualControllerNatureID` | 实际控制人性质编码 |
| ownership | `EquityNature` | `ownership_nature` | 股权性质 |
| ownership | `EquityNatureID` | `ownership_code` | 股权性质编码 |
| ownership | `Hierarchy` | `Hierarchy` | 层级判断 |
| ownership | `Seperation` | `Seperation` | 两权分离率(%) |
| company | `Stkcd` | `stock_code` | 证券代码 |
| company | `Stknme` | `Stknme` | 证券简称 |
| company | `ListedDate` | `listing_date_company` | 上市日期 |
| company | `Regcap` | `Regcap` | 注册资本 |
| company | `EstablishDate` | `EstablishDate` | 成立日期 |
| company | `DelistedDate` | `delisting_date` | 退市日期 |
| income | `Stkcd` | `stock_code` | 证券代码 |
| income | `ShortName` | `ShortName` | 证券简称 |
| income | `Accper` | `Accper` | 统计截止日期 |
| income | `Typrep` | `Typrep` | 报表类型 |
| income | `B001101000` | `revenue` | 营业收入 |
| income | `Bbd1102203` | `Bbd1102203` | 利息支出 |
| income | `B001201000` | `B001201000` | 营业成本 |
| income | `B001209000` | `B001209000` | 销售费用 |
| income | `B001210000` | `B001210000` | 管理费用 |
| income | `B001216000` | `rd_expense` | 研发费用 |
| income | `B001211000` | `B001211000` | 财务费用 |
| income | `B001300000` | `operating_profit` | 营业利润 |
| income | `B001000000` | `total_profit` | 利润总额 |
| income | `B002000000` | `net_income` | 净利润 |
| income | `B002000101` | `parent_net_income` | 归属于母公司所有者的净利润 |
| shareholders | `Stkcd` | `stock_code` | 证券代码 |
| shareholders | `Reptdt` | `Reptdt` | 统计截止日期 |
| shareholders | `S0101b` | `S0101b` | 股东名称 |
| shareholders | `S0501b` | `holder_rank` | 持股排名 |
| shareholders | `S0201b` | `shares_held` | 持股数量 |
| shareholders | `S0301b` | `top_holder_pct` | 持股比例(%) |
| shareholders | `S0401b` | `S0401b` | 股份性质 |
| disclosure | `Stkcd` | `stock_code` | 证券代码 |
| disclosure | `Stknme` | `Stknme` | 证券简称 |
| disclosure | `Accper` | `Accper` | 统计截止日期 |
| disclosure | `Firforecdt` | `predisclosure_date` | 首次预约日 |
| disclosure | `Actudt` | `actual_announcement_date` | 实际披露日 |
| market | `Stkcd` | `stock_code` | 证券代码 |
| market | `Trdynt` | `Trdynt` | 交易年份 |
| market | `Yclsprc` | `Yclsprc` | 年收盘价 |
| market | `Ysmvosd` | `Ysmvosd` | 年个股流通市值 |
| market | `Ysmvttl` | `market_value_thousand` | 年个股总市值 |
| market | `Yretwd` | `annual_stock_return` | 考虑现金红利再投资的年个股回报率 |
| market | `Yarkettype` | `market_type` | 市场类型 |
| governance | `Stkcd` | `stock_code` | 证券代码 |
| governance | `Reptdt` | `Reptdt` | 统计截止日期 |
| governance | `Y0501b` | `Y0501b` | 前十大股东是否存在关联 |
| governance | `Y0601b` | `employees` | 员工人数 |
| governance | `ChairmanHoldsharesRatio` | `ChairmanHoldsharesRatio` | 董事长持股比例 |
| governance | `ManagerHoldsharesRatio` | `ManagerHoldsharesRatio` | 总经理持股比例 |
| governance | `Y1001b` | `chair_ceo_code` | 董事长与总经理兼任情况 |
| cashflow | `Stkcd` | `stock_code` | 证券代码 |
| cashflow | `ShortName` | `ShortName` | 证券简称 |
| cashflow | `Accper` | `Accper` | 统计截止日期 |
| cashflow | `Typrep` | `Typrep` | 报表类型 |
| cashflow | `C001000000` | `operating_cash_flow` | 经营活动产生的现金流量净额 |
| cashflow | `C002006000` | `C002006000` | 购建固定资产、无形资产和其他长期资产支付的现金 |
| cashflow | `C002000000` | `investing_cash_flow` | 投资活动产生的现金流量净额 |
| cashflow | `C003000000` | `financing_cash_flow` | 筹资活动产生的现金流量净额 |
| cashflow | `C006000000` | `C006000000` | 期末现金及现金等价物余额 |
| balance | `Stkcd` | `stock_code` | 证券代码 |
| balance | `ShortName` | `ShortName` | 证券简称 |
| balance | `Accper` | `Accper` | 统计截止日期 |
| balance | `Typrep` | `Typrep` | 报表类型 |
| balance | `A001101000` | `cash` | 货币资金 |
| balance | `A001111000` | `A001111000` | 应收账款净额 |
| balance | `A001123000` | `inventory` | 存货净额 |
| balance | `A001100000` | `current_assets` | 流动资产合计 |
| balance | `A001212000` | `fixed_assets` | 固定资产净额 |
| balance | `A001218000` | `A001218000` | 无形资产净额 |
| balance | `A001200000` | `A001200000` | 非流动资产合计 |
| balance | `A001000000` | `total_assets` | 资产总计 |
| balance | `A002101000` | `A002101000` | 短期借款 |
| balance | `A002107000` | `A002107000` | 应付票据 |
| balance | `A002108000` | `A002108000` | 应付账款 |
| balance | `A002114000` | `A002114000` | 应付利息 |
| balance | `A002100000` | `current_liabilities` | 流动负债合计 |
| balance | `A002201000` | `A002201000` | 长期借款 |
| balance | `A002000000` | `total_liabilities` | 负债合计 |
| balance | `A003101000` | `A003101000` | 实收资本(或股本) |
| balance | `A003100000` | `parent_equity` | 归属于母公司所有者权益合计 |
| balance | `A003000000` | `total_equity` | 所有者权益合计 |

## 日期、单位和派生列

- `report_date` 从 Accper/EndDate/Reptdt 解析；年度层使用年末日期，不表示公告日期。`fiscal_year` 为该日期年份，市场表来自 Trdynt。
- `firm_id` 来自 ListedCoID。未把证券代码重命名为公司 ID；证券代码变更须另行审计。
- `actual_announcement_date` 来自 Actudt；`predisclosure_date` 来自 Firforecdt。无效或空日期不相互填补。
- 财务金额使用原始数值尺度。TXT 未提供足够的币种/单位证据，金额不声明为元；跨表 ROA/ROE 待确认。
- `market_value_thousand` 在已确认 A 股市场使用人民币千元，`market_value = market_value_thousand * 1000`。
- `annual_stock_return` 为考虑现金红利再投资的年回报率，按源值保留小数，不与未复权价格涨幅混用。
- `top1_pct` 来自股东排名为 1 的 S0301b，单位为百分数；`top1 = top1_pct / 100`。`shares_held` 为该股东股数。
- `top1_ownership_pct` 为股权性质表 LargestHolderRate。治理综合表本次未导出 Top1 字段，因此交叉核验对象为股权性质表。
- `_parent_statement` 后缀表示 Typrep=B；无此后缀的财务金额来自 Typrep=A。归母权益/利润仍属于合并报表内部归属口径。
- `_lag` 按证券代码匹配精确 t−1 年；`_avg` 为 (本年值 + 上年值)/2。公司代码迁移尚未裁定，不能跨代码拼接分母。
- Leverage=负债/资产；ROA=净利润/期末或平均资产；ROE=净利润/期末或平均总权益。归母 ROE 用归母净利润和归母权益匹配。
- 比率均为小数，0.05 表示 5%；零分母置为缺失，负分母保留。`roa_parent_income_*_candidate` 是另列候选，不能视作统一标准。
- `financial_industry` 按本年行业 J 前缀诊断；`industry_standard` 标明 2023 年分类体系切换。行业缺失不前填。
- `st_source`、`pt_source` 仅反映源状态标签，不表示完整年内历史；`soe` 仅映射单一性质码，复合码为缺失。
- `has_*` 记录该来源是否存在对应行；字段本身仍可能缺失。`firm_year_conflict` 与 `listing_date_conflict` 提醒人工核查。
- `eligible_known` 是候选规则：存在 A 股身份和上市日期证据、非已知上市前或退市后。不是对总体完备性和上市日期冲突的背书。
