# -*- coding: utf-8 -*-
"""统一页脚：删掉所有既有的「项目行 / n / m」文本框，再按页序重建（封面除外）。

用法：python fix_footers.py [--pptx 路径] [--keep-cover]   # 默认封面不写页脚
"""
import argparse, os, re
from pptx import Presentation
from pptx.util import Inches, Pt
from pptx.dml.color import RGBColor
from pptx.enum.text import PP_ALIGN
from pptx.oxml.ns import qn
from lxml import etree

_HERE = os.path.dirname(os.path.abspath(__file__))
REP = os.path.dirname(_HERE)
DEFAULT = os.path.join(REP, "RFID读取能力评估_2026-10-22.pptx")

NUM = re.compile(r"^\s*\d+\s*/\s*\d+\s*$")
PROJ_KEY = "7H3AA-PALLET"
GRAY, LATIN, EA = "8C8C8C", "Arial", "微软雅黑"
W, MARGIN = 13.333, 0.62


def set_font(run, size, color=GRAY):
    f = run.font
    f.size, f.name = Pt(size), LATIN
    f.color.rgb = RGBColor.from_string(color)
    rPr = run._r.get_or_add_rPr()
    for tag in ("a:ea", "a:cs"):
        el = rPr.find(qn(tag))
        if el is None:
            el = etree.SubElement(rPr, qn(tag))
        el.set("typeface", EA if tag == "a:ea" else LATIN)


def add_tb(slide, x, y, w, text, align=PP_ALIGN.LEFT):
    tb = slide.shapes.add_textbox(Inches(x), Inches(y), Inches(w), Inches(0.26))
    tf = tb.text_frame
    tf.word_wrap = False
    tf.margin_left = tf.margin_right = tf.margin_top = tf.margin_bottom = 0
    p = tf.paragraphs[0]
    p.alignment = align
    r = p.add_run(); r.text = text
    set_font(r, 8)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--pptx", default=DEFAULT)
    ap.add_argument("--cover", action="store_true", help="封面也写页脚（默认不写）")
    a = ap.parse_args()
    prs = Presentation(a.pptx)
    total = len(prs.slides)

    # 1) 先清掉所有「项目行 / 页码」样式文本框
    removed = 0
    for s in prs.slides:
        for sh in list(s.shapes):
            if not sh.has_text_frame:
                continue
            t = sh.text_frame.text.strip()
            if NUM.match(t) or (PROJ_KEY in t and len(t) < 80):
                sh._element.getparent().remove(sh._element)
                removed += 1

    # 2) 按页序重建
    added = 0
    for i, s in enumerate(prs.slides, start=1):
        if i == 1 and not a.cover:
            continue
        add_tb(s, MARGIN, 7.02, 8.0, "RFID 读取能力评估 · 7H3AA-PALLET · 2026-10-22")
        add_tb(s, W - MARGIN - 0.8, 7.02, 0.8, f"{i} / {total}", PP_ALIGN.RIGHT)
        added += 2

    prs.save(a.pptx)
    print(f"removed={removed}  added={added}  slides={total}  -> {a.pptx}")


if __name__ == "__main__":
    main()
