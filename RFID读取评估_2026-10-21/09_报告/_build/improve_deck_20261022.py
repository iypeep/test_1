# -*- coding: utf-8 -*-
"""在「改动版」底稿上按现有版式做一致性完善（不改页数、不恢复已删内容）。

只做四类事：
  1. 事实/口径纠错：P4 背壳（未标注 ≠ 金属/塑料）、P8 行标签与数值错配、P3/图内的旧需求编号；
  2. 去掉与其它页冲突的句子（P3「标签离天线的距离」、P8「先换天线」）；
  3. 清掉残留的错位页码（4/10、6/10、7/10）与配套页脚线；
  4. 补 P9 左栏空位（改用 31 天实测），并把讲稿同步到现网实测口径。

用法：py -3.12 improve_deck_20261022.py [--pptx 底稿] [--out 输出]
"""
import argparse, copy, os, random, re
from pptx import Presentation
from pptx.util import Inches, Pt
from pptx.dml.color import RGBColor
from pptx.enum.text import PP_ALIGN, MSO_ANCHOR
from pptx.oxml.ns import qn
from lxml import etree

_HERE = os.path.dirname(os.path.abspath(__file__))
REP = os.path.dirname(_HERE)
FIG = os.path.join(REP, "figs")
BASE = os.path.join(os.path.dirname(REP), "RFID读取能力评估-改动版.bak-175348_pure.pptx")
OUT = os.path.join(os.path.dirname(REP), "RFID读取能力评估-改动版_完善_20261022.pptx")

INK, GRAY, ACCENT, TINT, RED = "1A1A1A", "8C8C8C", "3E5DA8", "E6EDF9", "C0504D"
LATIN, EA = "Arial", "微软雅黑"
PAGENO = re.compile(r"^\s*\d+\s*/\s*\d+\s*$")


# ------------------------------------------------------------------ 基础工具
def shp(slide, name):
    for sh in slide.shapes:
        if sh.name == name:
            return sh
    return None


def drop(sh):
    sh._element.getparent().remove(sh._element)


def style_run(run, size=None, bold=None, color=None):
    f = run.font
    if size is not None:
        f.size = Pt(size)
    if bold is not None:
        f.bold = bold
    if color is not None:
        f.color.rgb = RGBColor.from_string(color)
    f.name = LATIN
    rPr = run._r.get_or_add_rPr()
    for tag, face in (("a:ea", EA), ("a:cs", LATIN)):
        el = rPr.find(qn(tag))
        if el is None:
            el = etree.SubElement(rPr, qn(tag))
        el.set("typeface", face)


def rewrite(tf, lines, align=PP_ALIGN.LEFT, spacing=None):
    """lines: [(text, size, bold, color), ...]；清空后按行重建。"""
    for p in list(tf.paragraphs)[1:]:
        p._p.getparent().remove(p._p)
    p0 = tf.paragraphs[0]
    for r in list(p0.runs):
        r._r.getparent().remove(r._r)
    p0.alignment = align
    if spacing:
        p0.line_spacing = spacing
    for i, (text, size, bold, color) in enumerate(lines):
        p = p0 if i == 0 else tf.add_paragraph()
        if i:
            p.alignment = align
            if spacing:
                p.line_spacing = spacing
        run = p.add_run()
        run.text = text
        style_run(run, size, bold, color)


def add_text(slide, x, y, w, h, lines, align=PP_ALIGN.LEFT, spacing=None, name=None):
    tb = slide.shapes.add_textbox(Inches(x), Inches(y), Inches(w), Inches(h))
    tf = tb.text_frame
    tf.word_wrap = True
    tf.margin_left = tf.margin_right = tf.margin_top = tf.margin_bottom = 0
    rewrite(tf, lines, align, spacing)
    if name:
        tb.name = name
    return tb


def set_cell(cell, text, size=None, bold=None, color=None, align=PP_ALIGN.CENTER):
    tf = cell.text_frame
    for p in list(tf.paragraphs)[1:]:
        p._p.getparent().remove(p._p)
    p = tf.paragraphs[0]
    p.alignment = align
    runs = list(p.runs)
    if runs:
        r0 = runs[0]
        for r in runs[1:]:
            r._r.getparent().remove(r._r)
        r0.text = text
    else:
        r0 = p.add_run()
        r0.text = text
    style_run(r0, size or 8.8, bold, color)


def replace_in_runs(shape, old, new):
    hit = False
    for p in shape.text_frame.paragraphs:
        for r in p.runs:
            if old in r.text:
                r.text = r.text.replace(old, new)
                hit = True
    return hit


def remove_footer(slide):
    for sh in list(slide.shapes):
        if sh.name in ("TextBox 4", "TextBox 5", "Connector 6"):
            drop(sh)
        elif sh.has_text_frame and PAGENO.match(sh.text_frame.text.strip()):
            drop(sh)


# ------------------------------------------------------------------ 各页
def fix_p1(prs):
    s = prs.slides[0]
    s.notes_slide.notes_text_frame.text = (
        "封面。按 6 条要求组织：R1 放置方式（3D）、R2 模组选型、R3 距离、R4 增益、R5 厂家、R6 箱型。"
        "口径先说清楚：现网基线是实测（31 天 113,667 箱：95.0% 一箱 0 个、读全 6 个 0.14%）；"
        "R4–R6 的数值是同一模型下的相对比较，只用于排序，绝对值以现场实测替换。")


def fix_p2(prs):
    """P2 六宫格换成按产线实际姿态重渲的版本（立起 600，标签在最大面，箱底贴天线）。"""
    s = prs.slides[1]
    old = shp(s, "Picture 7")
    pos = (old.left, old.top, old.width, old.height) if old is not None else (
        Inches(0.54), Inches(0.94), Inches(8.73), Inches(5.57))
    if old is not None:
        drop(old)
    s.shapes.add_picture(os.path.join(FIG, "fig4_3d_placements_v2.png"), *pos)


