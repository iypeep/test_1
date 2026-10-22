# -*- coding: utf-8 -*-
"""把 10_实测框架/ 里填好的 CSV 变成实测图与汇总（与 _sim 的预测值对照）

用法：
    python apply_measured.py                      # 读 ../10_实测框架/*.csv，输出 figs/fig7m|fig8m|fig11m + 实测汇总.md
    python apply_measured.py --tpl DIR --out DIR  # 空跑/校验用：换输入输出目录，不碰仓库
    python apply_measured.py --check              # 只做数据体检与判定，不出图

空单元一律跳过（只画已填的档位），所以可以边测边跑。
判定口径（与 10_实测框架/README.md §3 一致）：读全 ≥6.0；可用 ≥5.4 且无箱 <5；
临界 4.8–5.4；不可用 <4.8。
"""
import os, csv, sys, argparse

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib import font_manager as fm

_HERE = os.path.dirname(os.path.abspath(__file__))
REP = os.path.dirname(_HERE)
ROOT = os.path.dirname(REP)

INK, GRAY, BAR, ACCENT, ACCENT_L = "#1A1A1A", "#8C8C8C", "#C9C9C9", "#3E5DA8", "#5C7ED4"
fm.fontManager.addfont(r"C:\Windows\Fonts\msyh.ttc")
plt.rcParams["font.family"] = "Microsoft YaHei"
plt.rcParams["axes.unicode_minus"] = False

VERDICT = ((6.0, "读全"), (5.4, "可用"), (4.8, "临界"), (-1, "不可用"))


def verdict(v):
    if v is None:
        return "未填"
    for lo, name in VERDICT:
        if v >= lo:
            return name
    return "不可用"


def load(tpl, name):
    p = os.path.join(tpl, name)
    if not os.path.exists(p):
        return []
    return list(csv.DictReader(open(p, encoding="utf-8-sig")))


def num(row, *keys):
    """取第一个能转成数字的列，取不到返回 None"""
    for k in keys:
        v = (row.get(k) or "").strip()
        if not v:
            continue
        try:
            return float(v.replace("，", "").replace(",", ""))
        except ValueError:
            pass
    return None


