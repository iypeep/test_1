# -*- coding: utf-8 -*-
"""硬件图：把手册/厂商页里的产品图拼成一张（R2 用）"""
import os
from PIL import Image, ImageDraw, ImageFont

_HERE = os.path.dirname(os.path.abspath(__file__))
REP = os.path.dirname(_HERE)
FIG = os.path.join(REP, "figs")
HW = os.path.join(FIG, "hw")

INK, GRAY, LINE, ACCENT = "#1A1A1A", "#8C8C8C", "#D9D9D9", "#3E5DA8"
f = lambda sz, b=False: ImageFont.truetype(r"C:\Windows\Fonts\msyhbd.ttc" if b else r"C:\Windows\Fonts\msyh.ttc", sz)

ITEMS = [
    ("RodinBell_M703_E710.png", "Impinj E710 平台模块（M-703）",
     "8 天线口 · 最大 33 dBm · 900 tags/s｜来源：impinj.com 合作方页"),
    ("Kathrein-RRU-4000_p1_1.png", "Kathrein RRU 4000 系列 工业读头",
     "4 口 · 30/33 dBm · 以太网｜来源：Kathrein RRU 4000 系列 datasheet"),
    ("silion1.png", "Silion SQM5100（QM100 方案，国产）",
     "读芯片灵敏度 −79 dBm · 片内 PA 4 dBm，需外置功放｜来源：silion.com.cn 产品页"),
]
CW, CH, CAP = 470, 330, 78
gap, pad = 20, 24
W = pad * 2 + len(ITEMS) * CW + (len(ITEMS) - 1) * gap
H = 96 + CH + CAP + pad
canvas = Image.new("RGB", (W, H), "white")
d = ImageDraw.Draw(canvas)
d.text((pad, 18), "R2 可挑选的 RFID 模组类型 —— 手册/厂商页产品图对照", font=f(30, True), fill=INK)
d.text((pad, 58), "同一张表里只比“手册写明的参数”，不靠印象；参数以最新 datasheet 为准", font=f(18), fill=GRAY)

for i, (fn, title, src) in enumerate(ITEMS):
    p = os.path.join(HW, fn)
    x = pad + i * (CW + gap)
    y = 96
    box = Image.new("RGB", (CW, CH), "#F7F8FA")
    im = Image.open(p).convert("RGB")
    im.thumbnail((CW - 24, CH - 24), Image.LANCZOS)
    box.paste(im, ((CW - im.width) // 2, (CH - im.height) // 2))
    canvas.paste(box, (x, y))
    d.rectangle([x, y, x + CW - 1, y + CH - 1], outline=LINE, width=2)
    d.text((x, y + CH + 8), title, font=f(20, True), fill=INK)
    # 来源行自动折行
    words = src
    line, lines = "", []
    for ch in words:
        if d.textlength(line + ch, font=f(15)) > CW - 8:
            lines.append(line); line = ch
        else:
            line += ch
    lines.append(line)
    for j, ln in enumerate(lines[:2]):
        d.text((x, y + CH + 34 + j * 20), ln, font=f(15), fill=GRAY)

canvas.save(os.path.join(FIG, "fig10_hw_modules.png"))
print("fig10 ok", canvas.size)
