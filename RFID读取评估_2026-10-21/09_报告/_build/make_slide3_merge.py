# -*- coding: utf-8 -*-
"""把 2026-10-19 中箱读取测试（AX7907A 金属背板 Kinder）融合到「改动版」PPT 第 3 页。

原则：
  * 只改第 3 页；其余页一律不动（不改页序、不改页脚、不改母版）。
  * 原有 3D 图（R4 距离测量几何）保留在左上方。
  * 左侧下方新增「readStatus=True 实测样例」小表（真实日志行，SN 末段打码，数值不修改）。
  * 右侧新增中箱测试矩阵（6 个面 × 大/小平板）+ 现象/结论/建议，数据逐格取自
    `E:\\feishu_Download\\RFID中箱读取测试报告_20261019.pdf`，与原报告文字自洽
    （上/下各 5 处、左/右各 2 处、前 1、后 0；大平板单次最多 1、小平板最多 2）。

用法：
    python make_slide3_merge.py --pptx "E:\\Desktop\\RFID读取能力评估-改动版.pptx"
    python make_slide3_merge.py --pptx ... --out 另一个.pptx      # 不改原文件
    python make_slide3_merge.py --pptx ... --samples-tsv <rfidboxes2.tsv> --sscc-tsv <sscc_model.tsv>
"""
import os, csv, re, argparse, shutil, datetime

from pptx import Presentation
from pptx.util import Inches, Pt
from pptx.dml.color import RGBColor
from pptx.enum.text import PP_ALIGN, MSO_ANCHOR
from pptx.oxml.ns import qn
from lxml import etree

INK, GRAY, LINE = "1A1A1A", "8C8C8C", "D9D9D9"
ACCENT, TINT, RED = "3E5DA8", "E6EDF9", "C0504D"
LATIN, EA = "Arial", "微软雅黑"
W, MARGIN = 13.333, 0.62

# ---------------------------------------------------------------- 中箱测试矩阵（原报告逐格抄录）
# 表头列＝箱体朝下接触底部读取器的那个面；格子＝该姿态下一次试验读出的平板数（空白＝0）
BOX = {
    "大平板": [[1, 0, 0, 1, 0, 0],    # 第1次：上=1 右=1
               [1, 1, 1, 1, 0, 0],    # 第2次：上=1 下=1 左=1 右=1
               [1, 1, 0, 0, 0, 0],    # 第3次：上=1 下=1
               [0, 1, 0, 0, 0, 0]],   # 第4次：下=1
    "小平板": [[1, 1, 0, 0, 0, 0],    # 第1次：上=1 下=1
               [2, 0, 2, 0, 0, 0],    # 第2次：上=2 左=2
               [0, 0, 0, 0, 1, 0],    # 第3次：前=1
               [0, 1, 0, 0, 0, 0]],   # 第4次：下=1
}
FACES = ["上", "下", "左", "右", "前", "后"]
BOX_TITLE = "中箱读取测试（2026-10-19）· 实验对象：AX7907A 金属背板 Kinder（原报告称大/小平板）"


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


