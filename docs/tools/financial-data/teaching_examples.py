"""三章理论的小表例子。全部数值为虚构教学数据，不需要 CSMAR。"""
from io import StringIO, BytesIO
import sqlite3
import numpy as np
import pandas as pd
from IPython.display import display


def run_examples():
    # 明确类型读取，保留前导零；先看结构，再做计算。
    source = StringIO('code,date,assets\n000001,2020-12-31,100\n000002,2020-12-31,200\n')
    read_demo = pd.read_csv(source, dtype={'code': 'string'}, parse_dates=['date'])
    assert read_demo.code.iloc[0] == '000001'
    display(read_demo)
    display(read_demo.dtypes.astype(str).rename('dtype').to_frame())

    # 与理论篇对应的两公司、三交易日小表，绝非真实公司记录。
    annual = pd.DataFrame({'firm': ['A', 'B'], 'year': [2020, 2020], 'assets': [100., 200.]})
    company = pd.DataFrame({'firm': ['A', 'B'], 'industry': ['甲行业', '乙行业']})
    daily = pd.DataFrame({'firm': ['A', 'A', 'B'],
                          'date': pd.to_datetime(['2020-01-02', '2020-01-03', '2020-01-02']),
                          'turnover': [1., 3., 2.]})
    daily['year'] = daily.date.dt.year
    wrong = annual.merge(daily, on=['firm', 'year'])
    yearly = daily.groupby(['firm', 'year'], as_index=False).turnover.mean()
    correct = annual.merge(yearly, on=['firm', 'year'], validate='one_to_one', indicator=True)
    assert len(wrong) == 3 and len(correct) == 2
    assert correct.turnover.tolist() == [2., 2.]
    display(pd.DataFrame({'操作': ['年度输入', '直接连接', '聚合后连接'], '行数': [2, len(wrong), len(correct)]}))
    display(correct)

    # append 保留来源；同一片段重复追加时应被键检查发现。
    appended = pd.concat([annual.iloc[:1].assign(source='part1'),
                          annual.iloc[1:].assign(source='part2')], ignore_index=True)
    assert not appended.duplicated(['firm', 'year']).any()
    duplicated = pd.concat([appended, appended.iloc[:1]], ignore_index=True)
    assert duplicated.duplicated(['firm', 'year'], keep=False).sum() == 2

    # 宽长转换只重排信息，不能自动聚合重复公司年度。
    wide = pd.DataFrame({'firm': ['A', 'B'], 'assets_2019': [90., 180.], 'assets_2020': [100., 200.]})
    long = wide.melt(id_vars='firm', var_name='period', value_name='assets')
    long['year'] = long.period.str[-4:].astype(int)
    restored = long.pivot(index='firm', columns='period', values='assets').reset_index()
    pd.testing.assert_frame_equal(wide, restored, check_names=False)
    display(long[['firm', 'year', 'assets']].sort_values(['firm', 'year']))

    # Parquet 保存与读取类型；使用内存字节流，不改写任何原始文件。
    buffer = BytesIO()
    read_demo.to_parquet(buffer, index=False)
    buffer.seek(0)
    restored_types = pd.read_parquet(buffer)
    pd.testing.assert_frame_equal(read_demo, restored_types)

    # SQLite 唯一索引是显式设置的，不是 to_sql 自动识别业务键。
    with sqlite3.connect(':memory:') as conn:
        annual.to_sql('annual', conn, index=False)
        company.to_sql('company', conn, index=False)
        conn.execute('CREATE UNIQUE INDEX annual_key ON annual(firm, year)')
        conn.execute('CREATE UNIQUE INDEX company_key ON company(firm)')
        query = '''SELECT c.industry, COUNT(*) AS n, AVG(f.assets) AS mean_assets
                   FROM annual AS f JOIN company AS c ON f.firm = c.firm
                   WHERE f.year = 2020 GROUP BY c.industry ORDER BY c.industry'''
        sql_result = pd.read_sql_query(query, conn)
    pandas_result = (annual.merge(company, on='firm', validate='many_to_one')
                     .groupby('industry', as_index=False)
                     .agg(n=('firm', 'size'), mean_assets=('assets', 'mean')))
    pd.testing.assert_frame_equal(sql_result, pandas_result)
    display(sql_result)

    # 缺失填零改变了假设和统计分母；这里只比较，不作处理推荐。
    rd = pd.Series([0., np.nan, 2.]) / 100
    assert np.isclose(rd.mean(), .01)
    assert np.isclose(rd.fillna(0).mean(), 2/300)
    # 算术和复合回报、股利回报、盈利比率均为手算可核对的小例子。
    comparisons = pd.DataFrame({
        '指标': ['研发率_已知样本均值', '研发率_填零后均值',
                 '两日算术平均收益', '两日复合收益', '含股利回报',
                 '期末资产ROA', '平均资产ROA', '近零权益ROE'],
        '数值': [rd.mean(), rd.fillna(0).mean(), np.mean([.1, -.1]),
                 np.prod(1 + np.array([.1, -.1])) - 1,
                 (9 + 1) / 10 - 1, 10/200, 10/150, 1/.01]})
    display(comparisons.round(6))
    assert np.isclose(comparisons.loc[3, '数值'], -.01)
    print('教学小表检查通过：读取、合并、追加、宽长往返、类型保存、SQL 对照与手算。')


if __name__ == '__main__':
    run_examples()
