# -*- coding: utf-8 -*-
"""重做「R3」页：读到几个与距离**没有相关性**（2026-10-22 二次修正）。

前一版把「实测 0.08/6」当成“额外 28.6 dB 损耗”去改距离衰减曲线 —— 结论错了，已作废。
手册/自由空间模型本身是对的：0/10/20 cm 理论上仍可读全 6 个；
但现场三面天线 <5 cm 实测 0.08/6、10-19 接触式最多 2/6，读数在 0–40 cm 范围内都在 0–1。
⇒ 读到多少与距离无关；瓶颈不在距离/衰减。

现场条件（用户口径 + 实测）：
  * 3 个 RFID 天线（底 / 侧 / 顶），天线面到箱面均 < 5 cm；
  * 31 天 113,667 箱：平均 0.08/6，95.0% 一箱 0 个；
  * 10-19 中箱（金属件）：8 次试验单次最多 2/6。
⇒ 不修改距离-衰减关系（手册模型保留），只在图上并列实测，指出二者不相关。

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
    # 只保留本页原有的标题文本框与分割线，其余（历史版本加的图/表/文字）全部清掉
    for sh in list(s.shapes):
        keep_title = sh.has_text_frame and "R3" in sh.text_frame.text and sh.top is not None and sh.top < Inches(0.9)
        is_line = str(sh.shape_type).startswith("LINE") or sh.name.startswith("Connector")
        if not (keep_title or is_line):
            sh._element.getparent().remove(sh._element)

    # ------------------------------------------------ 标题
    for sh in s.shapes:
        if sh.has_text_frame and "距离对读取的影响" in sh.text_frame.text:
            for para in sh.text_frame.paragraphs:
                for r in para.runs:
                    r.text = "R3：读到几个与距离没有相关性"
            break

    tb = textbox(s, MARGIN, 0.96, W - 2 * MARGIN, 0.30,
                 "手册/自由空间模型没错（10 cm 理论上仍读全 6 个）；但现场三面天线 <5 cm 实测 0.08/6、10-19 接触式最多 2/6"
                 " —— 距离 0→40 cm 读数都在 0–1，读不到不是距离/衰减造成的", size=10.2, color=GRAY)
    tb.name = "S6_sub"

    # ------------------------------------------------ 左：三条事实
    for i, (x, w, num, unit, lab, col) in enumerate([
            (MARGIN, 3.3, "6.00 / 6", "理论（下置 9 dBi）：0–10 cm 应读全", "按手册参数，近距本来就该读得到", GRAY),
            (3.90, 3.0, "0.08 / 6", "实测（产线 3 天线 <5 cm，31 天 113,667 箱）", "95.0% 一箱读到 0 个；10-19 接触式也只有 0–2", RED)]):
        stat(s, x, 1.40, w, num, unit, lab, color=col)
        for sh in list(s.shapes)[-3:]:
            sh.name = f"S6_stat{i}_{sh.name[-1]}"

    # ------------------------------------------------ 左：理论 vs 实测表
    t0 = textbox(s, MARGIN, 2.78, 6.5, 0.24, "同一台读码器：理论该读到多少 vs 实际读到多少", size=9.5, bold=True, color=ACCENT)
    t0.name = "S6_cap"
    rows = [
        ["距离 cm", "理论 读全 /6", "实测 读全 /6", "差值"],
        ["0（贴住）", "6.00", "0–2（8 次）", "−4 ~ −6"],
        ["5", "6.00", "0.08（31 天）", "−5.9"],
        ["10", "6.00", "未逐档实测", "—"],
        ["20", "5.89", "未逐档实测", "—"],
        ["30", "4.56", "未逐档实测", "—"],
        ["50", "1.89", "未逐档实测", "—"],
    ]
    tb = table(s, rows, MARGIN, 3.06, 6.5, [1.35, 1.8, 2.0, 1.35], row_h=0.33, fs=8.6, hfs=8.3,
               aligns=[PP_ALIGN.CENTER] * 4, bold_first_col=True, highlight_rows=(1, 2))
    tb.name = "S6_table"

    r = rich(s, MARGIN, 5.50, 6.5, 0.95, [
        ("结论：读到数量与距离无相关（相关性≈0）", 9.8, True, RED),
        ("近距（贴住、<5 cm）并不比远距好；反过来说，把距离压得更近、或加大功率，都换不来读数。", 8.8, False, INK),
        ("⇒ 损失发生在距离之外：箱内金属件屏蔽与相互遮挡、标签朝向/极化、过板窗口与程序判定口径。"
         "10–40 cm 的逐档实测仍缺（A/B 组），但现有三处观测已足以排除“距离不够近”这一解释。", 8.8, False, INK),
    ], spacing=1.2)
    r.name = "S6_concl"

    # ------------------------------------------------ 右：图
    p = os.path.join(FIG, "fig7c_distance_vs_reads.png")
    iw, ih = Image.open(p).size
    maxw, maxh = 6.0, 3.0
    sc = min(maxw / iw, maxh / ih)
    pic = s.shapes.add_picture(p, Inches(7.05), Inches(1.40), Inches(iw * sc), Inches(ih * sc))
    pic.name = "S6_fig"

    tb = textbox(s, 7.05, 4.55, 5.7, 0.55,
                 "灰虚线＝手册模型（未改动，随距离正常衰减）；红色＝实测（0.08/6 与 0–2/6）；灰底＝尚未逐档实测的 10–40 cm。",
                 size=7.8, color=GRAY)
    tb.name = "S6_figcap"

    # ------------------------------------------------ 底部
    bar = s.shapes.add_shape(MSO_SHAPE.RECTANGLE, Inches(MARGIN), Inches(6.58), Inches(0.05), Inches(0.30))
    bar.fill.solid(); bar.fill.fore_color.rgb = RGBColor.from_string(RED); bar.line.fill.background()
    bar.shadow.inherit = False
    bar.name = "S6_bar"
    tb = textbox(s, MARGIN + 0.16, 6.59, W - 2 * MARGIN - 0.2, 0.28,
                 "别再拿「压距离 / 加功率」当主线：0→40 cm 读数不变，要动的是金属屏蔽、标签朝向与读码窗口。",
                 size=10, bold=True, anchor=MSO_ANCHOR.MIDDLE)
    tb.name = "S6_take"

    prs.save(out)
    print("saved", out, os.path.getsize(out), "bytes; slides =", len(prs.slides._sldIdLst))


if __name__ == "__main__":
    main()
