# -*- coding: utf-8 -*-
"""新增第 10 页：包装机型口径（KKE / N-KKE × 背壳），并把「厂家」从包装变量里拆出来。

为什么加这一页（2026-10-23 经理口径）：
  * 分析单元是**包装机型**（KKE 金属版 / N-KKE 金属版 / KKE 塑料版 / N-KKE 塑料版），不是 RFID 厂家；
  * 金属背壳版：标签贴**中框**；塑料背壳版：标签贴**背壳**；KKE＝带卡通保护壳、N-KKE＝只有平板。
  * 唐博知同日确认「不同厂家的模组测试还没做」⇒ 原 R4+R5 页的 A/B 厂 2 dB 只是模型假设。

本脚本做三件事（只改第 8/9 页的文案，并追加 1 页）：
  1) 第 8 页（R4+R5）副标题补「厂家为模型假设、须按包装机型分组后重测」；
  2) 第 9 页（R6）结论条改成「金属背壳标签在中框 ⇒ 改侧向读」；
  3) 追加第 10 页：四象限表 + fig14 + 现网字段缺口 + 厂家对比的正确做法；
  4) 全页页脚 / 10 → / 11。

数据源：_sim/G_包装机型_模拟.csv（_build/make_pkg_variants.py 生成）
图：figs/fig14_pkg_variants.png

用法：
    py -3.12 make_slide10_pkg.py --pptx "E:\\Desktop\\RFID读取能力评估-改动版.pptx"
可重复执行（本页按 S10_ 前缀先清后加；追加过一次就不会重复追加）。
"""
import os, csv, argparse, shutil, datetime, copy

from pptx import Presentation
from pptx.util import Inches, Pt
from pptx.dml.color import RGBColor
from pptx.enum.text import PP_ALIGN, MSO_ANCHOR
from pptx.enum.shapes import MSO_SHAPE, PP_PLACEHOLDER
from pptx.oxml.ns import qn
from lxml import etree
from PIL import Image

_HERE = os.path.dirname(os.path.abspath(__file__))
REP = os.path.dirname(_HERE)
FIG = os.path.join(REP, "figs")
PKG_CSV = os.path.join(REP, "_sim", "G_包装机型_模拟.csv")

INK, GRAY, LINE = "1A1A1A", "8C8C8C", "D9D9D9"
ACCENT, TINT, RED = "3E5DA8", "E6EDF9", "C0504D"
LATIN, EA = "Arial", "微软雅黑"
W, H, MARGIN = 13.333, 7.5, 0.62
FIX_R4R5 = False      # 老 deck 的 R4+R5 页（有「配置」表）才需要
FIX_R6 = False        # 老 deck 的 R6 页「读全/6」列是空的时才打开
ADD_FIG11 = False     # 老 deck 的 R6 页左半页空着时才打开
TITLE = "包装机型口径：KKE / N-KKE × 背壳 —— 厂家不能混在包装里比"
KICK = ("经理 10-23 口径：金属背壳版标签贴中框、塑料背壳版贴背壳；KKE＝带卡通保护壳、N-KKE＝只有平板本身。"
        "条件 9 dBi / 箱面 10 cm / 姿态 A1，数值为模型预测")


# ------------------------------------------------------------------ 基础组件（与 make_slide6_r3 同源）
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


def textbox(slide, x, y, w, h, text, size=10, bold=False, color=INK,
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


def rich(slide, x, y, w, h, parts, spacing=1.0):
    tb = slide.shapes.add_textbox(Inches(x), Inches(y), Inches(w), Inches(h))
    tf = tb.text_frame
    tf.word_wrap = True
    tf.margin_left = tf.margin_right = tf.margin_top = tf.margin_bottom = 0
    for i, (t, sz, bold, color) in enumerate(parts):
        p = tf.paragraphs[0] if i == 0 else tf.add_paragraph()
        p.line_spacing = spacing
        r = p.add_run(); r.text = t
        set_font(r, sz, bold, color)
    return tb


def hline(slide, x, y, w, color=LINE, pt=0.75):
    from pptx.enum.shapes import MSO_CONNECTOR
    c = slide.shapes.add_connector(MSO_CONNECTOR.STRAIGHT, Inches(x), Inches(y), Inches(x + w), Inches(y))
    c.line.color.rgb = RGBColor.from_string(color)
    c.line.width = Pt(pt)
    return c


def rect(slide, x, y, w, h, fill=None, line=None):
    sh = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, Inches(x), Inches(y), Inches(w), Inches(h))
    sh.shadow.inherit = False
    if fill:
        sh.fill.solid(); sh.fill.fore_color.rgb = RGBColor.from_string(fill)
    else:
        sh.fill.background()
    if line:
        sh.line.color.rgb = RGBColor.from_string(line); sh.line.width = Pt(0.75)
    else:
        sh.line.fill.background()
    return sh


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


