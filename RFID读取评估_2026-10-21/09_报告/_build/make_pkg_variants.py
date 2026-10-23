# -*- coding: utf-8 -*-
"""包装机型口径（2026-10-23 经理口径）：按「背壳材质 × 外壳形态」四象限重切。

经理（钟慧玲）口径：
  * 分析单元是**包装机型**，不是 RFID 厂家 —— 厂家差异已与包装机型混在一起，必须按包装机型分组；
  * 金属背壳版：RFID 标签贴在中框（mid-frame）上；塑料背壳版：直接贴在背壳上；
  * KKE = 带卡通保护壳（tablet + 卡通壳一起包装）；N-KKE = 只有平板本身。

四象限（机型无关的包装口径）：
    N-KKE · 塑料   标签在背壳，正对底面，只有瓦楞纸 + 塑料背壳
    KKE   · 塑料   同上，外面多一层卡通保护壳（TPU/PC + 空气间隙）
    N-KKE · 金属   标签在中框，正下方被金属背壳屏蔽；底面照射基本无效，只能侧向读
    KKE   · 金属   金属屏蔽 + 卡通壳

⚠️ 全部数字仍是「手册参数 + 参数化模型」的预测值（本模型常数与 sim_model.MODEL 一致，
   见 §9 与 _sim/模型假设.json），不是实测。用途是把「按包装机型分组」先立成口径与表结构，
   等现场按同口径填数后一键替换。

输出：
    09_报告/_sim/G_包装机型_模拟.csv
    09_报告/figs/fig14_pkg_variants.png
"""
import os, csv, math, random

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib import font_manager as fm

_HERE = os.path.dirname(os.path.abspath(__file__))
REP = os.path.dirname(_HERE)
SIM = os.path.join(REP, "_sim")
FIG = os.path.join(REP, "figs")
os.makedirs(SIM, exist_ok=True)
os.makedirs(FIG, exist_ok=True)

INK, GRAY, BAR, ACCENT, ACCENT_L = "#1A1A1A", "#8C8C8C", "#D9D9D9", "#3E5DA8", "#7F97C4"
RED = "#C0504D"
fm.fontManager.addfont(r"C:\Windows\Fonts\msyh.ttc")
plt.rcParams["font.family"] = "Microsoft YaHei"
plt.rcParams["axes.unicode_minus"] = False

# ---------------------------------------------------------------- 模型常数（与 sim_model.MODEL 一致）
MODEL = {
    "rssi_ref": -41.0,   # dBm：6 dBi / 下置 / 瓦楞纸面 / A 厂 / 5 cm 参考点
    "d_ref": 0.05,       # m
    "d_min": 0.02,       # m
    "rssi_th": -62.0,    # dBm
    "sigma": 2.0,        # dB
    "tag_spread": 4.0,   # dB
    "gain": {9: 3.0, 6: 0.0},
    "rate_base": 26.0,   # tags/s
    "seed": 20261022,
    "face_loss": {"B-BOTTOM": 3.5, "S-LEFT": 8.0},
}
random.seed(MODEL["seed"])
TAG_OFFSETS = [random.gauss(0, MODEL["tag_spread"]) for _ in range(6)]

# ---------------------------------------------------------------- 包装机型四象限（假设值，实测替换）
# loss_bottom / loss_side = 相对「塑料背壳 · N-KKE · 下置」的附加损耗（dB）
# 依据：金属背壳屏蔽 13 dB（与 _sim/E_箱型对比_模拟.csv 的 7907-M 同源）；
#       卡通保护壳 ≈ +2.5 dB（TPU/PC 层 + 约 1 mm 间隙，实测两枚常驻标签差 17 dB 属量级参考）。
PKG = {
    "N-KKE": {"name": "N-KKE", "note": "只有平板本身"},
    "KKE": {"name": "KKE", "note": "带卡通保护壳"},
}
SHELL = {
    "塑料": {"tag": "背壳", "loss_bottom": 0.0, "loss_side": 4.5,
             "why": "标签在背壳、正对底面：只有瓦楞纸 + 塑料背壳"},
    "金属": {"tag": "中框", "loss_bottom": 13.0, "loss_side": 1.5,
             "why": "标签在中框：正下方被金属背壳屏蔽，只能靠侧面开口/边缘绕射"},
}
CASE_LOSS = 2.5          # 卡通保护壳（仅 KKE）
BIG_EXTRA = 3.5          # 大件（AX8252 7″ vs AX7907 6″）附加，同 E_箱型对比


def rssi(d_m, gain, face, extra):
    d = max(d_m, MODEL["d_min"])
    return (MODEL["rssi_ref"] + MODEL["gain"][gain]
            - 20.0 * math.log10(d / MODEL["d_ref"])
            - MODEL["face_loss"][face] - extra)


