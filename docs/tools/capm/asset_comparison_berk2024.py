"""Transcribe and cross-check published CAPM asset summary statistics.

Reads the user supplied Berk/DeMarzo book. It does not reproduce the
underlying 96 annual return observations and never downloads market data.
Provide your own licensed copy of the book; it is not included.
Run: python tools/capm/asset_comparison_berk2024.py --book path/to/book.pdf
"""
from pathlib import Path
from decimal import Decimal
import argparse
import csv
import hashlib
import json
import re
from urllib.parse import quote
from pypdf import PdfReader

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / 'data/capm'
AUDIT = ROOT / 'logs/capm/review-20261111-20comments/data-research'
STEM = 'asset-comparison-berk2024-20261111'
RETRIEVED = '2026-11-11'
EXPECTED = {
    'Small stocks': ('18.6', '38.6', '15.3'),
    'S&P 500': ('12.2', '19.7', '8.9'),
    'Corporate bonds': ('6.2', '6.3', '2.9'),
    'Treasury bills': ('3.3', '3.1', '0.0'),
}
LABELS = ['美国小盘股票', 'S&P 500', '美国长期公司债(AAA)', '30 天美国国库券(Rf)']
LINK = 'https://eu.pearson.com/corporate-finance-global-edition/9781292446356'
PREVIEW = 'https://www.pearson.de/media/muster/ext/9781292446417.pdf'
SCHOLAR = 'https://scholar.google.com/scholar?q=' + quote('Berk DeMarzo Corporate Finance 6th Global Edition 2024')


def digest(path):
    h = hashlib.sha256()
    with path.open('rb') as f:
        for b in iter(lambda: f.read(1048576), b''):
            h.update(b)
    return h.hexdigest()


def one_column(text, table):
    section = re.split(r'TABLE\s+10\.\s*' + str(table), text, maxsplit=1)[1]
    result = {}
    for asset in EXPECTED:
        match = re.search(re.escape(asset) + r'\s+([0-9.]+)%', section)
        if match is None:
            raise ValueError(f'Missing {asset} in Table 10.{table}')
        result[asset] = Decimal(match.group(1))
    return result


def parse_book_argument():
    parser = argparse.ArgumentParser(
        description=(
            'Transcribe published summary statistics from a user-supplied copy '
            'of Berk and DeMarzo, Corporate Finance, 6th ed., Global ed. (2024). '
            'The book is not included; provide your own licensed copy.'
        )
    )
    parser.add_argument(
        '--book', type=Path, required=True,
        help='Path to your own copy of the book PDF (required; no default).'
    )
    book = parser.parse_args().book.expanduser()
    if not book.is_file():
        parser.error('--book must identify an existing PDF file')
    return book.resolve()


