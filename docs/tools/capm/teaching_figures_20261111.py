"""Deterministic CAPM teaching diagrams; no data fetch or model execution.

Run with the project's Python:
    python -B tools/capm/teaching_figures_20261111.py
Each run uses a new Asia/Shanghai timestamp and refuses to overwrite images.
"""
from __future__ import annotations

import argparse
from datetime import datetime, timedelta, timezone
import hashlib
import json
from pathlib import Path
import warnings

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib import font_manager
from matplotlib.patches import Rectangle
from matplotlib.text import Text
import numpy as np
from PIL import Image, ImageOps

ROOT = Path(__file__).resolve().parents[2]
BLUE = "#176185"
ORANGE = "#A76421"
INK = "#23333E"
GREY = "#73828B"
PALE = "#E7F0F4"
GREEN = "#337467"
PALE_GREEN = "#E7F1ED"


def configure() -> str:
    available = {item.name for item in font_manager.fontManager.ttflist}
    font = next((name for name in ("SimHei", "Microsoft YaHei",
                                  "Noto Sans CJK SC") if name in available), None)
    if font is None:
        raise RuntimeError("A verified CJK font is required.")
    plt.rcParams.update({
        "font.family": font, "font.size": 13.5,
        "axes.labelsize": 14, "xtick.labelsize": 13,
        "ytick.labelsize": 13, "axes.edgecolor": INK,
        "axes.labelcolor": INK, "text.color": INK,
        "xtick.color": INK, "ytick.color": INK,
        "axes.spines.top": False, "axes.spines.right": False,
        "axes.linewidth": 1, "axes.unicode_minus": False,
        "mathtext.fontset": "dejavusans",
        "pdf.fonttype": 42, "ps.fonttype": 42,
        "svg.fonttype": "path", "savefig.facecolor": "white",
        "figure.facecolor": "white",
    })
    return font


def return_axes(ylabel: str):
    fig, ax = plt.subplots(figsize=(6.4, 4.35), dpi=200)
    fig.subplots_adjust(left=.15, right=.965, bottom=.20, top=.96)
    ax.set_xlim(-.045, 1.65)
    ax.set_ylim(0, 13)
    ax.set_xticks([0, .5, 1, 1.5], ["0", "0.5", "1", "1.5"])
    ax.set_yticks([0, 2, 5, 8, 11])
    ax.set_xlabel(r"市场风险暴露 $\beta$", labelpad=9)
    ax.set_ylabel(ylabel, labelpad=9)
    ax.tick_params(length=4, width=1)
    return fig, ax


def sml_figure():
    fig, ax = return_axes("年度预期收益 (%)")
    beta = np.linspace(0, 1.6, 100)
    ax.plot(beta, 2 + 6 * beta, color=BLUE, lw=2.3)
    for x, y in zip([0, .5, 1, 1.5], [2, 5, 8, 11]):
        if x > 0:
            ax.plot([x, x], [0, y], ls=(0, (3, 3)),
                    color=GREY, lw=.8, zorder=1)
            ax.plot([0, x], [y, y], ls=(0, (3, 3)),
                    color=GREY, lw=.8, zorder=1)
        ax.plot(x, y, "o", ms=7.5, mfc="white", mec=BLUE,
                mew=1.8, clip_on=False, zorder=4)
    ax.text(.055, 12.0, r"$E(R_i)=2\%+\beta_i\times 6\%$", fontsize=15)
    ax.text(.045, 1.0, "无风险资产", fontsize=12.8)
    ax.text(.69, 8.55, "市场组合", fontsize=12.8)
    ax.text(.94, 3.8, "CAPM 理论线\n(SML)", color=BLUE,
            fontsize=14, ha="center", linespacing=1.35)
    return fig


