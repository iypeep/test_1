# -*- coding: utf-8 -*-
"""「读取方向测试」页的方向示意图：把 上/下/左/右/前/后 六个面与 3 个天线画在一起。

目的：让右侧实验表格的列（上/下/左/右/前/后）能一眼对上图 —— 颜色一致、面名直接标在图上。

面定义（沿用报告 §3）：
    前 = 防爆标签面（长×高）；后 = 条码 + 6 个序列号面（长×高）
    上/下 = 封箱带面（长×宽）；左/右 = 无标识侧面（宽×高）
机台：3 个 RFID 天线 —— ① 底（箱体下方，读取器朝上）② 侧（正面一侧）③ 顶（箱体上方）
测试方式：中箱以不同面朝下，贴到底部读取器上。

输出：09_报告/figs/fig_faces_axes.png
"""
import os
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle, Polygon, FancyArrowPatch, Arc
from matplotlib import font_manager as fm

_HERE = os.path.dirname(os.path.abspath(__file__))
REP = os.path.dirname(_HERE)
FIG = os.path.join(REP, "figs")

INK, GRAY, LIGHT = "#1A1A1A", "#8C8C8C", "#E8E8E8"
C = {"上": "#3E5DA8", "下": "#2E8B57", "左": "#C0504D",
     "右": "#D98C1F", "前": "#5C7ED4", "后": "#9E9E9E"}
fm.fontManager.addfont(r"C:\Windows\Fonts\msyh.ttc")
plt.rcParams["font.family"] = "Microsoft YaHei"
plt.rcParams["axes.unicode_minus"] = False


def box(ax, ox, oy, L, W, H, dx=0.55, dy=0.42):
    """等轴测立方体：前面(长×高) / 顶面(长×宽) / 右侧面(宽×高)"""
    front = [(ox, oy), (ox + L, oy), (ox + L, oy + H), (ox, oy + H)]
    top = [(ox, oy + H), (ox + L, oy + H), (ox + L + dx, oy + H + dy), (ox + dx, oy + H + dy)]
    right = [(ox + L, oy), (ox + L + dx, oy + dy), (ox + L + dx, oy + H + dy), (ox + L, oy + H)]
    ax.add_patch(Polygon(front, closed=True, facecolor=C["前"], alpha=0.16, edgecolor=C["前"], lw=1.4))
    ax.add_patch(Polygon(top, closed=True, facecolor=C["上"], alpha=0.16, edgecolor=C["上"], lw=1.4))
    ax.add_patch(Polygon(right, closed=True, facecolor=C["右"], alpha=0.18, edgecolor=C["右"], lw=1.4))
    # 隐藏边（虚线）
    for a, b in [((ox, oy), (ox + dx, oy + dy)), ((ox + dx, oy + dy), (ox + dx, oy + H + dy)),
                 ((ox + dx, oy + dy), (ox + L + dx, oy + dy))]:
        ax.plot([a[0], b[0]], [a[1], b[1]], ls=(0, (3, 2)), lw=0.9, color="#B9B9B9", zorder=1)
    return front, top, right


def antenna(ax, cx, cy, w, h, label, axis="up", color="#33475B"):
    ax.add_patch(Rectangle((cx - w / 2, cy - h / 2), w, h, facecolor="#F2F5F9", edgecolor=color, lw=1.2, zorder=3))
    ax.plot([cx - w / 2, cx + w / 2], [cy - h / 2, cy - h / 2], lw=2.2, color=color, zorder=4)
    for r in (0.10, 0.17, 0.24):
        if axis == "up":
            ax.add_patch(Arc((cx, cy + h / 2), r * 2, r * 2, theta1=20, theta2=160, color=color, lw=0.8, alpha=0.55))
        elif axis == "down":
            ax.add_patch(Arc((cx, cy - h / 2), r * 2, r * 2, theta1=200, theta2=340, color=color, lw=0.8, alpha=0.55))
        else:
            ax.add_patch(Arc((cx + w / 2, cy), r * 2, r * 2, theta1=-70, theta2=70, color=color, lw=0.8, alpha=0.55))
    ax.text(cx, cy - h / 2 - 0.16 if axis == "up" else cy + h / 2 + 0.10, label,
            ha="center", va="top" if axis == "up" else "bottom", fontsize=8.2, color=color)


