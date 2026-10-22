# -*- coding: utf-8 -*-
"""重做「R3 距离对读取的影响」页：按现场实测重标定后的口径。

现场条件（用户口径 + 实测）：
  * 3 个 RFID 天线（底 / 侧 / 顶），天线面到箱面均 < 5 cm；
  * 31 天 113,667 箱：平均 0.08/6，95.0% 一箱 0 个；
  * 10-19 中箱（金属件）：8 次试验单次最多 2/6。
⇒ 旧模型「≤10 cm 读全 6/6」作废；把 28.6 dB 综合损耗（箱内负载/遮挡/极化/窗口）补进模型后重画。

用法：
    python make_slide6_r3.py --pptx "E:\\Desktop\\RFID读取能力评估-改动版.pptx"
只改第 6 页（索引 5），其余页不动；可重复执行（按 S6_ 前缀先清后加）。
"""
import os, csv, argparse, shutil, datetime

from pptx import Presentation
from pptx.util import Inches, Pt
from pptx.dml.color import RGBColor
from pptx.enum.text import PP_ALIGN, MSO_ANCHOR
from pptx.enum.shapes import MSO_SHAPE
from pptx.oxml.ns import qn
from lxml import etree
from PIL import Image

_HERE = os.path.dirname(os.path.abspath(__file__))
REP = os.path.dirname(_HERE)
FIG = os.path.join(REP, "figs")
CAL_CSV = os.path.join(REP, "_sim", "R3_距离_标定.csv")

INK, GRAY, LINE = "1A1A1A", "8C8C8C", "D9D9D9"
ACCENT, TINT, RED = "3E5DA8", "E6EDF9", "C0504D"
LATIN, EA = "Arial", "微软雅黑"
W, MARGIN = 13.333, 0.62
SLIDE_NO = 6


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


