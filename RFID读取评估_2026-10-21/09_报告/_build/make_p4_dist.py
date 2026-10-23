# -*- coding: utf-8 -*-
"""P4 机型口径表加「读到 ≤5 / ≤4 / ≤3 / ≤2 / ≤1 的百分比」（2026-10-23 晚第二批）

数据：03_数据/model_baseline_*.csv（机型×背壳的箱数/readStatus/读全6）
      03_数据/model_readout_dist_*.csv（同一批逐箱窗口的 0..6 分布，readout_dist.py 生成）
口径：≤N ＝ 该箱在窗口内读到的整机标签数 ≤ N 的箱占比（累计）；读全 6 个 ＝ 读到 6 个。

同时给 P5 结论框补一行合计 ≤1（98.1%），避免与 P4 重复整张表。

用法：py -3.12 make_p4_dist.py --pptx "<deck>.pptx"
可重复执行（按表头定位表格、按名字定位图片与脚注）。
"""
import os, csv, glob, argparse, shutil, datetime

from pptx import Presentation
from pptx.util import Inches, Pt
from pptx.dml.color import RGBColor
from pptx.enum.text import PP_ALIGN, MSO_ANCHOR
from pptx.enum.shapes import MSO_SHAPE
from pptx.oxml.ns import qn
from lxml import etree

_HERE = os.path.dirname(os.path.abspath(__file__))
REP = os.path.dirname(_HERE)
ROOT = os.path.dirname(REP)
DATA = os.path.join(ROOT, "03_数据")

INK, GRAY, LINE = "1A1A1A", "8C8C8C", "D9D9D9"
ACCENT, TINT = "3E5DA8", "E6EDF9"
LATIN, EA = "Arial", "微软雅黑"
MARGIN = 0.62


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


def table(slide, rows, x, y, w, col_w, row_h=0.38, fs=8.4, hfs=7.8, aligns=None, name=None):
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
            cell.margin_left = cell.margin_right = Inches(0.04)
            cell.margin_top = cell.margin_bottom = Inches(0.008)
            cell.vertical_anchor = MSO_ANCHOR.MIDDLE
            cell.fill.solid()
            cell.fill.fore_color.rgb = RGBColor.from_string("F2F2F2" if ri == 0 else "FFFFFF")
            _border(cell)
            p = cell.text_frame.paragraphs[0]
            p.alignment = aligns[ci] if aligns else (PP_ALIGN.CENTER if ci else PP_ALIGN.LEFT)
            p.line_spacing = 1.0
            r = p.add_run(); r.text = str(rows[ri][ci])
            set_font(r, hfs if ri == 0 else fs, ri == 0)
    if name:
        shp.name = name
    return shp


