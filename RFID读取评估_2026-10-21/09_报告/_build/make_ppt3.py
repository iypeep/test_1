# -*- coding: utf-8 -*-
"""在 make_ppt2.py 产出的 8 页基础上：
   1) 更正箱型代号（KD-*/PT-*/Kinder → 7907-P … 7513-M）与相关文案；
   2) 页脚 /8 → /10，封面版本改 V1.3；
   3) 末尾追加 2 页：P9 现网实测基线（31 天）、P10 机型口径（客户代码/尺寸）+ 逐机型实测。

make_ppt2.py 在本机是加密态（工具无法直接改），所以增量改版放在这里。
重建顺序：make_ppt2.py → make_ppt3.py

用法：python make_ppt3.py
输出：覆盖 ../RFID读取能力评估_2026-10-22.pptx
"""
import os, csv
from pptx import Presentation
from pptx.util import Inches, Pt
from pptx.dml.color import RGBColor
from pptx.enum.text import PP_ALIGN, MSO_ANCHOR
from pptx.oxml.ns import qn
from lxml import etree
from PIL import Image

_HERE = os.path.dirname(os.path.abspath(__file__))
REP = os.path.dirname(_HERE)
ROOT = os.path.dirname(REP)
FIG = os.path.join(REP, "figs")
PPTX = os.path.join(REP, "RFID读取能力评估_2026-10-22.pptx")
BASE_CSV = os.path.join(ROOT, "03_数据", "model_baseline_20260922_20261022.csv")

INK, GRAY, LINE = "1A1A1A", "8C8C8C", "D9D9D9"
ACCENT, ACCENT_2, TINT = "3E5DA8", "5C7ED4", "E6EDF9"
RED = "C0504D"
LATIN, EA = "Arial", "微软雅黑"
W, H, MARGIN = 13.333, 7.5, 0.62
TOTAL = 10

prs = Presentation(PPTX)
BLANK = prs.slide_layouts[6]

CODE_MAP = {"KD-SP": "7907-P", "KD-LP": "8252-P", "KD-SM": "7907-M",
            "KD-LM": "8252-M", "PT-SM": "7771-M", "PT-LM": "7513-M"}
