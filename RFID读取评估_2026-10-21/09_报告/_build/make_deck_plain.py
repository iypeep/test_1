# -*- coding: utf-8 -*-
"""把汇报 deck 收敛成「简洁版」：加目录、去编号、每页一行结论（实验 / 变量 / 结论）

对应 2026-10-23 晚的反馈：
  * 「每一页尽可能简洁，不做太多啰嗦的说明」
  * 「P1 后加目录，要求简洁」
  * 「六种放置方式与读取方向测试联系不紧：A1–A6 改成 *面朝下 的描述，并在读取方向测试页改表头」
  * 「每页的结论需要写清楚，注意简洁」+「用自己的语言总结每页是什么实验、数据来源、控制变量和结论」

做法：
  1) P1 之后插入 1 页目录（9 条，带页码）；
  2) P2 换图为「*面朝下」版（`figs/fig4_faces.png`，由 `make_fig4_faces.py` 生成），表格改成
     「朝下的面 / 箱体高度 / 标签离天线」三列，删掉 A1–A6；
  3) P3 表头 上/下/左/右/前/后 → 顶面/底面/正面/背面/左侧/右侧 朝下；现象与结论压成 2 行；
  4) P2/P4/P6/P7/P8/P9 加统一底座条：实验 / 变量 / 结论 三段（P3/P5 已有结论条，就地精简）；
  5) 砍掉长段落：P4 脚注、P5 口径说明与结论框、P6 副标题、P7 脚注、P8/P9 正文与来源说明。

用法：py -3.12 make_deck_plain.py --pptx "<deck>.pptx"
可重复执行（按名字/标题定位；本脚本添加的形状都以 PX_/TOC_ 前缀命名，重跑先清）。
"""
import os, argparse, shutil, datetime

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
ACCENT, TINT, RED = "3E5DA8", "E6EDF9", "C0504D"
LATIN, EA = "Arial", "微软雅黑"
W, H, MARGIN = 13.333, 7.5, 0.62

TOC = [
    ("六种放置方式", 3),
    ("读取方向测试", 4),
    ("机型口径：31 天日志统计", 5),
    ("机型口径结论", 6),
    ("R2 模组选型", 7),
    ("天线选型", 8),
    ("R3 距离实测", 9),
    ("R4 增益实测", 10),
    ("附录（手册出处 / 选型问题清单）", 11),
]

# 每页底座条：实验 / 变量 / 结论（白话，尽量短）
STRIPS = {
    "六种放置方式": ("同一只箱，只换「哪个面朝下」；读码器固定在下、天线朝上。",
                "朝下的面（6 种）",
                "底面朝下最好；箱体立起越高，箱内标签离天线越远，侧躺最差。"),
    "机型口径：31 天日志统计": ("机台日志回溯 31 天，逐箱对齐「读到没读到」（readStatus × EpcLog）。",
                       "机型（4 个在产组合）",
                       "95.0% 的箱一个标签都读不到；读全 6 个只有 0.14%。"),
    "R2：模组选型": ("7 款模组按手册参数换算「一次过板读全 6 台」的概率。",
                 "模组形态 / 功率 / 天线口（手册值）",
                 "判据是过板窗口 6/6；近距都能读，差异全在远档。"),
    "天线选型": ("4 款天线尺寸/增益对比 + 现网 3 副天线实测。",
             "增益 / 极化 / 尺寸",
             "现网贴到 <5 cm 仍 0.08/6 —— 换天线解决覆盖，不解决金属屏蔽。"),
    "R3：距离不是变量": ("同一只箱，天线正上方 0 / 10 / 20 / 30 / 40 / 50 cm。",
                    "距离",
                    "1.3 → 0：读数与距离无关，别再压距离或加功率。"),
    "R4：同一台音频杰读码器": ("同一台读码器、同一批 4 箱，换 9 dBi / 6 dBi 各测一轮。",
                       "天线增益",
                       "0.79 vs 0.58（差 0.21）—— 增益不是主变量。"),
}


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
            align=PP_ALIGN.LEFT, spacing=1.05, name=None):
    tb = slide.shapes.add_textbox(Inches(x), Inches(y), Inches(w), Inches(h))
    tf = tb.text_frame
    tf.word_wrap = True
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


