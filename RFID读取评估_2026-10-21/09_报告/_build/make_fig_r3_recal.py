# -*- coding: utf-8 -*-
"""R3 距离曲线：按现场实测重新标定（旧模型 5 cm 读全 6/6 → 实测 0.08/6）

标定口径（写进报告/PPT 必须一致）：
  * 现场几何：3 个 RFID 天线（底 / 侧 / 顶），天线面到箱面均 < 5 cm；
  * 实测锚点：31 天 113,667 箱，平均每箱读到 0.079 个整机标签（95.0% 为 0）；
  * 把「箱内负载 + 多台金属件遮挡 + 极化/朝向 + 过板窗口」的综合损耗 28.6 dB 补进模型，
    使 5 cm 处的期望读数落到 0.08/6；
  * d_min 抬到 5 cm：现场已压到底，0–5 cm 视为同一档，不对更近场做外推。

输出：
  09_报告/figs/fig7r_distance_recal.png
  09_报告/_sim/R3_距离_标定.csv
"""
import os, csv, math, random, statistics

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib import font_manager as fm

_HERE = os.path.dirname(os.path.abspath(__file__))
REP = os.path.dirname(_HERE)
SIM, FIG = os.path.join(REP, "_sim"), os.path.join(REP, "figs")

INK, GRAY, LIGHT, ACCENT, RED = "#1A1A1A", "#8C8C8C", "#BFBFBF", "#3E5DA8", "#C0504D"
fm.fontManager.addfont(r"C:\Windows\Fonts\msyh.ttc")
plt.rcParams["font.family"] = "Microsoft YaHei"
plt.rcParams["axes.unicode_minus"] = False

REF, TH, SIG, GAIN9, DSCALE = -41.0, -62.0, 2.0, 3.0, 0.05
FACE = {"下": 3.5, "上": 4.0, "正面侧": 10.0, "背面侧": 12.0}
CAL = 28.6            # 实测标定：综合附加损耗 dB
DMIN = 0.05           # 0–5 cm 视为同一档
MEASURED = 0.079      # 31 天实测均值（113,667 箱）
MEASURED_ZERO = 95.0  # 一箱读到 0 个的占比

random.seed(20261022)
OFFS = [random.gauss(0, 4.0) for _ in range(6)]
DISTS = [5, 10, 20, 30, 50]


def p_hit(r, rssi_th=TH, sigma=SIG):
    return 1.0 / (1.0 + math.exp((rssi_th - r) / sigma))


def r0(d_cm, pos, cal):
    d = max(d_cm / 100.0, DMIN)
    return REF + GAIN9 - FACE[pos] - 20.0 * math.log10(d / DSCALE) - cal


def box_expect(d_cm, pos, cal):
    r = r0(d_cm, pos, cal)
    return sum(p_hit(r + o) for o in OFFS)


def box_count(d_cm, pos, cal):
    """与原 sim_model.measure() 同口径：9 次取样（3 箱 × 3 次）、每标签 0.8 dB 读噪声，取均值"""
    r = r0(d_cm, pos, cal)
    per = []
    for _ in range(9):
        cnt = 0
        for off in OFFS:
            if random.random() < p_hit(r + off + random.gauss(0, 0.8)):
                cnt += 1
        per.append(cnt)
    return statistics.mean(per)