TEXT_MAP = {
    "小 Kinder · 塑料背壳": "AX7907 · 6″ · 塑料",
    "大 Kinder · 塑料背壳": "AX8252 · 7″ · 塑料",
    "小 Kinder · 金属背壳": "AX7907 · 6″ · 金属",
    "大 Kinder · 金属背壳": "AX8252 · 7″ · 金属",
    "小平板 · 金属背壳": "AX7771 · 8″ · 金属",
    "大平板 · 金属背壳": "AX7513 · 11″ · 金属",
    "六项里只有 R1/R2 是“已确定”；R3–R6 全为预测，必须用明日实测替换后才可对外":
        "R1/R2 已确定；P9–P10 的现网基线是实测；R3–R6 仍是预测，须现场实测后才可对外",
    "塑料背壳（7907-P / 8252-P）稳定读全，尺寸影响可忽略。": "塑料背壳（7907-P / 8252-P）稳定读全，尺寸影响可忽略。",
    "平板类优于 Kinder（形体薄、遮挡少），但都无法在金属背壳下读全。":
        "平板类（7771/7513）优于 e-reader（形体薄、遮挡少），但都无法在金属背壳下读全。",
    "平板类比 Kinder 略好但同样救不回来。若产线要上金属背壳，改贴标位置或在开口侧加天线。":
        "平板类比 e-reader 略好但同样救不回来。若产线要上金属背壳，改贴标位置或在开口侧加天线。",
    "E_箱型.csv（6 行）\nKD-SP…PT-LM 六个代号\n固定 9 dBi / 10 cm / A1":
        "E_箱型.csv（6 行）\n7907-P…7513-M 六个代号\n固定 9 dBi / 10 cm / A1",
    "六种箱型": "六种箱型（按机型口径）",
    "项目代号见右表；距离固定 10 cm、姿态 A1、厂家 A —— 只有箱型不同":
        "代号＝HQ代码-背壳（客户代码见 P10）；距离 10 cm、姿态 A1、厂家 A —— 只有箱型不同",
    "同一读码器(9 dB) × 6 种箱型": "同一读码器(9 dB) × 6 种箱型（按机型口径）",
    "六项要求 · 3D 示意 · 距离与箱型读取结果（模型预测版，待实测替换）":
        "六项要求 · 3D 示意 · 现网实测基线（P9–P10）+ 距离/箱型预测（待现场实测替换）",
    "版本  V1.2（框架 + 预测数据）": "版本  V1.3（+ 现网实测基线）",
    "封面起全部数值：手册参数推算 + 参数化模型预测，非实测；明日按 P8 模板填表后重出":
        "P9–P10 为机台日志回溯的实测值；其余为手册参数推算 + 模型预测；现场按 P8 模板填表后重出 V2",
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


def textbox(slide, x, y, w, h, text, size=11, bold=False, color=INK,
            align=PP_ALIGN.LEFT, anchor=MSO_ANCHOR.TOP, spacing=1.0):
    tb = slide.shapes.add_textbox(Inches(x), Inches(y), Inches(w), Inches(h))
    tf = tb.text_frame
    tf.word_wrap = True
    tf.vertical_anchor = anchor
    tf.margin_left = tf.margin_right = tf.margin_top = tf.margin_bottom = 0
    for i, line in enumerate(text.split("\n")):
        p = tf.paragraphs[0] if i == 0 else tf.add_paragraph()
        p.alignment, p.line_spacing = align, spacing
        r = p.add_run(); r.text = line
        set_font(r, size, bold, color)
    return tb


def rich(slide, x, y, w, h, parts, spacing=1.0):
    tb = slide.shapes.add_textbox(Inches(x), Inches(y), Inches(w), Inches(h))
    tf = tb.text_frame
    tf.word_wrap = True
    tf.margin_left = tf.margin_right = tf.margin_top = tf.margin_bottom = 0
    for i, (t, sz, bold, color) in enumerate(parts):
        p = tf.paragraphs[0] if i == 0 else tf.add_paragraph()
        p.line_spacing = spacing
        r = p.add_run(); r.text = t
        set_font(r, sz, bold, color)
    return tb


def hline(slide, x, y, w, color=LINE, pt=0.75):
    from pptx.enum.shapes import MSO_CONNECTOR
    c = slide.shapes.add_connector(MSO_CONNECTOR.STRAIGHT, Inches(x), Inches(y), Inches(x + w), Inches(y))
    c.line.color.rgb = RGBColor.from_string(color)
    c.line.width = Pt(pt)


def rect(slide, x, y, w, h, fill=None, line=None, lw=0.75):
    from pptx.enum.shapes import MSO_SHAPE
    sh = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, Inches(x), Inches(y), Inches(w), Inches(h))
    sh.shadow.inherit = False
    if fill:
        sh.fill.solid(); sh.fill.fore_color.rgb = RGBColor.from_string(fill)
    else:
        sh.fill.background()
    if line:
        sh.line.color.rgb = RGBColor.from_string(line); sh.line.width = Pt(lw)
    else:
        sh.line.fill.background()
    return sh


def pic(slide, name, x, y, maxw, maxh):
    p = os.path.join(FIG, name)
    iw, ih = Image.open(p).size
    s = min(maxw / iw, maxh / ih)
    slide.shapes.add_picture(p, Inches(x), Inches(y), Inches(iw * s), Inches(ih * s))


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


def table(slide, rows, x, y, w, col_w, row_h=0.32, fs=9.5, hfs=9,
          aligns=None, bold_first_col=False, header_fill="F2F2F2"):
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
            cell.fill.fore_color.rgb = RGBColor.from_string(header_fill if ri == 0 else "FFFFFF")
            _border(cell)
            p = cell.text_frame.paragraphs[0]
            p.alignment = aligns[ci] if aligns else (PP_ALIGN.CENTER if ci else PP_ALIGN.LEFT)
            p.line_spacing = 1.0
            r = p.add_run(); r.text = str(rows[ri][ci])
            set_font(r, hfs if ri == 0 else fs, (ri == 0) or (bold_first_col and ci == 0))
    return shp


def stat(slide, x, y, w, num, unit, label, color=ACCENT):
    textbox(slide, x, y, w, 0.5, num, size=26, bold=True, color=color)
    textbox(slide, x, y + 0.46, w, 0.24, unit, size=9.5, color=GRAY)
    textbox(slide, x, y + 0.72, w, 0.5, label, size=10, color=INK, spacing=1.15)


def takeaway(slide, y, text, x=MARGIN, w=None):
    w = w or (W - x - MARGIN)
    rect(slide, x, y, 0.05, 0.34, fill=ACCENT)
    textbox(slide, x + 0.16, y + 0.02, w - 0.2, 0.32, text, size=11, bold=True, anchor=MSO_ANCHOR.MIDDLE)


