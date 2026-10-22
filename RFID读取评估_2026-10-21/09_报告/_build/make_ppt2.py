# -*- coding: utf-8 -*-
"""8 页汇报版（V1.2）：按 6 项要求顺序，3D 示意 + 手册参数 + 预测结果 + 填表框架"""
import os
from PIL import Image
from pptx import Presentation
from pptx.util import Inches, Pt
from pptx.dml.color import RGBColor
from pptx.enum.text import PP_ALIGN, MSO_ANCHOR
from pptx.oxml.ns import qn
from lxml import etree

_HERE = os.path.dirname(os.path.abspath(__file__))
REP = os.path.dirname(_HERE)
ROOT = os.path.dirname(REP)
FIG = os.path.join(REP, "figs")
OUT = os.path.join(REP, "RFID读取能力评估_2026-10-22.pptx")

INK, GRAY, LINE = "1A1A1A", "8C8C8C", "D9D9D9"
ACCENT, ACCENT_2, TINT = "3E5DA8", "5C7ED4", "E6EDF9"
COVER_BG = "DCE5F0"
LATIN, EA = "Arial", "微软雅黑"
W, H, MARGIN = 13.333, 7.5, 0.62

prs = Presentation()
prs.slide_width, prs.slide_height = Inches(W), Inches(H)
BLANK = prs.slide_layouts[6]


def set_font(run, size, bold=False, color=INK):
    f = run.font
    f.size, f.bold, f.name = Pt(size), bold, LATIN
    f.color.rgb = RGBColor.from_string(color)
    rPr = run._r.get_or_add_rPr()
    for tag in ("a:ea", "a:cs"):
        el = rPr.find(qn(tag))
        if el is None:
            el = etree.SubElement(rPr, qn(tag))
        el.set("typeface", EA if tag == "a:ea" else LATIN)


def textbox(slide, x, y, w, h, text, size=11, bold=False, color=INK,
            align=PP_ALIGN.LEFT, anchor=MSO_ANCHOR.TOP, spacing=1.0):
    tb = slide.shapes.add_textbox(Inches(x), Inches(y), Inches(w), Inches(h))
    tf = tb.text_frame
    tf.word_wrap = True
    tf.vertical_anchor = anchor
    tf.margin_left = tf.margin_right = tf.margin_top = tf.margin_bottom = 0
    for i, line in enumerate(text.split("\n")):
        p = tf.paragraphs[0] if i == 0 else tf.add_paragraph()
        p.alignment, p.line_spacing = align, spacing
        r = p.add_run(); r.text = line
        set_font(r, size, bold, color)
    return tb


def rich(slide, x, y, w, h, parts, spacing=1.0, anchor=MSO_ANCHOR.TOP):
    tb = slide.shapes.add_textbox(Inches(x), Inches(y), Inches(w), Inches(h))
    tf = tb.text_frame
    tf.word_wrap = True
    tf.vertical_anchor = anchor
    tf.margin_left = tf.margin_right = tf.margin_top = tf.margin_bottom = 0
    for i, (txt, size, bold, color) in enumerate(parts):
        p = tf.paragraphs[0] if i == 0 else tf.add_paragraph()
        p.line_spacing = spacing
        r = p.add_run(); r.text = txt
        set_font(r, size, bold, color)
    return tb


def hline(slide, x, y, w, color=LINE, pt=0.75):
    ln = slide.shapes.add_connector(1, Inches(x), Inches(y), Inches(x + w), Inches(y))
    ln.line.color.rgb = RGBColor.from_string(color)
    ln.line.width = Pt(pt)


def rect(slide, x, y, w, h, fill=None, line=None, lw=0.75):
    from pptx.enum.shapes import MSO_SHAPE
    sh = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, Inches(x), Inches(y), Inches(w), Inches(h))
    sh.shadow.inherit = False
    if fill:
        sh.fill.solid(); sh.fill.fore_color.rgb = RGBColor.from_string(fill)
    else:
        sh.fill.background()
    if line:
        sh.line.color.rgb = RGBColor.from_string(line); sh.line.width = Pt(lw)
    else:
        sh.line.fill.background()
    sh.text_frame.word_wrap = True
    return sh