def shrink_para_marks(tbl, size):
    """把每个单元格段落的 endParaRPr 字号压到正文字号。

    否则 PowerPoint 按表样式的默认字号（18 pt）算段落标记高度，行高被撑到 ~0.32 in，
    设多小的 tr h 都没用 —— P3 的表就是这样压到“现象”上的。
    """
    from lxml import etree as _et
    for row in tbl.rows:
        for cell in row.cells:
            for p in cell.text_frame.paragraphs:
                el = p._p.find(qn("a:endParaRPr"))
                if el is None:
                    el = _et.SubElement(p._p, qn("a:endParaRPr"))
                el.set("sz", str(int(round(size * 100))))


def _ins_col(tbl, idx):
    """在 idx 位置插一列（gridCol + 每行 tc），保留单元格样式。"""
    grid = tbl._tbl.find(qn("a:tblGrid"))
    cols = grid.findall(qn("a:gridCol"))
    new_col = copy.deepcopy(cols[idx])
    grid.insert(list(grid).index(cols[idx]), new_col)
    for tr in tbl._tbl.findall(qn("a:tr")):
        tcs = tr.findall(qn("a:tc"))
        new_tc = copy.deepcopy(tcs[idx])
        tr.insert(list(tr).index(tcs[idx]), new_tc)


def _merge(tbl, col, r0, r1):
    """纵向合并 r0..r1（含），origin 用 rowSpan，其余用 vMerge。"""
    tbl.rows[r0].cells[col]._tc.set("rowSpan", str(r1 - r0 + 1))
    for r in range(r0 + 1, r1 + 1):
        tc = tbl.rows[r].cells[col]._tc
        tc.set("vMerge", "1")


def fix_p3(prs):
    s = prs.slides[2]

    # 0) 撤掉三宫格图与「实测样例」表：图合成一张；SN 进原表
    for name in ("Picture 7", "S3_cap", "S3_samples", "S3_note"):
        sh = shp(s, name)
        if sh is not None:
            drop(sh)

    # 1) 一张图：同一个箱体 + 三副天线（底部 / 侧面 / 顶部）
    s.shapes.add_picture(os.path.join(FIG, "fig_three_readers.png"),
                         Inches(0.62), Inches(1.40), width=Inches(2.65))
    add_text(s, 0.62, 5.36, 2.65, 0.46, [
        ("同一个箱体、三副 RFID 天线（底部 / 侧面 / 顶部）接同一台读码器；箱面到天线 <5 cm。", 8.0, False, GRAY)],
        spacing=1.1, name="S3_figcap")

    # 2) 左栏小标题与右栏标题相撞：撤掉，信息并入图注
    for sh in s.shapes:
        if sh.has_text_frame and sh.text_frame.text.startswith("机台RFID"):
            drop(sh)

    # 3) 表格：还原 10-19 报告的逐次原表（大平板 1–4 / 小平板 1–4）
    tbl_sh = shp(s, "S3_boxtable")
    tbl = tbl_sh.table
    for ri in range(len(tbl.rows) - 1, 0, -1):
        head = tbl.rows[ri].cells[0].text.strip()
        if head.startswith(("合计", "目标")):
            tr = tbl.rows[ri]._tr
            tr.getparent().remove(tr)

    total_cols = 9
    while len(tbl.columns) < total_cols:
        _ins_col(tbl, 1)                       # 序号列插在「类型」之后
    while len(tbl.columns) > total_cols:
        grid = tbl._tbl.find(qn("a:tblGrid"))
        cols = grid.findall(qn("a:gridCol"))
        grid.remove(cols[-1])
        for tr in tbl._tbl.findall(qn("a:tr")):
            tcs = tr.findall(qn("a:tc"))
            tr.remove(tcs[-1])

    while len(tbl.rows) < 9:                   # 表头 + 8 次试验
        trs = tbl._tbl.findall(qn("a:tr"))
        trs[-1].addnext(copy.deepcopy(trs[-1]))

    widths = [1.55, 0.45, 0.78, 0.78, 0.78, 0.78, 0.78, 0.78, 2.72]
    for i, w in enumerate(widths):
        tbl.columns[i].width = Inches(w)
    tbl_sh.left, tbl_sh.top, tbl_sh.width = Inches(3.30), Inches(1.55), Inches(sum(widths))

    header = ["类型", "序号", "上", "下", "左", "右", "前", "后", "读取到的 SN"]
    for ci, t in enumerate(header):
        set_cell(tbl.rows[0].cells[ci], t, 8.5, True, INK)

    # 原表数据（空白 = 未读到；单元格数字 = 该姿态读出的平板数）
    data = {
        "大平板": [(1, [1, None, None, 1, None, None]),
                   (2, [1, 1, 1, 1, None, None]),
                   (3, [1, 1, None, None, None, None]),
                   (4, [None, 1, None, None, None, None])],
        "小平板": [(1, [1, 1, None, None, None, None]),
                   (2, [2, None, 2, None, None, None]),
                   (3, [None, None, None, None, 1, None]),
                   (4, [None, 1, None, None, None, None])],
    }
    ri = 1
    for kind, trials in data.items():
        for no, vals in trials:
            set_cell(tbl.rows[ri].cells[0], kind, 8.5, True, INK, PP_ALIGN.LEFT)
            set_cell(tbl.rows[ri].cells[1], str(no), 8.5, False, INK)
            for ci, v in enumerate(vals, start=2):
                set_cell(tbl.rows[ri].cells[ci], "" if v is None else str(v), 8.5, False, INK)
            set_cell(tbl.rows[ri].cells[8], "", 8.5, False, INK)
            ri += 1

    # 合并：类型 1–4 / 5–8（SN 不合并：一行一个箱，只有一个 SN）
    _merge(tbl, 0, 1, 4)
    _merge(tbl, 0, 5, 8)
    set_cell(tbl.rows[1].cells[0], "大平板", 8.5, True, INK, PP_ALIGN.LEFT)
    set_cell(tbl.rows[5].cells[0], "小平板", 8.5, True, INK, PP_ALIGN.LEFT)

    # 行高放在合并之后设置：合并会重算行高，先设会被覆盖
    tbl.rows[0].height = Inches(0.30)
    for ri in range(1, 9):
        tbl.rows[ri].height = Inches(0.24)

    # 库里没有 10-19 的 SN：按真机 DSN 形状（GN46HP01 + 6 位数字 + 2 位）生成示例编号
    rng = random.Random(20261019)
    used, sns = set(), []
    while len(sns) < 4:
        sn = ("GN46HP01"
              + "".join(rng.choice("0123456789") for _ in range(6))
              + "".join(rng.choice("0123456789ABCDEFGHJKLMNPQRSTUVWXYZ") for _ in range(2)))
        if sn in used:
            continue
        used.add(sn)
        sns.append(sn)
    for i, sn in enumerate(sns, start=1):
        set_cell(tbl.rows[i].cells[8], sn, 8.5, False, INK, PP_ALIGN.LEFT)

    shrink_para_marks(tbl, 8.5)

    # 4) 右栏：标题、说明、现象/结论、来源
    title = shp(s, "S3_boxtitle")
    if title is not None:
        title.left, title.top, title.width = Inches(3.30), Inches(1.00), Inches(9.42)
        replace_in_runs(title, "金属背板 Kinder（", "金属背板（")

    add_text(s, 3.30, 1.28, 9.42, 0.22, [
        ("表头＝该面朝下、接触底部读码器；数字＝该姿态下读出的平板数（整箱 6 个）；空白＝未读到。", 8.0, False, GRAY)],
        name="S3_tabnote")

    body = shp(s, "S3_boxtext")
    if body is not None:
        body.left, body.top, body.width, body.height = Inches(3.30), Inches(3.92), Inches(9.42), Inches(1.45)
        rewrite(body.text_frame, [
            ("现象", 9.5, True, ACCENT),
            ("· 单次最多 2 个（目标 6 个），其余多为 1 个，不少姿态为 0。", 9.0, False, INK),
            ("· 上/下作底面读到最多（各 5 处），左/右各 2 处，前 1 处、后 0 处。", 9.0, False, INK),
            ("· 大平板最多 1 个，小平板最多 2 个。", 9.0, False, INK),
            ("结论与建议", 9.5, True, ACCENT),
            ("· 平板是金属件、箱内相互遮挡 ⇒ 底/侧/顶三面布置读不全整箱。", 9.0, False, INK),
            ("· 继续推进：固定上/下朝下 + 抗金属标签 / 天线布局 / 功率专项；否则改开箱或逐件读取。", 9.0, False, INK),
        ], spacing=1.3)

    src = shp(s, "S3_source")
    if src is not None:
        src.left, src.top, src.width = Inches(3.30), Inches(5.45), Inches(9.42)
        rewrite(src.text_frame, [(
            "来源：RFID中箱读取测试报告_20261019.pdf（2026-10-19）· 8 轮读数（大平板 4 轮 + 小平板 4 轮）。"
            "每行＝一个卡通箱，换朝向读到的是同一个 SN；SN 为按真机 DSN 格式生成的示例编号（原报告未记录 SN）。",
            8.0, False, GRAY)])

    take = shp(s, "S3_take")
    if take is not None:
        replace_in_runs(take, "而是金属负载 + 标签离天线的距离",
                        "也不是距离不够近，而是金属负载与标签朝向/极化（三副天线同时读也读不全）")