def table(slide, rows, x, y, w, col_w, row_h=0.36, fs=8.8, hfs=8.4,
          aligns=None, bold_first_col=False, header_fill="F2F2F2", highlight_rows=(), highlight_fill=TINT):
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
            cell.margin_left = cell.margin_right = Inches(0.05)
            cell.margin_top = cell.margin_bottom = Inches(0.01)
            cell.vertical_anchor = MSO_ANCHOR.MIDDLE
            cell.fill.solid()
            cell.fill.fore_color.rgb = RGBColor.from_string(
                header_fill if ri == 0 else (highlight_fill if ri in highlight_rows else "FFFFFF"))
            _border(cell)
            p = cell.text_frame.paragraphs[0]
            p.alignment = aligns[ci] if aligns else (PP_ALIGN.CENTER if ci else PP_ALIGN.LEFT)
            p.line_spacing = 1.0
            r = p.add_run(); r.text = str(rows[ri][ci])
            set_font(r, hfs if ri == 0 else fs, (ri == 0) or (bold_first_col and ci == 0))
    return shp


# ------------------------------------------------------------------ 读数据
def load_rows():
    if os.path.exists(PKG_CSV):
        return list(csv.DictReader(open(PKG_CSV, encoding="utf-8-sig")))
    # 兜底（CSV 缺失时不让页面开天窗）：与 make_pkg_variants.py 同参数的解析期望值
    return [
        {"包装机型": "N-KKE-塑料", "标签位置": "背壳", "下置_读全_6": "5.99", "侧向_读全_6": "5.06",
         "大件_8252_下置_读全_6": "5.92", "大件_8252_侧向_读全_6": "3.34"},
        {"包装机型": "KKE-塑料", "标签位置": "背壳", "下置_读全_6": "5.95", "侧向_读全_6": "3.92",
         "大件_8252_下置_读全_6": "5.73", "大件_8252_侧向_读全_6": "1.89"},
        {"包装机型": "N-KKE-金属", "标签位置": "中框", "下置_读全_6": "3.05", "侧向_读全_6": "5.73",
         "大件_8252_下置_读全_6": "1.17", "大件_8252_侧向_读全_6": "4.88"},
        {"包装机型": "KKE-金属", "标签位置": "中框", "下置_读全_6": "1.63", "侧向_读全_6": "5.22",
         "大件_8252_下置_读全_6": "0.43", "大件_8252_侧向_读全_6": "3.64"},
    ]


