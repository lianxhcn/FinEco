# Monte Carlo 案例数据

- `adjusted_prices.csv`: 投资组合案例最终股票池的后复权价格教学数据。
- `returns.csv`: 共同有效交易日的日收益数据。
- `stock_pool.csv`: 最终股票池与行业信息。
- `portfolio-results/portfolio_weights.csv`: 五只股票的等权与固定市值权重。
- `portfolio-results/` 的其余文件保留单日风险分析与补充诊断的已保存结果。统一 Notebook 的最新输出另存于 `output/monte-carlo/cases/`。

企业估值、OLS/IV、Brownian/GBM 案例使用模拟数据，不依赖外部数据文件。

数据通过 AKShare 获取，抓取日期为 2026-10-01。五只股票的共同有效日收益样本为 2016-09-05 至 2026-09-30，共 2397 日。收益先在完整日期轴上计算，再保留五股均有效的日期，不填补缺失值。

克隆仓库后，统一 Notebook 直接读取以上处理后文件，无需联网取数或访问供应商缓存。后复权价格用于教学性的收益与风险比较，固定市值权重取自样本末日，不代表无前视信息的历史投资策略。接口、处理规则与适用范围见[数据说明](../../resources/monte-carlo/portfolio-report.md)。供应商原始缓存不作为学生运行依赖，也不随网站提供。