def main():
    rows = []
    # 旧模型：直接读同目录 _sim/B_距离_9dBi_模拟.csv，保证与现有 PPT 数字一致
    src = os.path.join(SIM, "B_距离_9dBi_模拟.csv")
    old_curve = {}
    if os.path.exists(src):
        for r in csv.DictReader(open(src, encoding="utf-8-sig")):
            try:
                old_curve[(r["位置"], int(float(r["距离_cm"])))] = float(r["读全数_6"])
            except (KeyError, ValueError):
                pass
    for pos in FACE:
        for d in DISTS:
            old_curve.setdefault((pos, d), box_count(d, pos, 0.0))
    # 标定后：解析期望（平滑，适合画曲线）
    new_curve = {(pos, d): box_expect(d, pos, CAL) for pos in FACE for d in DISTS}
    for pos in FACE:
        for d in DISTS:
            old = round(old_curve[(pos, d)], 2)
            new = round(new_curve[(pos, d)], 3)
            rows.append({"位置": pos, "距离_cm": d, "旧模型_读全_6": old,
                         "标定后_读全_6": new,
                         "单标签命中率_%": round(100 * p_hit(r0(d, pos, CAL)), 2)})
    os.makedirs(SIM, exist_ok=True)
    out = os.path.join(SIM, "R3_距离_标定.csv")
    with open(out, "w", newline="", encoding="utf-8-sig") as fh:
        w = csv.DictWriter(fh, fieldnames=list(rows[0]))
        w.writeheader()
        w.writerows(rows)
    print("wrote", out)

    fig, ax = plt.subplots(figsize=(7.4, 3.6), dpi=220)
    colors = {"下": ACCENT, "上": "#5C7ED4", "正面侧": "#8C8C8C", "背面侧": "#C0C0C0"}

    # 旧模型：灰虚线（4 个位置）
    for pos in FACE:
        ys_old = [old_curve[(pos, d)] for d in DISTS]
        ax.plot(DISTS, ys_old, ls=(0, (4, 3)), lw=1.2, color=LIGHT, zorder=1)
    ax.text(6, 6.22, "旧模型（无标定）：5 cm 读全 6/6", fontsize=8.4, color="#9A9A9A")

    # 标定后：贴在 0 附近（主图只示意，细节看插图）
    for pos in FACE:
        ys = [new_curve[(pos, d)] for d in DISTS]
        ax.plot(DISTS, ys, "-o", ms=4.0, lw=1.8, color=colors[pos], label=f"标定后 · {pos}", zorder=4)

    ax.axhline(5.4, color="#B0B0B0", lw=0.9, ls=(0, (4, 3)))
    ax.text(50, 5.52, "旧口径「可用」5.4/6", fontsize=7.8, color=GRAY, ha="right")

    ax.scatter([5], [MEASURED], s=60, color=RED, zorder=6, marker="D")
    ax.annotate(f"实测：31 天 113,667 箱\n平均 {MEASURED:.2f}/6，{MEASURED_ZERO:.1f}% 一箱 0 个",
                xy=(5, MEASURED), xytext=(12, 1.35), fontsize=8.6, color=RED,
                arrowprops=dict(arrowstyle="->", color=RED, lw=1.0), zorder=6)

    ax.set_xlim(0, 52)
    ax.set_ylim(0, 6.7)
    ax.set_xlabel("读码器天线面到箱面的距离（cm）—— 现场三面天线均 < 5 cm", fontsize=9.2, color=INK)
    ax.set_ylabel("每箱读到的整机标签数（/6）", fontsize=9.2, color=INK)
    for sp in ("top", "right"):
        ax.spines[sp].set_visible(False)
    ax.grid(axis="y", color="#ECECEC", lw=0.8)
    ax.set_axisbelow(True)
    ax.tick_params(colors=INK, labelsize=8.6, length=0)
    ax.legend(frameon=False, fontsize=7.6, ncol=2, loc="lower left", bbox_to_anchor=(0.005, 0.02))

    # 插图：标定后的真实量级
    axi = ax.inset_axes([0.47, 0.30, 0.45, 0.33])
    for pos in FACE:
        ys = [new_curve[(pos, d)] * 100 for d in DISTS]
        axi.plot(DISTS, ys, "-o", ms=3.0, lw=1.5, color=colors[pos])
    axi.scatter([5], [MEASURED * 100], s=34, color=RED, marker="D", zorder=5)
    axi.set_xlim(0, 52)
    axi.set_ylim(0, 10)
    axi.set_title("标定后（放大 100×：数值＝每箱读到个数 ×100）", fontsize=7.2, color=INK, pad=3)
    axi.tick_params(labelsize=6.6, colors=INK, length=0)
    for sp in ("top", "right"):
        axi.spines[sp].set_visible(False)
    axi.grid(axis="y", color="#F2F2F2", lw=0.6)

    fig.tight_layout(pad=0.35)
    fp = os.path.join(FIG, "fig7r_distance_recal.png")
    fig.savefig(fp, facecolor="white")
    print("wrote", fp)

    for r in rows:
        if r["位置"] == "下":
            print(r)


if __name__ == "__main__":
    main()