def build_page(s, notes_template):
    # 页眉
    tb = textbox(s, MARGIN, 0.40, W - 2 * MARGIN, 0.55, TITLE, size=22, bold=True)
    tb.name = "S10_title"
    tb = textbox(s, MARGIN, 0.96, W - 2 * MARGIN, 0.30, KICK, size=9.8, color=GRAY)
    tb.name = "S10_kick"
    hline(s, MARGIN, 1.32, W - 2 * MARGIN).name = "S10_line"

    # 左：四象限表（推荐方向列 + 推荐值着色）
    rows = [["包装机型", "标签位置", "下置 读全/6", "侧向 读全/6", "推荐", "7″ 大件\n下置 / 侧向"]]
    rec_col = []
    for r in load_rows():
        rec = "下置" if r["标签位置"] == "背壳" else "侧向"
        rec_col.append(rec)
        rows.append([r["包装机型"], r["标签位置"], r["下置_读全_6"], r["侧向_读全_6"], rec,
                     f"{r['大件_8252_下置_读全_6']} / {r['大件_8252_侧向_读全_6']}"])
    tb = table(s, rows, MARGIN, 1.46, 6.55, [1.72, 0.78, 1.02, 1.02, 0.72, 1.5], row_h=0.42,
               fs=9.2, hfs=8.0, bold_first_col=True,
               aligns=[PP_ALIGN.LEFT, PP_ALIGN.CENTER, PP_ALIGN.CENTER, PP_ALIGN.CENTER,
                       PP_ALIGN.CENTER, PP_ALIGN.CENTER])
    tb.name = "S10_table"
    # 推荐方向所在列的数字加粗着色，避免「整行高亮」被误读成整行都推荐
    tbl = tb.table
    for i, rec in enumerate(rec_col, start=1):
        ci = 2 if rec == "下置" else 3
        for run in tbl.cell(i, ci).text_frame.paragraphs[0].runs:
            set_font(run, 9.6, True, ACCENT)
        for run in tbl.cell(i, 4).text_frame.paragraphs[0].runs:
            set_font(run, 9.0, True, ACCENT)
    tb = textbox(s, MARGIN, 3.62, 6.55, 0.24,
                 "同一读码器 9 dBi、箱面 10 cm、姿态 A1、A 厂；蓝色＝该包装机型的推荐照射方向", size=7.8, color=GRAY)
    tb.name = "S10_tabcap"

    # 左下：读法（三条）
    r = rich(s, MARGIN, 3.96, 6.55, 1.42, [
        ("读法：照射方向必须跟标签位置配对", 9.6, True, ACCENT),
        ("① 标签在背壳（塑料版）⇒ 用下置天线；标签在中框（金属版）⇒ 用侧向天线。", 8.6, False, INK),
        ("② 用错方向：金属批次 5.73 → 3.05。10-22 现场「距离 0→40 cm 读数都在 0–1」正对上 —— "
         "下置天线对中框标签本来就无效，不是距离不够近。", 8.6, False, INK),
        ("③ KKE 相对 N-KKE 固定再吃 2.5 dB；大件 7″ 再 −3.5 dB，金属 + KKE 大件最差（0.43/6）。", 8.6, False, INK),
    ], spacing=1.22)
    r.name = "S10_read"

    # 左底：厂家对比的正确做法
    bw = 6.55
    rect(s, MARGIN, 5.16, bw, 0.96, fill=TINT).name = "S10_venbox"
    r = rich(s, MARGIN + 0.14, 5.24, bw - 0.26, 0.84, [
        ("厂家对比：把「厂家」从包装变量里拆出来", 9.2, True, ACCENT),
        ("固定：包装机型 + 箱型 + 姿态 A1 + 天线方向/距离 + 过板 ≥30 s × ≥3 箱；变量：只换读码器/天线。",
         8.2, False, INK),
        ("厂家（A/B 模组）实测仍未做（唐工 10-23）；报告里的「B 厂 −2 dB」是模型假设 —— "
         "必须在同一包装机型、同一箱体下只换读码器重测。",
         8.2, False, RED),
    ], spacing=1.2)
    r.name = "S10_vendor"

    # 右：图
    p = os.path.join(FIG, "fig14_pkg_variants.png")
    iw, ih = Image.open(p).size
    maxw, maxh = 5.95, 2.70
    sc = min(maxw / iw, maxh / ih)
    pic = s.shapes.add_picture(p, Inches(7.13), Inches(1.46), Inches(iw * sc), Inches(ih * sc))
    pic.name = "S10_fig"

    # 右下：现网字段缺口
    x2, w2 = 7.13, 5.58
    rect(s, x2, 4.28, w2, 1.84, fill="FFFFFF", line=LINE).name = "S10_gapbox"
    r = rich(s, x2 + 0.14, 4.36, w2 - 0.26, 1.70, [
        ("现网还分不出 KKE / N-KKE", 9.4, True, RED),
        ("背壳材质有：MES CongfigSize 写 (Metal)/(Plastic)，AX8252 两种都在产。", 8.2, False, INK),
        ("KKE / N-KKE 没有：机台日志、Rfid_<日期>.log、EpcLog 里都没有这个字段。", 8.2, False, INK),
        ("现网能按背壳分：8252 塑料 98.9%、8252 金属 95.2%、7907 未标注 99.1%（都是几乎全漏）；"
         "KKE / N-KKE 分不出 —— 材质与外壳的效应被系统级漏读压平（与 R6 页「没拉开差距」不矛盾）。",
         8.2, False, INK),
        ("需要：机型 × KKE/N-KKE 的配置码或 BOM 区分方式（拿到才能按四象限重算箱数）。", 8.2, True, ACCENT),
    ], spacing=1.18)
    r.name = "S10_gap"

    # 底部结论条
    bar = rect(s, MARGIN, 6.52, 0.05, 0.32, fill=ACCENT)
    bar.name = "S10_bar"
    tb = textbox(s, MARGIN + 0.16, 6.53, W - 2 * MARGIN - 0.2, 0.30,
                 "按包装机型分组：金属背壳批次改侧向读（3.05 → 5.73）；KKE 再吃 2.5 dB —— 厂家差异要在这之后才谈",
                 size=10.2, bold=True, anchor=MSO_ANCHOR.MIDDLE)
    tb.name = "S10_take"

    if notes_template is None:
        return
    ns = s.notes_slide  # 备注：deck 的 notes master 没有正文占位符时从既有备注页复制
    if ns.notes_text_frame is None:
        # 本 deck 的 notes master 没有正文占位符：从既有备注页复制一个
        for sp in notes_template.shapes:
            if sp.placeholder_format.type == PP_PLACEHOLDER.BODY:
                ns.shapes._spTree.append(copy.deepcopy(sp._element))
                break
    ns.notes_text_frame.text = (
        "这一页是 10-23 按经理口径新加的：分析单元改成「包装机型」，不是 RFID 厂家。"
        "两条硬件事实决定了读取几何：金属背壳版的标签贴在中框，正下方被金属背壳屏蔽，只能用侧向天线读；"
        "塑料背壳版的标签直接贴在背壳上，正对箱底，下置天线是最好条件。"
        "KKE 是带卡通保护壳包装，N-KKE 是只有平板本身，卡通壳按模型固定再吃 2.5 dB。"
        "四个象限的预测：塑料下置 5.95–5.99，金属下置只有 1.63–3.05、换侧向 5.22–5.73。"
        "这正好解释 10-22 现场「0 到 40 cm 读数都在 0–1」：不是距离不够近，是照射方向与标签位置不匹配。"
        "另外要主动交代三点：一是现网日志里没有 KKE/N-KKE 字段，只有 (Metal)/(Plastic)，所以之前只能按机型+背壳分组，"
        "要按四象限重算箱数需要事业部给配置码或 BOM 区分；二是厂家 A/B 的 2 dB 是模型假设，"
        "模组实测还没做（唐工下午补），必须在固定包装机型的前提下重测，否则厂家与包装混在一起，结论不可用。"
        "三是这一页与 R6 页的实测不矛盾：现网按背壳分也几乎全漏（98.9% vs 95.2%），"
        "材质差异被系统级漏读压平；金属背壳的真正问题是照射方向与标签位置不匹配，不是「金属就一定更差」。"
    )