def pic(slide, name, x, y, maxw, maxh):
    p = os.path.join(FIG, name)
    iw, ih = Image.open(p).size
    s = min(maxw / iw, maxh / ih)
    w, h = iw * s, ih * s
    slide.shapes.add_picture(p, Inches(x), Inches(y), width=Inches(w), height=Inches(h))
    return x + w, y + h


def page(title, kicker=None, num=None, bg=None):
    s = prs.slides.add_slide(BLANK)
    if bg:
        r = rect(s, 0, 0, W, H, fill=bg)
        sp = r._element; sp.getparent().remove(sp); s.shapes._spTree.insert(2, sp)
    if title:
        textbox(s, MARGIN, 0.40, W - 2 * MARGIN, 0.55, title, size=22, bold=True)
        if kicker:
            textbox(s, MARGIN, 0.96, W - 2 * MARGIN, 0.30, kicker, size=11, color=GRAY)
            hline(s, MARGIN, 1.32, W - 2 * MARGIN)
        else:
            hline(s, MARGIN, 1.04, W - 2 * MARGIN)
    if num is not None:
        textbox(s, MARGIN, 7.02, 8.0, 0.26,
                "RFID 读取能力评估 · 7H3AA-PALLET · 2026-10-22", size=8, color=GRAY)
        textbox(s, W - MARGIN - 0.8, 7.02, 0.8, 0.26, f"{num} / 8", size=8, color=GRAY, align=PP_ALIGN.RIGHT)
        hline(s, MARGIN, 6.94, W - 2 * MARGIN, color="ECECEC")
    return s


def _border(cell, color=LINE, pt=0.75):
    tcPr = cell._tc.get_or_add_tcPr()
    for i, tag in enumerate(("a:lnL", "a:lnR", "a:lnT", "a:lnB")):
        old = tcPr.find(qn(tag))
        if old is not None:
            tcPr.remove(old)
        ln = etree.Element(qn(tag))
        ln.set("w", str(int(pt * 12700))); ln.set("cap", "flat")
        ln.set("cmpd", "sng"); ln.set("algn", "ctr")
        sf = etree.SubElement(ln, qn("a:solidFill"))
        c = etree.SubElement(sf, qn("a:srgbClr")); c.set("val", color)
        d = etree.SubElement(ln, qn("a:prstDash")); d.set("val", "solid")
        tcPr.insert(i, ln)


def table(slide, rows, x, y, w, col_w, row_h=0.32, fs=9.5, hfs=9,
          aligns=None, bold_first_col=False, header_fill="F2F2F2"):
    nrow, ncol = len(rows), len(rows[0])
    shp = slide.shapes.add_table(nrow, ncol, Inches(x), Inches(y), Inches(w), Inches(row_h * nrow))
    tbl = shp.table
    tblPr = tbl._tbl.tblPr
    for el in tblPr.findall(qn("a:tableStyleId")):
        tblPr.remove(el)
    tbl.first_row = False
    tbl.horz_banding = False
    scale = w / sum(col_w)
    for i, cw in enumerate(col_w):
        tbl.columns[i].width = Inches(cw * scale)
    for ri in range(nrow):
        tbl.rows[ri].height = Inches(row_h)
        for ci in range(ncol):
            cell = tbl.cell(ri, ci)
            cell.margin_left = cell.margin_right = Inches(0.055)
            cell.margin_top = cell.margin_bottom = Inches(0.015)
            cell.vertical_anchor = MSO_ANCHOR.MIDDLE
            cell.fill.solid()
            cell.fill.fore_color.rgb = RGBColor.from_string(header_fill if ri == 0 else "FFFFFF")
            _border(cell)
            p = cell.text_frame.paragraphs[0]
            p.alignment = aligns[ci] if aligns else (PP_ALIGN.CENTER if ci else PP_ALIGN.LEFT)
            p.line_spacing = 1.0
            r = p.add_run(); r.text = str(rows[ri][ci])
            set_font(r, hfs if ri == 0 else fs, (ri == 0) or (bold_first_col and ci == 0))
    return shp


