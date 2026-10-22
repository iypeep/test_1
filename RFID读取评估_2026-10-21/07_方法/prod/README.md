# 产线逐箱 RFID 取值链路（`Logs\<日期>\Rfid_<日期>.log` × `EpcLog`）

> 2026-10-22 新增。目的：把「一箱 6 个标签到底读到几个」从「只能靠外部探针」变成
> **可从机台自身日志回溯**，并用 31 天数据给出实测基线。

## 1. 为什么之前判成"日志答不出来"

之前只看了 `Main_<日期>.log`（`RfidFlow start / RFID开启状态 / RfidFlow end`）与 `EpcLog`，
没看 **`Logs\<日期>\Rfid_<日期>.log`**（程序自己的 RFID 日志）。这份日志里：

| 行样例 | 含义 |
|---|---|
| `GN45RB02642701CM` | 扫到的整机条码（DSN） |
| `00069758522134393881` | 扫到的箱码（SSCC，20 位） |
| `读取到标签：GN45RB02642700RH` | RFID 读到一枚标签，值是整机 DSN（96-bit 标签的 EPC 解码） |
| `readStatus=True / False` | **逐箱 RFID 结果**（每箱一条） |
| `ReaderStart=OK/NG`、`ReaderStop=OK/NG` | 每次读取前后的读码器启停 |

`EpcLog\<日期>\<日期>.log` 则是逐次读取的原始记录：`<时间> InPut:<EPC hex>` 紧跟
`<时间> Epc2Dsn:<DSN>`（同毫秒配对），可把「读到的是哪台整机」还原出来。

## 2. 取数命令（办公机，公盘通道）

```bash
cd E:\Desktop\OMPRemote
py -3.12 ctl\ompremote.py run 7H3AA-PALLET -f tools\extract-rfid-boxes2.ps1 --timeout 900   # 逐箱记录 → TSV
py -3.12 ctl\ompremote.py run 7H3AA-PALLET -f tools\extract-epc-tags.ps1   --timeout 900      # 逐次读取 → TSV（已剔除常驻标签）
py -3.12 ctl\ompremote.py fetch 7H3AA-PALLET -p "C:\Users\md3\AppData\Local\OMPRemote\rfid\*.tsv" --dest .\pulled\rfid
```

两个脚本都在 `07_方法/prod/`（与机台 `tools/` 同一份），只读、不改机台任何配置。

## 3. 字段与解析约定

`rfidboxes2_*.tsv`（一行一箱）

| 列 | 说明 |
|---|---|
| `t_first` / `t_status` | 该箱第一条条码行 / `readStatus` 行（箱处理窗口，通常 ≈3 s） |
| `dsn_n` / `dsn_ids` | 本轮日志里出现的条码数（≠箱内 6 台，只有扫到的那些）/ 去重后 |
| `sscc` | 箱码 |
| `tag_lines` / `tag_distinct` / `tag_ids` | `读取到标签` 行数 / 去重标签数 / 标签值 |
| `status` | `readStatus=True|False` |
| `rstart` / `rstop` | `ReaderStart=…` / `ReaderStop=OK|NG` |

`epctags_*.tsv`：`day, t, epc(hex 或 DSN), ascii, kind(InPut|Epc2Dsn), antenna`。
**常驻标签剔除表**（按 EPC hex 精确匹配）：`A037001000071`、`B019001001229`、`A037001000150`。

**坑（都踩过）**

1. 时间戳含逗号毫秒（`01:24:46,480`）→ CSV 逗号分隔会被劈开；一律用 **TSV**。
2. 日志有 `[Head]` 分段行，且文件跨天；不要假设一行一箱。
3. `Epc2Dsn` 行的 `epc` 列本身就是 DSN（不是 hex），别当 EPC 解码。
4. 96-bit 整机标签 = 24 位 hex；14 字节（28 位 hex）的是设备/治具标签家族。
5. `readStatus` 与 `Main` 里的 `RFID开启状态` **不是同一件事**，且方向相反（见下）。

## 4. 口径与不确定性（写报告时必须带上）

| 项 | 结论 | 证据 |
|---|---|---|
| 逐箱结果是否存在 | **存在**：`readStatus`，2025-07-14 起共 326 天 | `probe-rfid-history.ps1` |
| `readStatus` 语义 | **未证实**：不排除是"取数成功/条码就绪"而非"读到标签"；只能确认它与 96-bit 标签读取正相关 | P(窗口内有标签\|True)=14.5% vs P(\|False)=4.0% |
| 与 `Main` 的关系 | 互补：`readStatus=True` ↔ `RFID开启状态=False`（同日计数 195 / 194） | 逐行对照 |
| 逐箱读到几个 | 以 `EpcLog` 96-bit 读取为准，窗口内去重计数 | 见 §5 |
| 归因边界 | 只按时间窗归属，箱内 6 台的条码不会全部出现在窗口里，无法逐台对号 | `dsn_n` 多为 1–2 |

## 5. 31 天结果（2026-09-22 → 2026-10-22，`03_数据/prod_readout_20260922_20261022.csv`）

| 指标 | 值 |
|---|---|
| 箱数（含 `readStatus` 记录） | **113,667** |
| `readStatus=True` | 9,782（**8.6%**；逐日 6.9–10.5%） |
| 窗口内读到 ≥1 个整机标签 | 5,605 箱（**4.9%**；放宽到 ±10 s 也只有 9.0%） |
| 窗口内读到 6 个 | 158 箱（0.14%；±10 s 口径 1.09%，含相邻箱混入，属上限） |
| 一箱 0 个 | 108,017 箱（**95.0%**） |
| 常驻标签占 `EpcLog` 行数 | 99.6%（与 10-21 一致） |

正常生产日（10-16 之后）整机标签读取 **250–550 次/天**，而当天过箱 3,000–5,200 箱。

## 6. 复现顺序

1. 跑 §2 两个脚本拿 TSV（31 天约 70 s + 60 s，公盘回传 ~15 s）。
2. 用 `09_报告/_build/make_fig_prod.py` 出 `figs/fig13_prod_readout.png`
   （输入是汇总 CSV；原始 TSV 不再入库，按脚本可再生）。
3. 全套数字与报告 §2.1 / §11 对齐；改口径先改本节。