def page(title, kicker=None, num=None):
    s = prs.slides.add_slide(BLANK)
    textbox(s, MARGIN, 0.40, W - 2 * MARGIN, 0.55, title, size=22, bold=True)
    if kicker:
        textbox(s, MARGIN, 0.96, W - 2 * MARGIN, 0.30, kicker, size=11, color=GRAY)
        hline(s, MARGIN, 1.32, W - 2 * MARGIN)
    else:
        hline(s, MARGIN, 1.04, W - 2 * MARGIN)
    if num is not None:
        textbox(s, MARGIN, 7.02, 8.0, 0.26,
                "RFID 读取能力评估 · 7H3AA-PALLET · 2026-10-22", size=8, color=GRAY)
        textbox(s, W - MARGIN - 0.8, 7.02, 0.8, 0.26, f"{num} / {TOTAL}", size=8, color=GRAY, align=PP_ALIGN.RIGHT)
        hline(s, MARGIN, 6.94, W - 2 * MARGIN, color="ECECEC")
    return s


# ============================================================ 1) 旧页文案更正
def patch_run(t):
    for a, b in TEXT_MAP.items():
        if a in t:
            t = t.replace(a, b)
    for a, b in CODE_MAP.items():          # 代号是唯一 token，允许嵌在句子里
        if a in t:
            t = t.replace(a, b)
    return t


def patch_slide(slide):
    for sh in slide.shapes:
        if sh.has_text_frame:
            for p in sh.text_frame.paragraphs:
                for r in p.runs:
                    t = patch_run(r.text)
                    if t != r.text:
                        r.text = t
        if getattr(sh, "has_table", False) and sh.has_table:
            for row in sh.table.rows:
                for cell in row.cells:
                    for p in cell.text_frame.paragraphs:
                        for r in p.runs:
                            t = patch_run(r.text)
                            if t != r.text:
                                r.text = t


for sl in prs.slides:
    patch_slide(sl)

# 页脚 /8 → /10
for sl in prs.slides:
    for sh in sl.shapes:
        if sh.has_text_frame:
            for p in sh.text_frame.paragraphs:
                for r in p.runs:
                    if r.text.strip().endswith("/ 8"):
                        r.text = r.text.replace("/ 8", f"/ {TOTAL}")

# ============================================================ 2) P9 现网实测基线
s = page("现网实测基线：95% 的箱一个整机标签都没读到",
         "机台自身日志回溯 31 天（2026-09-22 → 10-22）；Rfid_<日期>.log 逐箱 readStatus × EpcLog 逐次读取 —— 实测，不是模型", 9)

stat(s, MARGIN, 1.46, 3.9, "95.0%", "一箱读到 0 个整机标签（108,017 / 113,667 箱）", "RFID 环节目前是“形式执行”")
stat(s, 4.62, 1.46, 3.9, "0.14%", "真正读全 6 个（158 箱）", "一箱 6 台，标签全读到几乎不发生", color=RED)
stat(s, 8.62, 1.46, 3.9, "8.6%", "程序 readStatus=True（逐日 6.9–10.5%）", "失败不阻断放行 ⇒ 产线上看不见")

pic(s, "fig13_prod_readout.png", 6.55, 2.72, 6.2, 2.2)

rows = [
    ["指标（31 天）", "值"],
    ["一箱读到 0 个整机标签", "108,017 箱 = 95.0%"],
    ["读到 1 / 2 / 6 个", "3,997 / 972 / 158"],
    ["窗口内 ≥1 个", "4.9%（±10 s 口径 9.0%）"],
    ["读全 6 个", "158 箱 = 0.14%"],
    ["正常日标签读取次数", "250–550 次/日（过箱 3,000–5,200）"],
]
table(s, rows, MARGIN, 2.72, 5.75, [2.5, 3.25], row_h=0.36, fs=9.2, hfs=9,
      bold_first_col=True, aligns=[PP_ALIGN.LEFT, PP_ALIGN.LEFT])

rich(s, MARGIN, 5.32, 5.75, 1.35, [
    ("三条解读", 10, True, ACCENT),
    ("① 不是“偶尔漏一个”，是几乎完全不读：95% 的箱窗口内 0 个标签。", 9.2, False, INK),
    ("② 失败不阻断：readStatus=False 后照常 Weight Flow，无报警、不停线。", 9.2, False, INK),
    ("③ “6 台/箱”来自 MES 报文（BoxQty=6），与 RFID 读到几个无关，两者长期被混为一谈。", 9.2, False, INK),
], spacing=1.25)
takeaway(s, 6.42, "现网基线已实测：先修“读不到”与“失败不阻断”，再谈距离/增益/厂家——否则改造收益无法验证")

# ============================================================ 3) P10 机型口径 + 逐机型实测
rows = [["HQ代码", "客户代码", "尺寸 / 品类", "背壳", "箱数", "readStatus=True", "窗口 0 标签", "读全 6 个"]]
extra = [["AX7771", "Roselite", "8 inch tablet", "—", "本线未生产", "—", "—", "—"],
         ["AX7513", "Turquoise", "11 inch tablet", "—", "本线未生产", "—", "—", "—"]]
