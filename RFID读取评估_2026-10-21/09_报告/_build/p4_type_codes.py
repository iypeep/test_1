# -*- coding: utf-8 -*-
"""P4「变更放置方式的 RFID 测试」表：类型列 大/小电子书 → 项目代号

依据：2026-10-19 当天在产的金属背壳机型是 AX8252A / AX8252B（7″ e-reader），
非金属那批是 AX7907B（6″）。按尺寸对应：大电子书＝AX8252A（7″），小电子书＝AX7907A（6″）。
只改这张表的「类型」列（第 1 列），其它不动。

用法：py -3.12 p4_type_codes.py --pptx <deck>.pptx --out <新.pptx>
"""
import os, argparse
from pptx import Presentation
from pptx.util import Pt
from pptx.enum.text import PP_ALIGN
from pptx.dml.color import RGBColor
from pptx.oxml.ns import qn
from lxml import etree

LATIN, EA, INK = "Arial", "微软雅黑", "1A1A1A"
MAP = {"大电子书": "AX8252A", "小平板": "AX7907A", "小电子书": "AX7907A", "大平板": "AX8252A"}


def set_font(run, size=8.4, bold=False, color=INK):
    f = run.font
    f.size, f.bold, f.name = Pt(size), bold, LATIN
    f.color.rgb = RGBColor.from_string(color)
    rPr = run._r.get_or_add_rPr()
    for tag in ("a:ea", "a:cs"):
        el = rPr.find(qn(tag))
        if el is None:
            el = etree.SubElement(rPr, qn(tag))
        el.set("typeface", EA if tag == "a:ea" else LATIN)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--pptx", required=True)
    ap.add_argument("--out", required=True)
    a = ap.parse_args()
    prs = Presentation(a.pptx)

    t = None
    for sl in prs.slides:
        for sh in sl.shapes:
            if getattr(sh, "has_table", False) and sh.has_table:
                tb = sh.table
                if tb.cell(0, 0).text.strip() == "类型" and len(tb.columns) >= 9:
                    t = tb; page = sl; break
        if t is not None:
            break
    if t is None:
        raise SystemExit("找不到「类型」表")

    changed = 0
    for ri in range(1, len(t.rows)):
        cell = t.cell(ri, 0)
        txt = cell.text_frame.text.strip()
        if txt in MAP:
            cell.text_frame.paragraphs[0].clear()
            p = cell.text_frame.paragraphs[0]
            p.alignment = PP_ALIGN.CENTER
            r = p.add_run(); r.text = MAP[txt]
            set_font(r)
            changed += 1
    prs.save(a.out)
    print("saved", a.out, "changed cells:", changed)
    for ri in range(len(t.rows)):
        print("  ", [t.cell(ri, c).text.replace("\n", " ") for c in range(len(t.columns))])


if __name__ == "__main__":
    main()
