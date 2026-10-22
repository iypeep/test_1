# -*- coding: utf-8 -*-
"""生成报告用图（风格对齐 风格参考示例.pdf：白底、黑字、灰阶 + 单一商务蓝强调）"""
import csv, os, json, collections, statistics
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib import font_manager as fm
from matplotlib.patches import Rectangle, FancyArrowPatch, FancyBboxPatch

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))  # 09_报告 的上一级
_HERE = os.path.dirname(os.path.abspath(__file__))
REP = os.path.dirname(_HERE)
ROOT = os.path.dirname(REP)
OUT = os.path.join(REP, "figs")
os.makedirs(OUT, exist_ok=True)

INK, GRAY, LIGHT, BAR = "#1A1A1A", "#8C8C8C", "#BFBFBF", "#C9C9C9"
ACCENT, ACCENT_L = "#3E5DA8", "#5C7ED4"

FONT = "Microsoft YaHei"
for cand in [r"C:\Windows\Fonts\msyh.ttc", r"C:\Windows\Fonts\msyhbd.ttc"]:
    if os.path.exists(cand):
        fm.fontManager.addfont(cand)
plt.rcParams["font.family"] = FONT
plt.rcParams["axes.unicode_minus"] = False

def style_ax(ax, grid=True):
    for s in ("top", "right"):
        ax.spines[s].set_visible(False)
    for s in ("left", "bottom"):
        ax.spines[s].set_color(LIGHT); ax.spines[s].set_linewidth(0.8)
    ax.tick_params(colors=INK, labelsize=9, length=0)
    if grid:
        ax.grid(axis="y", color="#ECECEC", linewidth=0.8)
        ax.set_axisbelow(True)

# ---------------------------------------------------------------- fig1: 30 天 EPC
rows = list(csv.DictReader(open(os.path.join(ROOT, "03_数据/epc_per_day_30d.csv"), encoding="utf-8-sig")))
rows.reverse()
labels = [f"{r['date'][4:6]}/{r['date'][6:8]}" for r in rows]
vals = [int(r["lines"]) / 1000 for r in rows]
notes = [r["note"] for r in rows]
is_stop = ["stopped-early" in n for n in notes]
is_today = ["today-last-line" in n for n in notes]
colors = [ACCENT if (s or t) else BAR for s, t in zip(is_stop, is_today)]

fig, ax = plt.subplots(figsize=(8.2, 2.9), dpi=220)
ax.bar(range(len(vals)), vals, color=colors, width=0.66)
med = statistics.median(vals)
ax.axhline(med, color=GRAY, lw=0.9, ls=(0, (4, 3)))
ax.text(len(vals) - 0.4, med + 8, f"中位 {med:.0f}k", color=GRAY, fontsize=8, ha="right")
ax.set_xticks(range(len(vals)))
ax.set_xticklabels([l if i % 2 == 0 else "" for i, l in enumerate(labels)], fontsize=8, color=GRAY)
ax.set_ylabel("EPC 日志行数（千行）", fontsize=9, color=INK)
ax.set_ylim(0, max(vals) * 1.26)
style_ax(ax)
stop_idx = [i for i, s in enumerate(is_stop) if s]
for n, i in enumerate(stop_idx):
    dy = 5 if n % 2 == 0 else 17
    ax.annotate("提前停摆", (i, vals[i]), xytext=(0, dy), textcoords="offset points",
                ha="center", fontsize=7, color=ACCENT, fontweight="bold")
ti = [i for i, t in enumerate(is_today) if t][0]
ax.annotate("今日 16:16 停摆", (ti, vals[ti]), xytext=(0, 5), textcoords="offset points",
            ha="center", fontsize=7, color=ACCENT, fontweight="bold")
fig.tight_layout(pad=0.3)
fig.savefig(os.path.join(OUT, "fig1_epc_30d.png"), facecolor="white")
plt.close(fig)
print("fig1 ok", len(stop_idx), "次 stopped-early")

# ---------------------------------------------------------------- fig2: 天线/RSSI
recs = collections.defaultdict(lambda: {"n": 0, "rssi": [], "ant": collections.Counter()})
for line in open(os.path.join(ROOT, "02_日志/rfidmon_records-20261021.jsonl"), encoding="utf-8", errors="replace"):
    line = line.strip()
    if not line:
        continue
    try:
        o = json.loads(line)
    except Exception:
        continue
    k = o.get("ascii") or o.get("epc")
    recs[k]["n"] += 1
    if isinstance(o.get("rssi"), (int, float)):
        recs[k]["rssi"].append(o["rssi"])
    recs[k]["ant"][o.get("ant")] += 1
tags = [k for k, v in recs.items() if v["n"] > 100]
tags.sort(key=lambda t: -recs[t]["n"])
ants = [1, 3, 4]
fig, ax = plt.subplots(figsize=(4.5, 2.9), dpi=220)
w = 0.34
for j, t in enumerate(tags):
    tot = sum(recs[t]["ant"].values())
    hs = [100.0 * recs[t]["ant"].get(a, 0) / tot for a in ants]
    ax.bar([i + (j - 0.5) * w for i in range(len(ants))], hs, width=w,
           color=ACCENT if j == 0 else BAR, label=t)
