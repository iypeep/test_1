# -*- coding: utf-8 -*-
"""天线页下方：4 / 6 / 9 dBi 方形圆极化板状天线（Blender 渲染 + 尺寸标注）。

同一比例（0.90 px/mm）摆放，尺寸按手册：
  4 dBi 128×128×20；6 dBi 190×190×20；9 dBi 254×254×28（9 dBi 手册值）
输出：figs/antenna_row.png（1950×400）
用法：py -3.12 make_fig_antenna_row.py
"""
import os
from PIL import Image, ImageDraw, ImageFont

_HERE = os.path.dirname(os.path.abspath(__file__))
FIG = os.path.join(os.path.dirname(_HERE), "figs")
SRC = os.path.join(_HERE, "_3d_out2")
F = r"C:\Windows\Fonts\msyh.ttc"
FB = r"C:\Windows\Fonts\msyhbd.ttc"
INK, GRAY, ACCENT = "#1A1A1A", "#8C8C8C", "#3E5DA8"

W, H = 2630, 400
CW = 650
BASE = 250
SCALE = 0.90

ITEMS = [
    ("5.5 dBi", "ANT_55.png", 132, "132×132×18 mm", "Laird S9025PL · 近距补盲"),
    ("6 dBi", "ANT_6.png", 128, "128×128×20 mm", "捷创智联 6 dBi · 近距"),
    ("8 dBi", "ANT_8.png", 225, "225×225×35 mm", "Silion SLP1002 · 近距主力"),
    ("9 dBi", "ANT_9.png", 259, "259×259×34 mm", "Laird S9028PCL · 远距 / 大箱"),
]


def font(sz, bold=False):
    return ImageFont.truetype(FB if bold else F, sz)


def trim(im):
    box = im.split()[-1].getbbox()
    return im.crop(box) if box else im


def main():
    im = Image.new("RGB", (W, H), "white")
    d = ImageDraw.Draw(im)
    for i, (gain, fn, mm, dims, note) in enumerate(ITEMS):
        x0 = i * CW
        src = trim(Image.open(os.path.join(SRC, fn)))
        w = int(mm * SCALE)
        h = int(src.height * w / src.width)
        if h > 235:
            h = 235
            w = int(src.width * h / src.height)
        img = src.resize((w, h), Image.LANCZOS)
        im.paste(img, (x0 + (CW - w) // 2, BASE - h), img)

        cx = x0 + CW // 2
        d.text((cx, BASE + 26), gain, font=font(26, True), fill=INK, anchor="mm")
        d.text((cx, BASE + 60), dims, font=font(18), fill=GRAY, anchor="mm")
        d.text((cx, BASE + 90), note, font=font(17), fill=ACCENT, anchor="mm")

    d.text((W - 12, H - 10), "同一比例（0.9 px/mm）", font=font(16), fill=GRAY, anchor="rs")
    out = os.path.join(FIG, "antenna_row.png")
    im.save(out)
    print("wrote", out, im.size)


if __name__ == "__main__":
    main()
