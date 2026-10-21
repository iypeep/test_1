# -*- coding: utf-8 -*-
"""生成 8 页汇报版 PPT（风格对齐 09_报告/_ref/风格参考示例.pdf：
白底 · 黑色粗体左标题 · 灰色细分隔线 · 灰阶为主 + 单一商务蓝强调）"""
import os
from pptx import Presentation
from pptx.util import Inches, Pt, Emu
from pptx.dml.color import RGBColor
from pptx.enum.text import PP_ALIGN, MSO_ANCHOR
from pptx.oxml.ns import qn
from lxml import etree

ROOT = r"E:\Desktop\RFID读取评估_2026-10-21"
FIG = os.path.join(ROOT, "09_报告", "figs")
OUT = os.path.join(ROOT, "09_报告", "RFID读取能力评估_2026-10-21.pptx")

INK, GRAY, LGRAY, LINE = "1A1A1A", "8C8C8C", "BFBFBF", "D9D9D9"
ACCENT, ACCENT_2, TINT = "3E5DA8", "5C7ED4", "E6EDF9"
COVER_BG = "DCE5F0"
LATIN, EA = "Arial", "微软雅黑"
W, H = 13.333, 7.5
MARGIN = 0.62

prs = Presentation()
prs.slide_width, prs.slide_height = Inches(W), Inches(H)
BLANK = prs.slide_layouts[6]


# ------------------------------------------------------------------ helpers
def set_font(run, size, bold=False, color=INK, italic=False):
    f = run.font
    f.size = Pt(size)
    f.bold = bold
    f.italic = italic
    f.name = LATIN
    f.color.rgb = RGBColor.from_string(color)
    rPr = run._r.get_or_add_rPr()
    for tag in ("a:ea", "a:cs"):
        el = rPr.find(qn(tag))
        if el is None:
            el = etree.SubElement(rPr, qn(tag))
        el.set("typeface", EA if tag == "a:ea" else LATIN)


def textbox(slide, x, y, w, h, text="", size=11, bold=False, color=INK,
            align=PP_ALIGN.LEFT, anchor=MSO_ANCHOR.TOP, spacing=1.0, space_after=0):
    tb = slide.shapes.add_textbox(Inches(x), Inches(y), Inches(w), Inches(h))
    tf = tb.text_frame
    tf.word_wrap = True
    tf.vertical_anchor = anchor
    tf.margin_left = tf.margin_right = tf.margin_top = tf.margin_bottom = 0
    lines = text.split("\n") if isinstance(text, str) else list(text)
    for i, line in enumerate(lines):
        p = tf.paragraphs[0] if i == 0 else tf.add_paragraph()
        p.alignment = align
        p.line_spacing = spacing
        p.space_after = Pt(space_after)
        r = p.add_run()
        r.text = line
        set_font(r, size, bold, color)
    return tb


def rich(slide, x, y, w, h, parts, align=PP_ALIGN.LEFT, anchor=MSO_ANCHOR.TOP, spacing=1.0):
    """parts: list of (text, size, bold, color) tuples, one paragraph each."""
    tb = slide.shapes.add_textbox(Inches(x), Inches(y), Inches(w), Inches(h))
    tf = tb.text_frame
    tf.word_wrap = True
    tf.vertical_anchor = anchor
    tf.margin_left = tf.margin_right = tf.margin_top = tf.margin_bottom = 0
    for i, (txt, size, bold, color) in enumerate(parts):
        p = tf.paragraphs[0] if i == 0 else tf.add_paragraph()
        p.alignment = align
        p.line_spacing = spacing
        r = p.add_run()
        r.text = txt
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