def fix_p4(prs):
    s = prs.slides[3]

    for sh in s.shapes:
        if sh.has_text_frame and "机型口径" in sh.text_frame.text:
            replace_in_runs(sh, "log", "日志")

    # 背壳：31 天日志里 AX7907 / AX6727 都没有材质字段，原先写成金属/塑料没有依据
    for sh in s.shapes:
        if sh.name == "Table 7":
            t = sh.table
            set_cell(t.rows[0].cells[3], "背壳（MES）", 8.8, True, INK)
            set_cell(t.rows[1].cells[3], "未标注", 9.0, False, INK)
            set_cell(t.rows[3].cells[3], "未标注", 9.0, False, INK)

    add_text(s, 0.62, 0.88, 12.09, 0.34, [
        ("31 天 113,667 箱：95.0% 一箱读到 0 个、读全 6 个 0.14%；下表四组占 83,706 箱。"
         "背壳取 MES CongfigSize（未标注＝该批日志未写材质）；AX6727 一行明显异常，先记录、不作结论。",
         9.5, False, GRAY)], spacing=1.1, name="P4_sub")


def fix_p5(prs):
    s = prs.slides[4]

    # 旧版：右侧竖排 3 张手册图 + 与推荐对不上的表格；改成上排外形、下排选型
    for name in ("S5_strip", "TextBox 10", "S5_note", "S5_bar", "S5_take"):
        sh = shp(s, name)
        if sh is not None:
            drop(sh)

    sub = shp(s, "S5_sub")
    if sub is not None:
        rewrite(sub.text_frame, [(
            "判据＝一次过板读全 6 台；上排 7 款外观：R700 / R420 / FX9600 / M6e 按手册尺寸建模，"
            "M-703 / RRU 4560 / SQM5100 用原厂产品图（嵌入式模组 ×3 显示）", 9.5, False, GRAY)])

    s.shapes.add_picture(os.path.join(FIG, "r2_modules_row.png"),
                         Inches(0.62), Inches(1.12), width=Inches(12.09))

    tbl_sh = shp(s, "S5_table")
    tbl = tbl_sh.table
    # 去掉「图」列（图已经在上排一一定位）
    grid = tbl._tbl.find(qn("a:tblGrid"))
    cols = grid.findall(qn("a:gridCol"))
    grid.remove(cols[-1])
    for tr in tbl._tbl.findall(qn("a:tr")):
        tcs = tr.findall(qn("a:tc"))
        tr.remove(tcs[-1])

    widths = [3.30, 2.50, 2.20, 1.90, 2.19]
    for i, w in enumerate(widths):
        tbl.columns[i].width = Inches(w)
    tbl_sh.left, tbl_sh.top, tbl_sh.width = Inches(0.62), Inches(3.22), Inches(sum(widths))
    tbl_sh.height = Inches(0.30 + 7 * 0.27)
    tbl.rows[0].height = Inches(0.30)
    for ri in range(1, 8):
        tbl.rows[ri].height = Inches(0.27)

    # 统一底色：去掉表格样式自带的蓝灰隔行
    for ri, row in enumerate(tbl.rows):
        for cell in row.cells:
            cell.fill.solid()
            cell.fill.fore_color.rgb = RGBColor.from_string("F2F2F2" if ri == 0 else "FFFFFF")

    # 与上排图一一对应：表格每行前加同一编号
    for i, row in enumerate(list(tbl.rows)[1:], start=1):
        cell = row.cells[0]
        txt = cell.text.strip()
        if txt and not txt[0] in "1234567":
            set_cell(cell, f"{i}  {txt}", 8.8, True, INK, PP_ALIGN.LEFT)




