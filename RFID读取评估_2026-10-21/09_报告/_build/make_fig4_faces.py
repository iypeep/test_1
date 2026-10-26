# -*- coding: utf-8 -*-
"""重出 P2 的六宫格 3D 图：标注从 A1–A6 换成「*面朝下」的描述

输入：`_build/_3d_out/A1_bottom_down.png … A6_right_down.png`（Blender 渲染的单姿态面板，1024×768）
输出：`09_报告/figs/fig4_faces.png`

为什么要重出：经理要求「六种放置方式」与「读取方向测试」用同一套说法，
A1–A6 这种编号在两页之间没有语义联系，改成「底面朝下 / 顶面朝下 / 正面朝下 / 背面朝下 / 左侧朝下 / 右侧朝下」。

用法：py -3.12 make_fig4_faces.py
"""
import os
from PIL import Image, ImageDraw, ImageFont

_HERE = os.path.dirname(os.path.abspath(__file__))
REP = os.path.dirname(_HERE)
PANELS = os.path.join(_HERE, "_3d_out")
OUT = os.path.join(REP, "figs", "fig4_faces.png")

ORDER = [
    ("A1_bottom_down.png", "底面朝下（正立）"),
    ("A2_top_down.png", "顶面朝下（倒置）"),
    ("A3_front_down.png", "正面朝下（防爆标识面）"),
    ("A4_back_down.png", "背面朝下（条码面）"),
    ("A5_left_down.png", "左侧面朝下"),
    ("A6_right_down.png", "右侧面朝下"),
]

COLS, ROWS = 3, 2
PANE_W = 620
CAP_H = 42
GAP = 10
FONT = r"C:\Windows\Fonts\msyh.ttc"
INK = (26, 26, 26)


def main():
    pane_h = int(768 * PANE_W / 1024)
    width = COLS * PANE_W + (COLS + 1) * GAP
    height = ROWS * (pane_h + CAP_H) + (ROWS + 1) * GAP
    canvas = Image.new("RGB", (width, height), "white")
    draw = ImageDraw.Draw(canvas)
    try:
        font = ImageFont.truetype(FONT, 25)
    except Exception:
        font = ImageFont.load_default()

    for i, (fname, caption) in enumerate(ORDER):
        r, c = divmod(i, COLS)
        x = GAP + c * (PANE_W + GAP)
        y = GAP + r * (pane_h + CAP_H + GAP)
        im = Image.open(os.path.join(PANELS, fname)).convert("RGB")
        im = im.resize((PANE_W, pane_h), Image.LANCZOS)
        canvas.paste(im, (x, y))
        tw = draw.textlength(caption, font=font)
        draw.text((x + (PANE_W - tw) / 2, y + pane_h + 8), caption, fill=INK, font=font)

    canvas.save(OUT)
    print("wrote", OUT, canvas.size)


if __name__ == "__main__":
    main()