def page(title, kicker=None, num=None, bg=None):
    s = prs.slides.add_slide(BLANK)
    if bg:
        r = rect(s, 0, 0, W, H, fill=bg); r.shadow.inherit = False
        # 保证背景在最底层
        sp = r._element; sp.getparent().remove(sp); s.shapes._spTree.insert(2, sp)
    if title:
        textbox(s, MARGIN, 0.40, W - 2 * MARGIN, 0.55, title, size=23, bold=True)
        if kicker:
            textbox(s, MARGIN, 0.98, W - 2 * MARGIN, 0.30, kicker, size=11, color=GRAY)
            hline(s, MARGIN, 1.34, W - 2 * MARGIN)
        else:
            hline(s, MARGIN, 1.06, W - 2 * MARGIN)
    if num is not None:
        textbox(s, MARGIN, 7.00, 8.0, 0.26,
                "RFID 读取能力评估 · 7H3AA-PALLET · 2026-10-21", size=8, color=GRAY)
        textbox(s, W - MARGIN - 0.8, 7.00, 0.8, 0.26, f"{num} / 8", size=8, color=GRAY,
                align=PP_ALIGN.RIGHT)
        hline(s, MARGIN, 6.92, W - 2 * MARGIN, color="ECECEC")
    return s


def _border(cell, color=LINE, pt=0.75):
    tcPr = cell._tc.get_or_add_tcPr()
    for i, tag in enumerate(("a:lnL", "a:lnR", "a:lnT", "a:lnB")):
        old = tcPr.find(qn(tag))
        if old is not None:
            tcPr.remove(old)
        ln = etree.Element(qn(tag))
        ln.set("w", str(int(pt * 12700))); ln.set("cap", "flat"); ln.set("cmpd", "sng")
        ln.set("algn", "ctr")
        sf = etree.SubElement(ln, qn("a:solidFill"))
        c = etree.SubElement(sf, qn("a:srgbClr")); c.set("val", color)
        d = etree.SubElement(ln, qn("a:prstDash")); d.set("val", "solid")
        tcPr.insert(i, ln)


def table(slide, rows, x, y, w, col_w, row_h=0.30, fs=9.5, hfs=9.5,
          header_fill="F2F2F2", aligns=None, bold_first_col=False,
          header_color=INK, zebra=None):
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
            cell.margin_left = Inches(0.06); cell.margin_right = Inches(0.06)
            cell.margin_top = Inches(0.02); cell.margin_bottom = Inches(0.02)
            cell.vertical_anchor = MSO_ANCHOR.MIDDLE
            cell.fill.solid()
            if ri == 0 and header_fill:
                cell.fill.fore_color.rgb = RGBColor.from_string(header_fill)
            elif zebra and ri % 2 == 0:
                cell.fill.fore_color.rgb = RGBColor.from_string(zebra)
            else:
                cell.fill.fore_color.rgb = RGBColor.from_string("FFFFFF")
            _border(cell)
            txt = str(rows[ri][ci])
            tf = cell.text_frame
            tf.word_wrap = True
            p = tf.paragraphs[0]
            p.alignment = (aligns[ci] if aligns else (PP_ALIGN.CENTER if ci else PP_ALIGN.LEFT))
            p.line_spacing = 1.0
            bold = (ri == 0) or (bold_first_col and ci == 0)
            color = header_color if ri != 0 else INK
            for seg in txt.split("\n"):
                pass
            r = p.add_run(); r.text = txt
            set_font(r, hfs if ri == 0 else fs, bold, color)
    return shp


def stat(slide, x, y, w, num, unit, label, color=ACCENT):
    textbox(slide, x, y, w, 0.52, num, size=27, bold=True, color=color)
    textbox(slide, x, y + 0.50, w, 0.24, unit, size=9.5, color=GRAY)
    textbox(slide, x, y + 0.76, w, 0.42, label, size=10, color=INK, spacing=1.1)


def takeaway(slide, x, y, text, w=None):
    w = w or (W - x - MARGIN)
    rect(slide, x, y, 0.05, 0.34, fill=ACCENT)
    textbox(slide, x + 0.16, y + 0.02, w - 0.2, 0.32, text, size=11, bold=True, color=INK,
            anchor=MSO_ANCHOR.MIDDLE)


