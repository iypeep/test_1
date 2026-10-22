# -*- coding: utf-8 -*-
"""测量结果框架 + 参数化预测模型

目的：
  1) 用**透明可改的模型**生成“如果明天测出来是这样”的结果表与曲线，作为填表与评审的骨架；
  2) 明天现场按模板填数后，改读 CSV 即可替换（本脚本同时导空模板）。

⚠️ 本脚本产出的一切数字都是 **模型预测（模拟值）**，不是实测值。报告里必须标 _sim。
"""
import os, csv, json, math, random, statistics
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib import font_manager as fm

_HERE = os.path.dirname(os.path.abspath(__file__))
REP = os.path.dirname(_HERE)
ROOT = os.path.dirname(REP)
SIM = os.path.join(REP, "_sim")
TPL = os.path.join(ROOT, "10_实测框架")
FIG = os.path.join(REP, "figs")
for d in (SIM, TPL, FIG):
    os.makedirs(d, exist_ok=True)

INK, GRAY, LIGHT, BAR = "#1A1A1A", "#8C8C8C", "#BFBFBF", "#C9C9C9"
ACCENT, ACCENT_L, ACCENT_2 = "#3E5DA8", "#5C7ED4", "#2E8B57"
fm.fontManager.addfont(r"C:\Windows\Fonts\msyh.ttc")
plt.rcParams["font.family"] = "Microsoft YaHei"
plt.rcParams["axes.unicode_minus"] = False

# ============================================================ 模型参数（全部可改）
MODEL = {
    "rssi_ref": -41.0,      # dBm：6 dBi / 下置 / 瓦楞纸面 / 厂家A / 5 cm 参考点
    "d_ref": 0.05,          # m
    "d_min": 0.02,          # m，等效最近距离（天线面紧贴箱面）
    "rssi_th": -62.0,       # dBm：判定“可靠读到”的门限（含产线多径/金属环境）
    "sigma": 2.0,           # dB：门限附近的不确定度
    "tag_spread": 4.0,      # dB：箱内 6 台位置/朝向差异的标准差（实测两枚标签差 17 dB）
    "gain": {6: 0.0, 9: 3.0},                    # dBi 差 3 dB
    "vendor": {"A-Impinj体系": 0.0, "B-国产方案": -2.0},
    # 面损耗 = 材料穿透 + 极化/入射失配（侧面照射时标签长轴与天线电场正交，实测可丢 6–10 dB）
    "face_loss": {"B-BOTTOM": 3.5, "T-TOP": 4.0, "F-FRONT": 10.0, "F-BACK": 12.0,
                  "F-FRONT_DOWN": 5.0, "F-BACK_DOWN": 6.0,
                  "S-LEFT_DOWN": 4.5, "S-RIGHT_DOWN": 4.5,
                  "S-LEFT": 8.0, "S-RIGHT": 8.0},
    "rate_base": 26.0,      # tags/s 基准（读取率）
    "seed": 20261022,
}
random.seed(MODEL["seed"])
TAG_OFFSETS = [random.gauss(0, MODEL["tag_spread"]) for _ in range(6)]


def rssi(d_m, gain, vendor, face):
    d = max(d_m, MODEL["d_min"])
    path = -20.0 * math.log10(d / MODEL["d_ref"])
    return (MODEL["rssi_ref"] + MODEL["gain"][gain] + MODEL["vendor"][vendor]
            + path - MODEL["face_loss"][face])


def p_read(r):
    return 1.0 / (1.0 + math.exp((MODEL["rssi_th"] - r) / MODEL["sigma"]))


def measure(d_m, gain, vendor, face, repeats=3):
    """返回 (读全数均值/6, 达标箱数, 读取率 tags/s, RSSI 均值)"""
    r0 = rssi(d_m, gain, vendor, face)
    per_box = []
    for _ in range(repeats * 3):                      # 9 次取样（3 箱 × 3 次）
        cnt = 0
        for off in TAG_OFFSETS:
            r = r0 + off + random.gauss(0, 0.8)
            p = p_read(r)
            if random.random() < p:
                cnt += 1
        per_box.append(cnt)
    boxes = [statistics.mean(per_box[i::3]) for i in range(3)]
    full = sum(1 for b in boxes if b >= 5.99)
    mean_cnt = statistics.mean(per_box)
    rate = MODEL["rate_base"] * (mean_cnt / 6.0) * (1.15 if vendor.startswith("A") else 0.90)
    return round(mean_cnt, 2), full, round(rate, 1), round(r0, 1)


