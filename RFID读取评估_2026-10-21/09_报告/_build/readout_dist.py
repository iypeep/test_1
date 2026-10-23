# -*- coding: utf-8 -*-
"""逐机型「读到几个」的累计分布（实测，31 天）

对每个（HQ代码 × 背壳）统计：一箱读到 0..6 个整机标签的箱数，
并给出累计占比 P(≤1) / P(≤2) / P(≤3) / P(≤4) / P(≤5) 与 P(读全 6)。

口径与 model_baseline.py 完全一致（同一份逐箱窗口 × EpcLog 96-bit 读取，按箱时间窗去重），
只是额外输出「每个箱到底是几个」的分布。

输入（`03_数据/remote/`，机台生成、不入库）：
    rfidboxes2_*.tsv / epctags_*.tsv / sscc_model*.tsv
输出：
    03_数据/model_readout_dist_<from>_<to>.csv
用法：py -3.12 readout_dist.py
"""
import os, csv, re, bisect, glob, collections
from datetime import datetime

_HERE = os.path.dirname(os.path.abspath(__file__))
REP = os.path.dirname(_HERE)
ROOT = os.path.dirname(REP)
REMOTE = os.path.join(ROOT, "03_数据", "remote")

CATALOG = {
    "AX6727": ("Sangria/Seabreeze", "7 inch e-reader"),
    "AX7907": ("Prosecco/Marsala", "6 inch e-reader"),
    "AX8252": ("Amaro/Julep", "7 inch e-reader"),
    "AX7771": ("Roselite", "8 inch tablet"),
    "AX7513": ("Turquoise", "11 inch tablet"),
}


def ts(s):
    return datetime.strptime(s.replace(",", ".")[:23], "%Y-%m-%d %H:%M:%S.%f")


def pick(pattern):
    fs = sorted(glob.glob(os.path.join(REMOTE, pattern)))
    if not fs:
        raise SystemExit(f"missing {pattern} in {REMOTE}")
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
    reads = sorted((ts(r["t"]), r["epc"])
                   for r in csv.DictReader(open(tags_f, encoding="utf-8-sig", newline=""), delimiter="\t")
                   if (r.get("kind") or r.get("antenna")) == "InPut" and len(r["epc"]) == 24)
    rt = [x[0] for x in reads]
    rv = [x[1] for x in reads]
    print(f"sscc map {len(smap)}, 96-bit reads {len(reads)}")

    agg = collections.defaultdict(lambda: {"n": 0, "true": 0, "dist": [0] * 7})
    days = set()
    for r in csv.DictReader(open(boxes_f, encoding="utf-8-sig", newline=""), delimiter="\t"):
        m = smap.get(r.get("sscc") or "")
        if not m or not r["t_first"] or not r["t_status"]:
            continue
        key = (hq_of(m["model"]), shell_of(m.get("config_size", "")))
        t0, t1 = ts(r["t_first"]), ts(r["t_status"])
        i, j = bisect.bisect_left(rt, t0), bisect.bisect_right(rt, t1)
        k = len(set(rv[i:j]))
        a = agg[key]
        a["n"] += 1
        a["true"] += (r["status"] == "True")
        a["dist"][min(k, 6)] += 1
        days.add(r["day"])

    def pct(x, n):
        return round(100.0 * x / n, 2) if n else 0.0

    rows, tot = [], {"n": 0, "true": 0, "dist": [0] * 7}
    for (hq, shell), a in sorted(agg.items(), key=lambda kv: -kv[1]["n"]):
        n, d = a["n"], a["dist"]
        cust, size = CATALOG.get(hq, ("未登记", "未登记"))
        row = {
            "hq_code": hq, "customer_code": cust, "size_category": size, "shell": shell, "boxes": n,
            "read_true_pct": pct(a["true"], n),
            "boxes_0": d[0], "boxes_1": d[1], "boxes_2": d[2], "boxes_3": d[3],
            "boxes_4": d[4], "boxes_5": d[5], "boxes_6": d[6],
            "le1_pct": pct(sum(d[0:2]), n), "le2_pct": pct(sum(d[0:3]), n),
            "le3_pct": pct(sum(d[0:4]), n), "le4_pct": pct(sum(d[0:5]), n),
            "le5_pct": pct(sum(d[0:6]), n), "full6_pct": pct(d[6], n),
            "avg_tags": round(sum(i * d[i] for i in range(7)) / n, 2),
        }
        rows.append(row)
        for k in ("n",):
            pass
        tot["n"] += n
        tot["true"] += a["true"]
        for i in range(7):
            tot["dist"][i] += d[i]

    n, d = tot["n"], tot["dist"]
    rows.append({
        "hq_code": "合计", "customer_code": "", "size_category": "", "shell": "", "boxes": n,
        "read_true_pct": pct(tot["true"], n),
        "boxes_0": d[0], "boxes_1": d[1], "boxes_2": d[2], "boxes_3": d[3],
        "boxes_4": d[4], "boxes_5": d[5], "boxes_6": d[6],
        "le1_pct": pct(sum(d[0:2]), n), "le2_pct": pct(sum(d[0:3]), n),
        "le3_pct": pct(sum(d[0:4]), n), "le4_pct": pct(sum(d[0:5]), n),
        "le5_pct": pct(sum(d[0:6]), n), "full6_pct": pct(d[6], n),
        "avg_tags": round(sum(i * d[i] for i in range(7)) / n, 2),
    })

    span = (min(days), max(days))
    out = os.path.join(ROOT, "03_数据", f"model_readout_dist_{span[0]}_{span[1]}.csv")
    with open(out, "w", newline="", encoding="utf-8-sig") as fh:
        w = csv.DictWriter(fh, fieldnames=list(rows[0].keys()))
        w.writeheader(); w.writerows(rows)
    print("wrote", out)

    print("\n| HQ代码 | 背壳 | 箱数 | 0 个 | 1 | 2 | 3 | 4 | 5 | 6 | ≤1 | ≤2 | ≤3 | ≤4 | ≤5 | 读全6 |")
    print("|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|")
    for r in rows:
        print(f"| {r['hq_code']} | {r['shell']} | {r['boxes']:,} | " +
              " | ".join(f"{r[f'boxes_{i}']:,}" for i in range(7)) +
              f" | {r['le1_pct']}% | {r['le2_pct']}% | {r['le3_pct']}% | {r['le4_pct']}% | {r['le5_pct']}% | {r['full6_pct']}% |")
    print("\n注意：≤N 是累计（读到 ≤N 个的箱占比），读全 6 个＝读到 6 个（=100%−≤5）。")


if __name__ == "__main__":
    main()
