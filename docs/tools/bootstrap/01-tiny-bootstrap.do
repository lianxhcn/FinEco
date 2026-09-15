version 17.0
clear all
set more off

* 从 FinEco 项目根目录运行；本文件演示与讲义相同的五个数。
* 已在本地 Stata 19.5 执行；Python 穷举结果作为独立数值基准。
input double x
2
4
5
7
12
end

quietly summarize x
scalar original_mean = r(mean)
scalar analytical_se = r(sd)/sqrt(r(N))
display "Original mean = " original_mean
display "Analytical SE estimate = " analytical_se

* 每次有放回抽取五行，重新计算均值；不需要在程序内再次 bsample。
bootstrap mean=r(mean), reps(9999) seed(12345): ///
    summarize x
estat bootstrap, percentile normal

* Python 穷举基准：均值 6；Bootstrap SE 1.5231546212；百分位数区间 [3.4, 9.2]。
* 这里有限次模拟与精确基准无需逐位相同。
* 输出中的 normal-based z/p 不是讲义第 4 节构造的右尾 Bootstrap p 值。