def strip(slide, y, exp, var, concl, w=MARGIN, width=W - 2 * MARGIN):
    """底座条：实验 / 变量 / 结论（三段，短句）"""
    for sh in list(slide.shapes):
        if sh.name.startswith("PX_strip"):
            sh._element.getparent().remove(sh._element)
    hline(slide, w, y - 0.10, width, color="E4E4E4", name="PX_strip_rule")
    cols = [(0.0, 0.44, "实验", exp), (0.46, 0.20, "变量", var), (0.68, 0.32, "结论", concl)]
    for fx, fw, label, text in cols:
        x = w + width * fx
        cw = width * fw
        textbox(slide, x, y, cw, 0.20, [(label, 7.6, True, GRAY)], name=f"PX_strip_{label}")
        textbox(slide, x, y + 0.20, cw, 0.56,
                [(text, 9.2, label == "结论", INK if label != "结论" else ACCENT)],
                name=f"PX_strip_{label}_txt")


def strip_line(slide, y, exp, var, concl, w=MARGIN, width=W - 2 * MARGIN):
    """单行底座条：实验 ｜ 变量 ｜ 结论（页面下半区被图/表占满时用）"""
    for sh in list(slide.shapes):
        if sh.name and sh.name.startswith("PX_stripline"):
            sh._element.getparent().remove(sh._element)
    hline(slide, w, y - 0.09, width, color="E4E4E4", name="PX_stripline_rule")
    tb = slide.shapes.add_textbox(Inches(w), Inches(y), Inches(width), Inches(0.30))
    tf = tb.text_frame
    tf.word_wrap = True
    tf.margin_left = tf.margin_right = tf.margin_top = tf.margin_bottom = 0
    p0 = tf.paragraphs[0]
    for text, size, bold, color in (
            ("实验  ", 8.2, True, GRAY), (exp + "      ", 9.4, False, INK),
            ("变量  ", 8.2, True, GRAY), (var + "      ", 9.4, False, INK),
            ("结论  ", 8.2, True, GRAY), (concl, 9.4, True, ACCENT)):
        r = p0.add_run(); r.text = text
        set_font(r, size, bold, color)
    tb.name = "PX_stripline"
    return tb


def find_slide(prs, needle, idx=None):
    """按「标题」定位：只认页面顶部那块文字，避免命中目录页里的同名条目"""
    for i, sl in enumerate(prs.slides):
        if idx is not None and i != idx:
            continue
        if any(sh.name == "TOC_title" for sh in sl.shapes):
            continue
        for sh in sl.shapes:
            if (sh.has_text_frame and sh.top is not None and sh.top < Inches(1.2)
                    and sh.text_frame.text.strip().startswith(needle)):
                return sl
    return None


def set_para_text(shape, text, size=9.0, bold=None, color=None):
    tf = shape.text_frame
    first = tf.paragraphs[0]
    runs = [r for p in tf.paragraphs for r in p.runs]
    if runs:
        runs[0].text = text
        for extra in runs[1:]:
            extra.text = ""
    else:
        r = first.add_run(); r.text = text
    for p in list(tf.paragraphs)[1:]:
        p._p.getparent().remove(p._p)
    r0 = tf.paragraphs[0].runs[0]
    set_font(r0, size, bool(bold) if bold is not None else False, color or INK)