if os.path.exists(BASE_CSV):
    for r in csv.DictReader(open(BASE_CSV, encoding="utf-8-sig")):
        rows.append([r["hq_code"], r["customer_code"], r["size_category"], r["shell"],
                     f"{int(r['boxes']):,}", r["read_true_pct"] + "%", r["zero_tag_pct"] + "%", r["full6_pct"] + "%"])
rows += extra

s = page("机型口径：HQ 代码 / 客户代码 / 尺寸·品类（附 31 天实测）",
         "客户口径取自事业部机型对照表；MES CongfigSize 可交叉验证（Prosexxx / Amaxxx / Julxxx 为脱敏写法）", 10)
table(s, rows, MARGIN, 1.48, 12.1, [1.35, 2.5, 2.35, 1.0, 1.5, 1.7, 1.55, 1.25], row_h=0.37,
      fs=8.8, hfs=8.4, bold_first_col=True,
      aligns=[PP_ALIGN.LEFT, PP_ALIGN.LEFT, PP_ALIGN.LEFT, PP_ALIGN.CENTER] +
             [PP_ALIGN.RIGHT] * 4)

rich(s, MARGIN, 4.30, 7.45, 2.0, [
    ("口径更正（今天定的）", 10, True, RED),
    ("「Kinder」在机台日志里一次都没出现，是早期猜测 —— 作废；旧代号 KD-SP/LP/SM/LM、PT-SM/LM 一并作废。",
     9.0, False, INK),
    ("新代号＝HQ代码-背壳：7907-P / 7907-M / 8252-P / 8252-M / 7771-M / 7513-M。", 9.0, True, INK),
    ("背壳材质不是猜的：MES CongfigSize 直接写 (Metal)/(Plastic)，AX8252 两种都在产。", 9.0, False, INK),
    ("AX6727（Sangria/Seabreeze）读全 2.12%、均值 1.02，明显偏离其余机型 —— 记为异常，先查贴标/工位。",
     9.0, False, RED),
], spacing=1.3)

rect(s, 8.30, 4.30, 4.42, 2.0, fill=TINT)
rich(s, 8.48, 4.42, 4.06, 1.8, [
    ("数据来源与边界", 10, True, ACCENT),
    ("箱数＝31 天有 SSCC 且有 readStatus 的箱（94,284 个 SSCC 可映射机型）。", 8.8, False, INK),
    ("readStatus 判定口径仍需程序方确认（是否＝读到指定标签、RfidCheckFullOrSingle=2 的含义）。", 8.8, False, INK),
    ("逐台对号做不到：箱内 6 台条码不会同时出现在同一窗口。", 8.8, False, INK),
], spacing=1.3)
takeaway(s, 6.42, "对外一律用「HQ代码 + 客户代码 + 尺寸/品类」三件套标注机型，不再用 Kinder/大小 这类无法核对的写法")

# ============================================================ 4) 讲稿
NOTES = {
    9: "这一页是今天新增的实测基线，也是全场最硬的一页。数据不是探针测的，是机台自己日志回溯 31 天："
       "Rfid_<日期>.log 每箱一条 readStatus，EpcLog 每次读取都有时间戳和 DSN，按箱处理窗口（约 3 秒）对齐就能算“这箱读到几个”。"
       "结论：95% 的箱一个整机标签都没有，读全 6 个的 31 天只有 158 箱。要强调两点："
       "一是失败不阻断放行，所以产线上看不见；二是 6 台/箱 是 MES 报文，不等于读到 6 个。"
       "如果被问“为什么一直没人发现”，答案是程序既不停线也不报警，只看产量是正常的。",
    10: "机型口径页。旧的 Kinder 与 KD/PT 代号是早期猜测，机台日志里根本没有，今天作废。"
        "改成 HQ代码-背壳：7907-P/M、8252-P/M、7771-M、7513-M；客户代码按事业部对照表，MES 配置名可交叉验证。"
        "背壳材质有直接证据：CongfigSize 里写 (Metal)/(Plastic)，AX8252 两种都在产，所以同机型要分开看。"
        "AX6727 那行数字明显异常，先记录，不建议当结论。",
}
for i, sl in enumerate(prs.slides, start=1):
    if i in NOTES:
        sl.notes_slide.notes_text_frame.text = NOTES[i]

prs.save(PPTX)
print("saved", PPTX, os.path.getsize(PPTX), "bytes,", len(prs.slides._sldIdLst), "slides")