# ============================================================ 1) 距离 × 位置（9 dBi）
POS = {"上": "T-TOP", "下": "B-BOTTOM", "正面侧": "F-FRONT", "背面侧": "F-BACK"}
DISTS_CM = [0, 5, 10, 20, 30, 50]
rows_b = []
for pos, face in POS.items():
    for dcm in DISTS_CM:
        cnt, full, rate, r = measure(dcm / 100.0, 9, "A-Impinj体系", face)
        rows_b.append({"位置": pos, "距离_cm": dcm, "朝向面": face, "读全数_6": cnt,
                       "3箱读全数": full, "读取率_tags_s": rate, "RSSI_dBm": r})
with open(os.path.join(SIM, "B_距离_9dBi_模拟.csv"), "w", newline="", encoding="utf-8-sig") as f:
    w = csv.DictWriter(f, fieldnames=list(rows_b[0]))
    w.writeheader(); w.writerows(rows_b)

# ============================================================ 2) 厂家 × 增益（下置 10 cm）
CFG = [("A-Impinj体系", 9), ("A-Impinj体系", 6), ("B-国产方案", 9), ("B-国产方案", 6)]
rows_c = []
for vendor, gain in CFG:
    for dcm in [0, 10, 30]:
        cnt, full, rate, r = measure(dcm / 100.0, gain, vendor, "B-BOTTOM")
        rows_c.append({"厂家": vendor, "天线增益_dBi": gain, "距离_cm": dcm, "读全数_6": cnt,
                       "3箱读全数": full, "读取率_tags_s": rate, "RSSI_dBm": r})
with open(os.path.join(SIM, "C_厂家x增益_模拟.csv"), "w", newline="", encoding="utf-8-sig") as f:
    w = csv.DictWriter(f, fieldnames=list(rows_c[0]))
    w.writeheader(); w.writerows(rows_c)

# ============================================================ 3) 姿态 A1–A6（9 dBi / 10 cm）
# 读码器固定在下、天线朝上；只改箱体哪个面朝下。
# 标签在箱内，等效离天线距离 = 箱面距离(10 cm) + 沿竖直方向的箱体尺寸/2
POSES = [
    ("A1", "正立 · 底面朝下", "B-BOTTOM", "下", "B-BOTTOM", 0.30),
    ("A2", "倒置 · 顶面朝下", "T-TOP", "下", "T-TOP", 0.30),
    ("A3", "侧放 · 正面朝下", "F-FRONT_DOWN", "下", "F-FRONT", 0.40),
    ("A4", "侧放 · 背面朝下", "F-BACK_DOWN", "下", "F-BACK", 0.40),
    ("A5", "侧躺 · 左侧面朝下", "S-LEFT_DOWN", "下", "S-LEFT", 0.60),
    ("A6", "侧躺 · 右侧面朝下", "S-RIGHT_DOWN", "下", "S-RIGHT", 0.60),
]
rows_a = []
for code, desc, face, pos, down_face, vert in POSES:
    d_tag = 0.10 + vert / 2.0
    r0 = rssi(d_tag, 9, "A-Impinj体系", face)
    per = []
    for _ in range(9):
        cnt = 0
        for off in TAG_OFFSETS:
            r = r0 + off + random.gauss(0, 0.8)
            if random.random() < p_read(r):
                cnt += 1
        per.append(cnt)
    mean_cnt = statistics.mean(per)
    rows_a.append({"编号": code, "姿态": desc, "接触底面": down_face, "读码器位置": pos,
                   "箱面距离_cm": 10, "标签等效距离_cm": int(round(d_tag * 100)),
                   "读全数_6": round(mean_cnt, 2), "3箱读全数": sum(1 for v in per if v >= 5.99),
                   "读取率_tags_s": round(MODEL["rate_base"] * (mean_cnt / 6.0) * 1.15, 1),
                   "RSSI_dBm": round(r0, 1)})

with open(os.path.join(SIM, "A_姿态_模拟.csv"), "w", newline="", encoding="utf-8-sig") as f:
    w = csv.DictWriter(f, fieldnames=list(rows_a[0]))
    w.writeheader(); w.writerows(rows_a)