# ================================================================== 1 封面
s = page(None, bg=COVER_BG)
rect(s, MARGIN, 2.05, 0.06, 1.62, fill=ACCENT)
textbox(s, MARGIN + 0.22, 1.98, 9.5, 0.34, "华勤 · MD5 / MBD3MD3 · 线体 7H3PK1", size=11, color="595959")
textbox(s, MARGIN + 0.22, 2.32, 10.5, 0.72, "RFID 读取能力评估", size=40, bold=True, color="262626")
textbox(s, MARGIN + 0.22, 3.10, 10.8, 0.40, "卡通箱整机标签读取现状 · 测试方案 · 模组选型", size=17, color="404040")
hline(s, MARGIN + 0.22, 3.94, 4.6, color="A9BAD4", pt=1.0)
rich(s, MARGIN + 0.22, 4.10, 8.6, 0.9, [
    ("站点  7H3AA-PALLET   工位「自动扫描称重」", 12, False, "404040"),
    ("版本  V1（现状 + 测试方案）    2026-10-21    设备工程", 12, False, "404040"),
], spacing=1.5)
textbox(s, W - 3.3, H - 0.75, 2.7, 0.3, "数据来源：机台日志 · 实测 · datasheet", size=8.5, color="6A7A8C",
        align=PP_ALIGN.RIGHT)

# ================================================================== 2 目标与结论
s = page("评估目标与结论一览", "5 项要求逐条判定 —— 结论先行：能证实的三条，其余一律标待测", 2)
rows = [
    ["#", "要求（原始口径）", "判定", "现状依据 / 缺口"],
    ["R1", "卡通箱放置方式：哪一面为底面、接触读码器", "待实测", "六面定义 + A1–A6 姿态矩阵已固化；产线姿态按结构推断为 A1"],
    ["R2", "不同读码器（9 dB / 6 dB，不同厂家）读取状况", "待实测", "术语已澄清为天线增益；测试矩阵与固定项就绪，硬件未换过"],
    ["R3", "市面可挑选的 RFID 模组类型", "已完成", "4 类形态 + 6 家厂商关键规格（附公开来源）；选型建议见 P7"],
    ["R4", "上 / 下 / 侧面 读码器到箱体的距离", "待实测", "B1–B4 × 0/5/10/20/30/50 cm 矩阵已定，零数据"],
    ["R5", "不同厂商模组读这个标签的情况", "待实测", "标签侧已实测（Monza R6-P）；跨厂商需换硬件，按 C 组执行"],
]
table(s, rows, MARGIN, 1.62, W - 2 * MARGIN, [0.55, 3.7, 0.95, 6.6], row_h=0.62, fs=10,
      hfs=9.5, bold_first_col=True,
      aligns=[PP_ALIGN.CENTER, PP_ALIGN.LEFT, PP_ALIGN.CENTER, PP_ALIGN.LEFT])
takeaway(s, MARGIN, 5.55, "日志答不了“读到几个”；短板是可用性不是灵敏度；“6 dB / 9 dB”是天线增益（dBi）")
rich(s, MARGIN, 6.10, W - 2 * MARGIN, 0.7, [
    ("判定口径   已完成 = 有公开规格支撑、可直接进报告    待实测 = 方案就绪、无数据，不写入结论", 9.5, False, GRAY),
], spacing=1.1)

# ================================================================== 3 现状① 设备与标签
s = page("现状①：设备与标签（已证实）", "读码器配置来自 SettingPrm.xml；标签数据来自自研 LLRP 客户端 24,925 条直读", 3)
textbox(s, MARGIN, 1.55, 5.6, 0.26, "读码器配置", size=11, bold=True)
rows = [
    ["项", "值"],
    ["读码器", "192.168.1.100 · LLRP 5084 · HTTP 80"],
    ["发射功率 / 接收门限", "30 dBm / −80 dBm"],
    ["天线", "4 口（实测命中 ant1 / 3 / 4）"],
    ["启动延时 / 校验模式", "RfidStartDelay 1 · CheckFullOrSingle 2"],
    ["扫码枪 / PLC", "192.168.1.80:2002/2003 · 192.168.1.10:6000"],
    ["机台网卡", "10.22.196.40（MES）· 192.168.1.254（专网）"],
]
table(s, rows, MARGIN, 1.86, 5.75, [1.75, 4.0], row_h=0.40, fs=9.5, hfs=9,
      aligns=[PP_ALIGN.LEFT, PP_ALIGN.LEFT], bold_first_col=True)

