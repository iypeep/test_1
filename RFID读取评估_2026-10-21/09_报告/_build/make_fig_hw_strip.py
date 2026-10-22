# -*- coding: utf-8 -*-
"""R2 页右侧「手册 / 产品页」竖条图：① RodinBell M-703(E710) ② Kathrein RRU 4xxx ③ Silion SQM5100

目的：让“图”和“选型表”一一对应（表格最后加「图」列，填 ① / ② / ③）。
输出：09_报告/figs/hw_strip_r2.png
"""
import os
from PIL import Image, ImageDraw, ImageFont

_HERE = os.path.dirname(os.path.abspath(__file__))
REP = os.path.dirname(_HERE)
FIG = os.path.join(REP, "figs")
HW = os.path.join(FIG, "hw")
OUT = os.path.join(FIG, "hw_strip_r2.png")

INK, GRAY, LINE, ACCENT = (26, 26, 26), (140, 140, 140), (214, 214, 214), (62, 93, 168)
FONT = r"C:\Windows\Fonts\msyh.ttc"
W = 1080
PAD = 26
TILE_H = 400
CAP_H = 96

ITEMS = [
    ("①", os.path.join(HW, "RodinBell_M703_E710.png"), "RodinBell M-703（E710 平台）",
     "8 天线口 · 最大 33 dBm · 900 tags/s"),
    ("②", os.path.join(HW, "Kathrein-RRU-4000_p1_0.png"), "Kathrein RRU 4xxx 系列",
     "4 口（背板 ANT1–4）· 30/33 dBm · 以太网"),
    ("③", os.path.join(HW, "silion1.png"), "Silion SQM5100（QM100 方案）",
     "灵敏度 −79 dBm · 片内 PA 4 dBm，需外置功放"),
]


def font(sz):
    return ImageFont.truetype(FONT, sz)


def fit(im, box_w, box_h):
    w, h = im.size
    s = min(box_w / w, box_h / h)
    return im.resize((max(1, int(w * s)), max(1, int(h * s))), Image.LANCZOS)


def main():
    total_h = PAD + len(ITEMS) * (TILE_H + CAP_H + 18) + PAD
    canvas = Image.new("RGB", (W, total_h), "white")
    d = ImageDraw.Draw(canvas)
    y = PAD
    for badge, path, name, spec in ITEMS:
        im = Image.open(path).convert("RGB")
        inner_w, inner_h = W - 2 * PAD - 12, TILE_H
        d.rectangle([PAD, y, W - PAD, y + TILE_H], outline=LINE, width=2)
        im2 = fit(im, inner_w, inner_h - 16)
        canvas.paste(im2, (PAD + (W - 2 * PAD - im2.size[0]) // 2, y + (TILE_H - im2.size[1]) // 2))
        # 角标
        d.ellipse([PAD + 10, y + 10, PAD + 52, y + 52], fill=ACCENT)
        bb = d.textbbox((0, 0), badge, font=font(28))
        d.text((PAD + 31 - (bb[2] - bb[0]) / 2, y + 31 - (bb[3] - bb[1]) / 2 - 4), badge, font=font(28), fill="white")
        # 文字
        ty = y + TILE_H + 10
        d.text((PAD, ty), name, font=font(30), fill=INK)
        d.text((PAD, ty + 40), spec, font=font(23), fill=GRAY)
        y += TILE_H + CAP_H + 18
    canvas.save(OUT, "PNG")
    print("wrote", OUT, canvas.size)


if __name__ == "__main__":
    main()