def alpha_figure():
    fig, ax = return_axes("年度样本平均收益 (%)")
    beta = np.linspace(0, 1.6, 100)
    ax.plot(beta, 2 + 6 * beta, color=BLUE, lw=2.3)
    ax.set_yticks([0, 2, 5, 8, 10, 11])
    ax.plot([1, 1], [0, 10], color=GREY, lw=.9, ls=(0, (3, 3)))
    ax.plot([0, 1], [8, 8], color=GREY, lw=.8, ls=(0, (3, 3)))
    ax.plot([0, 1], [10, 10], color=GREY, lw=.8, ls=(0, (3, 3)))
    ax.plot(1, 8, "o", ms=7.5, mfc="white", mec=BLUE, mew=1.8, zorder=4)
    ax.plot(1, 10, "D", ms=7.5, mfc="white", mec=ORANGE, mew=1.8, zorder=4)
    ax.annotate("", xy=(1, 9.92), xytext=(1, 8.08),
                arrowprops={"arrowstyle": "<->", "color": ORANGE,
                            "lw": 1.8, "mutation_scale": 13}, zorder=5)
    ax.text(.12, 8.95, r"$\widehat{\alpha}=2$ 个百分点",
            color=ORANGE, fontsize=13.3, va="center")
    ax.annotate("资产平均收益 10%", xy=(.98, 10.03), xytext=(.10, 11.4),
                fontsize=13.5, color=ORANGE,
                arrowprops={"arrowstyle": "-", "color": ORANGE,
                            "lw": 1.0}, va="center")
    ax.text(.13, 5.9, "给定相同 $\\beta$ 的\n样本基准收益 8%",
            color=BLUE, fontsize=13.3, linespacing=1.3)
    ax.annotate("", xy=(.98, 8), xytext=(.59, 6.9),
                arrowprops={"arrowstyle": "-", "color": BLUE, "lw": 1.0})
    ax.text(.58, 1.2, r"$\widehat{\beta}=1$", fontsize=14)
    return fig


def rolling_figure():
    fig, ax = plt.subplots(figsize=(6.4, 4.4), dpi=200)
    fig.subplots_adjust(left=.055, right=.985, bottom=.16, top=.96)
    ax.set_xlim(-.7, 7.9)
    ax.set_ylim(-.45, 3.45)
    ax.axis("off")
    labels = [r"$t-6$", r"$t-5$", r"$t-4$", r"$t-3$",
              r"$t-2$", r"$t-1$", r"$t$", r"$t+1$"]
    rows = [
        (2.15, 0, 6, BLUE, PALE, r"目标月 $t$",
         r"使用窗口 $[t-w,\ t-1]$"),
        (.55, 1, 7, GREEN, PALE_GREEN, r"目标月 $t+1$",
         r"使用窗口 $[t-w+1,\ t]$"),
    ]
    for y, start, target, color, fill, row_label, window_label in rows:
        ax.text(-.40, y + .83, row_label, ha="left", va="center", fontsize=13.5)
        ax.annotate("", xy=(7.8, y), xytext=(-.45, y),
                    arrowprops={"arrowstyle": "->", "color": GREY, "lw": 1})
        ax.add_patch(Rectangle((start - .32, y - .23), 5.64, .46,
                               facecolor=fill, edgecolor=color, lw=1.1,
                               zorder=2))
        for month in range(start, start + 6):
            ax.plot(month, y, "o", ms=5.3, color=color, zorder=4)
        ax.plot(target, y, "D", ms=8.8, mec=ORANGE, mfc="white",
                mew=1.8, zorder=5)
        for month, label in enumerate(labels):
            ax.text(month, y - .43, label, ha="center", va="center",
                    fontsize=12.5)
        ax.text(start + 2.5, y + .50, window_label, ha="center",
                va="center", color=color, fontsize=14)
        ax.text(target, y + .40, "目标月", ha="center", color=ORANGE,
                fontsize=12.5)
    fig.text(.52, .065, r"示意窗口 $w=6$；真实行业案例使用 36 / 60 个月",
             ha="center", fontsize=12.5)
    return fig


CAPTIONS = {
    "sml": {
        "title": "证券市场线与预期收益",
        "note": ("注：沿用正文年度教学设定，无风险收益为 2%，市场预期收益为 8%。"
                 "β 为 0、0.5、1、1.5 时，CAPM 对应的年度预期收益为 2%、5%、8%、11%。"
                 "横轴为风险暴露，实线为理论定价关系，不是每月实现收益的回归拟合线。"),
        "insert_near": "sec-capm-pricing",
    },
    "alpha": {
        "title": "相同市场暴露下的收益偏离",
        "note": ("注：这是年度样本的图解设定，不是本章行业实证结果。设无风险收益为 2%，"
                 "市场样本平均收益为 8%，某资产估计 β 为 1、样本平均收益为 10%。"
                 "在相同 β 下，样本基准收益为 8%，竖直差为估计 α=2 个百分点。"
                 "α 依赖所选样本和基准，不能自动解释为经理能力。横轴为 β，而非逐期市场收益。"),
        "insert_near": "sec-capm-model-regression",
    },
    "rolling": {
        "title": "滚动窗口与目标月",
        "note": ("注：为便于计数，图中令窗口长度 w=6，正文真实行业案例使用 36 或 60 个月。"
                 "实心圆和阴影带表示用于估计的历史月份，空心菱形表示待估计风险暴露的目标月。"
                 "目标月 t 使用 [t-w,t-1]，向前移动一月后，目标月 t+1 使用 [t-w+1,t]。"
                 "每次均不使用该目标月尚未发生的收益；阴影不是置信区间。"),
        "insert_near": "sec-capm-rolling",
    },
}