# 模型参数随结果一起存档（评审要看假设）
with open(os.path.join(SIM, "模型假设.json"), "w", encoding="utf-8") as f:
    json.dump({"MODEL": MODEL, "tag_offsets_dB": [round(t, 2) for t in TAG_OFFSETS],
               "说明": "模拟值，非实测。rssi = rssi_ref + gain + vendor + (-20log10(d/d_ref)) + face_loss；"
                       "p = 1/(1+exp((rssi_th-rssi)/sigma))"}, f, ensure_ascii=False, indent=2)


# ============================================================ 空模板（明天现场填）
def tpl(name, cols, extra_rows=None):
    p = os.path.join(TPL, name)
    with open(p, "w", newline="", encoding="utf-8-sig") as f:
        w = csv.writer(f)
        w.writerow(cols)
        for r in (extra_rows or []):
            w.writerow(r)


C_METRIC = ["读全数_of_6", "3箱读全数", "读取率_tags_s", "RSSI_min", "RSSI_max", "拍照", "备注"]
tpl("A_姿态.csv", ["编号", "箱体姿态", "接触底面", "朝向读码器的面", "读码器位置", "距离_cm",
                   "读码器厂家型号", "天线增益_dBi", "天线号"] + C_METRIC,
    [["A1", "正立", "B-BOTTOM", "B-BOTTOM", "下", 10, "", "", ""],
     ["A2", "倒置", "T-TOP", "T-TOP", "下", 10, "", "", ""],
     ["A3", "侧放", "F-FRONT", "F-FRONT", "下", 10, "", "", ""],
     ["A4", "侧放", "F-BACK", "F-BACK", "下", 10, "", "", ""],
     ["A5", "侧躺", "S-LEFT", "S-LEFT", "下", 10, "", "", ""],
     ["A6", "侧躺", "S-RIGHT", "S-RIGHT", "下", 10, "", "", ""]])
rows = []
for pos in ["上", "下", "正面侧", "背面侧"]:
    for dcm in DISTS_CM:
        rows.append([pos, dcm, "", 9, "", "", "", "", "", "", "", "", ""])
tpl("B_距离_9dBi.csv", ["读码器位置", "距离_cm", "朝向面", "天线增益_dBi", "读码器厂家型号", "天线号"] + C_METRIC, rows)
rows = []
for vendor in ["A-Impinj体系", "B-国产方案"]:
    for gain in [9, 6]:
        for dcm in [0, 10, 30]:
            rows.append([vendor, gain, dcm, "", "", "", "", "", "", "", "", ""])
tpl("C_厂家x增益.csv", ["读码器厂家", "天线增益_dBi", "距离_cm", "型号", "天线号"] + C_METRIC, rows)
tpl("场地与标签.csv",
    ["项", "值", "来源/说明"],
    [["箱体外形_长x宽x高_mm", "", "卷尺实测"],
     ["箱重_kg", "", ""],
     ["整机型号", "Kinder（塑料背壳）", "待确认全称与背壳材质/厚度"],
     ["背壳材质/厚度_mm", "", "影响 UHF 穿透，需记录"],
     ["箱内金属件（是否有屏蔽罩）", "", "有则读全率会显著下降"],
     ["读码器IP/型号/固件", "", ""],
     ["天线型号/增益/极化", "", ""],
     ["环境（金属架/邻机/人员）", "", ""]])
print("sim + templates written")
print("A:", [(r["编号"], r["读全数_6"]) for r in rows_a])
print("C:", [(r["厂家"], r["天线增益_dBi"], r["距离_cm"], r["读全数_6"]) for r in rows_c])

# ============================================================ 图：距离曲线
fig, ax = plt.subplots(figsize=(7.2, 3.4), dpi=220)
styles = {"上": (ACCENT, "-"), "下": (ACCENT, "-"), "正面侧": ("#8C8C8C", "--"), "背面侧": ("#C0C0C0", "--")}
mk = {"上": "o", "下": "s", "正面侧": "^", "背面侧": "v"}
for pos in ["下", "上", "正面侧", "背面侧"]:
    ys = [r["读全数_6"] for r in rows_b if r["位置"] == pos]
    c, ls = styles[pos]
    ax.plot(DISTS_CM, ys, ls, marker=mk[pos], ms=5, lw=1.8 if pos in ("上", "下") else 1.2,
            color=c, label=f"读码器在{pos}")