def clear_paras(shape, lines, size=9.0, color=INK, spacing=1.2, bold_first=False):
    tf = shape.text_frame
    for p in list(tf.paragraphs)[1:]:
        p._p.getparent().remove(p._p)
    tf.paragraphs[0].clear()
    for i, line in enumerate(lines):
        p = tf.paragraphs[0] if i == 0 else tf.add_paragraph()
        p.line_spacing = spacing
        r = p.add_run(); r.text = line
        set_font(r, size, bold_first and i == 0, color)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--pptx", required=True)
    ap.add_argument("--upto", type=int, default=99, help="调试用：只做到第 N 步就保存退出")
    a = ap.parse_args()
    src = a.pptx
    shutil.copy2(src, os.path.splitext(src)[0] + ".bak-plain-" +
                 datetime.datetime.now().strftime("%H%M%S") + ".pptx")
    prs = Presentation(src)

    def checkpoint(n):
        if a.upto <= n:
            prs.save(src)
            print("checkpoint", n, "saved")
            raise SystemExit(0)

    # ---------------------------------------------------------------- 1) 目录页（插到 P1 之后）
    for sl in list(prs.slides):
        if any(sh.name == "TOC_title" for sh in sl.shapes):
            sl._element.getparent().remove(sl._element)
    cover = prs.slides[0]
    toc = prs.slides.add_slide(prs.slide_layouts[6])
    textbox(toc, MARGIN, 0.55, 6.0, 0.55, [("目录", 26, True, INK)], name="TOC_title")
    hline(toc, MARGIN, 1.30, W - 2 * MARGIN)
    y = 1.62
    for i, (name, page) in enumerate(TOC, start=1):
        textbox(toc, MARGIN + 0.30, y, 0.55, 0.30, [(f"{i}", 10.5, True, ACCENT)], name=f"TOC_n{i}")
        textbox(toc, MARGIN + 0.85, y - 0.03, 8.4, 0.34, [(name, 12.5, False, INK)], name=f"TOC_t{i}")
        textbox(toc, MARGIN + 9.60, y - 0.03, 1.6, 0.34, [(str(page), 11.5, False, GRAY)], name=f"TOC_p{i}")
        hline(toc, MARGIN + 0.30, y + 0.50, W - 2 * MARGIN - 0.60, color="EFEFEF")
        y += 0.58
    sldIdLst = prs.slides._sldIdLst
    ids = list(sldIdLst)
    sldIdLst.remove(ids[-1])
    sldIdLst.insert(1, ids[-1])          # P1 之后
    print("TOC inserted at position 2")

    checkpoint(1)

    # ---------------------------------------------------------------- 2) P2 六种放置方式
    p2 = find_slide(prs, "六种放置方式")
    for sh in list(p2.shapes):
        if sh.shape_type == 13:          # 旧 3D 图（带 A1–A6）换掉
            sh._element.getparent().remove(sh._element)
        if getattr(sh, "has_table", False) and sh.has_table:
            sh._element.getparent().remove(sh._element)
    pic = os.path.join(FIG, "fig4_faces.png")
    if os.path.exists(pic):
        iw, ih = Image.open(pic).size
        sc = min(7.55 / iw, 5.0 / ih)
        sp = p2.shapes.add_picture(pic, Inches(0.45), Inches(1.05), Inches(iw * sc), Inches(ih * sc))
        sp.name = "PX_fig4"
    else:
        print("!! fig4_faces.png 缺失，请先跑 make_fig4_faces.py")
    rows = [["朝下的面", "箱体高度", "标签离天线"],
            ["底面朝下（正立）", "300 mm", "250 mm"],
            ["顶面朝下（倒置）", "300 mm", "250 mm"],
            ["正面朝下（防爆标识面）", "400 mm", "300 mm"],
            ["背面朝下（条码面）", "400 mm", "300 mm"],
            ["左侧面朝下", "600 mm", "400 mm"],
            ["右侧面朝下", "600 mm", "400 mm"]]
    tw = 4.55
    tbl = p2.shapes.add_table(len(rows), 3, Inches(W - MARGIN - tw), Inches(1.12), Inches(tw), Inches(0.38 * len(rows)))
    t = tbl.table
    tblPr = t._tbl.tblPr
    for el in tblPr.findall(qn("a:tableStyleId")):
        tblPr.remove(el)
    t.first_row = False; t.horz_banding = False
    for ci, cw in enumerate([1.95, 1.15, 1.45]):
        t.columns[ci].width = Inches(cw)
    for ri in range(len(rows)):
        t.rows[ri].height = Inches(0.38)
        for ci in range(3):
            cell = t.cell(ri, ci)
            cell.margin_left = cell.margin_right = Inches(0.05)
            cell.margin_top = cell.margin_bottom = Inches(0.01)
            cell.vertical_anchor = MSO_ANCHOR.MIDDLE
            cell.fill.solid()
            cell.fill.fore_color.rgb = RGBColor.from_string("F2F2F2" if ri == 0 else "FFFFFF")
            p = cell.text_frame.paragraphs[0]
            p.alignment = PP_ALIGN.LEFT if ci == 0 else PP_ALIGN.CENTER
            r = p.add_run(); r.text = rows[ri][ci]
            set_font(r, 8.4 if ri else 8.0, ri == 0)
    tbl.name = "PX_faceTable"
    y_note = 1.12 + 0.38 * len(rows) + 0.06          # 单位统一用英寸（不要拿 Emu 再加浮点数，会写成非整数 EMU）
    textbox(p2, W - MARGIN - tw, y_note, tw, 0.34,
            [("＝标签离天线的等效距离（箱高/2 + 箱面 10 cm）。", 7.6, False, GRAY)],
            name="PX_faceNote")
    strip(p2, 6.52, *STRIPS["六种放置方式"])

    checkpoint(2)

    # ---------------------------------------------------------------- 3) P3 读取方向测试
    p3 = find_slide(prs, "读取方向测试")
    HEAD = {2: "顶面\n朝下", 3: "底面\n朝下", 4: "左侧\n朝下", 5: "右侧\n朝下", 6: "正面\n朝下", 7: "背面\n朝下"}
    for sh in p3.shapes:
        if getattr(sh, "has_table", False) and sh.has_table and sh.table.cell(0, 1).text.strip() == "序号":
            t = sh.table
            for ci, txt in HEAD.items():
                cell = t.cell(0, ci)
                cell.text_frame.paragraphs[0].clear()
                for k, line in enumerate(txt.split("\n")):
                    p = cell.text_frame.paragraphs[0] if k == 0 else cell.text_frame.add_paragraph()
                    p.alignment = PP_ALIGN.CENTER
                    r = p.add_run(); r.text = line
                    set_font(r, 7.8, True)
            print("P3 headers updated")
        if sh.name == "S3_tabnote":
            set_para_text(sh, "表头＝该面朝下、贴底部读取器；数字＝该姿态读出的台数（整箱 6 台）；空白＝未读到。", 7.8, False, GRAY)
        if sh.name == "S3_boxtext":
            clear_paras(sh, [
                "现象：单次最多 2 台（目标 6 台）；顶面 / 底面朝下读到最多，正面 / 背面几乎为 0。",
                "原因：金属背板 + 箱内互相遮挡 ⇒ 三副天线同时读也读不全。",
            ], size=8.8, color=INK, spacing=1.3)
        if sh.name == "S3_source":
            set_para_text(sh, "来源：RFID 中箱读取测试报告（2026-10-19，8 轮）· 每行＝一只箱，换朝向读到的是同一台；SN 取自机台 EpcLog 实读。", 7.2, False, GRAY)
    for sh in list(p3.shapes):
        if sh.name in ("S3_bar", "S3_take", "S3_figcap"):
            sh._element.getparent().remove(sh._element)
    strip(p3, 6.55, "一只中箱，8 轮换面朝下；机台三副天线（底/侧/顶）同时读。", "朝下的面",
          "单次最多 2/6；顶/底面朝下最多，正面/背面几乎读不到。")

    checkpoint(3)

    # ---------------------------------------------------------------- 4) P4 机型口径
    p4 = find_slide(prs, "机型口径：31 天")
    for sh in list(p4.shapes):
        if sh.name == "P4_sub":
            sh._element.getparent().remove(sh._element)
    strip_line(p4, 3.78,
               "31 天逐箱对齐（readStatus × EpcLog）；分母＝读到 ≥1 台的箱。",
               "机型（4 个在产组合）",
               "95.0% 的箱一台都读不到；读全 6 台仅 0.14%。")

    checkpoint(4)

    # ---------------------------------------------------------------- 5) P5 机型口径结论（精简既有结论）
    p5 = find_slide(prs, "机型口径结论")
    for sh in p5.shapes:
        if sh.name == "P5_kick":
            set_para_text(sh, "同一批 31 天日志，按背壳分组；AX7771 / AX7513 无包装日志，已移除。", 9.4, False, GRAY)
        if sh.name == "P5_note":
            clear_paras(sh, [
                "口径",
                "readStatus × EpcLog 按箱对齐；读全 6 台＝6 台都在同一窗口读到。",
                "背壳取 MES CongfigSize（7907 / 6727 未标注，只能到机型级）。",
                "AX6727 明显偏高，待查贴标与工位。",
            ], size=8.0, color=INK, spacing=1.3)
        if sh.name == "P5_concl_box":
            sh.height = Inches(1.18)
        if sh.name == "P5_concl":
            clear_paras(sh, [
                "结论",
                "读全 6 台 0–3.56%；一箱 0 台 40.5–99.1%。",
                "塑料 7.8% vs 金属 8.7%（差 0.9 点）⇒ 背壳、尺寸都换不来读全。",
            ], size=8.6, color=INK, spacing=1.3, bold_first=True)
        if sh.name == "P5_take":
            set_para_text(sh, "金属背壳机型：改贴标位置，或在箱外侧加天线 —— 只加功率无效。", 10.2, True)

    checkpoint(5)

    # ---------------------------------------------------------------- 6) P6 / P7 / P8 / P9 底座条 + 精简
    p6 = find_slide(prs, "R2：模组选型")
    for sh in p6.shapes:
        if sh.name == "S5_sub":
            set_para_text(sh, "上排 7 款外观按手册尺寸建模 / 原厂产品图；判据＝一次过板读全 6 台。", 8.4, False, GRAY)
    strip(p6, 6.10, *STRIPS["R2：模组选型"])

    checkpoint(6)

    p7 = find_slide(prs, "天线选型")
    for sh in p7.shapes:
        if sh.name == "A_note":
            set_para_text(sh, "尺寸/增益按手册：S9025PL 5.5 dBic · 6 dBi 128²· SLP1002 8 dBi · S9028PCL 9 dBic（同比例绘制）。", 7.4, False, GRAY)
    strip(p7, 6.28, *STRIPS["天线选型"])

    checkpoint(7)

    p8 = find_slide(prs, "R3：距离不是变量")
    for sh in p8.shapes:
        if sh.name == "R3_concl":
            clear_paras(sh, [
                "手册说 0–10 cm 该读全 6 台，实测只有 1.3 台。",
                "金属背板互相遮挡 ⇒ 近场增益被吃掉，压距离换不来读数。",
            ], size=8.8, color=INK, spacing=1.3)
        if sh.name == "R3_src":
            set_para_text(sh, "理想值按 9 dBi / 30 dBm 链路预算；逐台读数为按均值拆分；SN 取自 EpcLog 实读。", 7.0, False, GRAY)
        if sh.name in ("S6_bar", "S6_take"):
            sh._element.getparent().remove(sh._element)
    for sh in list(p8.shapes):
        if getattr(sh, "has_table", False) and sh.has_table:
            sh.top = Inches(5.18)
            for r in sh.table.rows:
                r.height = Inches(0.30)
        if sh.name == "R3_src":
            sh._element.getparent().remove(sh._element)
    strip(p8, 6.74, *STRIPS["R3：距离不是变量"])

    checkpoint(8)

    p9 = find_slide(prs, "R4：同一台音频杰读码器")
    for sh in p9.shapes:
        if sh.name == "R4_body":
            clear_paras(sh, [
                "9 dBi 均值 0.79 台/箱，6 dBi 0.58 —— 差 0.21 台，手册的 +3 dB 没体现。",
                "1→6 个箱内金属背板互挡：增益救不回。",
            ], size=8.8, color=INK, spacing=1.3)
        if sh.name == "R4_src":
            set_para_text(sh, "同一批 4 只箱各测两轮；SN 取自 EpcLog 实读（同一批）。", 7.4, False, GRAY)
        if sh.name in ("R4_bar", "R4_take"):
            sh._element.getparent().remove(sh._element)
    strip(p9, 6.55, *STRIPS["R4：同一台音频杰读码器"])

    prs.save(src)
    print("saved", src, os.path.getsize(src), "bytes; slides =", len(prs.slides._sldIdLst))
    for i, sl in enumerate(prs.slides, start=1):
        t = next((sh.text_frame.text.split("\n")[0] for sh in sl.shapes
                  if sh.has_text_frame and sh.text_frame.text.strip()), "")
        print(f"  P{i}: {t[:46]}")


if __name__ == "__main__":
    main()
