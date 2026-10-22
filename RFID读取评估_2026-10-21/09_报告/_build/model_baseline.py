# -*- coding: utf-8 -*-
"""逐机型基线（实测）：把 31 天逐箱 RFID 结果按「HQ代码 + 客户代码 + 尺寸/品类 + 背壳」汇总

输入（`03_数据/remote/`，由 07_方法/prod/ 与 tools/extract-sscc-model.ps1 在机台上生成，不入库）：
    rfidboxes2_*.tsv   逐箱：窗口、readStatus、SSCC
    epctags_*.tsv      逐次：InPut(EPC hex) + Epc2Dsn(DSN)
    sscc_model.tsv     SSCC → MODEL / SETTINGNAME / CongfigSize

输出：
    03_数据/model_baseline_<from>_<to>.csv   一行一个（机型 × 背壳）

用法：python model_baseline.py
"""
import os, csv, re, bisect, glob, collections
from datetime import datetime

_HERE = os.path.dirname(os.path.abspath(__file__))
REP = os.path.dirname(_HERE)
ROOT = os.path.dirname(REP)
REMOTE = os.path.join(ROOT, "03_数据", "remote")

# HQ代码 → (客户代码, 尺寸/品类)  —— 客户口径来自事业部机型对照表
CATALOG = {
    "AX6727": ("Sangria/Seabreeze", "7 inch e-reader"),
    "AX7907": ("Prosecco/Marsala", "6 inch e-reader"),
    "AX8252": ("Amaro/Julep", "7 inch e-reader"),
    "AX7771": ("Roselite", "8 inch tablet"),
    "AX7513": ("Turquoise", "11 inch tablet"),
    "AX7520": ("Spinel", "12 inch tablet"),
    "TS8265": ("Poplar", "TWS"),
    "SS8633": ("Miramar", "Echo"),
    "SS8972": ("Torte", "Echo"),
}
# MES 配置名里客户代码是脱敏写法
MASKED = {"Prosexxx": "Prosecco", "Amaxxx": "Amaro", "Julxxx": "Julep", "Marsala": "Marsala",
          "SANGRIA": "Sangria", "Seabreeze": "Seabreeze"}


def ts(s):
    return datetime.strptime(s.replace(",", ".")[:23], "%Y-%m-%d %H:%M:%S.%f")


def pick(pattern):
    fs = sorted(glob.glob(os.path.join(REMOTE, pattern)))
    if not fs:
        raise SystemExit(f"missing {pattern} in {REMOTE}（先在机台跑 07_方法/prod/ 的脚本）")
    return fs[-1]


def shell_of(cfg):
    if re.search(r"Metal|金属", cfg):
        return "金属"
    if re.search(r"Plastic|塑料", cfg):
        return "塑料"
    return "未标注"


def hq_of(model):
    m = re.match(r"^[A-Z]{2}(\d{4,5})", model or "")
    return ("AX" + m.group(1)) if m else (model or "未知")


def main():
    boxes_f, tags_f, map_f = pick("rfidboxes2_*.tsv"), pick("epctags_*.tsv"), pick("sscc_model*.tsv")
    smap = {r["sscc"]: r for r in csv.DictReader(open(map_f, encoding="utf-8-sig", newline=""), delimiter="\t")}
    print("sscc map", len(smap))

    reads = sorted((ts(r["t"]), r["epc"]) for r in csv.DictReader(open(tags_f, encoding="utf-8-sig", newline=""), delimiter="\t")
                   if (r.get("kind") or r.get("antenna")) == "InPut" and len(r["epc"]) == 24)
    rt, rv = [x[0] for x in reads], [x[1] for x in reads]
    print("96bit reads", len(reads))

    agg = collections.defaultdict(lambda: [0, 0, 0, 0, 0])  # n, true, tag0, full6, tags_total
    days = set()
    for r in csv.DictReader(open(boxes_f, encoding="utf-8-sig", newline=""), delimiter="\t"):
        m = smap.get(r.get("sscc") or "")
        if not m or not r["t_first"] or not r["t_status"]:
            continue
        hq = hq_of(m["model"])
        key = (hq, shell_of(m.get("config_size", "")))
        t0, t1 = ts(r["t_first"]), ts(r["t_status"])
        i, j = bisect.bisect_left(rt, t0), bisect.bisect_right(rt, t1)
        k = len(set(rv[i:j]))
        a = agg[key]
        a[0] += 1
        a[1] += (r["status"] == "True")
        a[2] += (k == 0)
        a[3] += (k >= 6)
        a[4] += k
        days.add(r["day"])

    rows = []
    for (hq, shell), (n, tt, z, f6, kt) in sorted(agg.items(), key=lambda kv: -kv[1][0]):
        cust, size = CATALOG.get(hq, ("未登记", "未登记"))
        rows.append(dict(hq_code=hq, customer_code=cust, size_category=size, shell=shell,
                         boxes=n, read_true_pct=round(100 * tt / n, 1), zero_tag_pct=round(100 * z / n, 1),
                         full6_pct=round(100 * f6 / n, 2), avg_tags=round(kt / n, 2)))
    span = (min(days), max(days)) if days else ("", "")
    out = os.path.join(ROOT, "03_数据", f"model_baseline_{span[0]}_{span[1]}.csv")
    with open(out, "w", newline="", encoding="utf-8-sig") as fh:
        w = csv.DictWriter(fh, fieldnames=list(rows[0].keys()))
        w.writeheader()
        w.writerows(rows)
    print("wrote", out, len(rows), "rows")
    for r in rows:
        print(r)


if __name__ == "__main__":
    main()
