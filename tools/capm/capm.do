* CAPM 月度收益分析  来源与口径见 data/capm/source.json
* SECTION setup
version 19
clear all
set more off
set linesize 76
capture mkdir logs/capm
capture mkdir figs/raw
local root : environment FINECO_ROOT
if "`root'" != "" {
    cd "`root'"
}
local stamp : environment CAPM_RUN_STAMP
if "`stamp'" == "" {
    display as error "请从本章运行器启动以设置图片时间戳"
    exit 198
}
global CAPM_STAMP "`stamp'"
set scheme s2color
use data/capm/industry_monthly.dta, clear
format mdate %tm
tsset mdate, monthly
assert _N == 432
assert mdate == tm(1990m1) + _n - 1
* 前六行保留原始行业收益  mktrf 已扣 rf
list mdate hitec utils mktrf rf in 1/6, noobs
foreach a in nodur durbl manuf enrgy hitec telcm shops hlth utils other {
    generate double ex_`a' = `a' - rf
}
summarize mktrf rf ex_hitec ex_utils

* SECTION estimates
* 相同样本比较三种方差估计  点估计必须相同
* V 是两种超额收益的样本协方差矩阵  不是 e(V)
correlate ex_hitec mktrf, covariance
matrix V = r(C)
matrix list V
display "beta = " %7.3f (V[1,2] / V[2,2])
regress ex_hitec mktrf
estimates store conventional
regress ex_hitec mktrf, vce(robust)
estimates store robust
newey ex_hitec mktrf, lag(6)
estimates store hac6
estimates table conventional robust hac6, ///
    b(%9.4f) se(%9.4f) stats(N)
test _cons = 0
test mktrf = 1

* SECTION result_tables
* 外部命令只整理结果  标准误口径仍由 newey 决定
which esttab
quietly newey ex_hitec mktrf, lag(6)
estimates store capm_hitec
quietly newey ex_utils mktrf, lag(6)
estimates store capm_utils
esttab capm_hitec capm_utils, b(3) se(3) nostar
esttab capm_hitec capm_utils, b(3) ci(3) level(95) nostar
esttab capm_hitec capm_utils using "logs/capm/regression.rtf", ///
    replace b(3) se(3) nostar

* SECTION industries
* 循环不改变数据  每个行业均使用同一 432 个月
capture postclose capm_results
postfile capm_results str8 industry double mean double sd ///
    double alpha double beta double se_alpha double se_beta ///
    double alpha_lo double alpha_hi double beta_lo double beta_hi ///
    double p_alpha double p_beta1 double r2 int n ///
    using logs/capm/estimates.dta, replace
foreach a in nodur durbl manuf enrgy hitec telcm shops hlth utils other {
    quietly summarize `a'
    scalar mean_r = r(mean)
    scalar sd_r = r(sd)
    quietly regress ex_`a' mktrf
    scalar fit_r2 = e(r2)
    quietly newey ex_`a' mktrf, lag(6)
    scalar a0 = _b[_cons]
    scalar b0 = _b[mktrf]
    scalar sa = _se[_cons]
    scalar sb = _se[mktrf]
    scalar cv = invttail(e(df_r), .025)
    scalar pa = 2 * ttail(e(df_r), abs(a0 / sa))
    scalar pb = 2 * ttail(e(df_r), abs((b0 - 1) / sb))
    post capm_results ("`a'") (mean_r) (sd_r) (a0) (b0) ///
        (sa) (sb) (a0-cv*sa) (a0+cv*sa) ///
        (b0-cv*sb) (b0+cv*sb) (pa) (pb) (fit_r2) (e(N))
}
postclose capm_results
preserve
use logs/capm/estimates.dta, clear
format mean sd alpha beta se_* %9.4f
list industry mean sd alpha beta se_beta p_alpha r2, noobs
export delimited using logs/capm/estimates.csv, replace
generate row = _n
twoway (rcap beta_lo beta_hi row, horizontal lcolor(navy)) ///
    (scatter row beta, mcolor(navy) msymbol(Oh)), ///
    ylabel(1 "NoDur" 2 "Durbl" 3 "Manuf" 4 "Enrgy" ///
    5 "HiTec" 6 "Telcm" 7 "Shops" 8 "Hlth" ///
    9 "Utils" 10 "Other", angle(0) labsize(medium)) ///
    xlabel(0(.5)1.5, labsize(medium)) ///
    yscale(reverse) ytitle("") xtitle("Market beta") ///
    xline(1, lpattern(dash) lcolor(gs8)) legend(off) ///
    graphregion(color(white)) xsize(6.4) ysize(4.5) ///
    name(betas, replace)