def main():
    book = parse_book_argument()
    reader = PdfReader(book)
    text = {page: reader.pages[page - 1].extract_text() for page in [358,359,367,369,371,372]}
    means = one_column(text[367], 3)
    volatility = one_column(text[369], 4)
    combined = re.split(r'TABLE\s+10\.\s*5', text[372], maxsplit=1)[1].split('FIGURE 10.6', 1)[0]
    excess = {}
    combined_vol = {}
    for asset in EXPECTED:
        label = re.escape(asset)
        if asset == 'Treasury bills':
            label += r'\s*\(30-day\)'
        match = re.search(label + r'\s+([0-9.]+)%\s+([0-9.]+)%', combined)
        if match is None:
            raise ValueError(f'Missing {asset} in Table 10.5')
        combined_vol[asset] = Decimal(match.group(1))
        excess[asset] = Decimal(match.group(2))
    checks = []
    for asset, expected in EXPECTED.items():
        actual = (str(means[asset]), str(volatility[asset]), str(excess[asset]))
        assert tuple(Decimal(x) for x in actual) == tuple(Decimal(x) for x in expected)
        assert volatility[asset] == combined_vol[asset]
        assert means[asset] - means['Treasury bills'] == excess[asset]
        checks.append({'asset': asset, 'annual_mean_pct': float(means[asset]),
                       'annual_sd_pct': float(volatility[asset]),
                       'annual_excess_mean_pct': float(excess[asset]),
                       'raw_mean_minus_rf_matches_table10_5': True,
                       'table10_4_sd_matches_table10_5': True})
    for page in [367,369,372]:
        assert re.search(r'1926[–-]2021', text[page])
    assert re.search(r'long-term,\s+AAA-rated U\.S\. corporate bonds', text[358])
    assert 'approximately 20 years' in text[358]
    assert 'one-month U.S. Treasury bills' in text[358]
    assert '1926–2014' in text[372]
    assert 'arithmetic average' in text[371]
    chapter_text = '\n'.join(reader.pages[i].extract_text() or '' for i in range(355,395))
    assert 'BBB' not in chapter_text

    OUT.mkdir(parents=True, exist_ok=True)
    AUDIT.mkdir(parents=True, exist_ok=True)
    rows = [
        ['统计项'] + LABELS,
        ['样本期间'] + ['1926–2021'] * 4,
        ['平均年收益率(算术平均，%)'] + [str(means[a]) for a in EXPECTED],
        ['年收益率波动率(标准差，%)'] + [str(volatility[a]) for a in EXPECTED],
        ['平均年超额收益率(相对国库券，%)'] + [str(excess[a]) for a in EXPECTED],
    ]
    with (OUT / (STEM + '.csv')).open('w', newline='', encoding='utf-8-sig') as f:
        csv.writer(f).writerows(rows)
    table = '\n'.join(['| ' + ' | '.join(rows[0]) + ' |',
                       '|---|---:|---:|---:|---:|'] +
                      ['| ' + ' | '.join(row) + ' |' for row in rows[1:]])
    md = '''美国不同资产的历史收益与波动(1926–2021)

''' + table + '''

注：各列均为 1926–2021 年的年度实现收益统计，股息和利息再投资，不计交易成本。平均收益为算术平均，波动率为年收益的标准差。公司债为约 20 年到期的 AAA 级美国长期公司债组合。国库券列统计逐年滚动持有 30 天国库券的年度收益，3.1% 的跨年标准差反映各年短期利率和再投资条件的变化。

行来源：样本期间、波动率和平均超额收益据 Berk and DeMarzo (2024) Table 10.5 (p. 371)；平均年收益据 Table 10.3 (p. 366)。波动率另与 Table 10.4 (p. 368) 逐项核对一致。资产定义见 p. 357，股息和利息再投资口径见 p. 358。

资料来源：Berk and DeMarzo (2024) 第 10 章，相关原始数据来源为 CRSP、Standard and Poor’s、MSCI 和 Global Financial Data；公司债组合基于 Global Financial Data 的 Corporate Bond Index。

参考文献：

1. Berk, J., & DeMarzo, P. (**2024**). *Corporate finance* (6th ed., Global ed.). Pearson. [Link](''' + LINK + '''), [PDF 试读](''' + PREVIEW + '''), [Google](<''' + SCHOLAR + '''>).
'''
    (OUT / (STEM + '.md')).write_text(md, encoding='utf-8')
    verification = {
        'status': 'PASS', 'retrieved_date': RETRIEVED,
        'method': 'Transcription and cross-check of published summary statistics; no raw-return replication',
        'source_pdf': str(book), 'source_sha256': digest(book), 'source_bytes': book.stat().st_size,
        'source_pages': [
            {'purpose':'asset definitions', 'printed_page':357, 'pdf_page_1based':358},
            {'purpose':'reinvestment and source attribution', 'printed_page':358, 'pdf_page_1based':359},
            {'purpose':'Table 10.3 annual arithmetic means', 'printed_page':366, 'pdf_page_1based':367},
            {'purpose':'Table 10.4 annual standard deviations', 'printed_page':368, 'pdf_page_1based':369},
            {'purpose':'arithmetic versus geometric average', 'printed_page':370, 'pdf_page_1based':371},
            {'purpose':'Table 10.5 excess returns and Figure 10.6 period discrepancy', 'printed_page':371, 'pdf_page_1based':372},
        ],
        'period':'1926-2021', 'calendar_year_count':96,
        'primary_numbers_direct_from_tables':True, 'rf_mean_guessed':False,
        'equity_reinvestment':'Dividends reinvested', 'bond_reinvestment':'Interest reinvested',
        'corporate_bond_rating':'AAA', 'corporate_bond_maturity':'Approximately 20 years',
        'rf_instrument':'One-month US Treasury bills; Table 10.5 labels 30-day',
        'bbb_present_in_chapter10_text':False,
        'fig10_6_period':'1926-2014; not merged into 1926-2021 table',
        'row_sources':{'period':'Table 10.5, p.371', 'annual_mean':'Table 10.3, p.366', 'annual_sd':'Table 10.5, p.371; checked against Table 10.4, p.368', 'annual_excess_mean':'Table 10.5, p.371'},
        'values':checks,
        'publisher_metadata_url':LINK, 'publisher_preview_url':PREVIEW,
        'generated_files':[str(OUT / (STEM + suffix)) for suffix in ['.csv','.md']],
        'protected_inputs_written':False,
        'new_market_data_downloaded':False,
    }
    (AUDIT / 'berk2024-numeric-verification.json').write_text(json.dumps(verification, ensure_ascii=False, indent=2)+'\n', encoding='utf-8')
    print(json.dumps({'status':'PASS', 'files':verification['generated_files'],
                      'verification':str(AUDIT/'berk2024-numeric-verification.json'),
                      'values':checks}, ensure_ascii=False, indent=2))


if __name__ == '__main__':
    main()