def table(slide, rows, x, y, w, col_w, row_h=0.3, fs=8.8, hfs=8.4,
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


def stat(slide, x, y, w, num, unit, label, color=ACCENT):
    textbox(slide, x, y, w, 0.44, num, size=22, bold=True, color=color)
    textbox(slide, x, y + 0.40, w, 0.22, unit, size=8.8, color=GRAY)
    textbox(slide, x, y + 0.62, w, 0.52, label, size=9.2, color=INK, spacing=1.15)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--pptx", required=True)
    ap.add_argument("--out", default="")
    a = ap.parse_args()
    src, out = a.pptx, (a.out or a.pptx)
    if out == src:
        bak = os.path.splitext(src)[0] + ".bak-r3-" + datetime.datetime.now().strftime("%H%M%S") + ".pptx"
        shutil.copy2(src, bak); print("backup:", bak)

    prs = Presentation(src)
    s = prs.slides[SLIDE_NO - 1]
    for sh in list(s.shapes):
        if sh.name.startswith("S6_"):
            sh._element.getparent().remove(sh._element)

    # ------------------------------------------------ 标题改成“按实测重标定”
    for sh in s.shapes:
        if sh.has_text_frame and "距离对读取的影响" in sh.text_frame.text:
            for para in sh.text_frame.paragraphs:
                for r in para.runs:
                    r.text = "R3：距离对读取的影响（按现场实测重标定）"
            break

    # ------------------------------------------------ 标题区补充（保留原标题与分割线）
    tb = textbox(s, MARGIN, 0.96, W - 2 * MARGIN, 0.30,
                 "现场 3 个 RFID 天线（底 / 侧 / 顶）到箱面均 < 5 cm；同一几何实测平均 0.08/6（95.0% 一箱 0 个）"
                 " ⇒ 旧「≤10 cm 可读全」结论作废", size=10.5, color=GRAY)
    tb.name = "S6_sub"

    # ------------------------------------------------ 左：三个数字 + 标定表
    stat(s, MARGIN, 1.42, 3.3, "3 个天线 · <5 cm", "底 / 侧 / 顶三面布置，天线面到箱面均 <5 cm",
         "距离已经压到底，不再是可调变量", color=ACCENT)
    stat(s, 4.05, 1.42, 3.3, "95.0%", "一箱读到 0 个整机标签（31 天 113,667 箱）",
         "现网 RFID 环节基本不产出结果", color=RED)
    t = textbox(s, MARGIN, 2.86, 6.6, 0.24, "标定前后对比（下置＝产线姿态）", size=9.5, bold=True, color=ACCENT)
    t.name = "S6_cap"

    rows = [["距离 cm", "旧模型 读全 /6", "标定后 读全 /6", "单标签命中率"]]
    if os.path.exists(CAL_CSV):
        for r in csv.DictReader(open(CAL_CSV, encoding="utf-8-sig")):
            if r["位置"] != "下":
                continue
            new = float(r["标定后_读全_6"])
            rng = f"{float(r['单标签命中率_%']):.2f}%" if float(r["单标签命中率_%"]) >= 0.01 else "<0.01%"
            rows.append([r["距离_cm"], f"{float(r['旧模型_读全_6']):.2f}",
                         f"{new:.3f}" if 0 < new < 0.01 else f"{new:.2f}", rng])
    tb = table(s, rows, MARGIN, 3.16, 6.55, [1.15, 1.9, 1.9, 1.6], row_h=0.32, fs=8.8, hfs=8.4,
               aligns=[PP_ALIGN.CENTER] * 4, bold_first_col=True, highlight_rows=(1,))
    tb.name = "S6_table"

    rich(s, MARGIN, 5.14, 6.55, 1.15, [
        ("怎么标定的（可复算）", 9.5, True, ACCENT),
        ("把「箱内负载 + 多台金属件遮挡 + 极化/朝向 + 过板窗口」的综合损耗 28.6 dB 补进模型，"
         "使 5 cm 处期望值落到实测的 0.08/6；0–5 cm 视为同一档，不对更近场外推。", 8.8, False, INK),
        ("旁证：10-19 中箱（金属件）8 次试验单次最多只读到 2/6，且前/后面几乎为 0。", 8.8, False, INK),
    ], spacing=1.2)

    tb = textbox(s, MARGIN, 5.92, 6.55, 0.26,
                 "⚠ 旧模型那列数字（6.00 / 5.89 / 4.56 / 1.89）不要再单独对外引用。",
                 size=9, bold=True, color=RED)
    tb.name = "S6_warn"

    # ------------------------------------------------ 右：图
    p = os.path.join(FIG, "fig7r_distance_recal.png")
    iw, ih = Image.open(p).size
    maxw, maxh = 6.0, 3.05
    sc = min(maxw / iw, maxh / ih)
    pic = s.shapes.add_picture(p, Inches(7.02), Inches(1.40), Inches(iw * sc), Inches(ih * sc))
    pic.name = "S6_fig"

    tb = textbox(s, 7.02, 4.62, 5.7, 0.5,
                 "灰虚线＝旧模型（无标定）；彩色实线＝标定后（插图放大 100×）；红色菱形＝实测 0.08/6。",
                 size=7.8, color=GRAY)
    tb.name = "S6_figcap"

    # ------------------------------------------------ 底部结论
    bar = s.shapes.add_shape(MSO_SHAPE.RECTANGLE, Inches(MARGIN), Inches(6.58), Inches(0.05), Inches(0.30))
    bar.fill.solid(); bar.fill.fore_color.rgb = RGBColor.from_string(RED); bar.line.fill.background()
    bar.shadow.inherit = False
    bar.name = "S6_bar"
    tb = textbox(s, MARGIN + 0.16, 6.59, W - 2 * MARGIN - 0.2, 0.28,
                 "距离不是杠杆：三面天线已经贴到 <5 cm，仍只有 0.08/6。下一步要改的是天线位置/极化、金属屏蔽与读码窗口。",
                 size=10, bold=True, anchor=MSO_ANCHOR.MIDDLE)
    tb.name = "S6_take"

    prs.save(out)
    print("saved", out, os.path.getsize(out), "bytes; slides =", len(prs.slides._sldIdLst))


if __name__ == "__main__":
    main()
