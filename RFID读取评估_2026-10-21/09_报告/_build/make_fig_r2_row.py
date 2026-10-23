# -*- coding: utf-8 -*-
"""P5 顶排：7 款候选外观（4 款 Blender 建模渲染 + 3 款原厂产品图）。

有原厂图的用原厂图（M-703 / Kathrein RRU 4560 / Silion SQM5100），没有的用
`rfid3d_modules.py` 按手册尺寸建的模型。全部按 1.02 px/mm 同一比例摆放，
嵌入式模组放大 3× 并标注。

输出：figs/r2_modules_row.png（2340×390）
用法：py -3.12 make_fig_r2_row.py
"""
import os
from PIL import Image, ImageDraw, ImageFont

_HERE = os.path.dirname(os.path.abspath(__file__))
FIG = os.path.join(os.path.dirname(_HERE), "figs")
OUT3D = os.path.join(_HERE, "_3d_out2")
F = r"C:\Windows\Fonts\msyh.ttc"
FB = r"C:\Windows\Fonts\msyhbd.ttc"

INK, GRAY, ACCENT = "#1A1A1A", "#8C8C8C", "#3E5DA8"
CW, CH, PAD = 330, 390, 15
SCALE = 1.02          # px / mm
BASELINE = 232


def font(sz, bold=False):
    return ImageFont.truetype(FB if bold else F, sz)


def trim(im):
    """裁掉透明/白底边。"""
    if im.mode == "RGBA":
        box = im.split()[-1].getbbox()
    else:
        rgb = im.convert("RGB")
        px = rgb.load()
        w, h = rgb.size
        xs, ys = [], []
        for y in range(h):
            for x in range(w):
                r, g, b = px[x, y]
                if r < 246 or g < 246 or b < 246:
                    xs.append(x); ys.append(y)
        box = (min(xs), min(ys), max(xs) + 1, max(ys) + 1) if xs else None
    return im.crop(box) if box else im


ITEMS = [
    # 名称, 形态, 宽mm, 高mm, 尺寸文字, 说明, 图片, 是否≈, 缩放
    ("1 Impinj R700", "工业读头", 214, 149, "214×149×30", "4 天线口", os.path.join(OUT3D, "MOD_R700.png"), False, 1.0),
    ("2 Impinj R420", "工业读头", 190, 127, "190×127×33", "4 天线口", os.path.join(OUT3D, "MOD_R420.png"), False, 1.0),
    ("3 RodinBell M-703", "读头 · E710", 200, 140, "200×140×40", "8 天线口 · 原厂图",
     os.path.join(FIG, "hw", "RodinBell_M703_E710.png"), True, 1.0),
    ("4 Zebra FX9600", "一体机", 273, 184, "273×184×51", "4/8 天线口", os.path.join(OUT3D, "MOD_FX9600.png"), False, 1.0),
    ("5 Kathrein RRU 4560", "读头", 230, 160, "230×160×45", "4 天线口 · 原厂图",
     os.path.join(FIG, "hw", "Kathrein-RRU-4000_p1_0.png"), True, 1.0),
    ("6 ThingMagic M6e", "嵌入模组", 66, 36, "66×36×8", "4 路 RF", os.path.join(OUT3D, "MOD_M6E.png"), False, 3.0),
    ("7 Silion SQM5100", "嵌入模组", 60, 45, "60×45×8", "原厂图 · 需外置 PA",
     os.path.join(FIG, "hw", "silion1.png"), True, 3.0),
]


def main():
    W = len(ITEMS) * CW + 2 * PAD
    im = Image.new("RGB", (W, CH), "white")
    d = ImageDraw.Draw(im)

    for i, (name, kind, mw, mh, dims, cap, path, approx, zoom) in enumerate(ITEMS):
        x0 = PAD + i * CW
        src = Image.open(path)
        src = trim(src)

        # 有图/没图都按 mm 近似比例：渲染图含接口凸出，留 14 mm 余量
        is_render = path.endswith(("MOD_R700.png", "MOD_R420.png", "MOD_FX9600.png", "MOD_M6E.png"))
        target_w = ((mw + (14 if is_render else 0)) * SCALE) * zoom
        scale = target_w / src.width
        h = int(src.height * scale)
        if h > 215:                      # 太高就按高度收
            scale = 215 / src.height
            h = 215
        w = int(src.width * scale)
        if w > 300:
            scale = 300 / src.width
            w, h = 300, int(src.height * scale)
        img = src.resize((max(1, w), max(1, h)), Image.LANCZOS)

        x = x0 + (CW - w) // 2
        y = BASELINE - h
        if img.mode == "RGBA":
            im.paste(img, (x, y), img)
        else:
            im.paste(img.convert("RGB"), (x, y))

        d.text((x0 + CW / 2, 258), name, font=font(21, True), fill=INK, anchor="mm")
        d.text((x0 + CW / 2, 286), kind, font=font(16), fill=GRAY, anchor="mm")
        dim_txt = ("≈" if approx else "") + dims + " mm" + ("（×3 显示）" if zoom > 1 else "")
        d.text((x0 + CW / 2, 314), dim_txt, font=font(15), fill=GRAY, anchor="mm")
        d.text((x0 + CW / 2, 342), cap, font=font(15), fill=ACCENT, anchor="mm")

    out = os.path.join(FIG, "r2_modules_row.png")
    im.save(out)
    print("wrote", out, im.size)


if __name__ == "__main__":
    main()
