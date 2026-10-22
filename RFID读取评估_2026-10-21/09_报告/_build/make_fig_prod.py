# -*- coding: utf-8 -*-
"""产线实测读取图（fig13）：数据来自 03_数据/prod_readout_20260922_20261022.csv
   与 03_数据/remote/*.tsv（由 07_方法/prod/extract-*.ps1 从机台日志抽出）

用法：python make_fig_prod.py
输出：../figs/fig13_prod_readout.png
"""
import os, csv
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib import font_manager as fm

_HERE = os.path.dirname(os.path.abspath(__file__))
REP = os.path.dirname(_HERE)
ROOT = os.path.dirname(REP)
FIG = os.path.join(REP, "figs")
CSV = os.path.join(ROOT, "03_数据", "prod_readout_20260922_20261022.csv")

INK, GRAY, BAR, ACCENT, ACCENT_L = "#1A1A1A", "#8C8C8C", "#D9D9D9", "#3E5DA8", "#7F97C4"
fm.fontManager.addfont(r"C:\Windows\Fonts\msyh.ttc")
plt.rcParams["font.family"] = "Microsoft YaHei"
plt.rcParams["axes.unicode_minus"] = False

rows = list(csv.DictReader(open(CSV, encoding="utf-8-sig")))
days = [r["day"][4:6] + "-" + r["day"][6:] for r in rows]
boxes = [int(r["boxes"]) for r in rows]
tag_pct = [float(r["boxes_with_tag_pct"]) for r in rows]
true_pct = [float(r["true_pct"]) for r in rows]

fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(9.6, 3.3), dpi=220,
                               gridspec_kw={"width_ratios": [2.05, 1]})

# ---------------- 左：每日箱数 + 两个比率
x = range(len(days))
ax1.bar(x, boxes, color=BAR, width=0.68, label="当日箱数（左轴）")
ax1.set_ylim(0, max(boxes) * 1.28)
ax1.set_ylabel("箱数 / 日", fontsize=9.5, color=INK)
ax1.set_xticks(list(x))
ax1.set_xticklabels(days, fontsize=7.2, rotation=90, color=INK)
ax1.tick_params(colors=INK, labelsize=8, length=0)
for s in ("top", "right"):
    ax1.spines[s].set_visible(False)
ax1.grid(axis="y", color="#EFEFEF", lw=0.8)
ax1.set_axisbelow(True)

ax1b = ax1.twinx()
ax1b.plot(list(x), tag_pct, "-o", ms=3.2, lw=1.6, color=ACCENT, label="窗口内读到≥1 标签的箱占比")
ax1b.plot(list(x), true_pct, "-s", ms=3.0, lw=1.3, color="#C0504D", label="程序 readStatus=True 占比")
ax1b.set_ylim(0, max(max(tag_pct), max(true_pct)) * 1.35)
ax1b.set_ylabel("占比（%）", fontsize=9.5, color=INK)
ax1b.tick_params(colors=INK, labelsize=8, length=0)
for s in ("top",):
    ax1b.spines[s].set_visible(False)

h1, l1 = ax1.get_legend_handles_labels()
h2, l2 = ax1b.get_legend_handles_labels()
ax1.legend(h1 + h2, l1 + l2, frameon=False, fontsize=7.6, loc="upper left", ncol=1)

# ---------------- 右：每箱读到几个（31 天合计）
dist = {0: 108017, 1: 3997, 2: 972, 3: 158, 4: 217, 5: 148, 6: 158}
total = sum(dist.values())
ks = list(range(7))
vals = [dist[k] for k in ks]
cols = [BAR] + [ACCENT_L] * 5 + [ACCENT]
ax2.bar(ks, vals, color=cols, width=0.62)
ax2.set_yscale("log")
ax2.set_ylim(1, max(vals) * 3)
for k, v in zip(ks, vals):
    ax2.text(k, v * 1.32, f"{v:,}", ha="center", fontsize=7.4, color=INK)
ax2.set_xticks(ks)
ax2.set_xticklabels([str(k) for k in ks], fontsize=9, color=INK)
ax2.set_xlabel("该箱处理窗口内读到的整机标签数（个）", fontsize=9, color=INK)
ax2.set_ylabel("箱数（对数轴）", fontsize=9.5, color=INK)
ax2.tick_params(colors=INK, labelsize=8, length=0)
for s in ("top", "right"):
    ax2.spines[s].set_visible(False)
ax2.grid(axis="y", color="#EFEFEF", lw=0.8)
ax2.set_axisbelow(True)
ax2.set_title(f"31 天 {total:,} 箱：95.0% 一箱 0 个", fontsize=9.2, color=INK, pad=6)

fig.tight_layout(pad=0.4)
out = os.path.join(FIG, "fig13_prod_readout.png")
fig.savefig(out, facecolor="white")
print("wrote", out)
