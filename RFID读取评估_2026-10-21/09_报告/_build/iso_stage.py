# -*- coding: utf-8 -*-
"""隔离测试：把 make_deck_plain 的各个操作单独作用在 P2 上，看哪个让 PowerPoint 打不开。
用法：py -3.12 iso_stage.py strip|pic|table|note
"""
import sys, os, importlib.util
from pptx.util import Inches
from PIL import Image

BUILD = os.path.dirname(os.path.abspath(__file__))
spec = importlib.util.spec_from_file_location("m", os.path.join(BUILD, "make_deck_plain.py"))
m = importlib.util.module_from_spec(spec); spec.loader.exec_module(m)

from pptx import Presentation

what = sys.argv[1]
src = r'E:\Desktop\RFID读取能力评估_20261023.pptx'
prs = Presentation(src)
p2 = m.find_slide(prs, "六种放置方式")

if what == "strip":
    m.strip(p2, 6.52, "a", "b", "c")
elif what == "pic":
    pic = os.path.join(m.FIG, "fig4_faces.png")
    iw, ih = Image.open(pic).size
    sc = min(9.4 / iw, 5.2 / ih)
    sp = p2.shapes.add_picture(pic, Inches(0.55), Inches(1.05), Inches(iw * sc), Inches(ih * sc))
    sp.name = "PX_fig4"
elif what == "table":
    shp = p2.shapes.add_table(2, 3, Inches(8), Inches(1.2), Inches(3), Inches(0.8))
    shp.name = "PX_t"
    t = shp.table
    for ri in range(2):
        for ci in range(3):
            t.cell(ri, ci).text = f"{ri}{ci}"
elif what == "picdel":
    for sh in list(p2.shapes):
        if sh.shape_type == 13:
            sh._element.getparent().remove(sh._element)
    pic = os.path.join(m.FIG, "fig4_faces.png")
    iw, ih = Image.open(pic).size
    sc = min(9.4 / iw, 5.2 / ih)
    sp = p2.shapes.add_picture(pic, Inches(0.55), Inches(1.05), Inches(iw * sc), Inches(ih * sc))
    sp.name = "PX_fig4"
elif what == "mytable":
    from pptx.util import Pt
    from pptx.dml.color import RGBColor
    from pptx.enum.text import PP_ALIGN, MSO_ANCHOR
    from pptx.oxml.ns import qn
    rows = [["朝下的面", "箱体高度", "标签离天线"],
            ["底面朝下（正立）", "300 mm", "250 mm"],
            ["顶面朝下（倒置）", "300 mm", "250 mm"],
            ["正面朝下（防爆标识面）", "400 mm", "300 mm"],
            ["背面朝下（条码面）", "400 mm", "300 mm"],
            ["左侧面朝下", "600 mm", "400 mm"],
            ["右侧面朝下", "600 mm", "400 mm"]]
    tw = 4.05
    tbl = p2.shapes.add_table(len(rows), 3, Inches(13.333-0.62-tw), Inches(1.10), Inches(tw), Inches(0.36*len(rows)))
    t = tbl.table
    tblPr = t._tbl.tblPr
    for el in tblPr.findall(qn("a:tableStyleId")):
        tblPr.remove(el)
    t.first_row=False; t.horz_banding=False
    for ci, cw in enumerate([1.75, 1.05, 1.25]):
        t.columns[ci].width = Inches(cw)
    for ri in range(len(rows)):
        t.rows[ri].height = Inches(0.36)
        for ci in range(3):
            cell = t.cell(ri, ci)
            cell.margin_left = cell.margin_right = Inches(0.05)
            cell.margin_top = cell.margin_bottom = Inches(0.01)
            cell.vertical_anchor = MSO_ANCHOR.MIDDLE
            cell.fill.solid(); cell.fill.fore_color.rgb = RGBColor.from_string("F2F2F2" if ri==0 else "FFFFFF")
            par = cell.text_frame.paragraphs[0]
            par.alignment = PP_ALIGN.LEFT if ci==0 else PP_ALIGN.CENTER
            r = par.add_run(); r.text = rows[ri][ci]
            m.set_font(r, 8.4 if ri else 8.0, ri==0)
    tbl.name = "PX_faceTable"
