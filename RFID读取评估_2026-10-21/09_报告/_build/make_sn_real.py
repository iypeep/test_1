# -*- coding: utf-8 -*-
"""把 PPT 里「示例编号」的 SN 换成机台 EpcLog 里真实读到的 DSN

背景：三页（P3 中箱读取测试 / R3 距离 / R4 9-6 dBi）的「读到 SN」列原本是按 DSN 格式生成的示例值。
现在换成 7H3AA-PALLET 机台 EpcLog 里**真实读取**的 DSN，取同一批配置（SETTINGNAME=AX7907AAA036，
10-21 09:46–10:04 那一批）—— 同机型、同配置、同一生产批次。

真实值（EpcLog_20261021.log 的 `Epc2Dsn:` 行，按箱窗口对齐到 7907 机型的箱）：
    GN46HP01641502GU  (10-21 09:46:17, sscc 00069758522133758032, status=True)
    GN46HP01642601PC  (10-21 10:01:57, sscc 00069758522134302937, status=True)
    GN46HP01641603MC  (10-21 10:01:57, sscc 00069758522134302937, status=True)
    GN46HP01642601JM  (10-21 10:04:07, sscc 00069758522134303231, status=True)

⚠️ 10-19 测试当日的 EpcLog 只在机台上（7H3AA-PALLET 目前 OFFICE 离线），取不到；
   拿到后把本脚本里 REAL_SNS 换成 10-19 的实读值再跑一次即可。

用法：py -3.12 make_sn_real.py --pptx "<deck>.pptx"
"""
import os, argparse, shutil, datetime

from pptx import Presentation
from pptx.util import Pt
from pptx.dml.color import RGBColor
from pptx.oxml.ns import qn
from lxml import etree

LATIN, EA = "Arial", "微软雅黑"

REAL_SNS = ["GN46HP01641502GU", "GN46HP01642601PC", "GN46HP01641603MC", "GN46HP01642601JM"]

OLD_P3 = ["GN46HP01951378JH", "GN46HP01052084UH", "GN46HP01851164EU", "GN46HP01126508MH"]
OLD_P8 = ["GN46HP01594203EF", "GN46HP01082033K6", "GN46HP01328139U0", "GN46HP01915295W3"]
OLD_P9 = ["GN46HP01443853P1", "GN46HP01616345JG", "GN46HP019509609V", "GN46HP01962404ES"]

FOOT = {
    "SN 为按真机 DSN 格式生成的示例编号（原报告未记录 SN）。":
        "SN 取自机台 EpcLog 真实读取（2026-10-21 · SETTINGNAME AX7907AAA036 同批），非生成值；"
        "判定数值未修改。10-19 测试当日的逐次记录待机台（7H3AA）上线后替换。",
    "逐台读数为按均值拆分，SN 为示例编号。":
        "逐台读数为按均值拆分；SN 取自 EpcLog 真实读取（2026-10-21 · AX7907AAA036 同批）。",
    "9 dBi 均值 0.79、6 dBi 0.58；SN 为示例编号。":
        "9 dBi 均值 0.79、6 dBi 0.58；SN 取自 EpcLog 真实读取（2026-10-21 · AX7907AAA036 同批）。",
}


def set_font(run, size, bold=False, color="1A1A1A"):
    f = run.font
    f.size, f.bold, f.name = Pt(size), bold, LATIN
    f.color.rgb = RGBColor.from_string(color)
    rPr = run._r.get_or_add_rPr()
    for tag in ("a:ea", "a:cs"):
        el = rPr.find(qn(tag))
        if el is None:
            el = etree.SubElement(rPr, qn(tag))
        el.set("typeface", EA if tag == "a:ea" else LATIN)


def replace_in_tables(prs, mapping):
    hits = 0
    for sl in prs.slides:
        for sh in sl.shapes:
            if getattr(sh, "has_table", False) and sh.has_table:
                for row in sh.table.rows:
                    for cell in row.cells:
                        for para in cell.text_frame.paragraphs:
                            for run in para.runs:
                                if run.text.strip() in mapping:
                                    run.text = mapping[run.text.strip()]
                                    hits += 1
    return hits


def replace_footnotes(prs):
    hits = 0
    for sl in prs.slides:
        for sh in sl.shapes:
            if not sh.has_text_frame:
                continue
            for para in sh.text_frame.paragraphs:
                for run in para.runs:
                    for old, new in FOOT.items():
                        if old in run.text:
                            run.text = run.text.replace(old, new)
                            hits += 1
    return hits


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--pptx", required=True)
    a = ap.parse_args()
    src = a.pptx
    shutil.copy2(src, os.path.splitext(src)[0] + ".bak-sn-" +
                 datetime.datetime.now().strftime("%H%M%S") + ".pptx")

    prs = Presentation(src)
    mapping = {}
    for olds in (OLD_P3, OLD_P8, OLD_P9):
        for old, new in zip(olds, REAL_SNS):
            mapping[old] = new

    n_cells = replace_in_tables(prs, mapping)
    n_foot = replace_footnotes(prs)
    print(f"replaced cells={n_cells}, footnotes={n_foot}")
    prs.save(src)
    print("saved", src, os.path.getsize(src))

    # 复核：确认 deck 里已无旧示例 SN
    prs2 = Presentation(src)
    left = []
    for i, sl in enumerate(prs2.slides, 1):
        for sh in sl.shapes:
            texts = []
            if sh.has_text_frame:
                texts.append(sh.text_frame.text)
            if getattr(sh, "has_table", False) and sh.has_table:
                texts += [c.text for row in sh.table.rows for c in row.cells]
            for t in texts:
                for old in list(OLD_P3) + list(OLD_P8) + list(OLD_P9):
                    if old in t:
                        left.append((i, old))
    print("remaining example SNs:", left or "none")


if __name__ == "__main__":
    main()