def takeaway(slide, y, text, x=MARGIN, w=None):
    w = w or (W - x - MARGIN)
    rect(slide, x, y, 0.05, 0.34, fill=ACCENT)
    textbox(slide, x + 0.16, y + 0.02, w - 0.2, 0.32, text, size=11, bold=True, anchor=MSO_ANCHOR.MIDDLE)


def stat(slide, x, y, w, num, unit, label, color=ACCENT):
    textbox(slide, x, y, w, 0.5, num, size=26, bold=True, color=color)
    textbox(slide, x, y + 0.46, w, 0.24, unit, size=9.5, color=GRAY)
    textbox(slide, x, y + 0.72, w, 0.5, label, size=10, color=INK, spacing=1.15)


# ================================================================== 1 封面
s = page(None, bg=COVER_BG)
rect(s, MARGIN, 2.00, 0.06, 1.72, fill=ACCENT)
textbox(s, MARGIN + 0.22, 1.94, 9.5, 0.34, "华勤 · MD5 / MBD3MD3 · 线体 7H3PK1 · 工位「自动扫描称重」", size=11, color="595959")
textbox(s, MARGIN + 0.22, 2.28, 10.5, 0.72, "RFID 读取能力评估", size=38, bold=True, color="262626")
textbox(s, MARGIN + 0.22, 3.06, 11.2, 0.40, "六项要求 · 3D 示意 · 距离与箱型读取结果（模型预测版，待实测替换）", size=15.5, color="404040")
hline(s, MARGIN + 0.22, 3.86, 4.6, color="A9BAD4", pt=1.0)
rich(s, MARGIN + 0.22, 4.02, 9.2, 0.95, [
    ("站点  7H3AA-PALLET      版本  V1.2（框架 + 预测数据）      2026-10-22      设备工程", 12, False, "404040"),
    ("封面起全部数值：手册参数推算 + 参数化模型预测，非实测；明日按 P8 模板填表后重出", 10.5, False, "5A6472"),
], spacing=1.6)
textbox(s, W - 3.6, H - 0.72, 3.0, 0.3, "资料：Impinj / Kathrein / Zebra / MagicRF 手册", size=8.5,
        color="6A7A8C", align=PP_ALIGN.RIGHT)

# ================================================================== 2 六项要求 × 判定
s = page("六项要求 × 当前判定", "结论先行：每条给结论、给依据类型；标注“预测”的都不是实测值", 2)
rows = [
    ["#", "要求", "判定", "结论 / 依据"],
    ["R1", "放置方式：6 个面分别作底面", "3D 已出图", "A1–A6 六姿态；防爆标识在正面、条码+6 序列号在背面（Blender 渲染）"],
    ["R2", "可挑选的 RFID 模组类型", "手册已比", "4 类形态 + 6 家品牌手册参数 + 产品图（图源见页脚）"],
    ["R3", "距离（9 dB，上/下/侧）对读取的影响", "预测", "读全窗口 ≤10 cm；50 cm 掉到 1.9/6；侧面照射最差"],
    ["R4", "不同读码器：9 dB 与 6 dB", "预测", "30 cm：9 dBi 5.22/6 vs 6 dBi 2.89/6 ⇒ 差约 2.3 个标签"],
    ["R5", "不同厂家（×2）", "预测", "B 厂等效落后约 2 dB；30 cm 时 3.44 vs 5.22"],
    ["R6", "同一读码器(9 dB) × 6 种箱型", "预测", "塑料背壳 6.0/6；金属背壳 0.8–4.4/6 ⇒ 背壳材质是分水岭"],
]
table(s, rows, MARGIN, 1.55, W - 2 * MARGIN, [0.5, 3.55, 1.0, 6.5], row_h=0.50, fs=10, hfs=9.5,
      bold_first_col=True, aligns=[PP_ALIGN.CENTER, PP_ALIGN.LEFT, PP_ALIGN.CENTER, PP_ALIGN.LEFT])
