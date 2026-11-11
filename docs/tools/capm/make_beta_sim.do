* 仅在建立新的模拟数据版本时使用  普通课堂不运行本文件
version 19
args outfile
if "`outfile'" == "" {
    local outfile "data/capm/beta_sim.dta"
}
* 冻结输入存在即停止  不静默覆盖
confirm new file "`outfile'"
clear
set rng mt64
set seed 20261029
set obs 240
generate int mdate = tm(2000m1) + _n - 1
format mdate %tm
generate double mktrf = .5 + 4*rnormal()
generate double eps = 4*rnormal()
generate double beta_true = 1 + .8*(_n > 120)
generate double ex_fixed = mktrf + eps
generate double ex_change = beta_true*mktrf + eps
save "`outfile'"
