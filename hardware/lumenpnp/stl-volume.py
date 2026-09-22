#!/usr/bin/env python3
"""从官方 LumenPnP STL 包估算 3D 打印耗材量（纯标准库，Python 3.7+）。

用法:
    python stl-volume.py LumenPnP-STLs-v4.1.0.zip            # 算包里全部件
    python stl-volume.py LumenPnP-STLs-v4.1.0.zip 8mm 12mm  # 只算文件名含关键字的件
    python stl-volume.py xxx.zip --tsv > cost.tsv            # 输出制表符分隔，便于 diff

原理:
    1. 解析二进制 STL 三角面片，用散度定理求闭合壳体体积（有符号四面体体积和取绝对值）。
    2. 实体体积 -> 实际挤出量: 这类薄壁件实测约为实体体积的 0.3~0.4 倍
       （2~3 圈墙 + 20% 填充），取 0.35。**这是估算，不是切片器结果**：
       要精确请用切片器的耗材统计（PrusaSlicer/Orca 里可直接看到克数）。
    3. 密度: PLA 1.24 g/cm^3, PETG 1.27 g/cm^3。默认按 1.24 计。

输出列: 文件 / 实体体积(cm3) / 外形尺寸(mm) / 估计耗材(g)
"""

import argparse
import os
import struct
import sys
import zipfile

DENSITY = 1.24  # g/cm^3, PLA
EXTRUSION_RATIO = 0.35  # 薄壁件实际挤出 / 实体体积


def stl_volume(data: bytes):
    """返回 (闭合壳体体积 mm^3, [x, y, z 尺寸 mm])。支持二进制 STL。"""
    if len(data) < 84:
        return None
    n = struct.unpack_from("<I", data, 80)[0]
    if 84 + n * 50 > len(data):
        # 二进制面数对不上，多半是 ASCII STL
        return None
    vol = 0.0
    lo = [float("inf")] * 3
    hi = [float("-inf")] * 3
    off = 84
    for _ in range(n):
        f = struct.unpack_from("<12f", data, off)
        off += 50
        a = (f[3], f[4], f[5])
        b = (f[6], f[7], f[8])
        c = (f[9], f[10], f[11])
        for p in (a, b, c):
            for k in range(3):
                lo[k] = min(lo[k], p[k])
                hi[k] = max(hi[k], p[k])
        vol += (
            a[0] * (b[1] * c[2] - c[1] * b[2])
            - b[0] * (a[1] * c[2] - c[1] * a[2])
            + c[0] * (a[1] * b[2] - b[1] * a[2])
        ) / 6.0
    return abs(vol), [round(hi[k] - lo[k], 1) for k in range(3)]


def iter_parts(zip_path, keys):
    with zipfile.ZipFile(zip_path) as z:
        for name in sorted(z.namelist()):
            base = os.path.basename(name)
            if not base.lower().endswith(".stl"):
                continue
            if keys and not any(k.lower() in base.lower() for k in keys):
                continue
            res = stl_volume(z.read(name))
            if res is None:
                print(f"# 跳过（非二进制 STL 或损坏）: {name}", file=sys.stderr)
                continue
            yield base, res[0], res[1], res[0] / 1000.0


def main():
    ap = argparse.ArgumentParser(description="估算 LumenPnP STL 包的打印耗材量")
    ap.add_argument("zipfile", help="官方 LumenPnP-STLs-vX.Y.Z.zip 路径")
    ap.add_argument("keys", nargs="*", help="只算文件名含这些关键字的件（可选）")
    ap.add_argument("--tsv", action="store_true", help="输出制表符分隔（便于重定向/diff）")
    ap.add_argument("--density", type=float, default=DENSITY, help=f"密度 g/cm3（默认 {DENSITY} PLA）")
    ap.add_argument("--ratio", type=float, default=EXTRUSION_RATIO, help=f"挤出比（默认 {EXTRUSION_RATIO}）")
    args = ap.parse_args()

    rows = []
    for base, vol_mm3, dims, vol_cm3 in iter_parts(args.zipfile, args.keys):
        grams = vol_cm3 * args.ratio * args.density
        rows.append((base, vol_cm3, dims, grams))

    sep = "\t" if args.tsv else "  "
    if args.tsv:
        print(sep.join(["file", "solid_cm3", "dims_mm", "grams"]))
    else:
        print(f"{'文件':<34}{'实体cm3':>9}{'尺寸mm':>22}{'估计g':>8}")
    for base, vol_cm3, dims, grams in rows:
        if args.tsv:
            print(sep.join([base, f"{vol_cm3:.1f}", "x".join(str(d) for d in dims), f"{grams:.1f}"]))
        else:
            print(f"{base:<34}{vol_cm3:>9.1f}{str(dims):>22}{grams:>8.1f}")

    total = sum(r[3] for r in rows)
    if args.tsv:
        print(sep.join([f"TOTAL ({len(rows)} 件)", "", "", f"{total:.1f}"]))
    else:
        print(f"\n合计 {len(rows)} 件 ≈ {total:.1f} g；按 ¥60/kg 计 ≈ ¥{total * 0.06:.1f}")


if __name__ == "__main__":
    main()
