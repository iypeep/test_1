# RFID 监测（rfidmon）—— 自己占住读码器、远程看标签

## 为什么要它

- Impinj 读码器**同时只允许一个 LLRP 客户端**。现场有人打开 MultiReader 调试，HQ Package System 的
  `RfidFlow` 就会报 `Rfid event error…must connect to the reader`，`EpcLog` 立刻停止写入
  （2026-10-21 16:16 实测：MultiReader 启动 16 秒后 EpcLog 停摆）。
- 而 HQ Package System 自己**不打逐台标签点**：`EpcLog` 里 99.6% 是两台设备/治具标签
  （`A037001000071`、`B019001001229`）的重复读取，真正的整机标签极少；`Main` 日志只有
  `RfidFlow start / RFID开启状态：True|False / RfidFlow end`，没有"读到几个、是否匹配"。
  所以"一箱 6 个标签到底读到几个"用现成日志答不出来。

rfidmon 就是补这个缺口的：一个我们自己的 LLRP 客户端，**占住会话**、逐条记录标签、
远程可开始/暂停。

## 结构

```
tools\rfidmon.cs            源（C# 5 / .NET 4.0，引用机台自带的 Impinj Octane SDK）
机台 C:\Users\<u>\AppData\Local\OMPRemote\rfid\
  rfidmon.cs               源码
  rfidmon.exe              现场用 csc 编译（机台有 .NET Framework，无需装任何东西）
  Impinj.OctaneSdk.dll …   从 D:\Ben Read RFID 拷来引用
  rfidmon.log              本地日志
公盘 <hub>\machines\<M>\rfid\
  control.json             办公机写：{"mode":"record"|"pause"|"stop"}
  status.json              机台写：每轮覆盖（state/connected/tags_total/distinct/last_error）
  live.txt                 最近 40 条，纯文本，方便 cat
  records-YYYYMMDD.jsonl   逐条：{"t":..,"epc":"<hex>","ascii":"A037001000071","ant":4,"rssi":-51.5,"seen":1}
```

## 编译（机台上，一条命令）

```powershell
cd $env:LOCALAPPDATA\OMPRemote\rfid
C:\Windows\Microsoft.NET\Framework64\v4.0.30319\csc.exe /nologo /target:exe /platform:anycpu /optimize+ `
  /main:RfidMon /out:rfidmon.exe /r:Impinj.OctaneSdk.dll /r:LLRP.dll /r:LLRP.Impinj.dll rfidmon.cs
```

## 远程操作（办公机）

```bash
python ctl\ompremote.py rfid <M> start     # 起监测（自动从 SettingPrm.xml 读读码器 IP，mode=record）
python ctl\ompremote.py rfid <M> status    # 连接状态 / 累计标签 / 去重数 / 心跳
python ctl\ompremote.py rfid <M> tail -n 20
python ctl\ompremote.py rfid <M> records -n 30
python ctl\ompremote.py rfid <M> pause     # 主动释放读码器（把会话还给产线软件）
python ctl\ompremote.py rfid <M> record    # 重新占住
python ctl\ompremote.py rfid <M> stop      # 退出监测进程
```

## 行为约定（重要）

| 模式 | 读码器会话 | 产线软件 |
|---|---|---|
| `record` | 我们占着 | HQ Package System 的 RfidFlow 会报错，EpcLog 停写 |
| `pause` | 释放 | 产线软件下次 RfidFlow 时可重新连上（EpcLog 恢复） |
| `stop` | 释放并退出 | 同上，且监测进程结束 |

- 若会话被别的客户端抢走，`record` 模式下会每 ~2.5 秒重试并夺回；`status.json.state` 会显示
  `connecting` / `error` 与 `last_error`。
- **永远不要**用 `kill` 去动 `HQ Package System`（产线主程序）；这里只操作 `rfidmon` 与
  `MultiReader`。
- 每次占用都写 `records-*.jsonl`，`live.txt` 只是尾巴；分析用 jsonl。

## 2026-10-21 首次实测

- 监测启动 11 秒读到 263 条（≈24 条/秒），去重后 **2 个标签**：
  `A037001000071`（天线 1/3/4，-43 ~ -58 dBm）、`B019001001229`（天线 1/4，-60 ~ -68.5 dBm）。
  与 `EpcLog` 里占 99.6% 的两个值一致 ⇒ 它们是常驻在读码范围内的设备/治具标签。
- `pause` 后端口无持有者；`record` 后立刻夺回（pid 换新，`connected=True`）。