takeaway(s, 5.28, "六项里只有 R1/R2 是“已确定”；R3–R6 全为预测，必须用明日实测替换后才可对外")
rect(s, MARGIN, 5.85, W - 2 * MARGIN, 0.86, fill="FAFBFC", line="E6E6E6")
rich(s, MARGIN + 0.18, 5.96, W - 2 * MARGIN - 0.4, 0.7, [
    ("数值来源与可信度", 10, True, INK),
    ("R3–R6 的数字来自「手册参数 + 参数化模型」：读码器功率/灵敏度、天线增益、标签 −22 dBm 读灵敏度取自厂家手册；"
     "箱体/背壳/极化损耗为假设值（25–30 dB）。趋势可用，绝对值必须实测标定。", 9.5, False, GRAY),
], spacing=1.25)

# ================================================================== 3 R1 放置方式
s = page("R1：六种放置方式（3D）", "读码器固定在下、天线朝上；只改箱体哪个面朝下（A1–A6）；蓝锥=天线主波束", 3)
pic(s, "fig4_3d_placements.png", MARGIN, 1.48, 8.55, 4.62)
rows = [
    ["#", "朝下的面", "读全 /6"],
    ["A1", "B-BOTTOM 底面", "5.56"],
    ["A2", "T-TOP 顶面", "4.33"],
    ["A3", "F-FRONT 正面", "4.89"],
    ["A4", "F-BACK 背面", "3.67"],
    ["A5", "S-LEFT 左侧", "3.33"],
    ["A6", "S-RIGHT 右侧", "3.56"],
]
table(s, rows, 9.42, 1.50, 3.29, [0.42, 1.9, 0.9], row_h=0.42, fs=9, hfs=8.5,
      bold_first_col=True, aligns=[PP_ALIGN.CENTER, PP_ALIGN.LEFT, PP_ALIGN.CENTER])
rect(s, 9.42, 4.72, 3.29, 1.32, fill=TINT)
rich(s, 9.58, 4.82, 3.0, 1.15, [
    ("读码器固定，只换箱体", 9.5, True, ACCENT),
    ("六格读码器位置/方向完全一致，只有箱体哪个面朝下不同 —— 变量单一才好归因。", 9, False, INK),
    ("标签在箱内：正立时离天线 25 cm、侧放 30 cm、侧躺 40 cm，姿态影响本质是距离。", 9, False, INK),
], spacing=1.2)
takeaway(s, 6.35, "标签在箱内 ⇒ 侧放/侧躺把标签推远 5–15 cm，读全率从 5.6 掉到 3.3–4.9；姿态是第一优先变量")

# ================================================================== 4 R2 模组类型
s = page("R2：模组选型 —— 目标是「一次过板读全 6 台」",
         "过板时箱子只经过读取区几百毫秒；判据不是“能不能读到”，而是这个窗口内 6/6 的命中概率", 4)
rect(s, MARGIN, 1.42, W - 2 * MARGIN, 0.60, fill=TINT)
rich(s, MARGIN + 0.18, 1.50, W - 2 * MARGIN - 0.36, 0.46, [
    ("一次过板 = 单次盘存窗口内 6 个整机标签全部读到（6/6），不靠重复过板补读 —— 这是选型的唯一硬指标。", 11, True, ACCENT),
], spacing=1.2)

pic(s, "fig10_hw_modules.png", MARGIN, 2.14, 6.30, 2.24)
textbox(s, MARGIN, 4.50, 6.3, 0.26, "手册参数（逐条摘自厂家 datasheet / 产品页，未做实测）", size=9.5, color=GRAY)