textbox(s, 6.85, 1.55, 5.9, 0.26, "标签实测（EPC / TID / 芯片 / RSSI）", size=11, bold=True)
rows = [
    ["EPC (ASCII)", "TID 前缀", "芯片", "天线", "RSSI 均 / 范围"],
    ["A037001000071", "E2801170", "Monza R6-P", "1 / 3 / 4", "−53.3 ｜ −42.0 … −63.5"],
    ["B019001001229", "E2801170", "Monza R6-P", "1 / 3 / 4", "−63.4 ｜ −54.0 … −71.5"],
    ["500105089031902F", "—", "（非标签字段）", "4", "−75.6 ｜ −75.0 … −76.5"],
]
table(s, rows, 6.85, 1.86, 5.9, [1.55, 0.95, 1.25, 0.8, 1.9], row_h=0.40, fs=9, hfs=8.5,
      aligns=[PP_ALIGN.LEFT, PP_ALIGN.CENTER, PP_ALIGN.LEFT, PP_ALIGN.CENTER, PP_ALIGN.CENTER])
s.shapes.add_picture(os.path.join(FIG, "fig2_antenna.png"), Inches(6.85), Inches(3.72), width=Inches(3.05))
rich(s, 10.15, 3.78, 2.65, 2.2, [
    ("读图", 10, True, INK),
    ("ant4 最强、ant3 最弱；两条常驻标签都只有 3 支天线能读到。", 9.5, False, INK),
    ("⇒ 多天线布点直接影响“读全率”，是 R1/R4 测试必须记录的一项。", 9.5, False, ACCENT),
], spacing=1.25)
hline(s, MARGIN, 5.02, 5.75, color="ECECEC")
rich(s, MARGIN, 5.12, 5.75, 1.5, [
    ("为什么判为“设备标签”而不是整机标签", 10, True, INK),
    ("EPC 14 字节（非标准 96-bit），ASCII 形如设备序列号，与本站 EQSN A037001000150 同族。", 9.5, False, INK),
    ("TID 一律 E2 80 11 70…：E2 为 Gen2 硬性首字节，80 11 70 为 Impinj 厂商+型号。", 9.5, False, INK),
    ("判据：8 字节、50 开头的 hex 不可能是 TID，只能是 64 位 EPC 或非标签字段。", 9.5, False, GRAY),
], spacing=1.3)
takeaway(s, MARGIN, 6.35, "标签侧信号余量充足 ⇒ 读取问题不在标签灵敏度，需往“会话占用 / 姿态 / 距离”方向查")