ax.axhline(5.4, color="#B0B0B0", lw=0.9, ls=(0, (4, 3)))
ax.text(48, 5.48, "可用线 5.4/6", fontsize=8, color=GRAY, ha="right")
ax.axvspan(-2, 11, color="#EDF1F9", zorder=0)
ax.text(5.0, 0.55, "读全窗口 ≤10 cm", fontsize=8.5, color=ACCENT, ha="center")
ax.set_xlabel("读码器到箱面距离（cm）", fontsize=9.5, color=INK)
ax.set_ylabel("每箱读到的整机标签数（/6）", fontsize=9.5, color=INK)
ax.set_xlim(-2, 55); ax.set_ylim(0, 6.4)
ax.set_xticks(DISTS_CM)
for s in ("top", "right"):
    ax.spines[s].set_visible(False)
ax.grid(axis="y", color="#ECECEC", lw=0.8); ax.set_axisbelow(True)
ax.legend(frameon=False, fontsize=8.5, ncol=2, loc="lower left")
ax.tick_params(colors=INK, labelsize=9, length=0)
fig.tight_layout(pad=0.3)
fig.savefig(os.path.join(FIG, "fig7_distance_curve.png"), facecolor="white")
plt.close(fig)

# ============================================================ 图：厂家 × 增益
fig, ax = plt.subplots(figsize=(6.4, 3.1), dpi=220)
labels = [f"{v.split('-')[0]}厂\n{g} dBi" for v, g in CFG]
vals = [next(r["读全数_6"] for r in rows_c if r["厂家"] == v and r["天线增益_dBi"] == g and r["距离_cm"] == 30)
        for v, g in CFG]
cols = [ACCENT, ACCENT_L, "#8C8C8C", "#C9C9C9"]
ax.bar(range(4), vals, color=cols, width=0.62)
for i, v in enumerate(vals):
    ax.text(i, v + 0.12, f"{v:.2f}", ha="center", fontsize=9.5, color=INK, fontweight="bold")
ax.set_xticks(range(4)); ax.set_xticklabels(labels, fontsize=9, color=INK)
ax.set_ylim(0, 6.6); ax.set_ylabel("30 cm 下置 · 每箱读全数（/6）", fontsize=9.5, color=INK)
ax.axhline(5.4, color="#B0B0B0", lw=0.9, ls=(0, (4, 3)))
for s in ("top", "right"):
    ax.spines[s].set_visible(False)
ax.grid(axis="y", color="#ECECEC", lw=0.8); ax.set_axisbelow(True)
ax.tick_params(colors=INK, labelsize=9, length=0)
fig.tight_layout(pad=0.3)
fig.savefig(os.path.join(FIG, "fig8_vendor_gain.png"), facecolor="white")
plt.close(fig)

# ============================================================ 图：姿态 A1–A6
fig, ax = plt.subplots(figsize=(7.2, 3.1), dpi=220)
vals = [r["读全数_6"] for r in rows_a]
cols = [ACCENT if v >= 5.4 else ("#7F97C4" if v >= 4.8 else "#C9C9C9") for v in vals]
ax.bar(range(6), vals, color=cols, width=0.6)
for i, v in enumerate(vals):
    ax.text(i, v + 0.10, f"{v:.2f}", ha="center", fontsize=9.5, color=INK, fontweight="bold")
ax.set_xticks(range(6))
ax.set_xticklabels([r["接触底面"] + chr(10) + f"标签距 {r['标签等效距离_cm']} cm" for r in rows_a],
                   fontsize=8.4, color=INK)
ax.set_ylim(0, 6.6)
ax.set_ylabel("每箱读全数（/6）", fontsize=9.5, color=INK)
ax.axhline(5.4, color="#B0B0B0", lw=0.9, ls=(0, (4, 3)))
for sp in ("top", "right"):
    ax.spines[sp].set_visible(False)
ax.grid(axis="y", color="#ECECEC", lw=0.8); ax.set_axisbelow(True)
ax.tick_params(colors=INK, labelsize=9, length=0)
fig.tight_layout(pad=0.3)
fig.savefig(os.path.join(FIG, "fig9_pose.png"), facecolor="white")
plt.close(fig)



