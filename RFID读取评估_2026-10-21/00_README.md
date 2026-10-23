# RFID 读取能力评估 · 数据包（2026-10-21）

> 站点：`7H3AA-PALLET`（工位「自动扫描称重」，线体 `7H3PK1`）
> 内容：机台日志摘录、标签实测、机型/箱数统计、自研读码器监测流水、现场测量协议与记录表、模组选型清单。
> 全部数字可复核：日志原文在 `02_日志`，统计脚本在 `07_方法`。

## 2026-10-23 改版：PPT / 3D / 手册都在哪

| 东西 | 位置 |
|---|---|
| **最新汇报 PPT / PDF（11 页）** | `RFID读取能力评估-改动版_完善_20261022.pptx` / `.pdf`（本目录根） |
| 整页重建脚本（从 `_pure` 底稿生成全部 11 页） | `09_报告/_build/improve_deck_20261022.py` |
| 3D **可编辑场景**（.blend，贴图已 pack） | `09_报告/_build/_3d_out2/*.blend` —— 19 个：A1–A6、D_up/D_down/D_side、THREE_readers、MOD_R700/R420/FX9600/M6E、ANT_55/ANT_6/ANT_8/ANT_9、R3_scan |
| 3D 建模脚本（Blender 4.3） | `09_报告/_build/rfid3d_fix.py`（姿态/三天线）、`rfid3d_modules.py`（读码器）、`rfid3d_antennas.py`（板状天线）、`rfid3d_r3.py`（剖箱+多距离） |
| 拼图 / 图表脚本 | `09_报告/_build/make_fig_relabel.py`、`make_fig4_fix.py`、`make_fig_r2_row.py`、`make_fig_antenna_row.py`、`make_fig_r3_bars.py`、`make_fig_r4_ant.py` |
| 单帧渲染 PNG | `09_报告/_build/_3d_out2/*.png`（与 .blend 同名） |
| 报告用图 | `09_报告/figs/`：新增 `fig4_3d_placements_v2`、`fig5_3d_antennas`、`fig6_3d_readers_r45`、`fig_three_readers`、`r2_modules_row`、`antenna_row`、`r3_distance_scan`、`r3_theory_vs_actual`、`r4_9_vs_6` |
| **天线/模组手册** | `09_报告/手册/`：Laird S9025P、S9028PCL/PCR 两份 datasheet（PDF）+ 网页类产品页规格摘录 + 索引（`README.md`） |

改版流程：改 `rfid3d_*.py` → `blender -b -P ...`（同时输出 PNG + .blend）→ 跑对应 `make_fig_*.py` 拼图 → 跑 `improve_deck_20261022.py` 生成 PPT → `render_ppt.py` 导 PNG 核对。

## 先看这几份

| 文件 | 看什么 |
|---|---|
| `09_报告/RFID读取能力评估_2026-10-22.md` | **V1.3（当前版）**：六项要求（R1 3D 放置 / R2 模组手册对比 / R3 距离 / R4 增益 / R5 厂家 / R6 箱型）+ 新增 §2.1 **现网实测基线** |
| `09_报告/RFID读取能力评估_2026-10-22.pptx` / `.pdf` | **9 页汇报版（以「改动版」为基线）**：P1 封面 · P2 六种放置方式(A1–A6) · **P3 读取方向测试**（3 天线布置 + 中箱实测表 + 表头↔P2 姿态映射）· P4 机型口径 · P5 R2 模组选型 · P6 R3 距离无相关 · P7 Back Up · P8 R4+R5 · P9 R6 箱型；含讲稿备注 |
| **`RFID读取能力评估-改动版_完善_20261022.pptx` + 包装机型页** | **当前汇报版**：11 页（`改动版_完善`）＋ 插在 R6 页之后的 **「包装机型口径：KKE / N-KKE × 背壳」**页 = 12 页；
| | 仓库产物：`09_报告/RFID读取能力评估_2026-10-23.pptx` / `.pdf`（12 页，含讲稿备注）；生成脚本 `09_报告/_build/make_slide10_pkg.py`（可重复执行） |
| `10_实测框架/` | **明天现场填的五张 CSV** + 填写纪律 + 判定口径（`README.md`） |
| `09_报告/RFID读取能力评估_2026-10-21.md` | 上一版（仅 R1–R5 旧口径）：现状证据、日志盲区、停摆复发 |
| `01_证据与结论.md` | 结论、证据链、标签 EPC/TID 对照、日志盲区 |
| `06_会话与任务摘要.md` | 今天做了什么、哪些已验证/未验证、回家怎么继续 |
| `11_进度与待办_20261022.md` | **当前进度 + 中午待办 + 机型号口径（客户代码/尺寸）决定** |
| `04_现场测量/现场测量-协议.md` | 现场要补的四类数据（朝向/距离/6dB-9dB/厂商） |

## 目录