ax.set_xticks(range(len(ants)))
ax.set_xticklabels([f"天线 {a}" for a in ants], fontsize=9, color=INK)
ax.set_ylabel("命中占比（%）", fontsize=9, color=INK)
ax.set_ylim(0, 62)
ax.legend(frameon=False, fontsize=8, loc="upper center", ncol=2, bbox_to_anchor=(0.5, 1.18))
style_ax(ax)
fig.tight_layout(pad=0.3)
fig.savefig(os.path.join(OUT, "fig2_antenna.png"), facecolor="white")
plt.close(fig)
print("fig2 ok", {t: (recs[t]["n"], round(min(recs[t]['rssi']),1), round(max(recs[t]['rssi']),1)) for t in tags})

# ---------------------------------------------------------------- fig3: 箱体六面展开
fig, ax = plt.subplots(figsize=(7.6, 3.6), dpi=220)
ax.set_xlim(0, 12.6); ax.set_ylim(0, 7.0); ax.axis("off")
W, H, SW = 3.2, 2.4, 1.9      # 长 × 高，宽
x0, y0 = 1.5, 2.55
faces = {                      # 外表面看：正面 → 右 → 背 → 左
    "F-FRONT": (x0, y0, W, H, "正面  F-FRONT", "防爆标识"),
    "S-RIGHT": (x0 + W, y0, SW, H, "侧面 S-RIGHT", "仅物流标"),
    "F-BACK":  (x0 + W + SW, y0, W, H, "背面  F-BACK", "箱体条码 + 6 个整机序列号"),
    "S-LEFT":  (x0 + W + SW + W, y0, SW, H, "侧面 S-LEFT", "无标识"),
}
for k, (x, y, w, h, name, sub) in faces.items():
    key_face = k in ("F-FRONT", "F-BACK")
    ax.add_patch(Rectangle((x, y), w, h, facecolor="#F1F3F7" if key_face else "#FCFCFC",
                           edgecolor=INK if key_face else "#8C8C8C",
                           linewidth=1.2 if key_face else 0.8))
    ax.text(x + w/2, y + h/2 + 0.3, name, ha="center", va="center", fontsize=9,
            color=INK, fontweight="bold" if key_face else "normal")
    ax.text(x + w/2, y + h/2 - 0.38, sub, ha="center", va="center", fontsize=7.6,
            color=ACCENT if key_face else "#595959", fontweight="bold" if key_face else "normal")
# 顶面 / 底面（挂在正面上下）
ax.add_patch(Rectangle((x0, y0 + H), W, SW, facecolor="#FCFCFC", edgecolor="#8C8C8C", linewidth=0.8))
ax.text(x0 + W/2, y0 + H + SW/2, "顶面 T-TOP · 封箱带", ha="center", va="center", fontsize=8, color="#595959")
ax.add_patch(Rectangle((x0, y0 - SW), W, SW, facecolor="#E6EDF9", edgecolor=ACCENT, linewidth=1.3))
ax.text(x0 + W/2, y0 - SW/2, "底面 B-BOTTOM · 封箱带", ha="center", va="center", fontsize=8,
        color=ACCENT, fontweight="bold")
# 读码器示意（A1 产线姿态：箱体正立、底面朝下、读码器在下）
ax.add_patch(FancyBboxPatch((x0 + W/2 - 0.5, y0 - SW - 1.15), 1.0, 0.44,
                            boxstyle="round,pad=0.02,rounding_size=0.06", facecolor=INK, edgecolor="none"))
ax.annotate("", xy=(x0 + W/2, y0 - SW - 0.08), xytext=(x0 + W/2, y0 - SW - 0.66),
            arrowprops=dict(arrowstyle="-|>", color=ACCENT, lw=1.4))
ax.text(x0 + W/2, y0 - SW - 1.55,
        "读码器天线朝向 —— A1 产线姿态：箱体正立、底面朝下、读码器在箱体下方\n"
        "（整机 RFID 标签在箱内机器上，不贴箱面）",
        ha="center", va="top", fontsize=8, color=INK, linespacing=1.5)
# 尺寸标注
ax.annotate("", xy=(x0, y0 + H + SW + 0.32), xytext=(x0 + W, y0 + H + SW + 0.32),
            arrowprops=dict(arrowstyle="<|-|>", color=ACCENT, lw=0.9))
ax.text(x0 + W/2, y0 + H + SW + 0.5, "长", ha="center", fontsize=8, color=ACCENT)
ax.annotate("", xy=(x0 - 0.4, y0), xytext=(x0 - 0.4, y0 + H),
            arrowprops=dict(arrowstyle="<|-|>", color=ACCENT, lw=0.9))
ax.text(x0 - 0.68, y0 + H/2, "高", ha="center", va="center", rotation=90, fontsize=8, color=ACCENT)
ax.annotate("", xy=(x0 + W, y0 + H + 0.3), xytext=(x0 + W + SW, y0 + H + 0.3),
            arrowprops=dict(arrowstyle="<|-|>", color=ACCENT, lw=0.9))
ax.text(x0 + W + SW/2, y0 + H + 0.12, "宽", ha="center", va="top", fontsize=8, color=ACCENT)
ax.text(0.2, 6.7, "正面与背面同为“长 × 高”，肉眼最易混 → 每张照片先贴 F-FRONT / F-BACK 面标再拍",
        fontsize=8.4, color="#595959")
fig.tight_layout(pad=0.25)
fig.savefig(os.path.join(OUT, "fig3_box_faces.png"), facecolor="white")
plt.close(fig)
print("fig3 ok")
