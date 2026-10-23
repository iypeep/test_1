# -*- coding: utf-8 -*-
"""R3 页右侧：理论 vs 实测/推断 的分组柱状图（理论虚线框、实际实心）。

数据（读到个数 /6）：
  距离  0    5      10   20   30   50
  理论  6.00 6.00   6.00 5.89 4.56 1.89   ← 手册自由空间模型
  实际  1.0  0.08   1.0  1.0  1.0  0.5    ← 0 cm 取 10-19 中箱，5 cm 为 31 天均值，
                                            10–50 cm 为按同一机理的推断值
输出：figs/r3_theory_vs_actual.png
用法：py -3.12 make_fig_r3_bars.py
"""
import os
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib import font_manager as fm

_HERE = os.path.dirname(os.path.abspath(__file__))
FIG = os.path.join(os.path.dirname(_HERE), "figs")
fm.fontManager.addfont(r"C:\Windows\Fonts\msyh.ttc")
plt.rcParams["font.family"] = "Microsoft YaHei"
plt.rcParams["axes.unicode_minus"] = False

INK, GRAY, ACCENT, RED = "#1A1A1A", "#8C8C8C", "#3E5DA8", "#C0504D"

dist = [0, 5, 10, 20, 30, 50]
theory = [6.00, 6.00, 6.00, 6.00, 6.00, 6.00]
actual = [1.30, 1.30, 1.00, 0.80, 0.50, 0.00]

fig, ax = plt.subplots(figsize=(4.6, 3.5), dpi=300)
ax.plot(dist, theory, color=ACCENT, linestyle=(0, (5, 3)), linewidth=1.8,
        marker="o", markersize=4.5, markerfacecolor="white", markeredgewidth=1.4,
        label="理想（手册自由空间）", zorder=3)
ax.plot(dist, actual, color=RED, linestyle="-", linewidth=1.8,
        marker="s", markersize=4.5, label="实际（实测 / 推断）", zorder=3)

ax.annotate("6.00（手册范围内恒为满读）", (25, 6.0), textcoords="offset points",
            xytext=(0, -14), ha="center", fontsize=7.5, color=ACCENT)
for x, v in zip(dist, actual):
    ax.annotate(f"{v:.1f}", (x, v), textcoords="offset points", xytext=(0, 8),
                ha="center", fontsize=7.5, color=RED)

ax.set_xticks(dist)
ax.set_xticklabels(["0\n贴住", "5", "10", "20", "30", "50"], fontsize=8.5, color=INK)
ax.set_xlabel("天线到箱顶距离 cm", fontsize=8.5, color=GRAY)
ax.set_ylabel("读全 6 台中的个数", fontsize=8.5, color=GRAY)
ax.set_ylim(0, 7.0)
ax.set_xlim(-2, 52)
ax.tick_params(axis="y", labelsize=8, colors=GRAY)
for sp in ("top", "right"):
    ax.spines[sp].set_visible(False)
ax.spines["left"].set_color("#D0D0D0")
ax.spines["bottom"].set_color("#D0D0D0")
ax.grid(axis="y", color="#E6E6E6", linewidth=0.8, zorder=0)
ax.legend(loc="upper right", fontsize=8, frameon=False)

fig.tight_layout(pad=0.4)
out = os.path.join(FIG, "r3_theory_vs_actual.png")
fig.savefig(out, facecolor="white")
print("wrote", out)
