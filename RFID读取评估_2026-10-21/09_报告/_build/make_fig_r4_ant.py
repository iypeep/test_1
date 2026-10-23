# -*- coding: utf-8 -*-
"""R4 页：同一台音频杰读码器，9 dBi vs 6 dBi 天线（0–50 cm 读数对比折线）。

数据为实测/推断（与 R3 页同一口径）：
  9 dBi  1.3 1.3 1.0 0.8 0.5 0.0
  6 dBi  1.0 1.0 0.8 0.6 0.3 0.0
输出：figs/r4_9_vs_6.png
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
a9 = [1.25, 1.25, 1.00, 0.75, 0.50, 0.00]
a6 = [1.00, 1.00, 0.75, 0.50, 0.25, 0.00]

fig, ax = plt.subplots(figsize=(4.6, 3.5), dpi=300)
ax.plot(dist, a9, color=ACCENT, linewidth=1.9, marker="o", markersize=4.5,
        label="9 dBi 天线")
ax.plot(dist, a6, color=GRAY, linewidth=1.9, linestyle=(0, (5, 3)), marker="s", markersize=4.5,
        label="6 dBi 天线")

def r1(v):
    return f"{int(v * 10 + 0.5) / 10:.1f}"


for x, v in zip(dist, a9):
    ax.annotate(r1(v), (x, v), textcoords="offset points", xytext=(0, 9),
                ha="center", fontsize=7.5, color=ACCENT)
for x, v in zip(dist, a6):
    ax.annotate(r1(v), (x, v), textcoords="offset points", xytext=(0, -14),
                ha="center", fontsize=7.5, color=GRAY)

ax.set_xticks(dist)
ax.set_xticklabels(["0\n贴住", "5", "10", "20", "30", "50"], fontsize=8.5, color=INK)
ax.set_xlabel("天线到箱顶距离 cm", fontsize=8.5, color=GRAY)
ax.set_ylabel("读全 6 台中的个数", fontsize=8.5, color=GRAY)
ax.set_ylim(0, 1.7)
ax.set_xlim(-2, 52)
ax.tick_params(axis="y", labelsize=8, colors=GRAY)
for sp in ("top", "right"):
    ax.spines[sp].set_visible(False)
ax.spines["left"].set_color("#D0D0D0")
ax.spines["bottom"].set_color("#D0D0D0")
ax.grid(axis="y", color="#E6E6E6", linewidth=0.8, zorder=0)
ax.legend(loc="upper right", fontsize=8, frameon=False)
fig.tight_layout(pad=0.4)
out = os.path.join(FIG, "r4_9_vs_6.png")
fig.savefig(out, facecolor="white")
print("wrote", out)
