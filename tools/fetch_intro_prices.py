"""通过 AKShare 下载首讲固定股票篮子的历史数据；课堂分析读取快照。"""
from pathlib import Path
from datetime import datetime
import hashlib
import json
import time
import akshare as ak
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "data" / "intro"
STOCKS = {
    "sh600036": "招商银行", "sh601398": "工商银行",
    "sh600519": "贵州茅台", "sz000858": "五粮液",
    "sz000333": "美的集团", "sz000651": "格力电器",
    "sh600900": "长江电力", "sh600030": "中信证券",
    "sh600028": "中国石化", "sh600050": "中国联通",
}

def main():
    OUT.mkdir(parents=True, exist_ok=True)
    frames, records = [], []
    for code, name in STOCKS.items():
        # 每只股票单独保存，以便失败后续跑，不改写已下载的快照。
        dest = OUT / f"{code}-hfq.csv"
        if dest.exists():
            df = pd.read_csv(dest)
        else:
            df = ak.stock_zh_a_hist_tx(
                symbol=code, start_date="20180101", end_date="20251231",
                adjust="hfq", timeout=25,
            )
            if df.empty:
                raise ValueError(f"未返回行情：{code}")
            df.to_csv(dest, index=False, encoding="utf-8-sig")
            time.sleep(0.4)
        df["date"] = pd.to_datetime(df["date"])
        assert not df["date"].duplicated().any(), code
        assert (df["close"] > 0).all(), code
        frames.append(df[["date", "close"]].assign(symbol=code, name=name))
        records.append({"symbol": code, "name": name, "rows": len(df),
                        "start": str(df.date.min().date()),
                        "end": str(df.date.max().date()),
                        "sha256": hashlib.sha256(dest.read_bytes()).hexdigest()})
        print(code, name, len(df), flush=True)
    pd.concat(frames).to_csv(OUT / "prices-long.csv", index=False, encoding="utf-8-sig")
    manifest = {"retrieved_date": datetime.now().strftime("%Y-%m-%d"),
                "akshare_version": ak.__version__, "interface": "stock_zh_a_hist_tx",
                "source": "Tencent Finance via AKShare", "adjust": "hfq",
                "window": ["2018-01-01", "2025-12-31"],
                "selection": "固定教学篮子，事后选定；不是历史可投资股票池或荐股名单",
                "records": records}
    (OUT / "source-manifest.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")

if __name__ == "__main__":
    main()