# ------------------------------------------------------------------ 第 8 页配置表（4 配置）
C_CSV = os.path.join(REP, "_sim", "C_厂家x增益_模拟.csv")
F_CSV = os.path.join(REP, "_sim", "F_过板读全概率.csv")
JUDGE = {("A-Impinj体系", "9"): "推荐基线", ("A-Impinj体系", "6"): "远档掉",
         ("B-国产方案", "9"): "勉强", ("B-国产方案", "6"): "不可用"}


def rebuild_reader_table(slide):
    tgt = None
    for sh in slide.shapes:
        if getattr(sh, "has_table", False) and sh.has_table and sh.table.cell(0, 0).text.strip() == "配置":
            tgt = sh
            break
    if tgt is None:
        print("no reader table found")
        return
    x, y, w = tgt.left / 914400, tgt.top / 914400, tgt.width / 914400

    f20 = {(r["厂家"], r["天线增益_dBi"]): r["过板读全概率_0.5s_%"]
           for r in csv.DictReader(open(F_CSV, encoding="utf-8-sig")) if r["距离_cm"] == "20"}
    rows = [["配置", "10 cm 读全/6", "30 cm 读全/6", "0.5 s 过板 6/6（20 cm）", "判定"]]
    for vendor, gain in (("A-Impinj体系", "9"), ("A-Impinj体系", "6"),
                         ("B-国产方案", "9"), ("B-国产方案", "6")):
        recs = [r for r in csv.DictReader(open(C_CSV, encoding="utf-8-sig"))
                if r["厂家"] == vendor and r["天线增益_dBi"] == gain]
        c10 = next(r for r in recs if r["距离_cm"] == "10")
        c30 = next(r for r in recs if r["距离_cm"] == "30")
        label = f"{vendor.split('-')[0]} 厂 + {gain} dBi"
        rows.append([label, f"{float(c10['读全数_6']):.2f}", f"{float(c30['读全数_6']):.2f}",
                     f"{float(f20[(vendor, gain)]):.1f}%", JUDGE[(vendor, gain)]])

    tgt._element.getparent().remove(tgt._element)
    tb = table(slide, rows, x, max(y, 4.42), w, [1.9, 1.5, 1.5, 2.35, 1.45], row_h=0.38, fs=9.5, hfs=8.6,
               bold_first_col=True,
               aligns=[PP_ALIGN.LEFT] + [PP_ALIGN.CENTER] * 3 + [PP_ALIGN.LEFT])
    tb.name = "S8_table_fixed"
    print("rebuilt reader table:", len(rows) - 1, "configs")