graph export "figs/raw/capm-fig02-betas-${CAPM_STAMP}.png", ///
    replace width(2400)
graph export "figs/raw/capm-fig02-betas-${CAPM_STAMP}.svg", ///
    replace fontface("Times New Roman")
graph export "figs/raw/capm-fig02-betas-${CAPM_STAMP}.pdf", ///
    replace fontface("Times New Roman")
restore

* SECTION market_graph
* 两个面板的横纵坐标范围一致  便于比较斜率和离散程度
twoway (scatter ex_hitec mktrf, msymbol(Oh) msize(small) ///
    mlcolor(navy%60) mfcolor(none)) ///
    (lfit ex_hitec mktrf, lcolor(navy)), ///
    title("(a) HiTec", size(medium)) ///
    xtitle("Market excess return (%)") ///
    ytitle("Industry excess return (%)") ///
    xlabel(-20(10)20) ylabel(-40(20)40, angle(0)) ///
    aspectratio(1) legend(off) ///
    graphregion(color(white)) name(hitec, replace)
twoway (scatter ex_utils mktrf, msymbol(Oh) msize(small) ///
    mlcolor(dkorange%60) mfcolor(none)) ///
    (lfit ex_utils mktrf, lcolor(dkorange)), ///
    title("(b) Utilities", size(medium)) ///
    xtitle("Market excess return (%)") ///
    ytitle("Industry excess return (%)") ///
    xlabel(-20(10)20) ylabel(-40(20)40, angle(0)) ///
    aspectratio(1) legend(off) ///
    graphregion(color(white)) name(utils, replace)
graph combine hitec utils, cols(2) xcommon ycommon iscale(1.20) ///
    imargin(0) graphregion(color(white) margin(zero)) ///
    xsize(6.4) ysize(3.2)
graph export "figs/raw/capm-fig01-market-${CAPM_STAMP}.png", ///
    replace width(2800)
graph export "figs/raw/capm-fig01-market-${CAPM_STAMP}.svg", ///
    replace fontface("Times New Roman")
graph export "figs/raw/capm-fig01-market-${CAPM_STAMP}.pdf", ///
    replace fontface("Times New Roman")

* SECTION portfolio
* 固定权重的线性恒等式不是 CAPM 的独立验证
quietly regress ex_hitec mktrf
scalar bh = _b[mktrf]
quietly regress ex_utils mktrf
scalar bu = _b[mktrf]
generate double ex_portfolio = .5*ex_hitec + .5*ex_utils
regress ex_portfolio mktrf
scalar beta_gap = _b[mktrf] - (.5*bh + .5*bu)
display "固定权重组合 beta 的代数误差 = " %16.12f beta_gap
assert abs(beta_gap) < 1e-10

