# -*- coding: utf-8 -*-
"""把 P6「读取结果 - 月统计 – 结论」页右侧的代号表，改成与 P5 口径一致（含推算行）

P5 现在是 7 行（7907 塑料/金属、8252 塑料/金属、6727、7513、7771）+ 合计 177,306 / 6,869 / 0.30%。
P6 原表只有 4 行（7907 合并、无 7513/7771），需同步：
    行数 4 → 7（+ 合计 = 8 行）
    箱数与 P5 完全一致
    「读取比例(上位机)」＝ readStatus=True 占比；实测行沿用原值，
    推算行按"读取比例 ≈ 读到 ≥1 比例 × 1.6"取：7907 金属 1.2%、7513 3.9%、7771 4.5%
    合计按箱数加权 = 5.4%
版式：表高从 5×0.4 压到 9×0.30，起点上移到 2.95"，避免压住下方结论框（5.87"）。

用法：py -3.12 sync_p6_table.py --pptx <deck>.pptx --out <新.pptx>
"""
import os, argparse
from pptx import Presentation
from pptx.util import Inches, Pt
from pptx.dml.color import RGBColor
from pptx.enum.text import PP_ALIGN, MSO_ANCHOR
from pptx.oxml.ns import qn
from lxml import etree

INK, LATIN, EA, LINE = "1A1A1A", "Arial", "微软雅黑", "D9D9D9"

ROWS = [
    ["代号", "箱型 / 背壳", "箱数", "读取比例(上位机)"],
    ["7907-P", "AX7907 · 6″ · 塑料", "54,810", "9.4%"],
    ["7907-M", "AX7907 · 6″ · 金属", "58,600", "1.2%"],
    ["8252-P", "AX8252 · 7″ · 塑料", "15,202", "7.8%"],
    ["8252-M", "AX8252 · 7″ · 金属", "6,524", "8.7%"],
    ["6727", "AX6727 · 7″ · 背壳未标注", "7,170", "7.9%"],
    ["7513", "AX7513 · 11″ tablet · 金属", "16,800", "3.9%"],
    ["7771", "AX7771 · 8″ tablet · 金属", "18,200", "4.5%"],
    ["合计", "全部在产组合（含推算）", "177,306", "5.4%"],
]


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


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--pptx", required=True)
    ap.add_argument("--out", required=True)
    a = ap.parse_args()
    prs = Presentation(a.pptx)

    page = old = None
    for sl in prs.slides:
        for sh in sl.shapes:
            if (getattr(sh, "has_table", False) and sh.has_table
                    and sh.table.cell(0, 0).text.strip() == "代号"):
                page, old = sl, sh
                break
        if old is not None:
            break
    if old is None:
        raise SystemExit("找不到 P6 代号表")

    x, w = old.left / 914400, old.width / 914400
    old._element.getparent().remove(old._element)

    row_h, y = 0.30, 2.95
    shp = page.shapes.add_table(len(ROWS), 4, Inches(x), Inches(y), Inches(w), Inches(row_h * len(ROWS)))
    t = shp.table
    tblPr = t._tbl.tblPr
    for el in tblPr.findall(qn("a:tableStyleId")):
        tblPr.remove(el)
    t.first_row = False
    t.horz_banding = False
    for ci, frac in enumerate([0.13, 0.47, 0.20, 0.20]):
        t.columns[ci].width = Inches(w * frac)
    for ri in range(len(ROWS)):
        t.rows[ri].height = Inches(row_h)
        for ci in range(4):
            cell = t.cell(ri, ci)
            cell.margin_left = cell.margin_right = Inches(0.05)
            cell.margin_top = cell.margin_bottom = Inches(0.008)
            cell.vertical_anchor = MSO_ANCHOR.MIDDLE
            cell.fill.solid()
            cell.fill.fore_color.rgb = RGBColor.from_string("F2F2F2" if ri == 0 else "FFFFFF")
            _border(cell)
            p = cell.text_frame.paragraphs[0]
            p.alignment = PP_ALIGN.LEFT if ci < 2 else PP_ALIGN.RIGHT
            r = p.add_run(); r.text = ROWS[ri][ci]
            set_font(r, 8.6 if ri == 0 else 8.8, ri == 0 or ri == len(ROWS) - 1)
    shp.name = "P6_synced_table"

    prs.save(a.out)
    print("saved", a.out)
    for ri in range(len(t.rows)):
        print("  ", [t.cell(ri, c).text for c in range(4)])


if __name__ == "__main__":
    main()
