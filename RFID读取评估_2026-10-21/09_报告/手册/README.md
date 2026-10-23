# 手册 / 数据表（P6 天线选型、P5 模组选型 的依据）

本目录只放**公开可引用的原厂文件**；网页类产品页没有 PDF，摘录放在
`网页面规格摘录.md`。PPT 上的尺寸/增益都以这里为准。

| 型号 | 用途（PPT 页） | 关键参数 | 文件 |
|---|---|---|---|
| Laird **S9025PL / S9025PR** | P6 第 1 张（5.5 dBi） | 5.5 dBic，132×132×18 mm，圆极化 | `Laird_S9025P_datasheet.pdf` |
| Laird **S9028PCL / S9028PCR** | P6 第 4 张（9 dBi） | 9 dBic，259×259×34 mm（10.2″×10.2″×1.32″），圆极化 | `Laird_S9028PCL_PCR_datasheet.pdf` |
| Silion **SLP1002** | P6 第 3 张（8 dBi） | 8 dBi，225×225×35 mm，N-female，ABS 面罩 + 铸铝后壳 | 见 `网页面规格摘录.md` |
| 捷创智联 **6 dBi 圆极化** | P6 第 2 张（6 dBi） | 6 dBi，128×128×20 mm，IP67，ASA + 铝 | 见 `网页面规格摘录.md` |

## 不在本目录、但同源的资料

- 模组产品图（RodinBell M-703、Kathrein RRU 4000、Silion SQM5100）：`../figs/hw/*.png`，
  来自各自产品页/手册页截图，PPT 的 P5、P10 用它们。
- 读码器手册参数（R700/R420 尺寸、口数、功率）：Laird/Impinj 公开 datasheet，
  文中引用即可，未单独存 PDF。
- **Impinj MultiReader 6.6.12**：是读码器演示**软件**，不是天线手册；本机只找到
  `MultiReader.exe` 与快捷方式，未入库。对应文档是 Impinj MultiReader User Guide
  （随 Speedway 系列发布）。

## 用法

- P6 的 4 张天线图（`../figs/antenna_row.png`）是按上表尺寸用 Blender 建的模，
  可编辑场景在 `../_build/_3d_out2/ANT_*.blend`。
- 换型号/换尺寸时：改 `../_build/rfid3d_antennas.py` 的尺寸 → 重跑 → 再跑
  `make_fig_antenna_row.py`，最后跑 `improve_deck_20261022.py` 重建 PPT。
