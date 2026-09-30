# Mroz 教学数据

来源：Stata 官方托管的 Wooldridge 数据，https://www.stata.com/data/jwooldridge/eacsap/mroz.dta 。retrieved_date: 2026-09-30。SHA256 见 `source.json`。

753 名女性的教学数据，非模拟。325 名未就业女性 (`inlf=0`) 的 `wage` 被编码为 0。本章明确限制 `inlf == 1 & !missing(wage, educ)`，保留 428 人；不把零编码当作观测到的小时工资。

原始文件保持不变。`wage` 为美元/小时，`educ` 为受教育年限。样本统计关系不能解释为教育的因果效果。数据版权归原来源，公开教学下载不意味着授予新的许可证。