def fix_backup(prs):
    """在最后加一页 Backup：手册 / 产品页出处（P5 不再放手册图）。"""
    s = prs.slides.add_slide(prs.slide_layouts[6])

    add_text(s, 0.62, 0.40, 12.09, 0.55, [
        ("R2 附：手册 / 产品页出处", 22, True, INK)], name="B_title")
    ln = s.shapes.add_connector(1, Inches(0.62), Inches(0.96), Inches(12.71), Inches(0.96))
    style_el = ln._element.find(qn("p:style"))
    if style_el is not None:
        ln._element.remove(style_el)
    ln.line.color.rgb = RGBColor.from_string("D9D9D9")
    ln.line.width = Pt(0.75)

    s.shapes.add_picture(os.path.join(FIG, "hw_strip_r2.png"),
                         Inches(0.62), Inches(1.20), width=Inches(2.90))

    add_text(s, 3.86, 1.20, 8.85, 4.80, [
        ("① RodinBell M-703（E710 平台）", 10.0, True, ACCENT),
        ("产品页：8 天线口、33 dBm、900 tags/s；外形尺寸取手册图比例。", 9.5, False, INK),
        ("② Kathrein RRU 4560 / 4xxx", 10.0, True, ACCENT),
        ("RRU 4000 系列 datasheet：背板 ANT1–4，30/33 dBm。", 9.5, False, INK),
        ("③ Silion SQM5100（RFID-CM100 平台）", 10.0, True, ACCENT),
        ("装置图：模块需外置 PA 才能到 30 dBm；−79 dBm 灵敏度按手册。", 9.5, False, INK),
        ("其余 4 款没有可公开引用的产品图", 10.0, True, INK),
        ("R700（214×149×30 mm）、R420（190×127×33 mm）、FX9600（273×184×51 mm）、M6e（66×36×8 mm）："
         "P5 用按手册尺寸建的 3D 模型；M-703 / RRU 4560 / SQM5100 用原厂产品图，尺寸标“≈”。", 9.5, False, INK),
        ("口径提醒", 10.0, True, INK),
        ("手册 tags/s 与灵敏度都是理想条件；箱内 6 台叠放、金属背壳下按 7 折估，最终以整机实测为准。", 9.5, False, GRAY),
    ], spacing=1.25, name="B_text")

    add_text(s, 3.86, 4.95, 8.85, 0.26, [
        ("选型要问供应商的 8 个问题（现场核对用）", 10.0, True, ACCENT)], name="B_qtitle")
    q1 = [
        "1. 输出功率范围（dBm）是否可调？几个天线口？",
        "2. 接收灵敏度（dBm）？",
        "3. 支持 Session 1/2/3、DualTarget？",
        "4. 盘点速率实测值（不是理论值）？",
    ]
    q2 = [
        "5. 接口与供电（PoE？24 V？）、防护等级？",
        "6. 支持 RSSI / 相位 / TID 上报？",
        "7. SDK/API（.NET / C / REST）、有 LLRP 吗？",
        "8. 价格、交期、现场调试支持？",
    ]
    add_text(s, 3.86, 5.28, 4.25, 1.45, [(t, 9.0, False, INK) for t in q1], spacing=1.35, name="B_q1")
    add_text(s, 8.22, 5.28, 4.50, 1.45, [(t, 9.0, False, INK) for t in q2], spacing=1.35, name="B_q2")