elif what.startswith("s2"):
    flags = what.split(":")[1] if ":" in what else "ptns"
    from pptx.util import Inches, Pt
    from pptx.dml.color import RGBColor
    from pptx.enum.text import PP_ALIGN, MSO_ANCHOR
    from pptx.oxml.ns import qn
    for sh in list(p2.shapes):
        if sh.shape_type == 13:
            sh._element.getparent().remove(sh._element)
        if getattr(sh, "has_table", False) and sh.has_table:
            sh._element.getparent().remove(sh._element)
    if "p" in flags:
        pic = os.path.join(m.FIG, "fig4_faces.png")
        iw, ih = Image.open(pic).size
        sc = min(9.4 / iw, 5.2 / ih)
        sp = p2.shapes.add_picture(pic, Inches(0.55), Inches(1.05), Inches(iw*sc), Inches(ih*sc)); sp.name="PX_fig4"
    if "t" in flags:
        rows = [["朝下的面", "箱体高度", "标签离天线"], ["底面朝下（正立）", "300 mm", "250 mm"]]
        tw = 4.05
        tbl = p2.shapes.add_table(len(rows), 3, Inches(13.333-0.62-tw), Inches(1.10), Inches(tw), Inches(0.36*len(rows)))
        t = tbl.table
        tblPr = t._tbl.tblPr
        for el in tblPr.findall(qn("a:tableStyleId")):
            tblPr.remove(el)
        t.first_row=False; t.horz_banding=False
        for ri in range(len(rows)):
            for ci in range(3):
                cell = t.cell(ri, ci)
                cell.fill.solid(); cell.fill.fore_color.rgb = RGBColor.from_string("F2F2F2" if ri==0 else "FFFFFF")
                par = cell.text_frame.paragraphs[0]
                r = par.add_run(); r.text = rows[ri][ci]
                m.set_font(r, 8.4, ri==0)
    if "n" in flags:
        m.textbox(p2, 8.6, 2.0, 4.0, 0.34, [("note", 7.6, False, m.GRAY)], name="PX_note")
    if "s" in flags:
        m.strip(p2, 6.52, "a", "b", "c")
elif what == "stage2full":
    from pptx.util import Inches, Pt
    from pptx.dml.color import RGBColor
    from pptx.enum.text import PP_ALIGN, MSO_ANCHOR
    from pptx.oxml.ns import qn
    for sh in list(p2.shapes):
        if sh.shape_type == 13:
            sh._element.getparent().remove(sh._element)
        if getattr(sh, "has_table", False) and sh.has_table:
            sh._element.getparent().remove(sh._element)
    pic = os.path.join(m.FIG, "fig4_faces.png")
    iw, ih = Image.open(pic).size
    sc = min(9.4 / iw, 5.2 / ih)
    sp = p2.shapes.add_picture(pic, Inches(0.55), Inches(1.05), Inches(iw*sc), Inches(ih*sc)); sp.name="PX_fig4"
    rows = [["朝下的面", "箱体高度", "标签离天线"],
            ["底面朝下（正立）", "300 mm", "250 mm"],
            ["顶面朝下（倒置）", "300 mm", "250 mm"],
            ["正面朝下（防爆标识面）", "400 mm", "300 mm"],
            ["背面朝下（条码面）", "400 mm", "300 mm"],
            ["左侧面朝下", "600 mm", "400 mm"],
            ["右侧面朝下", "600 mm", "400 mm"]]
    tw = 4.05
    tbl = p2.shapes.add_table(len(rows), 3, Inches(13.333-0.62-tw), Inches(1.10), Inches(tw), Inches(0.36*len(rows)))
    t = tbl.table
    tblPr = t._tbl.tblPr
    for el in tblPr.findall(qn("a:tableStyleId")):
        tblPr.remove(el)
    t.first_row=False; t.horz_banding=False
    for ci, cw in enumerate([1.75, 1.05, 1.25]):
        t.columns[ci].width = Inches(cw)
    for ri in range(len(rows)):
        t.rows[ri].height = Inches(0.36)
        for ci in range(3):
            cell = t.cell(ri, ci)
            cell.margin_left = cell.margin_right = Inches(0.05)
            cell.margin_top = cell.margin_bottom = Inches(0.01)
            cell.vertical_anchor = MSO_ANCHOR.MIDDLE
            cell.fill.solid(); cell.fill.fore_color.rgb = RGBColor.from_string("F2F2F2" if ri==0 else "FFFFFF")
            par = cell.text_frame.paragraphs[0]
            par.alignment = PP_ALIGN.LEFT if ci==0 else PP_ALIGN.CENTER
            r = par.add_run(); r.text = rows[ri][ci]
            m.set_font(r, 8.4 if ri else 8.0, ri==0)
    tbl.name = "PX_faceTable"
    m.textbox(p2, Inches(13.333-0.62-tw), Inches(1.10)+Inches(0.36*len(rows))+0.06, tw, 0.34,
              [("读数＝标签离天线的等效距离（箱体高度/2 + 箱面 10 cm）；朝下的面越高，标签越远。", 7.6, False, m.GRAY)],
              name="PX_faceNote")
    m.strip(p2, 6.52, "a", "b", "c")
elif what == "delpic":
    for sh in list(p2.shapes):
        if sh.shape_type == 13:
            sh._element.getparent().remove(sh._element)

prs.save(os.path.join(r'E:\Desktop\RFID_work', 'iso_' + what.replace(':', '-') + '.pptx'))
print("saved", what)
