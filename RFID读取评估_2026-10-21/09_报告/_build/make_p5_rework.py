# -*- coding: utf-8 -*-
"""重做「机型口径结论」页（P5）：按 2026-10-23 经理批注

批注三条：
  1) 「这里只要 2 个数：塑料的读取成功率和金属的成功率」→ 只留 塑料 / 金属 的 readStatus=True 两个大数
     （塑料 8252-P 7.8% / 金属 8252-M 8.7%），删掉 AX6727 的 40.5% 大数字块；
  2) 「这里把各个代号的 readStatus=True 的百分比加上」→ 右侧代号表加两列：箱数 / readStatus=True；
     并纠正代号：7907 / 6727 的背壳 MES 未标注，按实测只能到机型级（不再写 7907-P/7907-M 这种没有实测支撑的拆分）；
  3) 「这一坨不要，数据里面已经提过一遍了，不要重复的数据和结论」→ 删掉左侧 4 条 bullet 块
     （结论已在右侧结论框与底部结论条里，不再重复）。

数据源：03_数据/model_baseline_20260922_20261022.csv（31 天逐箱对齐）
图：figs/fig_reader_layout.png（读取方式示意，用户提供）

用法：
    py -3.12 make_p5_rework.py --pptx "<deck>.pptx"
可重复执行（整页重建，按标题定位）。
"""
import os, csv, argparse, shutil, datetime

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
ROOT = os.path.dirname(REP)
FIG = os.path.join(REP, "figs")
BASE_CSV = os.path.join(ROOT, "03_数据", "model_baseline_20260922_20261022.csv")

INK, GRAY, LINE = "1A1A1A", "8C8C8C", "D9D9D9"
ACCENT, TINT, RED = "3E5DA8", "E6EDF9", "C0504D"
LATIN, EA = "Arial", "微软雅黑"
W, MARGIN = 13.333, 0.62

TITLE = "机型口径结论：四个在产组合都没拉开差距"
KICK = ("R6（同一读码器 × 箱型）的答案：实测为 31 天逐箱对齐（readStatus × EpcLog）；"
        "AX7771 / AX7513 无包装日志，已从口径表移除")


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


def textbox(slide, x, y, w, h, lines, size=10, bold=False, color=INK,
            align=PP_ALIGN.LEFT, anchor=MSO_ANCHOR.TOP, spacing=1.0, name=None):
    tb = slide.shapes.add_textbox(Inches(x), Inches(y), Inches(w), Inches(h))
    tf = tb.text_frame
    tf.word_wrap = True
    tf.vertical_anchor = anchor
    tf.margin_left = tf.margin_right = tf.margin_top = tf.margin_bottom = 0
    if isinstance(lines, str):
        lines = lines.split("\n")
    for i, item in enumerate(lines):
        # item 可以是 (text, size, bold, color) 或纯文本
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


def rect(slide, x, y, w, h, fill=None, line=None, name=None):
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


def table(slide, rows, x, y, w, col_w, row_h=0.40, fs=9.4, hfs=8.6,
          aligns=None, bold_first_col=False, name=None):
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
            cell.margin_top = cell.margin_bottom = Inches(0.012)
            cell.vertical_anchor = MSO_ANCHOR.MIDDLE
            cell.fill.solid()
            cell.fill.fore_color.rgb = RGBColor.from_string("F2F2F2" if ri == 0 else "FFFFFF")
            _border(cell)
            p = cell.text_frame.paragraphs[0]
            p.alignment = aligns[ci] if aligns else (PP_ALIGN.CENTER if ci else PP_ALIGN.LEFT)
            p.line_spacing = 1.0
            r = p.add_run(); r.text = str(rows[ri][ci])
            set_font(r, hfs if ri == 0 else fs, (ri == 0) or (bold_first_col and ci == 0))
    if name:
        shp.name = name
    return shp


