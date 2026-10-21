# RFID 读取能力评估（2026-10-21）

`RFID读取评估_2026-10-21.7z` —— 华勤 7H3AA-PALLET（工位「自动扫描称重」，线体 7H3PK1）
的 RFID 读取能力评估数据包。

内容：
- 机台日志摘录：`EpcLog`（逐条 EPC）、`Main` 的 RFID/SSCC 行、`Plc` 握手、`scada` 报文、RFID 程序日志
- 标签实测：EPC / TID / 芯片型号（Impinj Monza R6-P）/ 天线 / RSSI
- 统计：近 30 天 EPC 行数与停摆点、今日逐小时 RfidFlow 与 RFID 开启率、机型×箱数×BoxQty
- 自研读码器客户端（LLRP）源码与逐条读取流水
- 现场测量协议 + 记录表（朝向 / 距离 / 6dB-9dB / 不同厂商模组）
- 模组选型清单、会话与任务摘要

要点：本系统的 `EpcLog` 不记录逐台标签（99.6% 是两个常驻标签的重复读取），
应用层也只记 `RfidFlow start / RFID开启状态 / RfidFlow end`，因此“一箱 6 个标签读到几个”
必须用外部探针实测 —— 包内有现成工具与协议。