def latest(pattern):
    fs = sorted(glob.glob(os.path.join(DATA, pattern)))
    if not fs:
        raise SystemExit(f"missing {os.path.join(DATA, pattern)}")
    return fs[-1]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--pptx", required=True)
    a = ap.parse_args()
    src = a.pptx
    shutil.copy2(src, os.path.splitext(src)[0] + ".bak-p4dist-" +
                 datetime.datetime.now().strftime("%H%M%S") + ".pptx")

    base = {(r["hq_code"], r["shell"]): r for r in csv.DictReader(open(latest("model_baseline_*.csv"), encoding="utf-8-sig"))}
    dist = {(r["hq_code"], r["shell"]): r for r in csv.DictReader(open(latest("model_readout_dist_*.csv"), encoding="utf-8-sig"))}
    total = dist[("合计", "")]

    prs = Presentation(src)
    p4 = None
    for sl in prs.slides:
        if any(sh.has_text_frame and "机型口径" in sh.text_frame.text and "31 天" in sh.text_frame.text for sh in sl.shapes):
            p4 = sl
            break
    if p4 is None:
        raise SystemExit("找不到机型口径页")

    old = None
    for sh in p4.shapes:
        if getattr(sh, "has_table", False) and sh.has_table and sh.table.cell(0, 0).text.strip() == "HQ代码":
            old = sh
            break
    if old is None:
        raise SystemExit("找不到机型口径表")
    x, y, h_old = old.left / 914400, old.top / 914400, old.height / 914400
    old._element.getparent().remove(old._element)

    order = [("AX7907", "未标注"), ("AX8252", "塑料"), ("AX6727", "未标注"), ("AX8252", "金属")]
    # 口径 B：分母＝读到 ≥1 个整机标签的箱（0 个的箱不计入，只在「箱数 / 读到≥1」两列体现）
    HEAD = ["HQ代码", "客户代码", "尺寸 / 品类", "背壳（MES）", "箱数", "读到\n≥1 箱",
            "≤1", "≤2", "≤3", "≤4", "≤5", "读全 6 个"]
    rows = [HEAD]
    for key in order:
        b, d = base[key], dist[key]
        rows.append([b["hq_code"], b["customer_code"], b["size_category"], b["shell"],
                     f"{int(b['boxes']):,}", f"{int(d['boxes_ge1']):,}",
                     f"{float(d['ge1_le1_pct']):.2f}%", f"{float(d['ge1_le2_pct']):.2f}%",
                     f"{float(d['ge1_le3_pct']):.2f}%", f"{float(d['ge1_le4_pct']):.2f}%",
                     f"{float(d['ge1_le5_pct']):.2f}%", f"{float(d['ge1_full6_pct']):.2f}%"])
    rows.append(["合计", "四个在产组合", "—", "—", f"{int(total['boxes']):,}", f"{int(total['boxes_ge1']):,}",
                 f"{float(total['ge1_le1_pct']):.2f}%", f"{float(total['ge1_le2_pct']):.2f}%",
                 f"{float(total['ge1_le3_pct']):.2f}%", f"{float(total['ge1_le4_pct']):.2f}%",
                 f"{float(total['ge1_le5_pct']):.2f}%", f"{float(total['ge1_full6_pct']):.2f}%"])

    col_w = [1.05, 1.95, 1.85, 0.95, 0.95, 1.05, 0.62, 0.62, 0.62, 0.62, 0.62, 0.95]
    tb = table(p4, rows, x, y, 12.10, col_w, row_h=0.38, fs=8.4, hfs=7.6,
               aligns=[PP_ALIGN.LEFT, PP_ALIGN.LEFT, PP_ALIGN.LEFT, PP_ALIGN.CENTER,
                       PP_ALIGN.RIGHT, PP_ALIGN.RIGHT] + [PP_ALIGN.RIGHT] * 6,
               name="P4_table")
    # 合计行加粗
    for ci in range(len(HEAD)):
        cell = tb.table.cell(len(rows) - 1, ci)
        for run in cell.text_frame.paragraphs[0].runs:
            set_font(run, 8.4, True, INK)

    # 表格下方脚注（覆盖原来的说明行，位置跟着新表底走）
    for sh in p4.shapes:
        if sh.has_text_frame and sh.text_frame.text.startswith("31 天 113,667 箱"):
            new_y = y + 0.38 * len(rows) + 0.06
            sh.top = Inches(new_y)
            sh.height = Inches(0.62)
            tf = sh.text_frame
            tf.paragraphs[0].clear()
            r = tf.paragraphs[0].add_run()
            r.text = ("分母＝该组「读到 ≥1 个」的箱（读到 0 个的箱不计入，只在「箱数 / 读到≥1 箱」两列体现）；"
                      "≤N＝这些箱里读到 ≤N 个的占比（累计），读全 6 个＝读到 6 个。"
                      "31 天 113,667 箱中可映射机型 83,706 箱，其中只有 5,247 箱（6.3%）读到过标签。")
            set_font(r, 8.2, False, GRAY)
            break

    # P5 结论框补一行合计 ≤1
    p5 = None
    for sl in prs.slides:
        if any(sh.has_text_frame and "机型口径结论" in sh.text_frame.text for sh in sl.shapes):
            p5 = sl
            break
    if p5 is not None:
        for sh in p5.shapes:
            if sh.has_text_frame and sh.text_frame.text.strip().startswith("结论"):
                tf = sh.text_frame
                # 幂等：先删掉上一轮加过的「≤1 / 只读到 1 个」行
                for para in list(tf.paragraphs):
                    if para.text.startswith("一箱读到 ≤1") or para.text.startswith("读到标签的"):
                        para._p.getparent().remove(para._p)
                p = tf.add_paragraph()
                p.line_spacing = 1.25
                r = p.add_run()
                r.text = (f"读到标签的 5,247 箱里：只读到 1 个占 {float(total['ge1_le1_pct']):.1f}%、"
                          f"读全 6 个仅 {float(total['ge1_full6_pct']):.1f}%。")
                set_font(r, 8.8, False, INK)
                print("P5 conclusion updated")
                break

    prs.save(src)
    print("saved", src, os.path.getsize(src), "bytes")


if __name__ == "__main__":
    main()