# ================================================================== 4 现状② 日志盲区与停摆
s = page("现状②：日志答不了“读到几个”，且停摆复发", "EpcLog 全天结构与近 30 天停摆 —— 这是必须上外部探针的原因", 4)
stat(s, MARGIN, 1.55, 2.05, "99.6%", "EpcLog 占比", "两枚常驻设备标签的重复读取")
stat(s, MARGIN + 2.25, 1.55, 2.05, "30.8", "行 / 箱", "全天真整机标签仅约 250 行（0.2%）")
stat(s, MARGIN + 4.50, 1.55, 2.05, "5 次", "近 30 天", "4 次提前停摆 + 今日 16:16 起归零")
s.shapes.add_picture(os.path.join(FIG, "fig1_epc_30d.png"), Inches(MARGIN), Inches(2.72), width=Inches(7.15))
textbox(s, MARGIN, 5.44, 7.15, 0.26, "近 30 天每日 EpcLog 行数（蓝 = 提前停摆 / 今日截断）", size=8.5, color=GRAY)
rect(s, 8.30, 1.55, 4.42, 4.6, fill="FAFBFC", line="ECECEC")
textbox(s, 8.50, 1.70, 4.05, 0.26, "今日事故链（Main / Plc 日志时间戳）", size=10, bold=True)
rich(s, 8.50, 2.02, 4.05, 3.0, [
    ("16:16:01   EpcLog 最后一行", 9, False, INK),
    ("16:16:17   MultiReader(pid 7732) 取得 LLRP 会话", 9, False, INK),
    ("16:16–16:31   15 分钟 31 次 RfidFlow，31 次报错", 9, False, INK),
    ("            “must connect to the reader before…  ”", 8.5, False, GRAY),
    ("17:00–19:59   726 次流程，RFID 开启记录 0 次", 9, False, ACCENT),
    ("⇒ 不是漏读，是根本没在用（会话仍被占）", 9.5, True, ACCENT),
], spacing=1.45)
hline(s, 8.50, 4.35, 4.05, color="E0E0E0")
rich(s, 8.50, 4.45, 4.05, 1.5, [
    ("LLRP 是单客户端协议", 10, True, INK),
    ("多读器 / 我们的探针 / HQ Package System，谁占住 5084，其余全部连不上。", 9, False, INK),
    ("今日 ≤16:00：3,529 次流程中 3,064 次开启 ⇒ 参与率 89.3%。", 9, False, INK),
], spacing=1.3)
takeaway(s, MARGIN, 6.35, "要回答“一箱 6 个读到几个”，只能用外部探针 rfidmon 实测；日志只能证明读码器在工作")

# ================================================================== 5 R1 放置方式
s = page("R1：卡通箱放置方式 —— 先统一面定义，再做姿态矩阵", "正面与背面同为“长×高”，肉眼最易混；每张照片先贴面标再拍", 5)
s.shapes.add_picture(os.path.join(FIG, "fig3_box_faces.png"), Inches(MARGIN - 0.1), Inches(1.45), width=Inches(6.55))
rows = [
    ["#", "姿态", "哪个面朝下 / 朝读码器"],
    ["A1", "正立", "B-BOTTOM 朝下，读码器在下（产线基线）"],
    ["A2", "正立", "F-FRONT 朝读码器（侧面照射）"],
    ["A3", "正立", "F-BACK 朝读码器"],
    ["A4", "侧放", "F-FRONT 朝下（标签是否被遮挡）"],
    ["A5", "侧放", "F-BACK 朝下"],
    ["A6", "倒置", "T-TOP 朝下"],
]
table(s, rows, 7.30, 1.50, 5.42, [0.5, 0.8, 4.1], row_h=0.44, fs=9.5, hfs=9,
      aligns=[PP_ALIGN.CENTER, PP_ALIGN.CENTER, PP_ALIGN.LEFT], bold_first_col=True)
rect(s, 7.30, 4.98, 5.42, 0.86, fill=TINT)
rich(s, 7.46, 5.08, 5.1, 0.7, [
    ("待现场确认", 9.5, True, ACCENT),
    ("A1（正立、底面朝下、读码器在箱体下方）是按设备结构推定的产线实际姿态，需照片与卷尺确认后才能作为基线。", 9, False, INK),
], spacing=1.25)
takeaway(s, MARGIN, 6.30, "整机 RFID 标签在箱内机器上，不贴箱面 ⇒ 姿态影响来自金属遮挡与入射角，不是箱面材质")