* SECTION rolling
* 目标月份为 i  只使用 i-window 至 i-1 的已观察收益
* 单个月份先核验  命令无需在 76 列以内另起续行
local t = tm(2025m12)
regress ex_hitec mktrf if inrange(mdate, `t'-60, `t'-1)
display "beta = " %7.3f _b[mktrf]
capture postclose capm_roll
postfile capm_roll str8 industry int window mdate end_used ///
    double beta using logs/capm/rolling.dta, replace
foreach a in hitec utils {
    foreach w in 36 60 {
        forvalues i = 61/432 {
            local first = `i' - `w'
            local last = `i' - 1
            quietly regress ex_`a' mktrf in `first'/`last'
            post capm_roll ("`a'") (`w') (mdate[`i']) ///
                (mdate[`last']) (_b[mktrf])
        }
    }
}
postclose capm_roll
preserve
use logs/capm/rolling.dta, clear
format mdate end_used %tm
assert end_used == mdate - 1
assert _N == 1488
sort industry window mdate
export delimited using logs/capm/rolling.csv, replace
foreach a in hitec utils {
    twoway (line beta mdate if industry=="`a'" & window==36, ///
        lcolor(navy) lpattern(solid)) ///
        (line beta mdate if industry=="`a'" & window==60, ///
        lcolor(dkorange) lpattern(dash)), ///
        title("`a'", size(medium)) xtitle("") ///
        ytitle("Estimated beta") ylabel(0(.5)2, angle(0)) ///
        xlabel(420 540 660 780, format(%tmCCYY)) ///
        legend(order(1 "36 months" 2 "60 months") rows(1) ///
        region(lstyle(none))) ///
        aspectratio(1) graphregion(color(white)) ///
        name(roll_`a', replace)
}
graph combine roll_hitec roll_utils, cols(2) ycommon iscale(1.20) ///
    imargin(0) graphregion(color(white) margin(zero)) ///
    xsize(6.4) ysize(3.2)
graph export "figs/raw/capm-fig03-rolling-${CAPM_STAMP}.png", ///
    replace width(2800)
graph export "figs/raw/capm-fig03-rolling-${CAPM_STAMP}.svg", ///
    replace fontface("Times New Roman")
graph export "figs/raw/capm-fig03-rolling-${CAPM_STAMP}.pdf", ///
    replace fontface("Times New Roman")
list in 1/4, noobs
restore

* SECTION simulation
* 同一市场收益和扰动  只改变 beta 的生成规则
use data/capm/beta_sim.dta, clear
format mdate %tm
assert _N == 240
assert mdate == tm(2000m1) + _n - 1
save logs/capm/simulation-input.dta, replace
export delimited using logs/capm/simulation-input.csv, replace
capture postclose capm_sim
postfile capm_sim int mdate double b_fixed double b_change ///
    double beta_true ///
    using logs/capm/simulation.dta, replace
forvalues i = 61/240 {
    local first = `i' - 60
    local last = `i' - 1
    quietly regress ex_fixed mktrf in `first'/`last'
    scalar bf = _b[mktrf]
    quietly regress ex_change mktrf in `first'/`last'
    post capm_sim (mdate[`i']) (bf) (_b[mktrf]) (beta_true[`i'])
}
postclose capm_sim
use logs/capm/simulation.dta, clear
format mdate %tm
generate fixed_true = 1
assert _N == 180
export delimited using logs/capm/simulation.csv, replace
twoway (line b_fixed mdate, lcolor(navy)) ///
    (line fixed_true mdate, lcolor(gs5) lpattern(dash)), ///
    title("(a) Constant beta", size(medium)) ///
    ytitle("Beta") xtitle("") ylabel(0(.5)2, angle(0)) ///
    xlabel(540 600 660 720, format(%tmCCYY)) ///
    legend(order(1 "Estimated" 2 "True") rows(1) ///
    region(lstyle(none))) ///
    aspectratio(1) graphregion(color(white)) ///
    name(sim_fixed, replace)
twoway (line b_change mdate, lcolor(navy)) ///
    (line beta_true mdate, lcolor(gs5) lpattern(dash)), ///
    title("(b) Changing beta", size(medium)) ///
    ytitle("Beta") xtitle("") ylabel(0(.5)2, angle(0)) ///
    xlabel(540 600 660 720, format(%tmCCYY)) ///
    legend(order(1 "Estimated" 2 "True") rows(1) ///
    region(lstyle(none))) ///
    aspectratio(1) graphregion(color(white)) ///
    name(sim_change, replace)
graph combine sim_fixed sim_change, cols(2) ycommon iscale(1.20) ///
    imargin(0) graphregion(color(white) margin(zero)) ///
    xsize(6.4) ysize(3.2)
graph export "figs/raw/capm-fig04-simulation-${CAPM_STAMP}.png", ///
    replace width(2800)
graph export "figs/raw/capm-fig04-simulation-${CAPM_STAMP}.svg", ///
    replace fontface("Times New Roman")
graph export "figs/raw/capm-fig04-simulation-${CAPM_STAMP}.pdf", ///
    replace fontface("Times New Roman")
summarize b_fixed b_change
display "CAPM 运行完成  模拟与真实数据的输出分别保存"