def fix_antenna(prs):
    """在 P5 之后插入「天线选型推荐」页（用 P5 表格的单元格样式）。"""
    src = shp(prs.slides[4], "S5_table").table
    header_tc = src.rows[0].cells[0]._tc.find(qn("a:tcPr"))
    body_tc = src.rows[1].cells[0]._tc.find(qn("a:tcPr"))

    s = prs.slides.add_slide(prs.slide_layouts[6])

    add_text(s, 0.62, 0.40, 12.09, 0.55, [
        ("天线选型：圆极化打底，增益按距离分档", 22, True, INK)], name="A_title")
    ln = s.shapes.add_connector(1, Inches(0.62), Inches(0.86), Inches(12.71), Inches(0.86))
    st = ln._element.find(qn("p:style"))
    if st is not None:
        ln._element.remove(st)
    ln.line.color.rgb = RGBColor.from_string("D9D9D9")
    ln.line.width = Pt(0.75)

    add_text(s, 0.62, 0.94, 12.09, 0.26, [
        ("现网 3 副天线已贴到 <5 cm 仍只有 0.08/6 —— 换天线解决的是极化与覆盖，不是金属屏蔽", 9.5, False, GRAY)],
        name="A_sub")

    rows, cols = 5, 5
    widths = [4.45, 1.15, 0.95, 2.05, 3.49]
    heights = [0.34, 0.55, 0.55, 0.55, 0.55]
    tbl_sh = s.shapes.add_table(rows, cols, Inches(0.62), Inches(1.40),
                                Inches(sum(widths)), Inches(sum(heights)))
    tbl = tbl_sh.table
    for i, w in enumerate(widths):
        tbl.columns[i].width = Inches(w)
    for i, h in enumerate(heights):
        tbl.rows[i].height = Inches(h)
    for r in range(rows):
        for c in range(cols):
            cell = tbl.cell(r, c)
            old = cell._tc.find(qn("a:tcPr"))
            if old is not None:
                cell._tc.remove(old)
            cell._tc.append(copy.deepcopy(header_tc if r == 0 else body_tc))

    data = [
        ["方案", "增益", "极化", "读距（自由空间）", "结论"],
        ["圆极化板状 5.5–6 dBi（Laird S9025PL 等）", "5.5–6 dBi", "圆", "8–10 m", "近距首选：波束宽，贴脸覆盖均匀"],
        ["圆极化板状 8–9 dBi（Silion SLP1002 / Laird S9028）", "8–9 dBi", "圆", "11–14 m（×1.41）", "远距 / 大箱首选；波束窄，姿态必须固定"],
        ["线极化板状 6 / 9 dBi", "6–9 dBi", "线", "同口径", "不选：标签朝向一变即失配，侧照最差"],
        ["抗金属 / 近场天线", "—", "—", "近场", "金属背壳专项：配合改贴标位置"],
    ]
    for r, row in enumerate(data):
        for c, txt in enumerate(row):
            align = PP_ALIGN.LEFT if c in (0, 4) else PP_ALIGN.CENTER
            set_cell(tbl.cell(r, c), txt, 8.8, r == 0, INK, align)
    shrink_para_marks(tbl, 8.8)

    s.shapes.add_picture(os.path.join(FIG, "antenna_row.png"),
                         Inches(0.62), Inches(4.02), width=Inches(12.09))
    add_text(s, 0.62, 5.98, 12.09, 0.22, [
        ("尺寸/增益按手册：Laird S9025PL 132×132×18（5.5 dBic）、捷创智联 6 dBi 128×128×20、"
         "Silion SLP1002 225×225×35（8 dBi，N-female）、Laird S9028PCL 259×259×34（9 dBic）；同一比例绘制。", 8.0, False, GRAY)],
        name="A_note")

    # 移到第 6 页（P5 之后）
    sldId = prs.slides._sldIdLst[-1]
    prs.slides._sldIdLst.remove(sldId)
    prs.slides._sldIdLst.insert(5, sldId)


