# RFID 读取能力评估（7H3AA-PALLET · 2026-10-21/22）

华勤 7H3AA-PALLET（工位「自动扫描称重」，线体 7H3PK1）卡通箱整机标签的读取能力评估：
现场取证、3D 示意、手册参数对比、距离/箱型读取结果与实测框架。

**一句话结论**：用机台自己的日志回溯 31 天 113,667 箱，**95.0% 的箱一个整机标签都没读到**、
真正读全 6 个的只有 0.14% —— 而且 RFID 失败**不阻断放行**，所以产线上完全看不见；第一风险仍是
LLRP 会话可用性（近 30 天 5 次停摆），其次是**标签离天线的距离**与**背壳材质**（预测侧：9 dBi + 下置 +
塑料背壳读全窗口只有 **≤10 cm**，金属背壳加功率/调距离都救不回来）。

## 数据性质（先看这一条）

| 范围 | 性质 |
|---|---|
| R1 放置方式、R2 模组参数 | ✅ 确定：前者按现场结构约定 + 3D 示意；后者逐条抄自厂家手册/产品页 |
| **现网逐箱读取基线（95% 读 0）** | ✅ **实测**：`Rfid_<日期>.log` × `EpcLog` 按箱窗口对齐，31 天 113,667 箱（报告 §2.1、`figs/fig13_prod_readout.png`） |
| R3 距离、R4 增益、R5 厂家、R6 箱型 | 🟡 **预测**：手册参数 + 参数化模型，非实测 |

预测值全部存在 `09_报告/_sim/*.csv`，模型常数在 `09_报告/_build/sim_model.py` 的 `MODEL` 字典里；
现场按 `10_实测框架/` 填表后 `python apply_measured.py` 即可替换成实测。

## 六项要求 → 结论

| # | 要求 | 结论 |
|---|---|---|
| R1 | 六个面分别作底面（读码器固定在下） | 只有底面朝下（产线姿态）接近读全 **5.56/6**；侧放/侧躺掉到 **3.3–4.9** —— 姿态影响的本质是标签离天线从 25 cm 变成 30/40 cm |
| R2 | 模组选型：目标是**一次过板读全 6 台** | 判据三条（覆盖/极化/读取率≥24 tags/s）+ 7 个型号手册参数与「过板 6/6 适配」；换算结果：0.5 s 窗口 20 cm 处 A 厂+9 dBi **99.0%**、A 厂+6 dBi 79.0%、B 厂+9 dBi 82.7%、B 厂+6 dBi **18.8%** |
| R3 | 距离（9 dBi）对读取的影响 | 读全窗口 **≤10 cm**；下置 20/30/50 cm = 5.89/4.56/1.89；正面侧 30 cm 只剩 1.22 |
| R4 | 9 dBi vs 6 dBi | 30 cm：**5.22 vs 2.89**（近距 ≤10 cm 都 6/6，看不出差别） |
| R5 | 不同厂家（×2） | A 厂 9 dBi **5.22** vs B 厂 9 dBi **3.44**，等效差约 2 dB |
| R6 | 六种箱型（按机型口径：代号＝HQ代码-背壳） | 7907-P（AX7907 Prosecco/Marsala 6″ 塑料）6.00 / 8252-P（AX8252 Amaro/Julep 7″ 塑料）6.00 / 7907-M 2.44 / 8252-M 0.78 / 7771-M（AX7771 Roselite 8″ 平板）4.44 / 7513-M（AX7513 Turquoise 11″ 平板）2.33 —— **金属背壳是分水岭** |

> 横切结论（实测，2026-10-22 补）：**现网一箱读到 0 个整机标签的占 95.0%**，读全 6 个 0.14%；
> 报告 §2.1、`figs/fig13_prod_readout.png`、`03_数据/prod_readout_20260922_20261022.csv`，
> 取数链路见 `07_方法/prod/README.md`。

## 目录

| 路径 | 内容 |
|---|---|
| `09_报告/RFID读取能力评估_2026-10-22.md` | **当前版报告**（六项要求） |
| `09_报告/RFID读取能力评估_2026-10-22.pptx` / `.pdf` | **9 页汇报版（以「改动版」为基线）**：P1 封面 · P2 六种放置方式(A1–A6) · **P3 读取方向测试**（3 天线布置 + 中箱实测表 + 表头↔P2 姿态映射）· P4 机型口径 · P5 R2 模组选型 · P6 R3 距离无相关 · P7 Back Up · P8 R4+R5 · P9 R6 箱型；含讲稿备注 |
| `09_报告/RFID读取能力评估_2026-10-21.*` | 上一版（旧口径 R1–R5）：现状证据、日志盲区、停摆复盘 |
| `09_报告/figs/` | fig1 30 天趋势 / fig2 天线命中 / fig3 箱面 / fig4 六种放置 3D / fig5 距离几何 3D / fig6 读码器阵容 3D / fig7 距离曲线 / fig8 增益·厂家 / fig9 姿态 / fig10 手册产品图 / fig11 六种箱型 / fig12 一次过板读全 6 台的概率 / fig13 现网逐箱读取分布 / **fig_reader_layout 读取方式示意（箱体正立 · 顶部+左侧天线）** |
| `09_报告/figs/hw/` | 厂家手册与产品页原图（RodinBell M-703 / Kathrein RRU 4000 / Silion SQM5100） |
| `09_报告/_sim/` | 预测结果 CSV（A 姿态 / B 距离 / C 厂家增益 / E 箱型）+ `模型假设.json` + `D_手册参数与相对读距.csv` |
| `09_报告/_build/` | 生成脚本：`rfid3d.py`+`make_labels.py`+`compose_3d.py`（Blender 3D）、`sim_model.py`（模型）、`make_ppt2.py`（幻灯片）、`apply_measured.py`（实测替换）、`render_ppt.py`（COM 导出 PNG 核对） |
| `10_实测框架/` | 现场填的五张 CSV + 填写纪律 + 判定口径（见其 `README.md`） |
| `11_进度与待办_20261022.md` | **进度快照（换机先看这份）**：已完成/待办、机型口径决定、复现命令 |
| `03_数据/prod_readout_*.csv` `03_数据/model_baseline_*.csv` | 现网实测基线（31 天，95% 一箱读 0）与逐机型基线 |
| `07_方法/prod/` `07_方法/机型对照.csv` | 逐箱取值脚本（`readStatus`×`EpcLog`）与 HQ代码×客户代码对照 |
| `02_日志/` `03_数据/` `04_现场测量/` `07_方法/` | 原始日志摘录、统计 CSV、现场测量协议与记录表、取数脚本与远程通道说明 |
| `07_方法/prod/` | **产线逐箱取值链路**：`extract-rfid-boxes2.ps1`（逐箱 record）/ `extract-epc-tags.ps1`（逐次读取）/ `probe-rfid-history.ps1`（326 天 readStatus 统计）+ README（口径与不确定性） |
| `03_数据/prod_readout_20260922_20261022.csv` | 逐日：箱数 / `readStatus` 占比 / 窗口内读到标签的箱占比 / 读全 6 个的箱数 |
| `00_README.md` `01_…` `05_…` `06_…` | 数据包索引、证据与结论、模组选型初稿、会话与任务摘要 |

