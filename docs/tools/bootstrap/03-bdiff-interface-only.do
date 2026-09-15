version 17.0
clear all
set more off

* 仅为命令接口与版本核对示例，不用于本讲模拟数据的主要推断。
* 系数相等并不推出完整记录可交换；本例两组 X 分布和误差尺度不同。
import delimited "data/bootstrap/two_groups_teaching.csv", clear
drop if missing(invest, cash, group)
cap which bdiff
if _rc ssc install bdiff
which bdiff
* 如需检查原文件，请单独执行：viewsource bdiff.ado

* 用 499 次避免把接口展示当成高精度尾概率分析。
* 1.04 存档代码中，默认随机重新分组；其输出较小尾部比例不是通常双侧 p 值。
bdiff, group(group) model(regress invest cash) ///
    reps(499) seed(12345)
