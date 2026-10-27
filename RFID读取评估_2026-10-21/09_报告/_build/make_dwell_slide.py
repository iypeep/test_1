# -*- coding: utf-8 -*-
"""把「窗口 → 读到率」单开一页（插在「机型月统计结论」之后），并同步目录页码

页面元素（与 deck 其它页同一套：标题 / 副标题 / 分割线 / 表 / 图 / 结论 / 底部条）：
    · 表：窗口 / 箱数 / 读到 ≥1 台 / 均值（31 天 113,667 箱）
    · 图：figs/fig_dwell.png（折线 + 均值副轴，标出 3 s 附近临界）
    · 结论：两句白话，不用模型术语
    · 目录：重排为 10 条，页码与插入后一致

只新增形状（DWELL7_* / TOC_* 重绘），不改动任何已有形状的内容（目录页是脚本自己生成的，允许重排）。
用法：py -3.12 make_dwell_slide.py --pptx <源.pptx> --out <新.pptx>
"""
import os, argparse, datetime, shutil

from pptx import Presentation
from pptx.util import Inches, Pt
from pptx.dml.color import RGBColor
from pptx.enum.text import PP_ALIGN, MSO_ANCHOR
from pptx.enum.shapes import MSO_SHAPE, MSO_CONNECTOR
from pptx.oxml.ns import qn
from lxml import etree
from PIL import Image

_HERE = os.path.dirname(os.path.abspath(__file__))
REP = os.path.dirname(_HERE)
FIG = os.path.join(REP, "figs")

INK, GRAY, LINE = "1A1A1A", "8C8C8C", "D9D9D9"
ACCENT, TINT = "3E5DA8", "E6EDF9"
LATIN, EA = "Arial", "微软雅黑"
W, H, MARGIN = 13.333, 7.5, 0.62

ROWS = [("窗口", "箱数", "读到 ≥1 台", "均值"),
        ("<1 s", "114", "0.0%", "0.000"),
        ("1–2 s", "306", "0.3%", "0.003"),
        ("2–3 s", "53,109", "0.7%", "0.009"),
        ("3–4 s", "52,157", "0.2%", "0.002"),
        ("≥4 s", "7,981", "64.6%", "1.056")]

TOC = [("六种放置方式", 3), ("读取方向测试", 4), ("机型月统计", 5), ("机型月统计结论", 6),
       ("停留时间梯度测试", 7), ("RFID 距离梯度测试", 8), ("R4 9 / 6 dBi 对比", 9),
       ("R2 模组选型", 10), ("天线选型", 11), ("附录（手册出处 / 选型问题清单）", 13)]


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


def textbox(slide, x, y, w, h, lines, size=9, bold=False, color=INK,
            align=PP_ALIGN.LEFT, spacing=1.05, name=None, anchor=None):
    tb = slide.shapes.add_textbox(Inches(x), Inches(y), Inches(w), Inches(h))
    tf = tb.text_frame
    tf.word_wrap = True
    if anchor is not None:
        tf.vertical_anchor = anchor
    tf.margin_left = tf.margin_right = tf.margin_top = tf.margin_bottom = 0
    if isinstance(lines, str):
        lines = [lines]
    for i, item in enumerate(lines):
        text, sz, bd, col = item if isinstance(item, tuple) else (item, size, bold, color)
        p = tf.paragraphs[0] if i == 0 else tf.add_paragraph()
        p.alignment, p.line_spacing = align, spacing
        r = p.add_run(); r.text = text
        set_font(r, sz, bd, col)
    if name:
        tb.name = name
    return tb


def hline(slide, x, y, w, color=LINE, pt=0.75, name=None):
    c = slide.shapes.add_connector(MSO_CONNECTOR.STRAIGHT, Inches(x), Inches(y), Inches(x + w), Inches(y))
    c.line.color.rgb = RGBColor.from_string(color)
    c.line.width = Pt(pt)
    if name:
        c.name = name
    return c


def rect(slide, x, y, w, h, fill=None, name=None):
    sh = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, Inches(x), Inches(y), Inches(w), Inches(h))
    sh.shadow.inherit = False
    if fill:
        sh.fill.solid(); sh.fill.fore_color.rgb = RGBColor.from_string(fill)
    else:
        sh.fill.background()
    sh.line.fill.background()
    if name:
        sh.name = name
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


