# -*- coding: utf-8 -*-
"""重出两张 3D 拼图，只改图内标题（版面/尺寸不变）。

背景：图内标题留着旧版需求编号 —— fig5 写「R4 距离测量几何」（距离其实是 R3），
fig6 写「R2 对比配置」（R2 是模组选型，页上用的是 R4+R5）。页面上又不方便覆盖，
所以按原管线重出一版，尺寸与旧图一致，直接替换图片即可。

输出：
    figs/fig5_3d_antennas.png       （P3「读取方向测试」用）
    figs/fig6_3d_readers_r45.png    （P8「R4+R5」用）

用法：py -3.12 make_fig_relabel.py
"""
import os
import compose_3d as c3          # 复用 panel()/grid()（导入时会重出 fig4/5/6，内容不变）

_HERE = os.path.dirname(os.path.abspath(__file__))
FIG = os.path.join(os.path.dirname(_HERE), "figs")


def fig5():
    c3.SRC = os.path.join(_HERE, "_3d_out2")     # 立起来的箱体（修正版渲染）
    P = [
        c3.panel("D_up.png", caption="上置（读码器在上方朝下）", sub="蓝线 = 天线面到箱面距离",
                 cap_px=32, sub_px=24, band=84),
        c3.panel("D_down.png", caption="下置（读码器在下方朝上）", sub="产线实际安装方向",
                 cap_px=32, sub_px=24, band=84),
        c3.panel("D_side.png", caption="侧面（读码器在正面侧）", sub="标签长轴与天线电场正交 → 极化失配",
                 cap_px=32, sub_px=24, band=84),
    ]
    # 不画图内标题/脚注：P3 上已有「机台RFID布置方式—3*RFID天线」小标题，
    # 图内再写一遍既是重复、字号又被压到 7 pt 看不清。
    out = c3.grid(P, 3)
    path = os.path.join(FIG, "fig5_3d_antennas.png")
    out.save(path)
    print("wrote", path, out.size)


def fig6():
    c3.SRC = os.path.join(_HERE, "_3d_out")      # 读码器阵容沿用原渲染
    P = [
        c3.panel("R_A6.png", w=360, caption="A 厂（Impinj 体系）", sub="4 口读头 + 6 dBi 天线"),
        c3.panel("R_A9.png", w=360, caption="A 厂 + 9 dBi", sub="口径更大、波束更窄"),
        c3.panel("R_B6.png", w=360, caption="B 厂（国产方案）", sub="外壳更小 + 6 dBi 天线"),
        c3.panel("R_B9.png", w=360, caption="B 厂 + 9 dBi", sub="对称比较：只改一个变量"),
    ]
    out = c3.grid(
        P, 4,
        header="R4 + R5 对比配置：2 家读码器 × 2 种天线增益（3D 示意）",
        header_sub="厂家 A = Impinj 体系 4 口读头（公开规格：4 口 / 最大 32.5–33 dBm / 1100 tags·s⁻¹）；厂家 B = 国产方案（QM100 类，需外置 PA 到 30 dBm）",
        footer="3D 为按公开尺寸比例建的示意模型（无公开免登录的厂商 3D 文件）；判定仍以实测 6/6 读全数为准。")
    path = os.path.join(FIG, "fig6_3d_readers_r45.png")
    out.save(path)
    print("wrote", path, out.size)


if __name__ == "__main__":
    fig5()
    fig6()
