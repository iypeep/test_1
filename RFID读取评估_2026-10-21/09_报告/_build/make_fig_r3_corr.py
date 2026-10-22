# -*- coding: utf-8 -*-
"""R3 图：读到几个 vs 距离（理论 vs 实测）—— 结论是「两者没有相关性」

要点（2026-10-22 修正，前一版把差异误归因成“额外 28.6 dB 损耗”，已作废）：
  * 手册/自由空间模型本身是对的：0/10/20/30/50 cm → 理论上 6.00 / 6.00 / 5.89 / 4.56 / 1.89（下置 9 dBi）；
  * 但实测（产线 3 天线 <5 cm＝0.08/6；10-19 接触＝单次最多 2/6）几乎不随距离变化；
  * ⇒ 读到多少与距离**无相关性**；把距离压得更近、或再加功率，都换不来读数。

输入：09_报告/_sim/B_距离_9dBi_模拟.csv（理论，未改动）
输出：09_报告/figs/fig7c_distance_vs_reads.png
      09_报告/_sim/R3_距离_理论与实测.csv
"""
import os, csv

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib import font_manager as fm

_HERE = os.path.dirname(os.path.abspath(__file__))
REP = os.path.dirname(_HERE)
SIM, FIG = os.path.join(REP, "_sim"), os.path.join(REP, "figs")

INK, GRAY, LIGHT, ACCENT, RED = "#1A1A1A", "#8C8C8C", "#CFCFCF", "#3E5DA8", "#C0504D"
fm.fontManager.addfont(r"C:\Windows\Fonts\msyh.ttc")
plt.rcParams["font.family"] = "Microsoft YaHei"
plt.rcParams["axes.unicode_minus"] = False

# 实测锚点（有据可查的两处）
MEAS = [
    (0.0, 0.0, 2.0, "10-19 中箱接触式\n8 次试验：0–2 个"),
    (4.5, 0.079, 0.079, "产线 3 天线 <5 cm\n31 天 113,667 箱：0.08 个"),
]


def main():
    rows = [r for r in csv.DictReader(open(os.path.join(SIM, "B_距离_9dBi_模拟.csv"), encoding="utf-8-sig"))
            if r["位置"] == "下"]
    d = [float(r["距离_cm"]) for r in rows]
    y_theory = [float(r["读全数_6"]) for r in rows]
    rssi = [float(r["RSSI_dBm"]) for r in rows]

    out_rows = [{"距离_cm": int(x), "理论_读全_6": y, "理论_RSSI_dBm": s, "实测_读全_6": ""} for x, y, s in zip(d, y_theory, rssi)]
    for r in out_rows:
        if r["距离_cm"] == 0:
            r["实测_读全_6"] = "0–2（8 次试验）"
        elif r["距离_cm"] == 5:
            r["实测_读全_6"] = "0.08（31 天均值）"
    p = os.path.join(SIM, "R3_距离_理论与实测.csv")
    with open(p, "w", newline="", encoding="utf-8-sig") as fh:
        w = csv.DictWriter(fh, fieldnames=list(out_rows[0]))
        w.writeheader(); w.writerows(out_rows)
    print("wrote", p)

    fig, ax = plt.subplots(figsize=(7.4, 3.55), dpi=220)

    # 10–40 cm：无逐档实测
    ax.axvspan(10, 40, color="#F4F4F4", zorder=0)
    ax.text(25, 5.95, "10–40 cm：尚未逐档实测\n（A/B 组待取数）", fontsize=8, color=GRAY, ha="center", va="top")

    ax.plot(d, y_theory, ls=(0, (5, 3)), lw=1.6, color=LIGHT, marker="o", ms=4, zorder=2,
            label="理论（手册/自由空间模型，未改动）")

    for x, y, hi, lab in MEAS:
        ax.plot([x - 1.6, x + 1.6], [y, y], lw=2.6, color=RED, solid_capstyle="round", zorder=4)
        if hi > y:
            ax.plot([x], [hi], marker="_", ms=14, mew=2.2, color=RED, zorder=4)
        ax.annotate(lab, xy=(x, y), xytext=(x + 3.2, y + (1.55 if x < 1 else 0.9)),
                    fontsize=8.2, color=RED,
                    arrowprops=dict(arrowstyle="-", color=RED, lw=0.8),
                    va="bottom", zorder=5)

    ax.text(30, 0.55, "实测：无论贴多近，都在 0–1 个之间 —— 与距离无关", fontsize=9, color=RED, fontweight="bold")

    ax.set_xlim(-2, 52)
    ax.set_ylim(0, 6.6)
    ax.set_xlabel("读码器天线面到箱面的距离（cm）", fontsize=9.2, color=INK)
    ax.set_ylabel("每箱读到的整机标签数（/6）", fontsize=9.2, color=INK)
    for s in ("top", "right"):
        ax.spines[s].set_visible(False)
    ax.grid(axis="y", color="#ECECEC", lw=0.8)
    ax.set_axisbelow(True)
    ax.tick_params(colors=INK, labelsize=8.6, length=0)
    ax.legend(frameon=False, fontsize=8, loc="center left", bbox_to_anchor=(0.02, 0.62))
    fig.tight_layout(pad=0.35)
    fp = os.path.join(FIG, "fig7c_distance_vs_reads.png")
    fig.savefig(fp, facecolor="white")
    print("wrote", fp)


if __name__ == "__main__":
    main()