# ------------------------------------------------------------------ 第 9 页（R6）
E_CSV = os.path.join(REP, "_sim", "E_箱型对比_模拟.csv")


def fix_r6_slide(slide, prs):
    val = {}
    if os.path.exists(E_CSV):
        for r in csv.DictReader(open(E_CSV, encoding="utf-8-sig")):
            val[r["代号"]] = float(r["读全数_6"])
    filled = 0
    for sh in slide.shapes:
        if (getattr(sh, "has_table", False) and sh.has_table
                and sh.table.cell(0, 0).text.strip() == "代号" and len(sh.table.columns) > 2):
            tbl = sh.table
            for ri in range(1, len(tbl.rows)):
                code = tbl.cell(ri, 0).text.strip()
                cell = tbl.cell(ri, 2)
                if code in val:
                    cell.text_frame.paragraphs[0].clear()
                    run = cell.text_frame.paragraphs[0].add_run()
                    run.text = f"{val[code]:.2f}"
                    set_font(run, 9.5, True, ACCENT if val[code] >= 5.4 else RED)
                    cell.text_frame.paragraphs[0].alignment = PP_ALIGN.CENTER
                    filled += 1
    # 「结论」底色块原高 1.62"，正文只有 4 行 → 收到 1.28"，避免下方大片空白
    for sh in slide.shapes:
        if sh.shape_type == 1 and abs(sh.width / 914400 - 5.16) < 0.05 and sh.height / 914400 > 1.4:
            sh.height = Inches(1.30)
    has_pic = any(sh.shape_type == 13 for sh in slide.shapes)
    if not has_pic and ADD_FIG11:
        p = os.path.join(FIG, "fig11_variants.png")
        iw, ih = Image.open(p).size
        sc = min(6.6 / iw, 3.4 / ih)
        pic = slide.shapes.add_picture(p, Inches(MARGIN), Inches(1.55), Inches(iw * sc), Inches(ih * sc))
        pic.name = "S9_fig11"
        print("added fig11 to R6 slide")
    print("filled R6 读全 column:", filled)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--pptx", required=True)
    ap.add_argument("--out", default="")
    a = ap.parse_args()
    src, out = a.pptx, (a.out or a.pptx)
    if out == src:
        bak = os.path.splitext(src)[0] + ".bak-pkg-" + datetime.datetime.now().strftime("%H%M%S") + ".pptx"
        shutil.copy2(src, bak); print("backup:", bak)

    prs = Presentation(src)

    # -------------------------------------------------- 1) 第 8 页（R4+R5）副标题补口径
    s8 = prs.slides[7]
    for sh in s8.shapes:
        if sh.has_text_frame and "只改一个变量" in sh.text_frame.text:
            for para in sh.text_frame.paragraphs:
                for run in para.runs:
                    if "只改一个变量" in run.text:
                        run.text = ("同一箱型（7907-P）、同一姿态（A1 下置）、同一距离档位；只改一个变量 —— "
                                    "厂家 A/B 为模型假设（模组实测待补），且须按包装机型分组后才可比（见 P10）")
                        set_font(run, 9.2, False, GRAY)
            print("patched slide8 subtitle")

    # -------------------------------------------------- 1b) 第 8 页（R4+R5）配置表：原表被误删成
    # 2 个配置且 B 厂行套着 A 厂的数据 —— 按 _sim 的 C/F 两个 CSV 重建成 4 配置
    if FIX_R4R5:
        rebuild_reader_table(s8)

    # -------------------------------------------------- 2) R6 页结论条指向新页（按标题定位，不依赖页序）
    r6 = None
    for sl in prs.slides:
        if any(sh.has_text_frame and sh.text_frame.text.strip().startswith("R6") for sh in sl.shapes):
            r6 = sl
    if r6 is None:
        raise SystemExit("找不到 R6 页")
    if FIX_R6:
        fix_r6_slide(r6, prs)
    for sh in r6.shapes:
        if sh.has_text_frame and "若产线要上金属背壳机型" in sh.text_frame.text:
            for para in sh.text_frame.paragraphs:
                for run in para.runs:
                    if "若产线要上金属背壳机型" in run.text:
                        run.text = ("若产线要上金属背壳机型（标签在中框）：把读取方向改成侧向，下置天线对它无效（见下页四象限）")
            print("patched R6 takeaway")


    # -------------------------------------------------- 3) 新建 / 重建「包装机型口径」页，插到 R6 页之后
    target = None
    for sl in prs.slides:
        if any(sh.has_text_frame and sh.text_frame.text.startswith("包装机型口径") for sh in sl.shapes):
            target = sl
            break
    if target is None:
        target = prs.slides.add_slide(prs.slide_layouts[6])
        sldIdLst = prs.slides._sldIdLst
        ids = list(sldIdLst)
        sldIdLst.remove(ids[-1])                      # 刚追加的这张
        pos = list(prs.slides).index(r6) + 1           # 插到 R6 页之后
        sldIdLst.insert(pos, ids[-1])
        print(f"inserted packaging slide at position {pos + 1}")
    else:
        for sh in list(target.shapes):
            sh._element.getparent().remove(sh._element)
        print("rebuilt existing packaging slide")
    notes_tpl = None
    for sl in prs.slides:
        try:
            if sl.notes_slide.notes_text_frame is not None:
                notes_tpl = sl.notes_slide
                break
        except Exception:
            pass
    if notes_tpl is not None:
        build_page(target, notes_tpl)
    else:
        build_page(target, None)

    # -------------------------------------------------- 4) 页脚按页码重排（本 deck 手工删过页，
    # 原有 "4 / 10""6 / 10""7 / 10" 与实际页码已经对不上，这里统一按 幻灯片序号 / 总页数 重写）
    total = len(prs.slides._sldIdLst)
    import re
    for idx, sl in enumerate(prs.slides, start=1):
        for sh in sl.shapes:
            if sh.has_text_frame:
                for p in sh.text_frame.paragraphs:
                    for run in p.runs:
                        if re.fullmatch(r"\d+\s*/\s*\d+", run.text.strip()):
                            run.text = f"{idx} / {total}"

    prs.save(out)
    print("saved", out, os.path.getsize(out), "bytes; slides =", len(prs.slides._sldIdLst))


if __name__ == "__main__":
    main()