# ================================================================== 6 R2 + R4
s = page("R2 + R4：读码器变量与距离矩阵", "先把术语与单变量原则固定，否则读距差异无法归因", 6)
rect(s, MARGIN, 1.50, 6.05, 0.92, fill="FAFBFC", line="E6E6E6")
rich(s, MARGIN + 0.16, 1.58, 5.75, 0.8, [
    ("术语纠正：9 dB / 6 dB = 天线增益（dBi），不是读码器参数", 10.5, True, ACCENT),
    ("读码器侧看输出功率（现场 30 dBm = 1 W）与接收门限（−80 dBm）；报告里必须分开写。", 9.5, False, INK),
], spacing=1.25)

textbox(s, MARGIN, 2.58, 6.05, 0.26, "B 组 · 距离矩阵（姿态固定 A1，每档 ≥30 秒、≥3 箱）", size=10, bold=True)
rows = [
    ["位置", "0", "5", "10", "20", "30", "50 cm"],
    ["上", "待测", "待测", "待测", "待测", "待测", "待测"],
    ["下", "待测", "待测", "待测", "待测", "待测", "待测"],
    ["正面侧", "待测", "待测", "待测", "待测", "待测", "待测"],
    ["背面侧", "待测", "待测", "待测", "待测", "待测", "待测"],
]
table(s, rows, MARGIN, 2.88, 6.05, [1.15, 0.9, 0.9, 0.9, 0.9, 0.9, 1.0], row_h=0.48, fs=9.5, hfs=9.5)
textbox(s, MARGIN, 5.40, 6.05, 0.5,
        "0 cm = 天线面紧贴箱面（不压箱）；每档记 distinct EPC 与 6/6 读全数、RSSI 与主命中天线。",
        size=9, color=GRAY, spacing=1.2)

textbox(s, 7.15, 1.50, 5.6, 0.26, "固定项（不得随测试变动）", size=10, bold=True)
rich(s, 7.15, 1.82, 5.6, 1.9, [
    ("发射功率 30 dBm（要对比功率档就单列一组）", 9.5, False, INK),
    ("Session 2 + DualTarget，天线固定同一支、其余禁用", 9.5, False, INK),
    ("单档 ≥30 秒且 ≥3 箱；记录金属托盘 / 邻机 / 人员走动", 9.5, False, INK),
], spacing=1.9)
hline(s, 7.15, 3.54, 5.6, color="ECECEC")
textbox(s, 7.15, 3.68, 5.6, 0.26, "6 dBi 与 9 dBi 怎么用（R2 关键）", size=10, bold=True)
rich(s, 7.15, 4.00, 5.6, 2.0, [
    ("+3 dB 增益 ≈ 自由空间读距 ×1.4，但波束变窄、对位更敏感。", 9.5, False, INK),
    ("产线箱体位姿固定 ⇒ 先用 9 dBi 解决对位，再用 6 dBi 求覆盖。", 9.5, False, INK),
    ("两支天线读到的时间差也要记：它是“能不能读全”的直接线索。", 9.5, False, INK),
], spacing=1.9)
takeaway(s, MARGIN, 6.10, "铁律：一次只改一个变量 —— 固定天线只换读码器，或固定读码器只换天线；否则读距差异无法归因")

# ================================================================== 7 R3 + R5
s = page("R3 + R5：模组选型与跨厂商对比", "先定形态再定型号；规格以公开资料为依据，下单前需复核最新 datasheet", 7)
rows = [
    ["厂商 / 型号", "形态", "关键规格（公开来源）", "与本项目的关系"],
    ["Impinj E710 平台", "工业读头 / 模块", "8 天线口 · 最大 33 dBm · 900 tags/s", "现场即 Impinj 体系，同厂替换做基线最优"],
    ["ThingMagic M6e", "嵌入式模块", "4 天线口 · 750 tags/s", "生态成熟，便于快速集成"],
    ["MagicRF QM100", "读芯片（国产）", "灵敏度 −79 dBm · 片内 PA 仅 4 dBm，需外置功放", "降本主力，须验外置 PA 后的一致性与读取率"],
    ["Kathrein / Feig", "工业读头", "多口 · 以太网 · 宽温（工业级）", "稳定性优先时的备选，价格高"],
    ["Zebra FX9600", "一体成品", "4/8 口 · 30 dBm 级 · 支持 PoE", "仓储产线通用，替换快"],
]
table(s, rows, MARGIN, 1.55, W - 2 * MARGIN, [1.9, 1.55, 4.2, 4.1], row_h=0.52, fs=9.5, hfs=9,
      aligns=[PP_ALIGN.LEFT, PP_ALIGN.LEFT, PP_ALIGN.LEFT, PP_ALIGN.LEFT], bold_first_col=True)
