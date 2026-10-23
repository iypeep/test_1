# -*- coding: utf-8 -*-
"""用修正后的 3D 帧（_3d_out2）重拼 P2 的六宫格。

与旧图的差别：箱体按产线实际姿态立起（600 高、400×300 着地），防爆标签在
最大的 600×400 面；读码器直接托住箱底，不再穿模。

输出：figs/fig4_3d_placements_v2.png（尺寸与旧图一致：1948×1244）
用法：py -3.12 make_fig4_fix.py
"""
import os
import compose_3d as c3

_HERE = os.path.dirname(os.path.abspath(__file__))
REP = os.path.dirname(_HERE)
FIG = os.path.join(REP, "figs")
c3.SRC = os.path.join(_HERE, "_3d_out2")     # panel() 读的是模块级 SRC

P = [
    c3.panel("A1_bottom_down.png", badge="A1", caption="底面 B-BOTTOM 朝下",
             sub="正立（产线实际姿态）"),
    c3.panel("A2_top_down.png", badge="A2", caption="顶面 T-TOP 朝下",
             sub="倒置"),
    c3.panel("A3_front_down.png", badge="A3", caption="正面 F-FRONT 朝下",
             sub="侧放 · 防爆标识面接触"),
    c3.panel("A4_back_down.png", badge="A4", caption="背面 F-BACK 朝下",
             sub="侧放 · 条码 + 6 序列号面接触"),
    c3.panel("A5_left_down.png", badge="A5", caption="左侧面 S-LEFT 朝下",
             sub="侧躺 · 侧面接触"),
    c3.panel("A6_right_down.png", badge="A6", caption="右侧面 S-RIGHT 朝下",
             sub="侧躺 · 侧面接触"),
]

out = c3.grid(
    P, 3,
    header="六种面分别作底面（读码器固定在下、朝向不变）",
    header_sub="只改箱体哪个面朝下：F-FRONT 有防爆标识；F-BACK 有箱体条码 + 6 个整机序列号；"
               "S-LEFT / S-RIGHT 为侧面；T-TOP / B-BOTTOM 为封箱带",
    footer="示意说明：箱体立起 600 × 400 × 300 mm，直接放在读码器天线上；读码器放大 1.3×。"
           "整机 RFID 标签在箱内机器上，不贴箱面；立起高度 A1/A2 600、A3/A4 300、A5/A6 400 mm。")
path = os.path.join(FIG, "fig4_3d_placements_v2.png")
out.save(path)
print("wrote", path, out.size)