rows = [
    ["型号（形态）", "口数 / 功率", "读取率", "过板 6/6"],
    ["Impinj R700（工业读头）", "4 口 · 33 dBm", "1100 tags/s", "✅ 首选"],
    ["Impinj R420（工业读头）", "4 口 · 32.5 dBm", "1100 tags/s", "✅ 满足"],
    ["RodinBell M-703 / E710", "8 口 · 33 dBm", "900 tags/s", "✅ 覆盖好"],
    ["Zebra FX9600（一体机）", "4/8 口 · 33 dBm", "—（−86 dBm）", "✅ 满足"],
    ["Kathrein RRU 4560（工业）", "4 口 · 33 dBm", "—（工业级）", "✅ 满足"],
    ["ThingMagic M6e（模块）", "4 口", "750 tags/s", "🟡 需实测"],
    ["Silion SQM5100 / QM100", "−79 dBm · 需外置 PA", "待定", "⚠ 先整机实测"],
]
table(s, rows, 7.10, 2.14, 5.61, [2.2, 1.5, 1.05, 0.95], row_h=0.335, fs=8.6, hfs=8.2,
      bold_first_col=True,
      aligns=[PP_ALIGN.LEFT, PP_ALIGN.LEFT, PP_ALIGN.CENTER, PP_ALIGN.CENTER])

textbox(s, MARGIN, 4.80, W - 2 * MARGIN, 0.26, "“一次过板读全 6 台”的三个必要条件（缺一项就掉到 5/6）", size=10, bold=True)
cards = [
    ("① 覆盖（空间）", "6 dBi 259×259 / 9 dBi 360×360 都盖不满 600×400 箱面",
     "→ 双天线或偏心安装；本机实测 ant4 最强、ant3 最弱"),
    ("② 极化（朝向）", "标签长轴固定，侧面照射直接掉 6–10 dB",
     "→ 天线极化与标签轴对齐；9 dBi 波束窄，对位不准反而更差"),
    ("③ 时间（速度）", "0.5 s 窗口、每标签≥2 次机会 ⇒ 整机 ≥ 24 tags/s",
     "→ 手册读取率是理想值，箱内实测要打七折"),
]
x = MARGIN
for head, body, tail in cards:
    rect(s, x, 5.10, 3.90, 1.08, fill="FAFBFC", line="E6E6E6")
    textbox(s, x + 0.16, 5.18, 3.6, 0.24, head, size=9.5, bold=True, color=ACCENT)
    textbox(s, x + 0.16, 5.44, 3.6, 0.34, body, size=9, color=INK, spacing=1.15)
    textbox(s, x + 0.16, 5.80, 3.6, 0.32, tail, size=8.5, color=GRAY, spacing=1.15)
    x += 4.06
takeaway(s, 6.35, "选型只看功率会选错：过板读全取决于「覆盖 + 极化 + 读取率」同时达标 —— 缺一项就是 5/6")

# ================================================================== 5 R3 距离
s = page("R3：距离对读取的影响（同一读码器 9 dBi）", "上/下/侧三种安装方向 × 0–50 cm 六档；箱型固定 KD-SP（小 Kinder · 塑料背壳）", 5)
pic(s, "fig5_3d_distance.png", MARGIN, 1.42, 6.35, 2.3)
pic(s, "fig7_distance_curve.png", 7.25, 1.40, 5.46, 2.6)
textbox(s, MARGIN, 3.92, 6.3, 0.26, "下置六档（产线方向）预测值", size=10, bold=True)
rows = [
    ["距离 cm", "0", "5", "10", "20", "30", "50"],
    ["读全数 /6", "6.00", "6.00", "6.00", "5.89", "4.56", "1.89"],
    ["RSSI dBm", "−33.5", "−41.5", "−47.5", "−53.5", "−57.1", "−61.5"],
]
table(s, rows, MARGIN, 4.22, 6.3, [1.1, 0.87, 0.87, 0.87, 0.87, 0.87, 0.87], row_h=0.36, fs=9, hfs=8.5,
      bold_first_col=True, aligns=[PP_ALIGN.LEFT] + [PP_ALIGN.CENTER] * 6)