def style(ax, ylab):
    for s in ("top", "right"):
        ax.spines[s].set_visible(False)
    ax.grid(axis="y", color="#ECECEC", lw=0.8)
    ax.set_axisbelow(True)
    ax.tick_params(colors=INK, labelsize=9, length=0)
    ax.set_ylabel(ylab, fontsize=9.5, color=INK)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--tpl", default=os.path.join(ROOT, "10_实测框架"), help="实测 CSV 目录")
    ap.add_argument("--out", default=os.path.join(REP, "figs"), help="图输出目录")
    ap.add_argument("--check", action="store_true", help="只体检不画图")
    ap.add_argument("--summary", default=os.path.join(REP, "实测汇总.md"), help="汇总 md 输出路径")
    a = ap.parse_args()
    tpl, figdir = a.tpl, a.out
    os.makedirs(figdir, exist_ok=True)

    report = ["# 实测汇总（由 apply_measured.py 生成）", ""]
    if a.check:
        report.append("> `--check` 模式：只体检，不写图。")
        report.append("")

    def filled(name, key="读全数_of_6", key2="读全数/6"):
        return [r for r in load(tpl, name) if num(r, key, key2) is not None]

    # ---------------------------------------------------------------- 体检
    checks = []
    a_rows = load(tpl, "A_姿态.csv")
    b_rows = load(tpl, "B_距离_9dBi.csv")
    c_rows = load(tpl, "C_厂家x增益.csv")
    e_rows = load(tpl, "E_箱型.csv")
    for nm, rows in (("A_姿态", a_rows), ("B_距离_9dBi", b_rows), ("C_厂家x增益", c_rows), ("E_箱型", e_rows)):
        done = [r for r in rows if num(r, "读全数_of_6", "读全数/6") is not None]
        miss = [r for r in done if not (r.get("读码器厂家型号") or r.get("读码器型号") or r.get("型号") or r.get("读码器厂家"))]
        checks.append((nm, len(rows), len(done), len(miss)))
    report += ["## 0. 数据体检", "", "| 表 | 行数 | 已填读全数 | 缺硬件标识 |", "|---|---|---|---|"]
    for nm, n, d, m in checks:
        report.append(f"| {nm} | {n} | {d} | {m} |")
    report.append("")

    if not a.check:
        # ------------------------------------------------------------ B 组：距离曲线
        rows = filled("B_距离_9dBi.csv")
        if rows:
            fig, ax = plt.subplots(figsize=(7.2, 3.4), dpi=220)
            colors = {"下": ACCENT, "上": ACCENT_L, "正面侧": "#8C8C8C", "背面侧": "#C0C0C0"}
            for pos in ["下", "上", "正面侧", "背面侧"]:
                pts = sorted([(num(r, "距离_cm"), num(r, "读全数_of_6", "读全数/6"))
                              for r in rows if r.get("读码器位置") == pos and num(r, "距离_cm") is not None])
                if pts:
                    ax.plot([p[0] for p in pts], [p[1] for p in pts], "-o", ms=5, lw=1.8,
                            color=colors.get(pos, GRAY), label=f"读码器在{pos}")
            ax.axhline(5.4, color="#B0B0B0", lw=0.9, ls=(0, (4, 3)))
            ax.set_ylim(0, 6.4)
            ax.set_xlabel("读码器到箱面距离（cm）", fontsize=9.5, color=INK)
            style(ax, "每箱读到的整机标签数（/6）")
            ax.legend(frameon=False, fontsize=8.5, ncol=2, loc="lower left")
            fig.tight_layout(pad=0.3)
            fig.savefig(os.path.join(figdir, "fig7m_distance_measured.png"), facecolor="white")
            plt.close(fig)
            report += ["## R3 距离（实测）", "", "| 位置 | 距离 cm | 读全 /6 | 判定 |", "|---|---|---|---|"]
            for r in sorted(rows, key=lambda x: (x.get("读码器位置", ""), num(x, "距离_cm") or 0)):
                v = num(r, "读全数_of_6", "读全数/6")
                report.append(f"| {r.get('读码器位置','')} | {r.get('距离_cm','')} | {v:.2f} | {verdict(v)} |")
            report.append("")
        else:
            report += ["## R3 距离（实测）", "", "未填写。", ""]

        # ------------------------------------------------------------ C 组：厂家 × 增益
        rows = filled("C_厂家x增益.csv")
        if rows:
            at30 = [r for r in rows if str(num(r, "距离_cm") or -1) in ("30.0", "30")]
            use = at30 or rows
            fig, ax = plt.subplots(figsize=(6.4, 3.1), dpi=220)
            labels, vals = [], []
            for r in use:
                labels.append(f"{r.get('读码器厂家','')}\n{r.get('天线增益_dBi','')} dBi")
                vals.append(num(r, "读全数_of_6", "读全数/6"))
            ax.bar(range(len(vals)), vals, color=[ACCENT, ACCENT_L, "#8C8C8C", "#C9C9C9"][:len(vals)], width=0.62)
            for i, v in enumerate(vals):
                ax.text(i, v + 0.12, f"{v:.2f}", ha="center", fontsize=9.5, color=INK, fontweight="bold")
            ax.set_xticks(range(len(vals)))
            ax.set_xticklabels(labels, fontsize=9, color=INK)
            ax.set_ylim(0, 6.6)
            style(ax, "每箱读全数（/6）")
            fig.tight_layout(pad=0.3)
            fig.savefig(os.path.join(figdir, "fig8m_vendor_measured.png"), facecolor="white")
            plt.close(fig)
            report += ["## R4 + R5 厂家 × 增益（实测）", "", "| 厂家 | 增益 | 距离 cm | 读全 /6 | 判定 |", "|---|---|---|---|---|"]
            for r in rows:
                v = num(r, "读全数_of_6", "读全数/6")
                report.append(f"| {r.get('读码器厂家','')} | {r.get('天线增益_dBi','')} | {r.get('距离_cm','')} | "
                              f"{v:.2f} | {verdict(v)} |")
            report.append("")
        else:
            report += ["## R4 + R5（实测）", "", "未填写。", ""]

        # ------------------------------------------------------------ E 组：箱型
        rows = filled("E_箱型.csv")
        if rows:
            fig, ax = plt.subplots(figsize=(7.0, 3.1), dpi=220)
            vals = [num(r, "读全数_of_6", "读全数/6") for r in rows]
            cols = [ACCENT if v >= 5.4 else ("#7F97C4" if v >= 2.5 else BAR) for v in vals]
            ax.bar(range(len(vals)), vals, color=cols, width=0.6)
            for i, v in enumerate(vals):
                ax.text(i, v + 0.1, f"{v:.2f}", ha="center", fontsize=9.5, color=INK, fontweight="bold")
            ax.set_xticks(range(len(vals)))
            ax.set_xticklabels([r.get("代号", "") for r in rows], fontsize=9, color=INK)
            ax.set_ylim(0, 6.6)
            ax.axhline(5.4, color="#B0B0B0", lw=0.9, ls=(0, (4, 3)))
            style(ax, "每箱读全数（/6）")
            fig.tight_layout(pad=0.3)
            fig.savefig(os.path.join(figdir, "fig11m_variants_measured.png"), facecolor="white")
            plt.close(fig)
            report += ["## R6 箱型（实测）", "", "| 代号 | 描述 | 读全 /6 | 判定 | 读取率 |", "|---|---|---|---|---|"]
            for r in rows:
                v = num(r, "读全数_of_6", "读全数/6")
                report.append(f"| {r.get('代号','')} | {r.get('箱型描述','')} | {v:.2f} | {verdict(v)} | "
                              f"{r.get('读取率_tags_s','')} |")
            report.append("")
        else:
            report += ["## R6 箱型（实测）", "", "未填写。", ""]

    # ---------------------------------------------------------------- A 组：姿态
    rows = filled("A_姿态.csv")
    if rows:
        report += ["## R1 姿态（实测）", "", "| 编号 | 姿态 | 读全 /6 | 判定 |", "|---|---|---|---|"]
        for r in rows:
            v = num(r, "读全数_of_6", "读全数/6")
            report.append(f"| {r.get('编号','')} | {r.get('箱体姿态','')} | {v:.2f} | {verdict(v)} |")
        report.append("")
    else:
        report += ["## R1 姿态（实测）", "", "未填写。", ""]

    out = a.summary
    os.makedirs(os.path.dirname(out), exist_ok=True)
    open(out, "w", encoding="utf-8").write("\n".join(report))
    print("wrote", out)
    print("\n".join(report[:14]))


if __name__ == "__main__":
    main()
