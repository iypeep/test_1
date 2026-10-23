# -*- coding: utf-8 -*-
"""按 2026-10-23 晚的口径改汇报 PPT（基线 = 「改动版_完善_20261022」11 页）：

1) 机型口径页（P4）删掉 AX7771 / AX7513 两行 —— 现场两台设备上都没有这两款的包装日志
   （3A1-SS8633A-RIT：Rfid_/EpcLog_ 零命中；7H3AA-PALLET：本线未生产），留着只是噪音；
2) 把 R6 页（原 P10）移到 P4 之后（新 P5），定位为「机型口径：31 天日志统计」的结论页；
   R6 的 6 行代号表同时删掉 7771-M / 7513-M；
3) 在 R6 页左侧附「读取方式」示意图（正立 + 顶部/左侧两副天线，`figs/fig_reader_layout.png`）。

可重复执行：按标题定位页面、按「代号」定位表、图片按名字 S5_fig 去重。

用法：
    py -3.12 make_r6_after_p4.py --pptx "<deck>.pptx"
"""
import os, argparse, shutil, datetime

from pptx import Presentation
from pptx.util import Inches, Pt
from pptx.dml.color import RGBColor
from pptx.enum.text import PP_ALIGN, MSO_ANCHOR
from pptx.oxml.ns import qn
from lxml import etree
from PIL import Image

_HERE = os.path.dirname(os.path.abspath(__file__))
REP = os.path.dirname(_HERE)
FIG = os.path.join(REP, "figs")
INK, GRAY = "1A1A1A", "8C8C8C"
LATIN, EA = "Arial", "微软雅黑"

T_OLD_TITLE = "R6：六种箱型"
T_NEW_TITLE = "机型口径结论：四个在产组合都没拉开差距"
K_OLD = "代号＝HQ代码-背壳（客户代码见「机型口径」页）；右表只做代号对照，实测见左栏（31 天逐箱对齐）"
K_NEW = ("R6（同一读码器 × 箱型）的答案：代号＝HQ代码-背壳，实测见左栏（31 天逐箱对齐）；"
         "AX7771 / AX7513 本线无包装日志，已从口径表移除")


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


def find_slide(prs, needle):
    for sl in prs.slides:
        for sh in sl.shapes:
            if sh.has_text_frame and needle in sh.text_frame.text:
                return sl
    return None


def drop_rows(tbl, codes):
    """删掉首列命中 codes 的行（从后往前删，避免索引错位）"""
    removed = []
    for ri in range(len(tbl.rows) - 1, 0, -1):
        key = tbl.cell(ri, 0).text.strip()
        if key in codes:
            tr = tbl.rows[ri]._tr
            tr.getparent().remove(tr)
            removed.append(key)
    return removed