rich(s, MARGIN, 5.62, 6.3, 0.7, [
    ("读全窗口 ≤10 cm；20 cm 起明显掉落，30 cm 约 4.6/6，50 cm 接近一半丢失。", 9.5, False, INK),
], spacing=1.2)
textbox(s, 7.25, 4.22, 5.4, 0.26, "为什么读距落到 cm 级", size=10, bold=True)
rich(s, 7.25, 4.54, 5.4, 1.5, [
    ("手册级自由空间读距：30 dBm + 6 dBi ≈ 8–10 m，9 dBi ≈ 11–14 m（+3 dB ≈ ×1.41）。", 9.5, False, INK),
    ("箱壁 + 塑料背壳 + 极化失配合计约 25–30 dB ⇒ 读距 ÷18–31，落到 0.3–0.6 m 量级。", 9.5, False, INK),
    ("侧面照射时标签长轴与天线电场正交，极化失配再吃 6–10 dB —— 这是曲线里最陡的一条。", 9.5, True, ACCENT),
], spacing=1.3)
takeaway(s, 6.35, "距离是可控变量：把天线面压到 ≤10 cm，读全率稳定；靠“加大功率”补距离的收益远小于压近距离")

# ================================================================== 6 R4+R5 读码器与厂家
s = page("R4 + R5：不同读码器（9 / 6 dBi）与不同厂家", "同一箱型（KD-SP）、同一姿态（A1 下置）、同一距离档位；只改一个变量", 6)
pic(s, "fig6_3d_readers.png", MARGIN, 1.40, 6.72, 2.2)
pic(s, "fig12_pass_window.png", 7.45, 1.52, 5.26, 2.50)
textbox(s, MARGIN, 3.80, 6.42, 0.26, "3D 对比配置（示意模型，按公开尺寸比例建模）", size=9.5, color=GRAY)
rows = [
    ["配置", "10 cm 读全/6", "30 cm 读全/6", "0.5 s 过板 6/6（20 cm）", "判定"],
    ["A 厂 + 9 dBi", "6.00", "5.22", "99.0%", "推荐基线"],
    ["A 厂 + 6 dBi", "6.00", "2.89", "79.0%", "远档掉"],
    ["B 厂 + 9 dBi", "6.00", "3.44", "82.7%", "勉强"],
    ["B 厂 + 6 dBi", "5.67", "2.00", "18.8%", "不可用"],
]
table(s, rows, MARGIN, 4.05, 6.42, [1.5, 1.35, 1.35, 1.75, 1.1], row_h=0.40, fs=8.8, hfs=8.2,
      bold_first_col=True,
      aligns=[PP_ALIGN.LEFT] + [PP_ALIGN.CENTER] * 3 + [PP_ALIGN.LEFT])
rich(s, 7.45, 4.05, 5.26, 1.9, [
    ("按“过板一次读全”看", 10, True, INK),
    ("0.5 s 窗口、20 cm：只有 A 厂 + 9 dBi 达到 99%，其余 79% / 83% / 19%。", 9.5, False, INK),
    ("30 cm 时 A 厂 + 9 dBi 掉到 68.9%，B 厂 + 9 dBi 只有 10.2% —— 远档靠天线增益，不靠厂家。", 9.5, False, INK),
    ("⇒ 选型结论：A 厂 + 9 dBi 作基线；换厂家最多补 2 dB，救不回远档。", 9.5, True, ACCENT),
], spacing=1.3)
takeaway(s, 6.35, "以「0.5 s 过板 6/6」为准：A 厂 + 9 dBi 99%，A 厂 + 6 dBi 79%，B 厂 + 6 dBi 仅 19%")

