"""小型模拟验证：检查会改变经济含义的键、日期和比率边界。"""
import unittest
import pandas as pd
from pipeline import require_key, construct_variables, merge_checked

class PipelineTests(unittest.TestCase):
    def test_key_refuses_duplicate_and_null(self):
        for d in [pd.DataFrame({'k':[1,1]}),pd.DataFrame({'k':[1,None]})]:
            with self.assertRaises(ValueError):
                require_key(d,['k'],'teaching')

    def test_lag_requires_adjacent_year_and_zero_not_infinity(self):
        d=pd.DataFrame({'stock_code':['000001']*3,'fiscal_year':[2014,2015,2017],
            'total_assets':[100.,200.,0.],'total_equity':[40.,50.,0.],
            'parent_equity':[30.,40.,0.],'total_liabilities':[60.,150.,5.],
            'net_income':[10.,30.,1.],'parent_net_income':[8.,20.,1.]})
        out=construct_variables(d)
        self.assertAlmostEqual(out.loc[1,'roa_avg_consolidated'],.2)
        self.assertAlmostEqual(out.loc[1,'roe_parent_avg_consolidated'],20/35)
        self.assertTrue(pd.isna(out.loc[2,'total_assets_lag']))
        self.assertTrue(pd.isna(out.loc[2,'leverage_consolidated']))

    def test_outer_merge_records_unmatched(self):
        a=pd.DataFrame({'stock_code':['000001','000002'],'fiscal_year':[2020,2020]})
        b=pd.DataFrame({'stock_code':['000002','000003'],'fiscal_year':[2020,2020],'v':[1.,2.]})
        audit,breakdown=[],[]
        out=merge_checked(a,b,'test',audit,breakdown)
        self.assertEqual(len(out),3)
        self.assertEqual([audit[0][k] for k in ['matched','master_only','using_only']],[1,1,1])

if __name__=='__main__':
    unittest.main()
