# -*- coding: utf-8 -*-
"""把 Blender 渲染的单帧拼成报告用图（3 张）"""
import os
from PIL import Image, ImageDraw, ImageFont

_HERE = os.path.dirname(os.path.abspath(__file__))
SRC = os.path.join(_HERE, "_3d_out")
REP = os.path.dirname(_HERE)
FIG = os.path.join(REP, "figs")
os.makedirs(FIG, exist_ok=True)

INK, GRAY, ACCENT, LINE = "#1A1A1A", "#8C8C8C", "#3E5DA8", "#D9D9D9"
FB = r"C:\Windows\Fonts\msyhbd.ttc"
F = r"C:\Windows\Fonts\msyh.ttc"


def f(sz, bold=False):
    return ImageFont.truetype(FB if bold else F, sz)


def panel(name, w=620, caption="", sub="", badge="", cap_px=21, sub_px=17, band=62):
    im = Image.open(os.path.join(SRC, name)).convert("RGB")
    h = int(im.height * w / im.width)
    im = im.resize((w, h), Image.LANCZOS)
    out = Image.new("RGB", (w, h + band), "white")
    out.paste(im, (0, 0))
    d = ImageDraw.Draw(out)
    d.line([0, h, w, h], fill=LINE, width=2)
    if badge:
        bw = d.textlength(badge, font=f(22, True)) + 20
        d.rectangle([10, 10, 10 + bw, 42], fill=ACCENT)
        d.text((20, 16), badge, font=f(22, True), fill="white")
    if caption:
        d.text((12, h + 8), caption, font=f(cap_px, True), fill=INK)
    if sub:
        d.text((12, h + max(34, 12 + cap_px)), sub, font=f(sub_px), fill=GRAY)
    return out


def grid(panels, cols, gap=18, header="", header_sub="", footer="", pad=26):
    rows = (len(panels) + cols - 1) // cols
    cw = max(p.width for p in panels)
    ch = max(p.height for p in panels)
    hh = 84 if header else 0
    fh = 62 if footer else 0
    W = pad * 2 + cols * cw + (cols - 1) * gap
    H = hh + pad + rows * ch + (rows - 1) * gap + fh
    canvas = Image.new("RGB", (W, H), "white")
    d = ImageDraw.Draw(canvas)
    if header:
        d.text((pad, 20), header, font=f(30, True), fill=INK)
        if header_sub:
            d.text((pad, 58), header_sub, font=f(18), fill=GRAY)
    y = hh + pad - (84 if header else 0) + (84 if header else 0)
    y = hh + pad - (84 if header else 0)
    y = hh + pad
    for i, p in enumerate(panels):
        r, c = divmod(i, cols)
        x = pad + c * (cw + gap)
        yy = y + r * (ch + gap)
        canvas.paste(p, (x, yy))
    if footer:
        d.line([pad, H - fh + 8, W - pad, H - fh + 8], fill=LINE, width=2)
        d.text((pad, H - fh + 18), footer, font=f(16), fill=GRAY)
    return canvas


# ---------------------------------------------------------------- fig4 六种放置
P = [
    panel("A1_bottom_down.png", badge="A1", caption="底面 B-BOTTOM 朝下",
          sub="正立（产线实际姿态）"),
    panel("A2_top_down.png", badge="A2", caption="顶面 T-TOP 朝下",
          sub="倒置"),
    panel("A3_front_down.png", badge="A3", caption="正面 F-FRONT 朝下",
          sub="侧放 · 防爆标识面接触"),
    panel("A4_back_down.png", badge="A4", caption="背面 F-BACK 朝下",
          sub="侧放 · 条码 + 6 序列号面接触"),
    panel("A5_left_down.png", badge="A5", caption="左侧面 S-LEFT 朝下",
          sub="侧躺 · 箱体长边立起"),
    panel("A6_right_down.png", badge="A6", caption="右侧面 S-RIGHT 朝下",
          sub="侧躺 · 箱体长边立起"),
]
grid(P, 3,
     header="六种面分别作底面（读码器固定在下、朝向不变）",
     header_sub="只改箱体哪个面朝下：F-FRONT 有防爆标识；F-BACK 有箱体条码 + 6 个整机序列号；S-LEFT / S-RIGHT 为侧面；T-TOP / B-BOTTOM 为封箱带",
     footer="示意说明：箱体按 600×400×300 mm 建模（现场实测后替换）；读码器放大 1.3×；半透明蓝锥为天线主波束。"
            "整机 RFID 标签在箱内机器上，不贴箱面；箱体侧躺后标签离天线更远（30/40/60 cm 高差），这是姿态影响的主因。").save(
    os.path.join(FIG, "fig4_3d_placements.png"))
print("fig4 ok")

# ---------------------------------------------------------------- fig5 距离几何
P = [
    panel("D_up.png", caption="上置（读码器在上方朝下）", sub="蓝线 = 天线面到箱面距离"),
    panel("D_down.png", caption="下置（读码器在下方朝上）", sub="产线实际安装方向"),
    panel("D_side.png", caption="侧面（读码器在正面侧）", sub="标签长轴与天线电场正交 → 极化失配"),
]
grid(P, 3,
     header="R4 距离测量几何（示值 10 cm）",
     header_sub="每一档距离都按同一口径记录：distinct EPC、6/6 读全数、读取率、RSSI、主命中天线",
     footer="现场按 0 / 5 / 10 / 20 / 30 / 50 cm 六档执行；0 cm = 天线面紧贴箱面（不压箱）。").save(
    os.path.join(FIG, "fig5_3d_distance.png"))
print("fig5 ok")

# ---------------------------------------------------------------- fig6 读码器阵容
P = [
    panel("R_A6.png", w=360, caption="A 厂（Impinj 体系）", sub="4 口读头 + 6 dBi 天线"),
    panel("R_A9.png", w=360, caption="A 厂 + 9 dBi", sub="口径更大、波束更窄"),
    panel("R_B6.png", w=360, caption="B 厂（国产方案）", sub="外壳更小 + 6 dBi 天线"),
    panel("R_B9.png", w=360, caption="B 厂 + 9 dBi", sub="对称比较：只改一个变量"),
]
grid(P, 4,
     header="R2 对比配置：2 家读码器 × 2 种天线增益（3D 示意）",
     header_sub="厂家 A = Impinj 体系 4 口读头（公开规格：4 口 / 最大 32.5–33 dBm / 1100 tags·s⁻¹）；厂家 B = 国产方案（MP QM100 类，需外置 PA 到 30 dBm）",
     footer="3D 为按公开尺寸比例建的示意模型（无公开免登录的厂商 3D 文件）；判定仍以实测 6/6 读全数为准。").save(
    os.path.join(FIG, "fig6_3d_readers.png"))
print("fig6 ok")