- `12_会话要点与决策_20261023.md`：**2026-10-23 全天决策记录**（经理口径逐条落地、终态 11 页结构、分布口径、SN 真值来源、未决项）

## 复现

```bash
# 3D 图（Blender 4.3 后台渲染 13 帧，约 40 秒）
blender --background --factory-startup --python 09_报告/_build/rfid3d.py
python 09_报告/_build/compose_3d.py

# 预测结果 + 图 + 空模板
python 09_报告/_build/sim_model.py

# 幻灯片（PowerPoint COM 导出 PDF / PNG 核对）
python 09_报告/_build/make_ppt2.py

# 实测替换（填完 10_实测框架/*.csv 后）
python 09_报告/_build/apply_measured.py
```

## 换机继续工作（另一台电脑）

```bash
git clone https://github.com/iypeep/test_1.git
cd "test_1/RFID读取评估_2026-10-21"
pip install -r 09_报告/_build/requirements.txt
```

| 想做什么 | 命令 | 说明 |
|---|---|---|
| 只改内容（文字 / 数字 / 配色） | `python 09_报告/_build/sim_model.py` → `python 09_报告/_build/make_ppt2.py` | 覆盖 `_sim/`、`figs/`、`09_报告/*.pptx` |
| 重渲 3D | `blender --background --factory-startup --python 09_报告/_build/rfid3d.py` → `python 09_报告/_build/compose_3d.py` | 输出到 `_build/_3d_out/`；**仓库已带 13 帧成品，不装 Blender 也能直接拼图** |
| 导 PDF / 逐页 PNG 核对 | `python 09_报告/_build/render_ppt.py` | 走本机 PowerPoint COM（Windows + Office） |
| 实测数据替换 | 填 `10_实测框架/*.csv` → `python 09_报告/_build/apply_measured.py` | 出 `fig7m/fig8m/fig11m` + `实测汇总.md` |
| R6 结论页重排 | `py -3.12 09_报告/_build/make_r6_after_p4.py --pptx <deck>`（按标题定位、删 7771/7513 行、把 R6 移到机型口径页之后、附图） | 11 页 deck：P4 机型口径（4 行）→ P5 机型口径结论（含读取方式图） |
| SN 换真值 | `py -3.12 09_报告/_build/make_sn_real.py --pptx <deck>`（把示例 SN 换成 EpcLog 实读 DSN；`REAL_SNS` 在使用前先核对） | P3/P8/P9 的「读到 SN」列与脚注 |
| P5 结论页重做 | `py -3.12 09_报告/_build/make_p5_rework.py --pptx <deck>`（只留塑料/金属两个 readStatus=True 大数；代号表补箱数与 readStatus；删重复 bullet） | P5 整页重建，顺序：先 make_r6_after_p4 → 再 make_p5_rework |

- **所有脚本的路径都相对脚本自身**（`_HERE / REP / ROOT`），换机不需要改任何绝对路径。
- Blender 4.3 建议用绝对路径调用（如 `"C:/Program Files/Blender Foundation/Blender 4.3/blender.exe"`）；
  `--factory-startup` 可避免插件干扰。
- 只装 pip 依赖、不装 PowerPoint 也能改内容出 PPTX，只有导 PDF/PNG 那一步需要 Office。
- 仓库不含 `08_对话记录/session_20261021.jsonl`（原始会话记录，含内部环境细节），本地另存。

## 注意

- 原先此目录只有一个 `RFID读取评估_2026-10-21.7z` 包；现已展开为可浏览的文件树，**旧 7z 已移除**
  （内容已被更全的文件树取代，含新增的 `09_报告/`、`10_实测框架/`）。
- **未包含** `08_对话记录/session_20261021.jsonl`（原始会话记录，含内部环境细节），只保留方法性文档。
- 3D 为**按公开尺寸比例建的示意模型**（箱体 600×400×300 mm、读头 240×150×55、6 dBi 天线 259×259、
  9 dBi 360×360），无公开免登录的厂商 3D 文件；现场实测后改常量重渲染即可。
- 本仓库为 public：日志/数据里含内部 IP、序列号与 MES 报文样例，介意的话告知，可改为只留报告与脚本。