def audit_figure(fig):
    fig.canvas.draw()
    renderer = fig.canvas.get_renderer()
    canvas = fig.bbox
    clipped = []
    for artist in fig.findobj(match=Text):
        if not artist.get_visible() or not artist.get_text().strip():
            continue
        bounds = artist.get_window_extent(renderer)
        if (bounds.x0 < canvas.x0 - 2 or bounds.y0 < canvas.y0 - 2
                or bounds.x1 > canvas.x1 + 2 or bounds.y1 > canvas.y1 + 2):
            clipped.append(artist.get_text())
    visible_text = [(a.get_text(), a.get_window_extent(renderer))
                    for a in fig.findobj(match=Text)
                    if a.get_visible() and a.get_text().strip()]
    overlaps = []
    for index, (label, box) in enumerate(visible_text):
        for other_label, other_box in visible_text[index + 1:]:
            overlap = box.intersection(box, other_box)
            if overlap is not None and overlap.width > 1 and overlap.height > 1:
                overlaps.append([label, other_label])
    return {"text_outside_canvas": clipped, "text_overlaps": overlaps,
            "text_count": sum(bool(a.get_text().strip())
                              for a in fig.findobj(match=Text))}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--stamp", default=datetime.now(
        timezone(timedelta(hours=8))).strftime("%Y%m%d-%H%M%S"))
    parser.add_argument("--outdir", type=Path, default=ROOT / "figs/raw")
    parser.add_argument("--qa-dir", type=Path, default=ROOT /
                        "logs/capm/review-20261111-20comments/figures")
    args = parser.parse_args()
    if not args.stamp.replace("-", "").isdigit() or len(args.stamp) != 15:
        raise ValueError("Use a YYYYMMDD-HHMMSS timestamp.")
    args.outdir.mkdir(parents=True, exist_ok=True)
    args.qa_dir.mkdir(parents=True, exist_ok=True)
    font = configure()
    assert [2 + 6 * b for b in (0, .5, 1, 1.5)] == [2, 5, 8, 11]
    assert 10 - (2 + 1 * (8 - 2)) == 2
    manifest = {"stamp": args.stamp, "font": font,
                "matplotlib": matplotlib.__version__,
                "source": str(Path(__file__).resolve()),
                "data_policy": "Deterministic teaching settings; no source data read.",
                "figures": []}
    builders = [("05", "sml", sml_figure),
                ("06", "alpha", alpha_figure),
                ("07", "rolling", rolling_figure)]
    for number, purpose, builder in builders:
        stem = f"capm-fig{number}-{purpose}-{args.stamp}"
        targets = [args.outdir / f"{stem}.{ext}"
                   for ext in ("png", "pdf", "svg")]
        if any(path.exists() for path in targets):
            raise FileExistsError("Use a new stamp; existing images are preserved.")
        with warnings.catch_warnings(record=True) as caught:
            warnings.simplefilter("always")
            fig = builder()
            audit = audit_figure(fig)
            for path in targets:
                fig.savefig(path, dpi=200, facecolor="white")
            plt.close(fig)
        missing = [str(item.message) for item in caught
                   if "missing from font" in str(item.message)]
        audit["missing_glyph_warnings"] = sorted(set(missing))
        with Image.open(targets[0]) as original:
            for width in (800, 360):
                height = round(original.height * width / original.width)
                original.resize((width, height), Image.Resampling.LANCZOS).save(
                    args.qa_dir / f"{stem}-preview-{width}.png")
            ImageOps.grayscale(original).save(args.qa_dir / f"{stem}-grayscale.png")
            pixel_size = list(original.size)
        row = {"number": number, "purpose": purpose, **CAPTIONS[purpose],
               "size_px": pixel_size, "audit": audit,
               "files": [{"path": str(path), "bytes": path.stat().st_size,
                          "sha256": hashlib.sha256(path.read_bytes()).hexdigest()}
                         for path in targets]}
        manifest["figures"].append(row)
    report = args.qa_dir / f"figure-manifest-{args.stamp}.json"
    report.write_text(json.dumps(manifest, ensure_ascii=False, indent=2),
                      encoding="utf-8")
    print(json.dumps({"manifest": str(report),
                      "outputs": [row["files"][0]["path"]
                                  for row in manifest["figures"]],
                      "audits": [row["audit"] for row in manifest["figures"]]},
                     ensure_ascii=False, indent=2))
    if any(row["audit"]["text_outside_canvas"]
           or row["audit"]["missing_glyph_warnings"]
           or row["audit"]["text_overlaps"]
           for row in manifest["figures"]):
        raise RuntimeError("Layout audit failed; inspect the manifest.")


if __name__ == "__main__":
    main()