def textbox(slide, x, y, w, h, text, size=10, bold=False, color=INK,
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


def table(slide, rows, x, y, w, col_w, row_h=0.3, fs=8.8, hfs=8.4,
          aligns=None, bold_first_col=False, header_fill="F2F2F2",
          highlight_rows=(), highlight_fill="FBE9E7"):
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
            cell.margin_left = cell.margin_right = Inches(0.05)
            cell.margin_top = cell.margin_bottom = Inches(0.01)
            cell.vertical_anchor = MSO_ANCHOR.MIDDLE
            cell.fill.solid()
            fill = header_fill if ri == 0 else (highlight_fill if ri in highlight_rows else "FFFFFF")
            cell.fill.fore_color.rgb = RGBColor.from_string(fill)
            _border(cell)
            p = cell.text_frame.paragraphs[0]
            p.alignment = aligns[ci] if aligns else (PP_ALIGN.CENTER if ci else PP_ALIGN.LEFT)
            p.line_spacing = 1.0
            r = p.add_run(); r.text = str(rows[ri][ci])
            set_font(r, hfs if ri == 0 else fs, (ri == 0) or (bold_first_col and ci == 0))
    return shp


# ---------------------------------------------------------------- 实测样例（真实日志，仅打码 SN）
def mask_sn(sn):
    sn = sn.strip()
    return (sn[:8] + "…" + sn[-4:]) if len(sn) > 12 else sn


def shell_of(cfg):
    if re.search(r"Metal|金属", cfg or ""):
        return "金属"
    if re.search(r"Plastic|塑料", cfg or ""):
        return "塑料"
    return "未标注"


def load_samples(boxes_tsv, sscc_tsv, n=5):
    if not (boxes_tsv and sscc_tsv and os.path.exists(boxes_tsv) and os.path.exists(sscc_tsv)):
        return None
    smap = {r["sscc"]: r for r in csv.DictReader(open(sscc_tsv, encoding="utf-8-sig", newline=""), delimiter="\t")}
    rows = list(csv.DictReader(open(boxes_tsv, encoding="utf-8-sig", newline=""), delimiter="\t"))
    pool = [r for r in rows if r["status"] == "True" and r["tag_distinct"] == "1" and r["sscc"] in smap]
    pool.sort(key=lambda r: r["t_status"])
    picked = pool[-n:] if len(pool) > n else pool
    out = []
    for r in picked:
        m = smap[r["sscc"]]
        hq = re.match(r"^[A-Z]{2}\d{4,5}", m["model"] or "")
        hq = hq.group(0) if hq else (m["model"] or "-")
        try:
            sec = float(r["delay_ms"]) / 1000.0
        except ValueError:
            sec = float("nan")
        out.append([r["t_status"][11:19], hq, shell_of(m.get("config_size", "")),
                    "1", f"{sec:.1f}", mask_sn(r["tag_ids"].split("|")[0])])
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--pptx", required=True)
    ap.add_argument("--out", default="")
    ap.add_argument("--samples-tsv", default=r"E:\Desktop\闲置\杂项\test_1\RFID读取评估_2026-10-21\03_数据\remote\rfidboxes2_20260922_20261022.tsv")
    ap.add_argument("--sscc-tsv", default=r"E:\Desktop\闲置\杂项\test_1\RFID读取评估_2026-10-21\03_数据\remote\sscc_model.tsv")
    a = ap.parse_args()

    src = a.pptx
    out = a.out or src
    if out == src:
        bak = os.path.splitext(src)[0] + ".bak-" + datetime.datetime.now().strftime("%H%M%S") + ".pptx"
        shutil.copy2(src, bak)
        print("backup:", bak)

    prs = Presentation(src)
    if len(prs.slides) < 3:
        raise SystemExit("第 3 页不存在")
    s = prs.slides[2]

    # 清掉上一版脚本加的块（可重复执行）：按名字前缀识别
    for sh in list(s.shapes):
        if sh.name.startswith("S3_"):
            sh._element.getparent().remove(sh._element)

    # ------------------------------------------------ 左：readStatus=True 实测样例
    samples = load_samples(a.samples_tsv, a.sscc_tsv)
    if samples:
        y = 4.02
        tb = textbox(s, MARGIN, y, 6.3, 0.26, "实测样例：readStatus=True 的箱（10-22 机台日志，逐箱一条）", size=9.5, bold=True, color=ACCENT)
        tb.name = "S3_cap"
        rows = [["时间", "机型", "背壳", "读到个数", "耗时 s", "读到标签（SN 打码）"]] + samples
        t = table(s, rows, MARGIN, y + 0.30, 6.3, [0.85, 1.0, 0.8, 0.95, 0.8, 2.1],
                  row_h=0.28, fs=8.2, hfs=8.0, bold_first_col=False,
                  aligns=[PP_ALIGN.CENTER, PP_ALIGN.CENTER, PP_ALIGN.CENTER, PP_ALIGN.CENTER, PP_ALIGN.CENTER, PP_ALIGN.LEFT])
        t.name = "S3_samples"
        tb = textbox(s, MARGIN, y + 0.30 + 0.28 * (len(rows)) + 0.06, 6.3, 0.24,
                     "口径：readStatus=True＝该箱 RFID 环节判定成功；读到 1 个标签即计入。SN 末段打码，数值未修改。",
                     size=7.8, color=GRAY)
        tb.name = "S3_note"
    else:
        print("!! 没有样例 TSV，跳过左侧小表")

    # ------------------------------------------------ 右：中箱测试矩阵
    x, w = 7.15, 5.56
    tb = textbox(s, x, 1.42, w, 0.28, BOX_TITLE, size=9.5, bold=True, color=INK)
    tb.name = "S3_boxtitle"

    rows = [["朝下面", "上", "下", "左", "右", "前", "后"]]
    for name, trials in BOX.items():
        hits = [sum(1 for t in trials if t[i] > 0) for i in range(6)]
        mx = max(max(t) for t in trials)
        rows.append([f"{name}（{len(trials)} 次，单次最多 {mx} 个）"] + [str(v) if v else "–" for v in hits])
    tot = [sum(1 for t in BOX[k] if t[i] > 0) for i in range(6) for k in BOX]  # placeholder, recompute below
    tot = [sum(1 for k in BOX for t in BOX[k] if t[i] > 0) for i in range(6)]
    rows.append(["合计（8 次试验）"] + [str(v) if v else "0" for v in tot])
    rows.append(["目标（整箱）"] + ["6"] * 6)

    t = table(s, rows, x, 1.74, w, [2.05, 0.58, 0.58, 0.58, 0.58, 0.58, 0.58],
              row_h=0.34, fs=8.8, hfs=8.6, bold_first_col=True,
              aligns=[PP_ALIGN.LEFT] + [PP_ALIGN.CENTER] * 6,
              highlight_rows=(len(rows) - 1,), highlight_fill=TINT)
    t.name = "S3_boxtable"

    rich(s, x, 3.62, w, 2.05, [
        ("现象", 9.5, True, ACCENT),
        ("· 单次最多只读到 2 个（目标 6 个）；其余大多 1 个，不少姿态为 0。", 8.8, False, INK),
        ("· 姿态差异明显：上/下作底面各有 5 处记录读到，左/右各 2 处，前 1 处、后 0 处。", 8.8, False, INK),
        ("· 大平板比小平板更差：大平板单次最多 1 个，小平板最多 2 个。", 8.8, False, INK),
        ("结论与建议", 9.5, True, RED),
        ("· 平板是金属件，屏蔽 + 相互遮挡 ⇒ 现有「底面＋侧面＋顶面」三面布置无法整箱读全。", 8.8, False, INK),
        ("· 若继续推进：姿态固定上/下朝下，并做抗金属标签 / 天线布局 / 功率专项；否则改开箱或逐件读取。", 8.8, False, INK),
    ], spacing=1.18)
    for sh in s.shapes:
        pass
    # rich() 只返回 textbox，命名留给清理
    s.shapes[-1].name = "S3_boxtext"

    tb = textbox(s, x, 5.78, w, 0.42,
                 "来源：RFID中箱读取测试报告_20261019.pdf（2026-10-19）。表格数字＝该姿态下一次试验读出的平板数，"
                 "「–」＝该次未读到；合计＝8 次试验中读到 ≥1 个的次数。",
                 size=7.6, color=GRAY)
    tb.name = "S3_source"

    # ------------------------------------------------ 底部一句
    from pptx.enum.shapes import MSO_SHAPE
    bar = s.shapes.add_shape(MSO_SHAPE.RECTANGLE, Inches(MARGIN), Inches(6.62), Inches(0.05), Inches(0.30))
    bar.fill.solid(); bar.fill.fore_color.rgb = RGBColor.from_string(ACCENT); bar.line.fill.background()
    bar.shadow.inherit = False
    bar.name = "S3_bar"
    tb = textbox(s, MARGIN + 0.16, 6.63, W - 2 * MARGIN - 0.2, 0.28,
                 "两次实验指向同一件事：读不全不是「角度没摆对」，而是金属负载 + 标签离天线的距离；先修读不到，再谈布置。",
                 size=10, bold=True, anchor=MSO_ANCHOR.MIDDLE)
    tb.name = "S3_take"

    prs.save(out)
    print("saved", out, os.path.getsize(out), "bytes; slides =", len(prs.slides._sldIdLst))


if __name__ == "__main__":
    main()
