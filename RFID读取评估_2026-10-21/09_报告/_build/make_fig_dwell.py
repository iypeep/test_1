# -*- coding: utf-8 -*-
"""画「窗口 vs 读到率」折线图（配合停留时间独立页）

数据（31 天 113,667 箱，delay_ms × EpcLog 按箱对齐）：
    <1 s   114 箱      读到 ≥1 台 0.0%   均值 0.000
    1–2 s  306 箱      0.3%            0.003
    2–3 s  53,109 箱   0.7%            0.009
    3–4 s  52,157 箱   0.2%            0.002
    ≥4 s   7,981 箱    64.6%           1.056

输出：09_报告/figs/fig_dwell.png
用法：py -3.12 make_fig_dwell.py
"""
import os
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib import font_manager as fm

_HERE = os.path.dirname(os.path.abspath(__file__))
REP = os.path.dirname(_HERE)
OUT = os.path.join(REP, "figs", "fig_dwell.png")

INK, GRAY = "#1A1A1A", "#8C8C8C"
ACCENT, ACCENT_L = "#3E5DA8", "#7F97C4"

fm.fontManager.addfont(r"C:\Windows\Fonts\msyh.ttc")
plt.rcParams["font.family"] = "Microsoft YaHei"
plt.rcParams["axes.unicode_minus"] = False

buckets = ["<1 s", "1–2 s", "2–3 s", "3–4 s", "4–5 s", "5–6 s", "6–10 s", "≥10 s"]
boxes = [114, 306, 53109, 52157, 24, 2859, 1403, 3695]
pct = [0.0, 0.3, 0.7, 0.2, 83.3, 98.3, 96.0, 26.4]
avg = [0.000, 0.003, 0.009, 0.002, 1.250, 1.432, 1.366, 0.647]


def main():
    fig, ax = plt.subplots(figsize=(7.8, 3.5), dpi=220)
    x = list(range(len(buckets)))

    ax.plot(x, pct, "-o", color=ACCENT, lw=2.2, ms=7, label="读到 ≥1 台的箱占比")
    ax.plot([4], [pct[4]], "o", ms=10, mfc="white", mec=ACCENT, mew=1.8, zorder=5)
    for xi, yi, nb in zip(x, pct, boxes):
        ax.annotate(f"{yi:.1f}%", (xi, yi), textcoords="offset points", xytext=(0, 10),
                    ha="center", fontsize=9.2, color=ACCENT, fontweight="bold")
        ax.annotate(f"{nb:,} 箱", (xi, 0), textcoords="offset points", xytext=(0, -24),
                    ha="center", fontsize=7.2, color=GRAY)

    ax2 = ax.twinx()
    ax2.plot(x, avg, "--s", color=GRAY, lw=1.4, ms=5, label="平均读到台数")
    ax2.set_ylim(0, 1.75)
    ax2.set_ylabel("平均读到台数（/6）", fontsize=9, color=GRAY)
    ax2.tick_params(colors=GRAY, labelsize=8.5, length=0)
    for sp in ("top",):
        ax2.spines[sp].set_visible(False)

    ax.axvspan(4.45, 5.55, color="#EDF1F9", zorder=0)
    ax.text(5.0, 46, "5 s 附近\n跳变", ha="center", fontsize=8.6, color=ACCENT)


    ax.set_xticks(x)
    ax.set_xticklabels(buckets, fontsize=8.4, color=INK)
    ax.set_xlim(-0.35, len(buckets) - 0.45)
    ax.set_ylim(0, 108)
    ax.set_xlabel("该箱处理窗口（开始 → 判定结束）", fontsize=9, color=INK, labelpad=10)
    ax.set_ylabel("读到 ≥1 台的箱占比（%）", fontsize=9, color=INK)
    for sp in ("top",):
        ax.spines[sp].set_visible(False)
    ax.grid(axis="y", color="#ECECEC", lw=0.8)
    ax.set_axisbelow(True)
    ax.tick_params(colors=INK, labelsize=9, length=0)

    lines1, labels1 = ax.get_legend_handles_labels()
    lines2, labels2 = ax2.get_legend_handles_labels()
    ax.legend(lines1 + lines2, labels1 + labels2, frameon=False, fontsize=8.4, loc="center left", bbox_to_anchor=(0.005, 0.62))

    fig.tight_layout(pad=0.4)
    fig.savefig(OUT, facecolor="white")
    print("wrote", OUT)


if __name__ == "__main__":
    main()