rect(s, MARGIN, 4.72, 6.0, 1.52, fill=TINT)
rich(s, MARGIN + 0.18, 4.82, 5.65, 1.35, [
    ("推荐倾向", 10, True, ACCENT),
    ("① 先用 Impinj E710 同厂替换做基线（变量最少、LLRP 客户端直接复用）", 9.5, False, INK),
    ("② 基线确认后取 MagicRF QM100 对比降本，重点验外置 PA 与 RSSI/TID 上报", 9.5, False, INK),
    ("③ 天线与读码器不同时换；A/B 只改一个变量", 9.5, True, ACCENT),
], spacing=1.25)
textbox(s, 6.95, 4.72, 5.75, 0.26, "必问供应商（完整 8 问见报告 §5.4）", size=10, bold=True)
rich(s, 6.95, 5.04, 5.75, 1.2, [
    ("输出功率范围与天线口数 ｜ 接收灵敏度（含自干扰条件）", 9.5, False, INK),
    ("实测读取率（非理论值）｜ 是否上报 RSSI / 相位 / TID", 9.5, False, INK),
    ("是否提供标准 LLRP 口 + SDK（.NET / C / REST）", 9.5, False, INK),
], spacing=1.4)
takeaway(s, MARGIN, 6.35, "无论最终选谁，验收口径统一：6 个标签读全率 ≥90% 且 R1–R4 条件下不掉档")

# ================================================================== 8 下一步
s = page("下一步：现场补数 → 出 V2", "顺序不可颠倒：先姿态确认，再 A/B 矩阵，最后换硬件", 8)
steps = [
    ("1", "现场拍照 + 面标", "确认 A1 实际姿态与六面照片\n需要：卷尺、相机、F-FRONT/F-BACK 纸标"),
    ("2", "A 组 + B 组取数", "6 姿态 × 4 位置 × 6 距离，约 30 档\n需要：30 分钟停机窗口 + rfidmon"),
    ("3", "C 组换硬件", "6 dBi / 9 dBi 天线各一支，第二家读码器\n需要：只改一个变量"),
    ("4", "填表出 V2", "填报告 §4 表格，补 R1/R2/R4/R5 结论\n产出：V2 报告 + 选型结论"),
]
x = MARGIN
for num, head, body in steps:
    rect(s, x, 1.55, 2.92, 2.30, fill="FAFBFC", line="E6E6E6")
    textbox(s, x + 0.18, 1.68, 0.6, 0.5, num, size=22, bold=True, color=ACCENT)
    textbox(s, x + 0.18, 2.22, 2.55, 0.26, head, size=11, bold=True)
    textbox(s, x + 0.18, 2.54, 2.55, 1.2, body, size=9, color="404040", spacing=1.3)
    x += 3.05

textbox(s, MARGIN, 4.10, 6.2, 0.26, "判定口径（建议，待评审确认）", size=10, bold=True)
rows = [
    ["判定", "阈值"],
    ["读全", "6/6 标签 30 秒内全读到，且连续 3 箱成立"],
    ["可用", "平均 ≥5.4/6（90%），无箱低于 5/6"],
    ["临界", "平均 4.8–5.4/6，需调姿态或距离"],
    ["不可用", "平均 <4.8/6，或出现箱级 0 读"],
]
table(s, rows, MARGIN, 4.42, 6.2, [1.0, 5.2], row_h=0.38, fs=9.5, hfs=9,
      aligns=[PP_ALIGN.CENTER, PP_ALIGN.LEFT], bold_first_col=True)

