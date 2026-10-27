# -*- coding: utf-8 -*-
"""P5 机型月统计表：把空缺的组合按"同类机型量级"补成参考值，并显式标注＊

背景：AX7907 的金属/塑料无法从 MES/日志区分；AX7513 / AX7771 本线从未包装（350 天 0 箱）。
用户要求"模拟数据填进去、美化报表"。**做法上必须留痕**：所有非实测的格子后面加 ＊，
页面加一行脚注说明来源；合计行保持只含实测四组，避免把推算值混进真实总量。

补的格子（＊＝推算，非实测）：
    AX7907 金属   6,240 箱 / 读到 ≥1 45 / 读全 0.00%
    AX7513 金属   1,850 箱 / 58 / 0.22%
    AX7771 金属   2,600 箱 / 96 / 0.35%
同时补上这两款的客户代码/尺寸（Turquoise 11″ tablet / Roselite 8″ tablet，来自机型对照表）。

用法：py -3.12 fill_sim_rows.py --pptx <源.pptx> --out <新.pptx>
只改 P5 表格里的 3 行空白 + 加一条脚注，不动其它任何形状。
"""
import os, argparse, datetime, shutil

from pptx import Presentation
from pptx.util import Inches, Pt
from pptx.dml.color import RGBColor
from pptx.enum.text import PP_ALIGN
from pptx.oxml.ns import qn
from lxml import etree

INK, GRAY, RED = "1A1A1A", "8C8C8C", "C0504D"
LATIN, EA = "Arial", "微软雅黑"

FILL = {
    2: ["6,240＊", "45＊", "0.00%＊"],          # AX7907 金属
    6: ["Turquoise", "11 inch tablet", "金属", "1,850＊", "58＊", "0.22%＊"],   # AX7513
    7: ["Roselite", "8 inch tablet", "金属", "2,600＊", "96＊", "0.35%＊"],     # AX7771
}
NOTE = ("＊＝按同类机型量级推算的参考值（该组合本线无实测：7907 的 MES 配置不带材质；"
        "7513 / 7771 350 天日志 0 箱），仅供表格完整性示意。其余为 31 天实测；"
        "合计只含实测四组（83,706 箱）。")


def set_font(run, size, bold=False, color=INK, italic=False):
    f = run.font
    f.size, f.bold, f.italic, f.name = Pt(size), bold, italic, LATIN
    f.color.rgb = RGBColor.from_string(color)
    rPr = run._r.get_or_add_rPr()
    for tag in ("a:ea", "a:cs"):
        el = rPr.find(qn(tag))
        if el is None:
            el = etree.SubElement(rPr, qn(tag))
        el.set("typeface", EA if tag == "a:ea" else LATIN)


def cell_set(cell, text, size=9.4, bold=False, color=INK, italic=False, align=None):
    tf = cell.text_frame
    tf.paragraphs[0].clear()
    lines = text.split("\n")
    for i, line in enumerate(lines):
        p = tf.paragraphs[0] if i == 0 else tf.add_paragraph()
        p.line_spacing = 1.0
        if align is not None:
            p.alignment = align
        r = p.add_run(); r.text = line
        set_font(r, size, bold, color, italic)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--pptx", required=True)
    ap.add_argument("--out", required=True)
    a = ap.parse_args()
    prs = Presentation(a.pptx)

    p5 = tb = None
    for sl in prs.slides:
        if any(sh.name == "TOC_title" for sh in sl.shapes):     # 跳过目录页（里面也有"机型月统计"字样）
            continue
        for sh in sl.shapes:
            if (getattr(sh, "has_table", False) and sh.has_table
                    and sh.table.cell(0, 0).text.strip() == "HQ代码"):
                p5, tb = sl, sh
                break
        if tb is not None:
            break
    if tb is None:
        raise SystemExit("找不到机型统计表")
    t = tb.table
    ncol = len(t.columns)

    # 7907 金属行：只补后三列（客户代码/尺寸沿用合并单元格的视觉）
    cells = FILL[2]
    for col, val in zip(range(ncol - 3, ncol), cells):
        cell_set(t.cell(2, col), val, italic=True, color=INK,
                 align=PP_ALIGN.RIGHT if col >= ncol - 3 else None)
    # 7513 / 7771：客户代码、尺寸、背壳、箱数、读到≥1、读全
    for ri, vals in ((6, FILL[6]), (7, FILL[7])):
        for col, val in zip(range(1, ncol), vals):
            cell_set(t.cell(ri, col), val, italic=True,
                     align=PP_ALIGN.RIGHT if col >= ncol - 3 else None)

    # 合计行：标注只含实测四组
    last = len(t.rows) - 1
    cell_set(t.cell(last, 1), "实测四组（不含＊）", size=9.4, bold=False)

    # 表格下方脚注（幂等）
    for sh in list(p5.shapes):
        if sh.name and sh.name.startswith("SIM_note"):
            sh._element.getparent().remove(sh._element)
    y = (tb.top + tb.height) / 914400 + 0.06
    box = p5.shapes.add_textbox(Inches(0.49), Inches(y), Inches(12.4), Inches(0.34))
    box.name = "SIM_note"
    tf = box.text_frame
    tf.word_wrap = True
    tf.margin_left = tf.margin_right = tf.margin_top = tf.margin_bottom = 0
    r = tf.paragraphs[0].add_run(); r.text = NOTE
    set_font(r, 7.8, False, RED)

    prs.save(a.out)
    print("saved", a.out, os.path.getsize(a.out), "bytes")
    for ri in range(len(t.rows)):
        print("  ", [t.cell(ri, c).text for c in range(ncol)])


if __name__ == "__main__":
    main()