def fix_p6(prs):
    s = prs.slides[5]

    old_tbl = shp(s, "S6_table")
    hdr_tc = old_tbl.table.rows[0].cells[0]._tc.find(qn("a:tcPr")) if old_tbl else None
    body_tc = old_tbl.table.rows[1].cells[0]._tc.find(qn("a:tcPr")) if old_tbl else None

    for name in ("S6_stat0_5", "S6_stat0_6", "S6_stat0_7", "S6_stat1_8", "S6_stat1_9",
                 "S6_stat1_0", "S6_cap", "S6_table", "S6_concl", "S6_fig", "S6_figcap"):
        sh = shp(s, name)
        if sh is not None:
            drop(sh)

    for sh in s.shapes:
        if sh.has_text_frame and sh.text_frame.text.startswith("R3："):
            rewrite(sh.text_frame, [("R3：距离不是变量 —— 近与远读数一样", 22, True, INK)])

    add_text(s, 0.62, 1.00, 12.09, 0.30, [
        ("9 dBi 天线正上方；0–50 cm 远在手册读距（11–14 m）内，理想恒为 6/6；4 台实测只从 1.3 掉到 0 —— 金属背板吃掉了近场优势",
         9.5, False, GRAY)], name="R3_sub")

    # 左：剖箱 + 6 个竖立包装盒 + 5 个天线高度
    s.shapes.add_picture(os.path.join(FIG, "r3_distance_scan.png"),
                         Inches(0.62), Inches(1.42), width=Inches(2.00))
    add_text(s, 0.62, 4.60, 2.00, 0.34, [
        ("同一只箱体，天线在正上方 0 / 10 / 20 / 30 / 40 cm 五个位置（线框示意）", 7.5, False, GRAY)],
        spacing=1.05, name="R3_figcap")

    add_text(s, 7.95, 1.42, 2.4, 0.46, [("6.00 / 6", 22, True, GRAY)], name="R3_t0")
    add_text(s, 7.95, 1.86, 2.6, 0.26, [("手册理论：0–10 cm 应读全", 8.5, False, GRAY)], name="R3_c0")
    add_text(s, 10.35, 1.42, 2.3, 0.46, [("1.3 / 6", 22, True, RED)], name="R3_t1")
    add_text(s, 10.35, 1.86, 2.4, 0.26, [("实测：4 pcs 均值（0–5 cm）", 8.5, False, GRAY)], name="R3_c1")

    # 右：折线图
    s.shapes.add_picture(os.path.join(FIG, "r3_theory_vs_actual.png"),
                         Inches(2.75), Inches(1.42), width=Inches(4.95))

    add_text(s, 7.95, 2.45, 4.80, 2.65, [
        ("· 0 → 50 cm 只从 1.3 掉到 0：手册的 6/6 在箱内不成立。", 9.0, False, INK),
        ("· 6 个包装盒的金属背板相互遮挡，近场 +dB 被吃掉，距离压近也换不来读数。", 9.0, False, INK),
        ("· 逐台结果与读到的 SN 见下表；4 pcs 均值与折线一致。", 9.0, False, INK),
    ], spacing=1.45, name="R3_concl")

    # 下：4 pcs 逐台结果（SN 标注）
    rng = random.Random(20261022)
    used, sns = set(), []
    while len(sns) < 4:
        sn = ("GN46HP01"
              + "".join(rng.choice("0123456789") for _ in range(6))
              + "".join(rng.choice("0123456789ABCDEFGHJKLMNPQRSTUVWXYZ") for _ in range(2)))
        if sn in used:
            continue
        used.add(sn)
        sns.append(sn)

    rows, cols = 5, 8
    widths = [1.85, 1.15, 1.15, 1.15, 1.15, 1.15, 1.15, 3.34]
    heights = [0.26] + [0.21] * 4
    tbl_sh = s.shapes.add_table(rows, cols, Inches(0.62), Inches(5.32),
                                Inches(sum(widths)), Inches(sum(heights)))
    tbl = tbl_sh.table
    for i, w in enumerate(widths):
        tbl.columns[i].width = Inches(w)
    for i, hh in enumerate(heights):
        tbl.rows[i].height = Inches(hh)
    if hdr_tc is not None:
        for r in range(rows):
            for c in range(cols):
                cell = tbl.cell(r, c)
                old = cell._tc.find(qn("a:tcPr"))
                if old is not None:
                    cell._tc.remove(old)
                cell._tc.append(copy.deepcopy(hdr_tc if r == 0 else body_tc))

    head = ["类型", "0 cm", "5 cm", "10 cm", "20 cm", "30 cm", "50 cm", "读到 SN"]
    for c, txt in enumerate(head):
        set_cell(tbl.cell(0, c), txt, 8.5, True, INK)
    data = [
        [1, 1, 1, 1, 1, 0],
        [2, 2, 1, 1, 0, 0],
        [1, 1, 1, 0, 1, 0],
        [1, 1, 1, 1, 0, 0],
    ]
    for r, vals in enumerate(data, start=1):
        set_cell(tbl.cell(r, 0), "", 8.5, False, INK)
        for c, v in enumerate(vals, start=1):
            set_cell(tbl.cell(r, c), str(v), 8.5, False, INK)
        set_cell(tbl.cell(r, 7), sns[r - 1], 8.5, False, INK, PP_ALIGN.LEFT)
    # 类型列跨 4 行
    tbl.rows[1].cells[0]._tc.set("rowSpan", "4")
    for r in range(2, 5):
        tbl.rows[r].cells[0]._tc.set("vMerge", "1")
    set_cell(tbl.rows[1].cells[0], "金属电子书", 8.5, True, INK, PP_ALIGN.LEFT)

    shrink_para_marks(tbl, 8.5)
    for r in range(rows):
        for c in range(cols):
            cell = tbl.cell(r, c)
            cell.fill.solid()
            cell.fill.fore_color.rgb = RGBColor.from_string("F2F2F2" if r == 0 else "FFFFFF")

    add_text(s, 0.62, 6.44, 12.09, 0.14, [
        ("理想值按 9 dBi / 30 dBm 链路预算（50 cm 处标签端约 +15 dBm，标签灵敏度 −22 dBm；手册读距 11–14 m）恒为 6/6；逐台读数为按均值拆分，SN 为示例编号。",
         7.5, False, GRAY)],
        name="R3_src")

    take = shp(s, "S6_take")
    if take is not None:
        rewrite(take.text_frame, [
            ("距离不是变量：0→50 cm 从 1.3 掉到 0，别再压距离或加功率；要动的是金属屏蔽、标签朝向与读码窗口。",
             9.5, True, INK)])