```
00_README.md                    本文件
01_证据与结论.md                 结论 + 证据 + 数据文件说明
02_日志/
  EpcLog_20261021.log           当天完整 EPC 日志（104,785 行）
  Main_RFID_lines_today.txt     Main 日志中 RFID/SSCC/读码 相关行（前 3000 条）
  rfidmon_records-20261021.jsonl 自研客户端逐条读取（EPC/天线/RSSI）
  FileAppender_rfid_app.log     RFID 程序日志（最后写入 2026-10-07）
  scada_today.log               上报 MES 报文
  Plc_20261021.log              PLC 握手（M80–M83 / M120）
  SQL_20261021.log              数据库查询样例
03_数据/
  epc_per_day_30d.csv           近 30 天每日首末/行数/字节（趋势图）
  rfid_hourly_today.csv         今日逐小时 RfidFlow 与 RFID 开启率
  models_today.csv              机型×箱数×BoxQty×每箱 6 个 DSN 样例
  rfidmon_status.json           监测客户端状态快照
  rfidmon_live.txt              最近 40 条读取
  prod_readout_20260922_20261022.csv  逐日：箱数 / readStatus 占比 / 窗口内读到标签的箱占比（31 天汇总）
  07_方法/包装机型口径.md            KKE/N-KKE × 背壳四象限、标签位置、厂家对比的控制变量（2026-10-23）
  model_baseline_20260922_20261022.csv 逐机型基线：HQ代码×客户代码×尺寸×背壳 → 箱数/readStatus/0标签占比/读全6占比/均标签
  （09_报告/_sim/G_包装机型_模拟.csv 包装机型四象限预测：标签位置/下置/侧向/大件，2026-10-23）
04_现场测量/
  现场测量-协议.md               面定义、姿态矩阵、距离矩阵、取数命令、拍照清单
  现场测量记录表.csv             每档一行，现场填
05_RFID模组选型.md               形态分类 + 主流厂商/型号 + 选型要问的 8 个问题
06_会话与任务摘要.md              时间线、交付物、已验证/未验证
07_方法/
  prod/                         产线逐箱取值链路：extract-rfid-boxes2.ps1（逐箱记录）/
                                extract-epc-tags.ps1（逐次读取）/ probe-rfid-history.ps1 /
                                probe-rfid-enable.ps1 + README（口径、坑、不确定性）
  rfidmon.cs                    自研 LLRP 客户端源码（机台本地 csc 编译）
  rfid-health.ps1               RFID 健康判定（会话占用/日志新鲜度/错误计数）
  probe-*.ps1 / extract-*.ps1   取数脚本（日志盘点、机型统计、报文模板）
  OMPRemote_README.md           机台远程通道（body + CLI）说明
  架构与用法.md                  通道协议与故障排查
  机型对照.csv                   HQ代码 × 客户代码 × 尺寸/品类 对照（机型口径唯一依据）
08_对话记录/
  session_20261021.jsonl        本次会话原始记录（完整可检索）
09_报告/                        V1.3 报告与汇报版 PPT（2026-10-22 生成）
  RFID读取能力评估_2026-10-22.md/.pptx/.pdf   六项要求版（当前）
  RFID读取能力评估_2026-10-21.md/.pptx/.pdf   上一版（R1–R5 旧口径）
  figs/                         fig1-2-3 趋势/命中/箱面；fig4-5-6 与 fig10 3D 与手册图；
                                fig7 距离曲线 / fig8 增益厂家 / fig11 箱型 / fig12 过板 6/6
                                fig13 现网逐箱读取分布（实测：95% 一箱 0 个）
  figs/hw/                      厂家手册/产品页原图（M-703 / Kathrein / Silion）
  手册/                          P6 天线依据：Laird S9025P / S9028PCL datasheet（PDF）+
                                 网页类产品页规格摘录 + 索引 README
  _sim/                         预测结果 CSV（A/B/C/E）+ 手册参数表 + 模型假设
  _build/                       生成脚本（rfid3d.py / make_labels.py / compose_*.py /
                                sim_model.py / make_ppt2.py / make_ppt3.py（增量：改名+追加 P9/P10）/
                                model_baseline.py（逐机型基线）/ make_fig_prod.py（fig13）/
                                make_fig_variants.py（fig11）/ apply_measured.py / render_ppt.py）
  _build/_3d_out2/               3D 单帧 PNG + 同名可编辑 .blend（19 个，贴图已打包）
  _ref/  _render/  _render2/     风格参考页 / 渲染核对 PNG
10_实测框架/                    现场要填的五张 CSV + README（填写纪律、判定口径、替换流程）
11_进度与待办_20261022.md       进度快照 + 待办 + 机型口径决定（换机先看这份）
```

## 四条必须记住的结论

1. **现网实测：一箱读到 0 个整机标签的占 95.0%**（31 天 113,667 箱，读全 6 个只有 0.14%）。
   数据来源是机台自身日志，不是探针：`Logs/<日期>/Rfid_<日期>.log` 的逐箱 `readStatus`
   × `EpcLog` 的逐次 `InPut`/`Epc2Dsn` 按箱窗口对齐（`07_方法/prod/README.md`）。
2. **日志口径更正**：`Main` 只打 `RfidFlow start / RFID开启状态 / RfidFlow end`、不打印数量，
   但 `Rfid_<日期>.log` 有逐箱结果（326 天留存）、`EpcLog` 有逐次读取（99.6% 是常驻标签，但真标签可辨）。
   "读到几个"**可以回溯**，只是要跨两份日志对齐。
3. **LLRP 单客户端**：任何人（MultiReader / 我们 / HQ Package System）占住 5084，其余全部连不上。
   10-21 16:16 的停摆就是这样发生的，近 30 天另有 4 次同类停摆。
4. **6 台/箱**有直接证据（`BoxQty=6` + `DSN1..DSN6`），与 RFID 是否读到无关 —— 两者长期被混为一谈。
   现场实验（`10_实测框架`）要回答的是"哪种布置能读全"，不是"现在读到几个"。

## 术语澄清

`9 dB / 6 dB` 更可能是**天线增益（dBi）**，读码器本身通常是 30 dBm 输出功率。
报告里请分开表述，否则结论会归因错。