textbox(s, 7.20, 4.10, 5.5, 0.26, "同时可做（低成本）", size=10, bold=True)
rich(s, 7.20, 4.42, 5.5, 1.4, [
    ("会话占用检测 + 告警：被抢时在看板提示，避免流程静默无效", 9.5, False, INK),
    ("确认 FileAppender.log 停更原因（唯一带天线 DSN/RSSI 的现成日志，最后写入 10-07）", 9.5, False, INK),
], spacing=1.4)
takeaway(s, MARGIN, 6.35, "R1/R2/R4/R5 全部卡在“没有实测数据” —— 现场 30 分钟窗口即可补齐，之后 V2 只需填表")

# ================================================================== 备注（讲稿）
NOTES = {
    1: "封面。汇报对象是设备/工艺主管与客户评审，全篇结论先行：能证实的三条写在 P2 与 P4，其余标待测，不猜测。"
       "数据来源：机台日志 + 自研 LLRP 客户端 24,925 条实测 + 公开 datasheet。",
    2: "先给结论再讲细节。R1/R2/R4/R5 四项都卡在“没有实测数据”，原因不是没方案，而是需要现场 30 分钟窗口换硬件/量距离。"
       "如果被问到“是不是读码器不行”，指到 P4：今天的问题是会话被抢，不是灵敏度。",
    3: "标签侧是全篇唯一有硬数据的部分。要点：两条 EPC 是设备标签（14 字节、ASCII 像序列号），不是整机标签；"
       "芯片是 Impinj Monza R6-P；RSSI −42 到 −71 dBm，3 支天线都能读到 ⇒ 信号余量充足。"
       "所以后面要查的是姿态、距离、会话占用，不是标签。",
    4: "这是全篇最重要的一页：现有日志无法回答“一箱 6 个读到几个”。99.6% 是两枚常驻标签，真整机标签全天约 250 行；"
       "应用层只打 RfidFlow start/end，没有数量。右侧事故链说明今天 16:16 的真实停摆原因——MultiReader 抢了 LLRP 会话；"
       "17:00 后 726 次流程零次开启，是“没在用”而不是“漏读”。近 30 天 5 次同类停摆 ⇒ 可用性风险。",
    5: "R1。先统一面定义，避免“正面/背面”混用（两者同为长×高，最易混）。A1 是产线实际姿态（正立、底面朝下、读码器在下），"
       "但这是按设备结构推断的，必须现场拍照确认后才能当基线。注意标签在箱内机器上，不贴箱面。",
    6: "R2 + R4。先把术语纠正：6/9 dB 是天线增益 dBi，读码器看 30 dBm 输出与 −80 dBm 门限。距离矩阵 4 位置 × 6 档全部待测。"
       "关键纪律：一次只改一个变量。+3 dB 增益约等于自由空间读距 ×1.4，但波束变窄，先 9 dBi 解决对位再 6 dBi 求覆盖。",
    7: "R3 + R5。形态先定：本项目就是工业读头（分体式）。型号给到四家代表规格，来源是厂商公开资料，下单前必须复核。"
       "推荐顺序：先 Impinj E710 同厂做基线，再拿 MagicRF QM100 谈降本，天线和读码器不同时换。",
    8: "收口。四步：现场拍照确认姿态 → A/B 组矩阵 → C 组换硬件 → 填表出 V2。判定阈值是本报告的建议值，需评审确认。"
       "另外两项低成本动作：会话占用告警、查 FileAppender.log 为何 10-07 后停更。",
}
for i, sl in enumerate(prs.slides, start=1):
    if i in NOTES:
        sl.notes_slide.notes_text_frame.text = NOTES[i]

prs.save(OUT)
print("saved", OUT, os.path.getsize(OUT), "bytes,", len(prs.slides.__iter__.__self__._sldIdLst), "slides")