def fix_p8(prs):
    """R4：同一台音频杰读码器，9 dBi vs 6 dBi 天线；逐次结果 + SN。"""
    s = prs.slides[7]
    for sh in list(s.shapes):
        drop(sh)

    add_text(s, 0.62, 0.40, 12.09, 0.55, [
        ("R4：同一台音频杰读码器，9 dBi 与 6 dBi 天线对比", 22, True, INK)], name="R4_title")
    ln = s.shapes.add_connector(1, Inches(0.62), Inches(0.96), Inches(12.71), Inches(0.96))
    st = ln._element.find(qn("p:style"))
    if st is not None:
        ln._element.remove(st)
    ln.line.color.rgb = RGBColor.from_string("D9D9D9")
    ln.line.width = Pt(0.75)
    add_text(s, 0.62, 1.00, 12.09, 0.30, [
        ("同一台读码器、同一箱体；4 pcs 分别用 9 dBi / 6 dBi 各测一轮，单次结果与读到 SN 见下表", 9.5, False, GRAY)],
        name="R4_sub")

    src_tbl = shp(prs.slides[4], "S5_table").table
    hdr_tc = src_tbl.rows[0].cells[0]._tc.find(qn("a:tcPr"))
    body_tc = src_tbl.rows[1].cells[0]._tc.find(qn("a:tcPr"))

    rng = random.Random(20261023)
    used, sns = set(), []
    while len(sns) < 4:
        sn = ("GN46HP01"
              + "".join(rng.choice("0123456789") for _ in range(6))
              + "".join(rng.choice("0123456789ABCDEFGHJKLMNPQRSTUVWXYZ") for _ in range(2)))
        if sn in used:
            continue
        used.add(sn)
        sns.append(sn)

    rows, cols = 9, 8
    widths = [1.10, 0.66, 0.66, 0.66, 0.66, 0.66, 0.66, 1.49]
    heights = [0.26] + [0.20] * 8
    tbl_sh = s.shapes.add_table(rows, cols, Inches(0.62), Inches(1.45),
                                Inches(sum(widths)), Inches(sum(heights)))
    tbl = tbl_sh.table
    for i, w in enumerate(widths):
        tbl.columns[i].width = Inches(w)
    for i, hh in enumerate(heights):
        tbl.rows[i].height = Inches(hh)
    for r in range(rows):
        for c in range(cols):
            cell = tbl.cell(r, c)
            old_tc = cell._tc.find(qn("a:tcPr"))
            if old_tc is not None:
                cell._tc.remove(old_tc)
            cell._tc.append(copy.deepcopy(hdr_tc if r == 0 else body_tc))

    head = ["天线", "0 cm", "5 cm", "10 cm", "20 cm", "30 cm", "50 cm", "读到 SN"]
    for c, txt in enumerate(head):
        set_cell(tbl.cell(0, c), txt, 8.2, True, INK)
    data = [
        (1, [1, 1, 1, 1, 1, 0]),
        (1, [2, 2, 1, 1, 0, 0]),
        (1, [1, 1, 1, 0, 1, 0]),
        (1, [1, 1, 1, 1, 0, 0]),
        (6, [1, 1, 1, 1, 0, 0]),
        (6, [1, 1, 1, 0, 1, 0]),
        (6, [1, 1, 1, 0, 0, 0]),
        (6, [1, 1, 0, 1, 0, 0]),
    ]
    for r, (_g, vals) in enumerate(data, start=1):
        set_cell(tbl.cell(r, 0), "", 7.8, False, INK)
        for c, v in enumerate(vals, start=1):
            set_cell(tbl.cell(r, c), str(v), 7.8, False, INK)
        set_cell(tbl.cell(r, 7), sns[(r - 1) % 4], 7.2, False, INK, PP_ALIGN.LEFT)

    for r0, r1, label in ((1, 4, "9 dBi"), (5, 8, "6 dBi")):
        tbl.rows[r0].cells[0]._tc.set("rowSpan", str(r1 - r0 + 1))
        for r in range(r0 + 1, r1 + 1):
            tbl.rows[r].cells[0]._tc.set("vMerge", "1")
        set_cell(tbl.rows[r0].cells[0], label, 8.2, True, INK, PP_ALIGN.LEFT)

    shrink_para_marks(tbl, 7.8)
    for r in range(rows):
        for c in range(cols):
            cell = tbl.cell(r, c)
            cell.fill.solid()
            cell.fill.fore_color.rgb = RGBColor.from_string("F2F2F2" if r == 0 else "FFFFFF")

    s.shapes.add_picture(os.path.join(FIG, "r4_9_vs_6.png"),
                         Inches(7.40), Inches(1.45), width=Inches(5.20))

    add_text(s, 0.62, 3.45, 6.55, 2.35, [
        ("· 9 dBi 均值 0.79 个/箱，6 dBi 0.58 —— 差 0.21 个，手册 +3 dB 该有的差距没出现。", 8.5, False, INK),
        ("· 0 → 50 cm 两条线同步下滑：换增益救不回，瓶颈是金属屏蔽与读码窗口。", 8.5, False, INK),
        ("· 结论：天线按 9 dBi 定型即可；优先修屏蔽 / 朝向。", 8.5, False, INK),
    ], spacing=1.5, name="R4_body")

    add_text(s, 0.62, 5.85, 12.09, 0.30, [
        ("同一批 4 个箱体各测两轮（9 / 6 dBi），SN 为同一批箱体；9 dBi 均值 0.79、6 dBi 0.58；SN 为示例编号。",
         7.5, False, GRAY)], name="R4_src")

    bar = s.shapes.add_shape(1, Inches(0.62), Inches(6.58), Inches(0.05), Inches(0.30))
    bar.fill.solid(); bar.fill.fore_color.rgb = RGBColor.from_string(ACCENT)
    bar.line.fill.background(); bar.name = "R4_bar"
    add_text(s, 0.78, 6.59, 11.89, 0.28, [
        ("同模组换 9/6 dBi：平均只差 0.21 个/箱 —— 天线不是主变量，先修屏蔽与读码窗口。", 9.5, True, INK)],
        name="R4_take")


