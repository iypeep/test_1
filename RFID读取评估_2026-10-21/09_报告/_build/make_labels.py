# -*- coding: utf-8 -*-
"""生成 3D 场景用的贴纸/标签 PNG（防爆标识、条码+DSN、面标）"""
import os, random
from PIL import Image, ImageDraw, ImageFont

OUT = r"C:\Users\TBZ\AppData\Local\hermes\cache\scratch\3d\labels"
os.makedirs(OUT, exist_ok=True)
F = r"C:\Windows\Fonts\msyh.ttc"
FB = r"C:\Windows\Fonts\msyhbd.ttc"

def font(sz, bold=False):
    return ImageFont.truetype(FB if bold else F, sz)

# ---------------------------------------------------------------- 正面：防爆标识
W, H = 720, 520
im = Image.new("RGB", (W, H), "#F5F1E6")
d = ImageDraw.Draw(im)
d.rectangle([0, 0, W-1, H-1], outline="#8C1D18", width=10)
d.rectangle([22, 22, W-23, H-23], outline="#8C1D18", width=3)
d.text((W//2, 96), "防 爆 标 识", font=font(58, True), fill="#8C1D18", anchor="mm")
# 三角形警示符号
cx, cy, r = W//2, 250, 86
d.polygon([(cx, cy-r), (cx-r*0.95, cy+r*0.72), (cx+r*0.95, cy+r*0.72)], outline="#111111", width=8)
d.text((cx, cy+18), "Ex", font=font(56, True), fill="#111111", anchor="mm")
d.text((W//2, 386), "Ex ib IIB T4 Gb", font=font(40, True), fill="#111111", anchor="mm")
d.text((W//2, 440), "FRONT · 长 × 高面", font=font(30), fill="#444444", anchor="mm")
im.save(os.path.join(OUT, "label_front.png"))

# ---------------------------------------------------------------- 背面：条码 + SSCC + 6 DSN
W, H = 900, 620
im = Image.new("RGB", (W, H), "#FFFFFF")
d = ImageDraw.Draw(im)
d.rectangle([0, 0, W-1, H-1], outline="#BBBBBB", width=2)
d.text((24, 22), "卡通箱标签 / CARTON LABEL", font=font(26, True), fill="#111111")
# 条码（示意条纹，宽度随机但固定种子）
random.seed(7)
x = 24; top, bot = 66, 196
while x < W - 24:
    w = random.choice([3, 3, 5, 7, 9])
    if random.random() < 0.55:
        d.rectangle([x, top, x + w, bot], fill="#111111")
    x += w + random.choice([3, 4, 6])
hdr = "（01）00069758522134123082"
d.text((24, 206), hdr, font=font(30, True), fill="#111111")
d.line([24, 246, W-24, 246], fill="#CCCCCC", width=2)
d.text((24, 258), "整机序列号 DSN1 – DSN6（一箱 6 台）", font=font(24), fill="#444444")
dsns = ["GN46HN01642400V1", "GN46HN01642400XD", "GN46HN01642400T0",
        "GN46HN01642304LU", "GN46HN01642303TW", "GN46HN01642304P9"]
for i, s in enumerate(dsns):
    y = 300 + i * 46
    d.text((24, y), f"DSN{i+1}", font=font(26, True), fill="#111111")
    d.text((150, y), s, font=font(28, True), fill="#0B2E6F")
d.text((24, 578), "BACK · 长 × 高面", font=font(24), fill="#666666")
im.save(os.path.join(OUT, "label_back.png"))

# ---------------------------------------------------------------- 面标（贴在每个面上）
FACE = {
    "F-FRONT": ("#1F5FBF", "F-FRONT 正面"),
    "F-BACK":  ("#1F5FBF", "F-BACK 背面"),
    "S-LEFT":  ("#6B7A8F", "S-LEFT 侧面"),
    "S-RIGHT": ("#6B7A8F", "S-RIGHT 侧面"),
    "T-TOP":   ("#8C8C8C", "T-TOP 顶面"),
    "B-BOTTOM":("#2E8B57", "B-BOTTOM 底面"),
}
for k, (c, txt) in FACE.items():
    W, H = 420, 150
    im = Image.new("RGB", (W, H), "#FFFFFF")
    d = ImageDraw.Draw(im)
    d.rectangle([0, 0, W-1, H-1], outline=c, width=6)
    d.text((W//2, H//2), txt, font=font(44, True), fill=c, anchor="mm")
    im.save(os.path.join(OUT, f"tag_{k}.png"))

print("labels:", sorted(os.listdir(OUT)))