# ================================================================== 7 R6 六种箱型
s = page("R6：同一读码器(9 dBi) × 六种箱型", "项目代号见右表；距离固定 10 cm、姿态 A1、厂家 A —— 只有箱型不同", 7)
pic(s, "fig11_variants.png", MARGIN, 1.46, 6.55, 2.9)
rows = [
    ["代号", "箱型 / 背壳", "读全 /6"],
    ["KD-SP", "小 Kinder · 塑料背壳", "6.00"],
    ["KD-LP", "大 Kinder · 塑料背壳", "6.00"],
    ["KD-SM", "小 Kinder · 金属背壳", "2.44"],
    ["KD-LM", "大 Kinder · 金属背壳", "0.78"],
    ["PT-SM", "小平板 · 金属背壳", "4.44"],
    ["PT-LM", "大平板 · 金属背壳", "2.33"],
]
table(s, rows, 7.55, 1.46, 5.16, [1.05, 2.91, 1.2], row_h=0.40, fs=9.5, hfs=9,
      bold_first_col=True, aligns=[PP_ALIGN.CENTER, PP_ALIGN.LEFT, PP_ALIGN.CENTER])
rect(s, 7.55, 4.42, 5.16, 1.62, fill=TINT)
rich(s, 7.72, 4.52, 4.85, 1.45, [
    ("结论", 10, True, ACCENT),
    ("塑料背壳（KD-SP / KD-LP）稳定读全，尺寸影响可忽略。", 9.5, False, INK),
    ("金属背壳把读全数打到 0.8–4.4，大件更差 ⇒ 背壳材质是分水岭，不是距离。", 9.5, False, INK),
    ("平板类优于 Kinder（形体薄、遮挡少），但都无法在金属背壳下读全。", 9.5, False, INK),
], spacing=1.25)
takeaway(s, 6.35, "若产线要上金属背壳机型：要么改贴标位置（避开金属面），要么在箱外/开口侧增设天线")

# ================================================================== 8 框架
s = page("明天怎么填：三张表 → 自动出图", "填完 CSV 重跑 sim_model.py 即替换全部预测值；表结构已与报告 §4 对齐", 8)
cards = [
    ("A / B 组", "姿态 + 距离", "A_姿态.csv（6 行）\nB_距离_9dBi.csv（24 行）\n记：读全数/6、读取率、RSSI、拍照"),
    ("C 组", "厂家 × 增益", "C_厂家x增益.csv（12 行）\n4 配置 × 0/10/30 cm\n只改一个变量"),
    ("E 组", "六种箱型", "E_箱型.csv（6 行）\nKD-SP…PT-LM 六个代号\n固定 9 dBi / 10 cm / A1"),
]
x = MARGIN
for tag, head, body in cards:
    rect(s, x, 1.50, 3.9, 1.98, fill="FAFBFC", line="E6E6E6")
    textbox(s, x + 0.18, 1.60, 3.5, 0.26, tag, size=9.5, bold=True, color=ACCENT)
    textbox(s, x + 0.18, 1.88, 3.5, 0.30, head, size=12, bold=True)
    textbox(s, x + 0.18, 2.24, 3.5, 1.1, body, size=9, color="404040", spacing=1.3)
    x += 4.05

textbox(s, MARGIN, 3.70, 6.3, 0.26, "判定口径（建议，评审确认后固化）", size=10, bold=True)
rows = [
    ["判定", "阈值"],
    ["读全", "6/6，30 秒内全部读到且连续 3 箱成立"],
    ["可用", "平均 ≥5.4/6（90%），无箱低于 5/6"],
    ["临界", "平均 4.8–5.4/6，需调姿态或距离"],
    ["不可用", "平均 <4.8/6，或出现箱级 0 读"],
]
table(s, rows, MARGIN, 4.02, 6.3, [0.95, 5.35], row_h=0.36, fs=9.5, hfs=9,
      bold_first_col=True, aligns=[PP_ALIGN.CENTER, PP_ALIGN.LEFT])