def replace_text(slide, old, new):
    hit = False
    for sh in slide.shapes:
        if sh.has_text_frame and old in sh.text_frame.text:
            for p in sh.text_frame.paragraphs:
                for r in p.runs:
                    if old in r.text:
                        r.text = r.text.replace(old, new)
                        hit = True
    return hit


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--pptx", required=True)
    a = ap.parse_args()
    src = a.pptx
    bak = os.path.splitext(src)[0] + ".bak-r6pos-" + datetime.datetime.now().strftime("%H%M%S") + ".pptx"
    shutil.copy2(src, bak)
    print("backup:", bak)

    prs = Presentation(src)

    # ---------------------------------------------------------------- 1) P4：删 7771 / 7513 两行
    p4 = find_slide(prs, "机型口径：31 天日志统计")
    if p4 is None:
        raise SystemExit("找不到「机型口径」页")
    for sh in p4.shapes:
        if getattr(sh, "has_table", False) and sh.has_table and sh.table.cell(0, 0).text.strip() == "HQ代码":
            print("P4 removed rows:", drop_rows(sh.table, {"AX7771", "AX7513"}))

    # ---------------------------------------------------------------- 2) R6 页：改标题/说明、删代号行
    r6 = find_slide(prs, T_OLD_TITLE)
    if r6 is None:
        r6 = find_slide(prs, T_NEW_TITLE)
    if r6 is None:
        raise SystemExit("找不到 R6 页")

    # 标题整串替换（原串是「R6：六种箱型 —— 在产四组实测没拉开差距」，只换前缀会留尾巴）
    for sh in r6.shapes:
        if sh.has_text_frame and ("R6：六种箱型" in sh.text_frame.text or sh.text_frame.text.strip() == T_NEW_TITLE):
            para = sh.text_frame.paragraphs[0]
            runs = [r for p_ in sh.text_frame.paragraphs for r in p_.runs]
            if runs:
                runs[0].text = T_NEW_TITLE
                for extra in runs[1:]:
                    extra.text = ""
            break
    replace_text(r6, K_OLD, K_NEW)
    replace_text(r6, "AX7771 / AX7513 本线未生产，7907 的背壳 MES 未标注，实测只能到机型级。",
                 "7907 的背壳 MES 未标注，实测只能到机型级。")
    for sh in r6.shapes:
        if getattr(sh, "has_table", False) and sh.has_table and sh.table.cell(0, 0).text.strip() == "代号":
            print("R6 removed rows:", drop_rows(sh.table, {"7771-M", "7513-M"}))

    # ---------------------------------------------------------------- 3) 左侧加「读取方式」示意图
    # 先把 bullets / 口径说明右移，给图腾出 0.62–2.30 这一列
    for sh in r6.shapes:
        if sh.name in ("P9_bullets", "P9_note"):
            sh.left = Inches(2.42)
            sh.width = Inches(4.65)
    for sh in list(r6.shapes):
        if sh.name == "S5_fig":                      # 重跑时先清旧的
            sh._element.getparent().remove(sh._element)
    for sh in list(r6.shapes):
        if sh.name == "S5_cap":
            sh._element.getparent().remove(sh._element)

    p = os.path.join(FIG, "fig_reader_layout.png")
    iw, ih = Image.open(p).size
    maxw, maxh = 1.86, 2.72
    sc = min(maxw / iw, maxh / ih)
    pic = r6.shapes.add_picture(p, Inches(0.60), Inches(3.12), Inches(iw * sc), Inches(ih * sc))
    pic.name = "S5_fig"

    cap = r6.shapes.add_textbox(Inches(0.62), Inches(5.95), Inches(1.86), Inches(0.34))
    cap.name = "S5_cap"
    tf = cap.text_frame
    tf.word_wrap = True
    tf.margin_left = tf.margin_right = tf.margin_top = tf.margin_bottom = 0
    for i, line in enumerate(["读取方式（现网）", "正立 · 顶部 + 左侧天线"]):
        para = tf.paragraphs[0] if i == 0 else tf.add_paragraph()
        para.line_spacing = 1.05
        r = para.add_run(); r.text = line
        set_font(r, 7.6, i == 0, GRAY if i else INK)

    # ---------------------------------------------------------------- 3b) 版式微调
    # 代号表只有 5 行了 → 「结论」块上移；左侧正文缩字号，避开图与画像
    for sh in r6.shapes:
        if sh.name == "P9_bullets":
            sh.top = Inches(3.16)
            sh.height = Inches(1.86)
            for para in sh.text_frame.paragraphs:
                para.line_spacing = 1.18
                for run in para.runs:
                    set_font(run, 11.2, run.font.bold, INK if run.text.strip().startswith("⇒") is False else "C0504D")
        if sh.name == "P9_note":
            sh.top = Inches(5.06)
            sh.height = Inches(0.62)
            for para in sh.text_frame.paragraphs:
                for run in para.runs:
                    set_font(run, 8.2, False, GRAY)
        # 「结论」底色块 + 正文
        if sh.shape_type == 1 and abs(sh.width / 914400 - 5.16) < 0.05 and sh.top / 914400 > 4.0:
            sh.top = Inches(3.62)
            sh.height = Inches(1.46)
        if sh.has_text_frame and sh.text_frame.text.strip().startswith("结论"):
            sh.top = Inches(3.72)
            sh.height = Inches(1.30)

    # ---------------------------------------------------------------- 4) 移到 P4 之后（第 5 页）
    sldIdLst = prs.slides._sldIdLst
    ids = list(sldIdLst)
    idx_r6 = list(prs.slides).index(r6)
    idx_p4 = list(prs.slides).index(p4)
    if idx_r6 != idx_p4 + 1:
        el = ids[idx_r6]
        sldIdLst.remove(el)
        sldIdLst.insert(idx_p4 + 1, el)
        print(f"moved R6 from page {idx_r6 + 1} to page {idx_p4 + 2}")
    else:
        print("R6 already right after P4")

    prs.save(src)
    print("saved", src, os.path.getsize(src), "bytes; slides =", len(prs.slides._sldIdLst))
    for i, sl in enumerate(prs.slides, start=1):
        t = next((sh.text_frame.text.split("\n")[0] for sh in sl.shapes
                  if sh.has_text_frame and sh.text_frame.text.strip()), "")
        print(f"  P{i}: {t[:52]}")


if __name__ == "__main__":
    main()
