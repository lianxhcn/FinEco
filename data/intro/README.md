# 第一讲数据说明

- 行情来源：Tencent Finance，经 AKShare stock_zh_a_hist_tx 获取。
- 抓取日期和接口版本：见 source-manifest.json。
- 窗口：2018-01-01 至 2025-12-31，后复权价格 (hfq)。
- 固定教学股票篮子为事后选定，不是历史选股策略，不能消除幸存者偏差。
- 每个股票 CSV 保留接口原始输出字段；prices-long.csv 只取 date、symbol、name、close。close 为后复权收盘价，不能直接用于按历史真实价格撮合交易；本实验不使用 amount 列，未为其另作成交量/金额解释。
- 训练期：2018—2023；验证：2024；测试：2025。采用共同有效收益日期，不对缺失数据自动填充。
- portfolio-results.csv 和 portfolio-weights.csv 来自运行后的 Python Notebook；policy-means.csv 来自运行后的 Stata 模拟。
- 交易成本为单边成交额的 10 个基点教学设定，无风险利率为年有效 2% 的教学假设。连续权重忽略整数股、滑点和交易受限。
- 行情为第三方数据，不声明本课程拥有其版权或另授开放许可；进一步再分发应核查原来源条件。此目录不含 CSMAR、私人账户或个人交易记录。
- 政策模拟为 40 城市、800 企业、10 年，参数与随机种子在 Stata Notebook 中公开；不能用于报告真实政策效果。