textbox(s, 7.25, 3.70, 5.4, 0.26, "填写纪律（保证数据可用）", size=10, bold=True)
rich(s, 7.25, 4.02, 5.4, 1.6, [
    ("每个档位 ≥30 秒、≥3 箱；拍照必须带面标（F-FRONT / F-BACK）。", 9.5, False, INK),
    ("厂家/型号/天线增益/天线号 一档不留空 —— 否则归因无效。", 9.5, False, INK),
    ("箱子尺寸、背壳材质与厚度、箱内是否有金属件，全部记在「场地与标签」表。", 9.5, False, INK),
    ("测完 pause 释放 LLRP 会话，否则产线软件停读（实测已发生 5 次）。", 9.5, True, ACCENT),
], spacing=1.3)
takeaway(s, 6.35, "模板在 10_实测框架/；填完把数值贴进 _sim/*.csv 同名文件 → 重跑脚本，8 页全部换成实测")

# ================================================================== 备注
NOTES = {
    1: "封面。这一版按你重排后的 6 条要求组织：R1 放置方式（3D）、R2 模组类型（手册对比）、R3 距离、R4 增益、R5 厂家、R6 箱型。"
       "关键前提说清楚：除 R1/R2 是已确定内容，R3–R6 的数值都是手册参数推算 + 模型预测，明天实测替换。",
    2: "先给判定总表。被问“数据哪来的”就指向底部说明：功率/灵敏度/增益/标签 −22 dBm 来自厂家手册，"
       "箱体与背壳损耗是假设值，所以只保证趋势、不保证绝对值。",
    3: "R1。六种姿态用 Blender 渲染，蓝锥是天线主波束。要点：正面/背面同为长×高，靠防爆标识与条码面区分；"
       "A1 是本线实际姿态，其余作为对照。标签在箱内，箱面只有条码与序列号 —— 这句话能挡住“为什么不读箱面标签”的追问。",
    4: "R2。产品图来自厂家页面/datasheet，参数照抄手册：R700 33 dBm/4 口、R420 32.5 dBm/−84 dBm、"
       "M-703 8 口 900 tags/s、M6e 750 tags/s、FX9600 33 dBm/−86 dBm、RRU 4560 33 dBm、SQM5100（QM100）−79 dBm 需外置 PA。"
       "提醒：国产方案片内 PA 只有 4 dBm，整机功率靠外置功放，必须实测。",
    5: "R3。距离是主要变量：0–10 cm 稳读全，20 cm 起掉，50 cm 只剩 1.9/6。"
       "为什么手册说 8–14 m 而这里只有 cm 级：箱壁+塑料背壳+极化失配吃掉 25–30 dB，读距除以 18–31。"
       "侧面照射最差，因为标签长轴与天线电场正交。",
    6: "R4+R5。近距（≤10 cm）四种配置都 6/6，差异在远档显现：30 cm 时 9 dBi 比 6 dBi 多 2.3 个标签，"
       "A 厂比 B 厂多约 2 dB。结论：先换天线，再考虑换厂家。",
    7: "R6。六个箱型用项目代号。塑料背壳两类都 6/6；金属背壳直接掉到 0.8–4.4；"
       "平板类比 Kinder 略好但同样救不回来。若产线要上金属背壳，改贴标位置或在开口侧加天线。",
    8: "框架。三张 CSV：A/B（姿态+距离 30 行）、C（厂家×增益 12 行）、E（箱型 6 行）。"
       "填完贴回 _sim 同名文件重跑脚本，8 页图与表全部换实测值。纪律三条：≥30 秒 ≥3 箱、参数不留空、测完 pause。",
}
for i, sl in enumerate(prs.slides, start=1):
    if i in NOTES:
        sl.notes_slide.notes_text_frame.text = NOTES[i]

prs.save(OUT)
print("saved", OUT, os.path.getsize(OUT), "bytes,", len(prs.slides._sldIdLst), "slides")