def load_baseline():
    rows = {}
    for r in csv.DictReader(open(BASE_CSV, encoding="utf-8-sig")):
        rows[(r["hq_code"], r["shell"])] = r
    return rows


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--pptx", required=True)
    a = ap.parse_args()
    src = a.pptx
    shutil.copy2(src, os.path.splitext(src)[0] + ".bak-p5-" +
                 datetime.datetime.now().strftime("%H%M%S") + ".pptx")
    prs = Presentation(src)

    target = None
    for sl in prs.slides:
        if any(sh.has_text_frame and "机型口径结论" in sh.text_frame.text for sh in sl.shapes):
            target = sl
            break
    if target is None:
        raise SystemExit("找不到「机型口径结论」页")

    for sh in list(target.shapes):                  # 整页重建
        sh._element.getparent().remove(sh._element)

    b = load_baseline()
    p_pl = b[("AX8252", "塑料")]      # 15,202 箱
    p_mt = b[("AX8252", "金属")]      # 6,524 箱
    l907 = b[("AX7907", "未标注")]
    t6727 = b[("AX6727", "未标注")]

    # ---------------------------------------------------------------- 页眉
    textbox(target, MARGIN, 0.40, W - 2 * MARGIN, 0.55, TITLE, size=22, bold=True, name="P5_title")
    textbox(target, MARGIN, 0.96, W - 2 * MARGIN, 0.30, KICK, size=10.0, color=GRAY, name="P5_kick")
    hline(target, MARGIN, 1.32, W - 2 * MARGIN, name="P5_rule")

    # ---------------------------------------------------------------- 左：只有两个数（塑料 / 金属 readStatus=True）
    textbox(target, MARGIN, 1.44, 6.45, 0.24,
            "readStatus=True（＝该箱 RFID 环节判定成功）",
            size=8.8, color=GRAY, name="P5_cap")

    def stat_pair(x, code, shell_label, rec, color):
        textbox(target, x, 1.72, 2.95, 0.62, rec["read_true_pct"] + "%", size=32, bold=True, color=color,
                name=f"P5_num_{code}_{shell_label}")
        textbox(target, x, 2.40, 2.95, 0.30, f"{shell_label}背壳  {code} · {int(rec['boxes']):,} 箱",
                size=9.6, bold=True, name=f"P5_lab_{code}_{shell_label}")
        textbox(target, x, 2.70, 2.95, 0.30,
                f"一箱 0 个 {rec['zero_tag_pct']}% · 读全 6 个 {rec['full6_pct']}%",
                size=8.4, color=GRAY, name=f"P5_sub_{code}_{shell_label}")

    stat_pair(MARGIN, "8252-P", "塑料", p_pl, INK)
    stat_pair(3.55, "8252-M", "金属", p_mt, ACCENT)

    # ---------------------------------------------------------------- 左：读取方式图 + caption
    p = os.path.join(FIG, "fig_reader_layout.png")
    iw, ih = Image.open(p).size
    sc = min(1.80 / iw, 2.62 / ih)
    pic = target.shapes.add_picture(p, Inches(MARGIN), Inches(3.16), Inches(iw * sc), Inches(ih * sc))
    pic.name = "P5_fig"
    textbox(target, MARGIN, 5.86, 1.86, 0.34,
            [("读取方式（现网）", 7.6, True, GRAY), ("正立 · 顶部 + 左侧天线", 7.6, False, GRAY)],
            name="P5_figcap")

    # ---------------------------------------------------------------- 左：口径说明（只讲数据边界，不重复结论）
    textbox(target, 2.55, 3.18, 4.50, 2.55, [
        ("口径", 8.6, True, GRAY),
        (f"readStatus × EpcLog 按箱窗口对齐；读全 6 个＝一箱 6 个整机标签都在同一窗口内读到。", 8.4, False, INK),
        (f"四个在产组合占 83,706 箱（31 天 113,667 箱的 74%）。", 8.4, False, INK),
        ("背壳材质取 MES CongfigSize；AX7907 / AX6727 的背壳未标注，实测只能到机型级。", 8.4, False, INK),
        ("AX6727 一箱 0 个 40.5%、读全 2.12%，明显偏离其余组 —— 先查该批贴标与工位。", 8.4, False, RED),
    ], spacing=1.22, name="P5_note")

    # ---------------------------------------------------------------- 右：代号表（补箱数 + readStatus=True）
    rows = [["代号", "箱型 / 背壳", "箱数", "readStatus=True"]]
    for code, label, rec in (
        ("7907", "AX7907 · 6″ · 背壳未标注", l907),
        ("8252-P", "AX8252 · 7″ · 塑料", p_pl),
        ("8252-M", "AX8252 · 7″ · 金属", p_mt),
        ("6727", "AX6727 · 7″ · 背壳未标注", t6727),
    ):
        rows.append([code, label, f"{int(rec['boxes']):,}", rec["read_true_pct"] + "%"])
    table(target, rows, 7.55, 1.46, 5.16, [1.05, 2.35, 0.85, 1.25], row_h=0.40, fs=9.2, hfs=8.4,
          bold_first_col=True,
          aligns=[PP_ALIGN.LEFT, PP_ALIGN.LEFT, PP_ALIGN.RIGHT, PP_ALIGN.RIGHT], name="P5_table")
    textbox(target, 7.55, 3.62, 5.16, 0.26,
            "代号＝HQ代码-背壳；readStatus=True 为该组箱级成功判定的占比",
            size=8.0, color=GRAY, name="P5_tabcap")

    # ---------------------------------------------------------------- 右下：结论（唯一一处结论文字）
    rect(target, 7.55, 3.96, 5.16, 1.62, fill=TINT, name="P5_concl_box")
    textbox(target, 7.72, 4.06, 4.85, 1.44, [
        ("结论", 10.0, True, ACCENT),
        ("读全 6 个：0.0%–2.12%；一箱读到 0 个：40.5%–99.1%。", 8.8, False, INK),
        ("塑料 vs 金属：readStatus=True 7.8% vs 8.7%（差 0.9 个点），一箱 0 个 98.9% vs 95.2% —— 没拉开差距。",
         8.8, False, INK),
        ("⇒ 背壳/尺寸都换不来读全：先修屏蔽、朝向与读码窗口，再按箱型复测。", 8.8, True, INK),
    ], spacing=1.25, name="P5_concl")

    # ---------------------------------------------------------------- 底部结论条
    rect(target, MARGIN, 6.34, 0.05, 0.34, fill=ACCENT, name="P5_bar")
    textbox(target, MARGIN + 0.16, 6.36, W - 2 * MARGIN - 0.2, 0.30,
            "若产线要上金属背壳机型：要么改贴标位置（避开金属面），要么在箱外/开口侧增设天线",
            size=11, bold=True, anchor=MSO_ANCHOR.MIDDLE, name="P5_take")

    prs.save(src)
    print("saved", src, os.path.getsize(src), "bytes; slides =", len(prs.slides._sldIdLst))


if __name__ == "__main__":
    main()