def p_read(r):
    return 1.0 / (1.0 + math.exp((MODEL["rssi_th"] - r) / MODEL["sigma"]))


def readout(d_m, gain, face, extra):
    """解析期望值：Σ_{6 个标签} p(rssi + tag_offset_i)，不抽样（消除抽样噪声，
    与 sim_model.measure 的 9 次取样只差 ±0.5，口径相同）"""
    r0 = rssi(d_m, gain, face, extra)
    return round(sum(p_read(r0 + o) for o in TAG_OFFSETS), 2), round(r0, 1)


rows = []
for case in ("N-KKE", "KKE"):
    for shell in ("塑料", "金属"):
        sh = SHELL[shell]
        case_loss = CASE_LOSS if case == "KKE" else 0.0
        b_extra = sh["loss_bottom"] + case_loss
        s_extra = sh["loss_side"] + case_loss
        b, b_rssi = readout(0.10, 9, "B-BOTTOM", b_extra)
        sid, s_rssi = readout(0.10, 9, "S-LEFT", s_extra)
        big_b, _ = readout(0.10, 9, "B-BOTTOM", b_extra + BIG_EXTRA)
        big_s, _ = readout(0.10, 9, "S-LEFT", s_extra + BIG_EXTRA)
        rows.append({
            "包装机型": f"{case}-{shell}",
            "外壳": case, "背壳": shell, "标签位置": sh["tag"],
            "下置_附加损耗_dB": round(b_extra, 1),
            "下置_读全_6": b,
            "下置_RSSI_dBm": b_rssi,
            "侧向_附加损耗_dB": round(s_extra, 1),
            "侧向_读全_6": sid,
            "侧向_RSSI_dBm": s_rssi,
            "大件_8252_下置_读全_6": big_b,
            "大件_8252_侧向_读全_6": big_s,
            "判别依据": sh["why"],
        })

out_csv = os.path.join(SIM, "G_包装机型_模拟.csv")
with open(out_csv, "w", newline="", encoding="utf-8-sig") as f:
    w = csv.DictWriter(f, fieldnames=list(rows[0]))
    w.writeheader(); w.writerows(rows)
print("wrote", out_csv)
for r in rows:
    print(f"  {r['包装机型']:<10} 下置 {r['下置_读全_6']:.2f} / 侧向 {r['侧向_读全_6']:.2f}  (大件 8252: "
          f"{r['大件_8252_下置_读全_6']:.2f} / {r['大件_8252_侧向_读全_6']:.2f})")

# ---------------------------------------------------------------- 图：四包装机型 × 两种照射方向
labels = [r["包装机型"] for r in rows]
tags = [r["标签位置"] for r in rows]
bot = [r["下置_读全_6"] for r in rows]
sid = [r["侧向_读全_6"] for r in rows]

fig, ax = plt.subplots(figsize=(7.4, 3.5), dpi=220)
w = 0.34
x = list(range(len(labels)))
b1 = ax.bar([i - w / 2 for i in x], bot, w, color=ACCENT, label="下置天线（9 dBi / 箱面 10 cm）")
b2 = ax.bar([i + w / 2 for i in x], sid, w, color=ACCENT_L, label="侧向天线（9 dBi / 箱面 10 cm）")
for bars in (b1, b2):
    for bar in bars:
        v = bar.get_height()
        ax.text(bar.get_x() + bar.get_width() / 2, v + 0.12, f"{v:.2f}",
                ha="center", fontsize=9.2, color=INK, fontweight="bold")
ax.axhline(5.4, color="#B0B0B0", lw=0.9, ls=(0, (4, 3)))
ax.text(0.28, 5.52, "可用线 5.4/6", fontsize=7.8, color=GRAY, ha="left")
ax.set_xticks(x)
ax.set_xticklabels([f"{l}\n标签：{t}" for l, t in zip(labels, tags)], fontsize=8.6, color=INK)
ax.set_ylim(0, 6.8)
ax.set_ylabel("每箱读全数（/6，模型预测）", fontsize=9.2, color=INK)
for sp in ("top", "right"):
    ax.spines[sp].set_visible(False)
ax.grid(axis="y", color="#ECECEC", lw=0.8); ax.set_axisbelow(True)
ax.tick_params(colors=INK, labelsize=8.6, length=0)
ax.legend(frameon=False, fontsize=8.2, loc="upper right", ncol=1)
fig.tight_layout(pad=0.35)
out_png = os.path.join(FIG, "fig14_pkg_variants.png")
fig.savefig(out_png, facecolor="white")
plt.close(fig)
print("wrote", out_png)