# ============================================================ 6) 一次过板读全 6 台的概率（R2 选型判据）
# 现场目标：箱子一次通过读取窗口 T 秒，窗口内 6 个整机标签全部被读到。
# 模型：每个标签在窗口内被盘存 n = 读取率*T/6 次，单次成功概率 p_i（同上），
#       P(读全 6) = Π_i [ 1 - (1-p_i)^n ]
WINDOWS = [0.3, 0.5, 1.0, 2.0]
rows_f = []
for vendor, gain in [(v, g) for v in ("A-Impinj体系", "B-国产方案") for g in (9, 6)]:
    for dcm in (10, 20, 30, 50):
        r0 = rssi(dcm / 100.0, gain, vendor, "B-BOTTOM")
        ps = [p_read(r0 + o) for o in TAG_OFFSETS]
        mean_cnt = sum(ps)
        rate = MODEL["rate_base"] * (mean_cnt / 6.0) * (1.15 if vendor.startswith("A") else 0.90)
        rec = {"厂家": vendor, "天线增益_dBi": gain, "距离_cm": dcm,
               "均读全_6": round(mean_cnt, 2), "读取率_tags_s": round(rate, 1)}
        for T in WINDOWS:
            n = max(rate * T / 6.0, 1.0)
            pall = 1.0
            for pi in ps:
                pall *= 1 - (1 - pi) ** n
            rec[f"过板读全概率_{T}s_%"] = round(100 * pall, 1)
        rows_f.append(rec)
with open(os.path.join(SIM, "F_过板读全概率.csv"), "w", newline="", encoding="utf-8-sig") as f:
    w = csv.DictWriter(f, fieldnames=list(rows_f[0])); w.writeheader(); w.writerows(rows_f)

# 设计规则：0.5 s 窗口、每标签至少 2 次机会 ⇒ 整机读取率 ≥ 6*2/0.5 = 24 tags/s
NEED_RATE = 6 * 2 / 0.5
print("F 过板读全（0.5 s @20 cm）:",
      {(r["厂家"][:2], r["天线增益_dBi"]): r["过板读全概率_0.5s_%"] for r in rows_f if r["距离_cm"] == 20})
print("设计规则：0.5 s 窗口需 ≥", NEED_RATE, "tags/s")

# 图：0.5 s 过板读全概率 vs 距离
fig, ax = plt.subplots(figsize=(6.4, 3.0), dpi=220)
style_map = {("A-Impinj体系", 9): (ACCENT, "-", "o"), ("B-国产方案", 9): ("#8C8C8C", "--", "^"),
             ("A-Impinj体系", 6): (ACCENT_2, "-.", "s"), ("B-国产方案", 6): ("#C9C9C9", ":", "v")}
for key, (c, ls, mk) in style_map.items():
    pts = [(r["距离_cm"], r["过板读全概率_0.5s_%"]) for r in rows_f
           if (r["厂家"], r["天线增益_dBi"]) == key]
    pts.sort()
    ax.plot([p[0] for p in pts], [p[1] for p in pts], ls, color=c, marker=mk, ms=5, lw=1.8,
            label=f"{key[0][:2]}厂 {key[1]} dBi")
ax.axhline(95, color="#B0B0B0", lw=0.9, ls=(0, (4, 3)))
ax.text(48, 88, "95% 门槛", fontsize=8, color=GRAY, ha="right")
ax.set_xlabel("读码器到箱面距离（cm）", fontsize=9.5, color=INK)
ax.set_ylabel("0.5 s 窗口读全 6 台的概率（%）", fontsize=9.5, color=INK)
ax.set_ylim(0, 105); ax.set_xlim(5, 52)
ax.set_xticks([10, 20, 30, 50])
for sp in ("top", "right"):
    ax.spines[sp].set_visible(False)
ax.grid(axis="y", color="#ECECEC", lw=0.8); ax.set_axisbelow(True)
ax.legend(frameon=False, fontsize=8, ncol=2, loc="lower left")
ax.tick_params(colors=INK, labelsize=9, length=0)
fig.tight_layout(pad=0.3)
fig.savefig(os.path.join(FIG, "fig12_pass_window.png"), facecolor="white")
plt.close(fig)

print("figs done")