def table(slide, rows, x, y, w, col_w, row_h=0.42, name=None):
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
            cell.margin_left = cell.margin_right = Inches(0.06)
            cell.margin_top = cell.margin_bottom = Inches(0.012)
            cell.vertical_anchor = MSO_ANCHOR.MIDDLE
            cell.fill.solid()
            cell.fill.fore_color.rgb = RGBColor.from_string("F2F2F2" if ri == 0 else "FFFFFF")
            _border(cell)
            p = cell.text_frame.paragraphs[0]
            p.alignment = PP_ALIGN.CENTER if ci else PP_ALIGN.LEFT
            p.line_spacing = 1.0
            r = p.add_run(); r.text = rows[ri][ci]
            set_font(r, 9.2 if ri == 0 else 9.6, ri == 0 or ci == 0)
    if name:
        shp.name = name
    return shp


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--pptx", required=True)
    ap.add_argument("--out", required=True)
    a = ap.parse_args()

    prs = Presentation(a.pptx)

    # ------------------------------------------------ 1) 找到「机型月统计结论」页
    anchor = None
    for sl in prs.slides:
        if any(sh.has_text_frame and sh.text_frame.text.strip().startswith("机型月统计结论") for sh in sl.shapes):
            anchor = sl
            break
    if anchor is None:
        raise SystemExit("找不到「机型月统计结论」页")

    # 幂等：已存在则删掉重建
    for sl in list(prs.slides):
        if any(sh.name == "DWELL7_title" for sh in sl.shapes):
            sl._element.getparent().remove(sl._element)

    s = prs.slides.add_slide(prs.slide_layouts[6])
    sldIdLst = prs.slides._sldIdLst
    ids = list(sldIdLst)
    pos = [sl.slide_id for sl in prs.slides].index(anchor.slide_id)
    sldIdLst.remove(ids[-1])
    sldIdLst.insert(pos + 1, ids[-1])      # 插到「机型月统计结论」之后

    # ------------------------------------------------ 2) 页面内容
    textbox(s, MARGIN, 0.40, W - 2 * MARGIN, 0.55, [("停留时间梯度测试 - 3 s 卡在临界以下", 22, True, INK)],
            name="DWELL7_title")
    textbox(s, MARGIN, 0.96, W - 2 * MARGIN, 0.30,
            [("31 天 113,667 箱；窗口＝该箱从开始到判定结束的时长（机台日志逐箱对齐）", 10, False, GRAY)],
            name="DWELL7_kick")
    hline(s, MARGIN, 1.32, W - 2 * MARGIN, name="DWELL7_rule")

    table(s, ROWS, MARGIN, 1.52, 5.55, [1.35, 1.35, 1.55, 1.30], row_h=0.44, name="DWELL7_table")
    textbox(s, MARGIN, 1.52 + 0.44 * len(ROWS) + 0.08, 5.55, 0.34,
            [("≥4 s 的 7,981 箱多为慢箱 / 异常窗口，跨 16 天分布。", 7.6, False, GRAY)],
            name="DWELL7_tabnote")

    fig_path = os.path.join(FIG, "fig_dwell.png")
    iw, ih = Image.open(fig_path).size
    sc = min(6.15 / iw, 2.95 / ih)
    pic = s.shapes.add_picture(fig_path, Inches(6.45), Inches(1.46), Inches(iw * sc), Inches(ih * sc))
    pic.name = "DWELL7_fig"

    rect(s, 6.45, 4.44, 6.26, 1.06, fill=TINT, name="DWELL7_concl_box")
    textbox(s, 6.62, 4.54, 5.95, 1.24, [
        ("结论", 10, True, ACCENT),
        ("3 s 以内，读到过标签的箱不到 1%；放到 ≥4 s，直接到 64.6%（均值 0.01 → 1.06 台）。", 9.2, False, INK),
        ("⇒ 现在的 3 s 正卡在临界以下。", 9.2, True, INK),
    ], spacing=1.25, name="DWELL7_concl")

    textbox(s, MARGIN, 4.44, 5.55, 1.70, [
        ("同批箱已排除的变量", 9.4, True, GRAY),
        ("距离 0–50 cm：1.3 → 0，读数与距离无关", 8.8, False, INK),
        ("天线 9 / 6 dBi：0.79 vs 0.58 台（差 0.21）", 8.8, False, INK),
        ("背壳 塑料 / 金属：7.8% vs 8.7%", 8.8, False, INK),
        ("⇒ 剩下的差别就在「给了多少时间」这一项。", 8.8, True, ACCENT),
    ], spacing=1.28, name="DWELL7_excluded")

    rect(s, MARGIN, 6.34, 0.05, 0.34, fill=ACCENT, name="DWELL7_bar")
    textbox(s, MARGIN + 0.16, 6.36, W - 2 * MARGIN - 0.2, 0.30,
            [("距离、增益都已排除：先把停留放到 ≥5 s（或「读到即停」）复测 30 分钟。", 11, True, INK)],
            anchor=MSO_ANCHOR.MIDDLE, name="DWELL7_take")

    # ------------------------------------------------ 3) 目录重排（只动脚本自己生成的 TOC_* 形状）
    toc = None
    for sl in prs.slides:
        if any(sh.name == "TOC_title" for sh in sl.shapes):
            toc = sl
            break
    if toc is not None:
        for sh in list(toc.shapes):
            nm = sh.name or ""
            is_rule = str(sh.shape_type).startswith("LINE") or nm.startswith("Straight Connector") or nm.startswith("Connector")
            if is_rule or nm.startswith("TOC_") or nm.startswith("PX_"):
                sh._element.getparent().remove(sh._element)
        textbox(toc, MARGIN, 0.55, 6.0, 0.55, [("目录", 26, True, INK)], name="TOC_title")
        hline(toc, MARGIN, 1.30, W - 2 * MARGIN, name="TOC_rule")
        y = 1.52
        step = 0.50
        for i, (name, page) in enumerate(TOC, start=1):
            textbox(toc, MARGIN + 0.30, y, 0.55, 0.28, [(f"{i}", 10.5, True, ACCENT)], name=f"TOC_n{i}")
            textbox(toc, MARGIN + 0.85, y - 0.03, 8.4, 0.32, [(name, 12, False, INK)], name=f"TOC_t{i}")
            textbox(toc, MARGIN + 9.60, y - 0.03, 1.6, 0.32, [(str(page), 11, False, GRAY)], name=f"TOC_p{i}")
            hline(toc, MARGIN + 0.30, y + 0.44, W - 2 * MARGIN - 0.60, color="EFEFEF", name=f"TOC_l{i}")
            y += step

    prs.save(a.out)
    print("saved", a.out, os.path.getsize(a.out), "slides =", len(prs.slides._sldIdLst))


if __name__ == "__main__":
    main()
