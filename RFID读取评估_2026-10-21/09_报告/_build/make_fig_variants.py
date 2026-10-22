# -*- coding: utf-8 -*-
"""重出 fig11_variants.png：R6 六种箱型（预测），代号按机型口径重命名

代号口径（2026-10-22 更正）：
    7907-P  AX7907 · Prosecco/Marsala · 6" e-reader · 塑料背壳
    8252-P  AX8252 · Amaro/Julep      · 7" e-reader · 塑料背壳
    7907-M  AX7907 · 6" · 金属背壳
    8252-M  AX8252 · 7" · 金属背壳
    7771-M  AX7771 · Roselite         · 8" tablet  · 金属背壳
    7513-M  AX7513 · Turquoise        · 11" tablet · 金属背壳
旧代号 KD-SP/KD-LP/KD-SM/KD-LM/PT-SM/PT-LM 与「Kinder」作废（机台日志从未出现）。

输入：09_报告/_sim/E_箱型对比_模拟.csv（数值不变，仅改标签）
输出：09_报告/figs/fig11_variants.png
"""
import os, csv
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib import font_manager as fm

_HERE = os.path.dirname(os.path.abspath(__file__))
REP = os.path.dirname(_HERE)
SIM = os.path.join(REP, "_sim")
FIG = os.path.join(REP, "figs")

INK, BAR, ACCENT, ACCENT_L = "#1A1A1A", "#D9D9D9", "#3E5DA8", "#7F97C4"
fm.fontManager.addfont(r"C:\Windows\Fonts\msyh.ttc")
plt.rcParams["font.family"] = "Microsoft YaHei"
plt.rcParams["axes.unicode_minus"] = False

# 旧代号 → (新代号, 两行标签)
RENAME = {
    "KD-SP": ("7907-P", "7907-P", "AX7907\n6″ · 塑料"),
    "KD-LP": ("8252-P", "8252-P", "AX8252\n7″ · 塑料"),
    "KD-SM": ("7907-M", "7907-M", "AX7907\n6″ · 金属"),
    "KD-LM": ("8252-M", "8252-M", "AX8252\n7″ · 金属"),
    "PT-SM": ("7771-M", "7771-M", "AX7771\n8″ tablet · 金属"),
    "PT-LM": ("7513-M", "7513-M", "AX7513\n11″ tablet · 金属"),
}


def main():
    rows = list(csv.DictReader(open(os.path.join(SIM, "E_箱型对比_模拟.csv"), encoding="utf-8-sig")))
    codes = [RENAME[r["代号"]][1] if r["代号"] in RENAME else r["代号"] for r in rows]
    labels = [RENAME[r["代号"]][2] if r["代号"] in RENAME else r["描述"] for r in rows]
    vals = [float(r["读全数_6"]) for r in rows]
    cols = [ACCENT if v >= 5.4 else (ACCENT_L if v >= 2.5 else BAR) for v in vals]

    fig, ax = plt.subplots(figsize=(7.2, 3.25), dpi=220)
    ax.bar(range(len(vals)), vals, color=cols, width=0.6)
    for i, v in enumerate(vals):
        ax.text(i, v + 0.1, f"{v:.2f}", ha="center", fontsize=9.5, color=INK, fontweight="bold")
    ax.set_xticks(range(len(vals)))
    ax.set_xticklabels([c + "\n" + l for c, l in zip(codes, labels)], fontsize=8.0, color=INK)
    ax.set_ylim(0, 6.7)
    ax.axhline(5.4, color="#B0B0B0", lw=0.9, ls=(0, (4, 3)))
    for s in ("top", "right"):
        ax.spines[s].set_visible(False)
    ax.grid(axis="y", color="#ECECEC", lw=0.8)
    ax.set_axisbelow(True)
    ax.tick_params(colors=INK, labelsize=9, length=0)
    ax.set_ylabel("每箱读全数（/6）", fontsize=9.5, color=INK)
    fig.tight_layout(pad=0.4)
    out = os.path.join(FIG, "fig11_variants.png")
    fig.savefig(out, facecolor="white")
    print("wrote", out)


if __name__ == "__main__":
    main()
