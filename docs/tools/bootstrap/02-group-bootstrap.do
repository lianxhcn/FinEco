version 17.0
clear all
set more off

* 在 FinEco 项目根目录运行。数据为教学模拟，不是真实企业实证数据。
import delimited "data/bootstrap/two_groups_teaching.csv", clear
assert inlist(group, 0, 1)
drop if missing(invest, cash, group)

capture program drop slope_diff
program define slope_diff, rclass
    tempname b0
    quietly regress invest cash if group == 0
    scalar `b0' = _b[cash]
    quietly regress invest cash if group == 1
    return scalar delta = scalar(`b0') - _b[cash]
    * 清除最后一组回归的 e(sample)，保留两组作为重抽样母样本。
    ereturn clear
end

* 先独立核对点估计；每次统计量是第 0 组减第 1 组。
quietly slope_diff
assert abs(r(delta) - (-0.3526753172950964)) < 1e-8
display "Observed slope difference = " r(delta)

* strata(group) 表示各组内部独立抽样，组别和组规模保持不变。
* 包含截距的一元回归；抽样单位为完整的企业记录。
bootstrap delta=r(delta), strata(group) ///
    reps(9999) seed(12345): slope_diff
estat bootstrap, percentile normal

* Python 9999 次模拟基准：SE = 0.1340657447，百分位数区间约 [-0.6144, -0.0905]。
* 不同软件的随机数与分位数实现不同，不断言模拟数值逐位一致。
* 不允许将此程序换成 bdiff, bsample，二者并非同一重抽样设计。