def main():
    """只画“箱体六面 + 三面天线 + 颜色图例”，说明文字交给幻灯片。"""
    fig, ax = plt.subplots(figsize=(7.2, 3.0), dpi=220)
    ax.set_xlim(0, 7.62)
    ax.set_ylim(0, 3.0)
    ax.axis("off")

    ox, oy, L, W, H = 2.30, 1.02, 2.30, 1.22, 1.10
    dx, dy = 0.48, 0.34
    box(ax, ox, oy, L, W, H, dx, dy)

    ax.text(ox + L / 2, oy + H / 2, "前（防爆标签面）", ha="center", va="center",
            fontsize=9.6, color=C["前"], fontweight="bold")
    ax.text(ox + L / 2 + dx / 2, oy + H + dy / 2, "上（封箱带）", ha="center", va="center",
            fontsize=9.6, color=C["上"], fontweight="bold")
    ax.text(ox + L + dx * 0.55, oy + H * 0.40, "右", ha="center", va="center",
            fontsize=9.6, color=C["右"], fontweight="bold")

    ax.add_patch(FancyArrowPatch((ox + dx * 0.55, oy + H + dy * 0.55), (1.72, 2.80),
                                 arrowstyle="-|>", mutation_scale=9, lw=1.0, ls=(0, (3, 2)), color=C["后"]))
    ax.text(1.64, 2.80, "后（条码 + 6 个序列号）", fontsize=8.8, color=C["后"], fontweight="bold",
            ha="right", va="center")
    ax.add_patch(FancyArrowPatch((ox + 0.02, oy + H * 0.58), (1.30, 1.52),
                                 arrowstyle="-|>", mutation_scale=9, lw=1.0, ls=(0, (3, 2)), color=C["左"]))
    ax.text(1.22, 1.52, "左", fontsize=8.8, color=C["左"], fontweight="bold", ha="right", va="center")

    # ① 底部天线
    ax.add_patch(Rectangle((ox + L / 2 - 1.00, oy - 0.56), 2.00, 0.20, facecolor="#F2F5F9",
                           edgecolor="#1F4E5F", lw=1.1, zorder=3))
    for r in (0.10, 0.16, 0.22):
        ax.add_patch(Arc((ox + L / 2, oy - 0.36), r * 2, r * 2, theta1=20, theta2=160,
                         color="#1F4E5F", lw=0.8, alpha=0.5))
    ax.text(ox + L / 2, oy - 0.66, "① 底部天线（贴底读取器）", ha="center", va="top",
            fontsize=8.6, color="#1F4E5F")

    # ② 侧面天线
    ax.add_patch(Rectangle((ox - 0.70, oy + H / 2 - 0.55), 0.22, 1.10, facecolor="#F2F5F9",
                           edgecolor="#1F4E5F", lw=1.1, zorder=3))
    for r in (0.10, 0.16, 0.22):
        ax.add_patch(Arc((ox - 0.48, oy + H / 2), r * 2, r * 2, theta1=-70, theta2=70,
                         color="#1F4E5F", lw=0.8, alpha=0.5))
    ax.text(ox - 0.58, oy + H + 0.14, "② 侧面天线", ha="center", va="bottom", fontsize=8.6, color="#1F4E5F")

    # ③ 顶部天线
    ax.add_patch(Rectangle((ox + L / 2 + dx / 2 - 1.00, oy + H + dy + 0.42), 2.00, 0.20,
                           facecolor="#F2F5F9", edgecolor="#1F4E5F", lw=1.1, zorder=3))
    for r in (0.10, 0.16, 0.22):
        ax.add_patch(Arc((ox + L / 2 + dx / 2, oy + H + dy + 0.42), r * 2, r * 2, theta1=200, theta2=340,
                         color="#1F4E5F", lw=0.8, alpha=0.5))
    ax.text(ox + L / 2 + dx / 2, oy + H + dy + 0.70, "③ 顶部天线", ha="center", va="bottom",
            fontsize=8.6, color="#1F4E5F")

    # 图例（与表格列同色）
    vy, x = 0.06, 4.95
    for name in ["上", "下", "左", "右", "前", "后"]:
        ax.add_patch(Rectangle((x, vy), 0.36, 0.26, facecolor=C[name], edgecolor="none", alpha=0.92))
        ax.text(x + 0.18, vy + 0.13, name, ha="center", va="center", fontsize=8.4, color="white", fontweight="bold")
        x += 0.44

    fig.tight_layout(pad=0.1)
    out = os.path.join(FIG, "fig_faces_axes.png")
    fig.savefig(out, facecolor="white")
    print("wrote", out)


if __name__ == "__main__":
    main()