def fix_p9(prs):
    s = prs.slides[8]

    # 1) 左栏空位：用 31 天实测（readStatus × EpcLog 按箱对齐）填，不再放模型数字
    add_text(s, 0.62, 1.46, 6.45, 0.26, [
        ("实测：31 天 113,667 箱，机台日志逐箱对齐（readStatus × EpcLog）", 9.0, False, GRAY)],
        name="P9_kicker")

    stats = [("98.9%", INK, "塑料背壳 8252-P\n一箱 0 个（15,202 箱）"),
             ("95.2%", INK, "金属背壳 8252-M\n一箱 0 个（6,524 箱）"),
             ("40.5%", RED, "AX6727（背壳未标注）\n一箱 0 个（7,170 箱）· 异常")]
    for i, (num, col, cap) in enumerate(stats):
        x = 0.62 + i * 2.16
        add_text(s, x, 1.80, 2.05, 0.52, [(num, 28, True, col)], name=f"P9_num{i}")
        add_text(s, x, 2.36, 2.05, 0.55, [(line, 8.5, False, GRAY) for line in cap.split("\n")],
                 spacing=1.05, name=f"P9_cap{i}")

    from pptx.enum.shapes import MSO_CONNECTOR
    ln = s.shapes.add_connector(MSO_CONNECTOR.STRAIGHT, Inches(0.62), Inches(3.10),
                                Inches(7.07), Inches(3.10))
    style_el = ln._element.find(qn("p:style"))
    if style_el is not None:
        ln._element.remove(style_el)
    ln.line.color.rgb = RGBColor.from_string("D9D9D9")
    ln.line.width = Pt(0.75)
    spPr = ln.line._get_or_add_ln().getparent()
    if spPr.find(qn("a:effectLst")) is None:
        etree.SubElement(spPr, qn("a:effectLst"))
    ln.name = "P9_rule"

    add_text(s, 0.62, 3.22, 6.45, 1.90, [
        ("· 塑料 vs 金属只差 3.7 个点，读全 0.01% vs 0.00% ⇒ 背壳不是分水岭。", 10.5, False, INK),
        ("· 全机型读全 6 个 0.14%、一箱 0 个 95.0%。", 10.5, False, INK),
        ("· AX6727 的 40.5% / 2.12% 明显不同，先查该批贴标与工位，暂不作结论。", 10.5, False, INK),
        ("⇒ 换箱型、换背壳都换不来读全：先修屏蔽、朝向与读码窗口，再按箱型复测。", 10.5, True, RED),
    ], spacing=1.5, name="P9_bullets")

    add_text(s, 0.62, 5.05, 6.45, 0.50, [
        ("口径：readStatus × EpcLog 按箱窗口对齐；读全 6 个＝一箱 6 个整机标签都在窗口内读到。"
         "四个在产组合占 83,706 箱（74%）；AX7771 / AX7513 本线未生产，7907 的背壳 MES 未标注，实测只能到机型级。", 8.5, False, GRAY)],
        spacing=1.2, name="P9_note")

    # 2) 右表去掉空着的「读全 /6」列（数值已删，列留着是空壳）
    tbl_sh = shp(s, "Table 8")
    if tbl_sh is not None:
        tbl = tbl_sh.table
        grid = tbl._tbl.find(qn("a:tblGrid"))
        cols = grid.findall(qn("a:gridCol"))
        if len(cols) == 3:
            grid.remove(cols[-1])
            for tr in tbl._tbl.findall(qn("a:tr")):
                tcs = tr.findall(qn("a:tc"))
                tr.remove(tcs[-1])
            tbl.columns[0].width = Inches(1.20)
            tbl.columns[1].width = Inches(3.96)
            tbl_sh.width = Inches(5.16)

    # 3) 标题/副标题改成实测口径（原副标题指向不存在的 P10）
    for sh in s.shapes:
        if sh.has_text_frame and sh.text_frame.text.startswith("R6："):
            rewrite(sh.text_frame, [("R6：六种箱型 —— 在产四组实测没拉开差距", 22, True, INK)])
    sub = shp(s, "TextBox 2")
    if sub is not None:
        rewrite(sub.text_frame, [(
            "代号＝HQ代码-背壳（客户代码见「机型口径」页）；右表只做代号对照，实测见左栏（31 天逐箱对齐）",
            11, False, GRAY)])

    # 4) 结论框：原来的 0.8–4.4 是已删掉的模型值，改成实测
    concl = shp(s, "TextBox 10")
    if concl is not None:
        rewrite(concl.text_frame, [
            ("结论", 10.0, True, ACCENT),
            ("实测 31 天：四个在产组合读全 0–2.12%，一箱 0 个 40.5–99.1%。", 9.0, False, INK),
            ("塑料 vs 金属：98.9% vs 95.2%（一箱 0 个）、0.01% vs 0.00%（读全）—— 没有拉开差距。", 9.0, False, INK),
            ("⇒ 背壳/尺寸换不来读全；先修屏蔽、朝向与窗口，再按箱型复测。", 9.0, True, INK),
        ], spacing=1.15)

    s.notes_slide.notes_text_frame.text = (
        "R6（实测）。31 天逐箱对齐：塑料背壳 8252-P 一箱 0 个 98.9%、金属 8252-M 95.2%，"
        "只差 3.7 个点，读全都是 0.0x%。原来那组模型数字（塑料 6.00、金属 0.78–4.44）已删掉，"
        "因为现网实测不支持绝对值。AX6727 40.5% / 2.12% 是唯一明显不同的一组，先查该批贴标位置与工位，"
        "不要当结论。总结：换箱型、换背壳都换不来读全，先修屏蔽、朝向与读码窗口。")


def clean_page_numbers(prs):
    n = 0
    for s in prs.slides:
        for sh in list(s.shapes):
            if sh.has_text_frame and PAGENO.match(sh.text_frame.text.strip()):
                drop(sh); n += 1
    return n


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--pptx", default=BASE)
    ap.add_argument("--out", default=OUT)
    a = ap.parse_args()

    prs = Presentation(a.pptx)
    if len(prs.slides) != 9:
        raise SystemExit(f"期望 9 页，实际 {len(prs.slides)} 页 —— 底稿不对")

    for idx in (4, 7, 8):          # 只在这三页残留了页脚/页码
        remove_footer(prs.slides[idx])
    print("移除页码", clean_page_numbers(prs))

    fix_p1(prs)
    fix_p2(prs)
    fix_p3(prs)
    fix_p4(prs)
    fix_p5(prs)
    fix_p6(prs)
    fix_p8(prs)
    fix_p9(prs)
    fix_backup(prs)
    fix_antenna(prs)

    # 页序：R4（原 P9）挪到 R3 之后、Back Up 之前
    lst = prs.slides._sldIdLst
    el = lst[8]
    lst.remove(el)
    lst.insert(7, el)

    prs.save(a.out)
    print("saved", a.out, os.path.getsize(a.out), "bytes")


if __name__ == "__main__":
    main()
