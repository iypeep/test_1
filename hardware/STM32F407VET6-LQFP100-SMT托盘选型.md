# STM32F407VET6（LQFP-100）SMT 托盘选型指南

**封装**：LQFP-100，本体 14.00 × 14.00 mm，引脚跨距 16.00 mm BSC，引脚间距 0.5 mm，厚 1.6 mm max。
因此所有腔位规格按 **"QFP 14×14"** 这一档去找。

---

## 先分清：SMT 语境下"托盘"是三种完全不同的东西

| 类型 | 正式名称 | 材质 / 标准 | 怎么获取 | 用在哪 |
|---|---|---|---|---|
| 来料 / 供料托盘 | **JEDEC 矩阵托盘（JEDEC Matrix Tray）**，俗称 **华夫盘 / Waffle Tray** | 改性聚砜 PSU / PES / PPO，防静电 10⁴–10⁹ Ω，可烘烤 | **买**，不打印 | 贴片机供料、来料存放、烘烤除湿 |
| 摆放 / 收纳盘 | **IC / SMD 元件托盘（SMD IC Tray）** | PLA / PETG / ESD 耗材 | **3D 打印** | 手工贴片时摆放芯片、收纳 |
| 过炉载具 | **回流焊治具 / SMT 载具（Reflow Carrier / Solder Pallet）** | 合成石（Durostone）、玻纤 FR4、铝合金、钛 | **买 / 加工**，或 PEEK / PEI 打印 | 托 PCB 过炉 |

选型前先确认你要的是哪一类，三者不能互相替代。

---

## 1. 贴片机供料 / 来料存放 → JEDEC 托盘

- 行业标准外形：**≈ 322.6 × 135.9 mm（12.7″ × 5.35″），厚 6.35 mm**。所有 JEDEC 矩阵托盘共用同一外形，只有腔位不同。
- 分类（TopLine 等厂商目录）：

  | 封装 | JEDEC 参考 | 尺寸范围 |
  |---|---|---|
  | QFP | JEDEC CS-004 | 10 mm ~ 40 mm |
  | LQFP | JEDEC CS-007 | 7 mm ~ 28 mm |

  QFP 托盘另有专项标准 **JEDEC ED-7614**（*JEDEC Standard for QFP Trays*）。
- 采购关键词：`JEDEC tray QFP 14x14`、`LQFP 托盘 14×14`、`矩阵托盘 QFP100`。
- 常见厂商：**TopLine、ePAK、RH Murphy**。
- 材质要点：一般为改性聚砜 / PES / PPO + 防静电（10⁴–10⁹ Ω）；**bakeable** 型号可耐 125–150 ℃，用于去湿烘烤。
- 设计要点：托盘必须**定位在封装本体**上，不能靠引脚受力（QFP 引脚极易变形）。

> ⚠️ **LQFP-100 14×14 常见两种来料：编带（reel，载带宽 32 mm、间距 16 mm）和托盘。**
> 如果你的贴片机是编带供料，需要的是 **载带 / 编带（Carrier Tape）**，跟托盘无关。

---

## 2. 手工贴片收纳 / 摆放 → 3D 打印

### MakerWorld / 其他平台现成模型

- **MakerWorld 197045 — "Stackable SMD IC tray"**（作者 Dreamer 1）
  一次放 8 颗 **QFP-128 及以下**，盖子摩擦配合、可叠放。**这是 MakerWorld 上最对症的一个。**
- **Thingiverse 3682694 — "Customizable QFP Chip Tray"**（作者 Chrismettal）
  **尺寸、腔数、深度全参数化可调**，改参数即为 LQFP-100 专用盘；另有改编版 3682998。
- **STLFinder 搜 `lqfp`** 有 153 个模型，含按 IPC-SM-872A 建立的 QFP / TQFP / LQFP 封装 STEP 模型。

### 站内搜索关键词

- 英文（命中率高）：`QFP tray`、`SMD IC tray`、`IC holder`、`component tray`、`chip tray`
- 中文（命中率低，不推荐）：`芯片收纳`、`贴片元件托盘`

> **结论**：MakerWorld 上 QFP 专用盘偏少，Thingiverse / Printables 生态更全。

### 自己打印的尺寸参数

| 项 | 取值 |
|---|---|
| 腔体平面尺寸 | 14.3 ~ 14.4 mm（14.0 + 0.2~0.3 间隙） |
| 腔深 | ≥ 1.6 mm（本体厚 1.4 mm + 引脚） |
| 腔底 | **必须留空让引脚悬空，不能压引脚** |
| 腔间距 | ≥ 2 mm（便于镊子取件） |

**耗材**：优先 **ESD / 导电耗材**。普通 PLA 摩擦起电，对 0.5 mm 间距、100 脚的芯片存在 ESD 风险。

---

## 3. 要过回流炉 → 不是打印件

PLA / PETG / ABS 在 250–260 ℃ 回流区会直接软化变形，**3D 打印托盘绝对不能进炉**。

- 正经治具：**合成石（Durostone）/ 玻纤 FR4 / 铝合金**。
- 硬要打印：只能用 **PEEK / PEI（ULTEM）/ 高温尼龙 + 玻纤**。

不过——**单贴一颗 LQFP-100 不需要过炉治具**，治具是托整块 PCB 用的。
手工贴这颗芯片的完整工具链是：**钢网 + 锡膏 + 镊子 / 真空吸笔 + 加热台或热风枪**（100 脚 0.5 mm 间距，四边拖焊，或锡膏一次回炉）。

---

## 建议

- **手工 / 小批量，只要个盘摆放收纳** → 用 **Thingiverse 3682694** 改参数打一个，或下载 **MakerWorld 197045**。
- **上贴片机** → 买 **JEDEC QFP 14×14 矩阵托盘**（CS-004 / CS-007 系列），或按机器供料方式配 32 mm 编带。
- **过炉载具** → 用合成石 / 铝，别打印。

---

## 参考来源

| 来源 | 链接 |
|---|---|
| MakerWorld 197045 Stackable SMD IC tray | https://makerworld.com/en/models/197045 |
| Thingiverse 3682694 Customizable QFP Chip Tray | https://www.thingiverse.com/thing:3682694 |
| STLFinder `lqfp` 模型库 | https://www.stlfinder.com/3dmodels/lqfp/ |
| yeggi `qfp` 模型库 | https://www.yeggi.com/q/qfp/ |
| TopLine JEDEC 矩阵托盘目录（CS-004 / CS-007） | https://www.topline.tv/tray.html |
| ePAK Matrix Trays | https://www.epak.com/products/matrix-trays/ |
| JEDEC ED-7614 QFP Tray 标准 | JEDEC *Standard for QFP Trays* |

> **核实说明**：本文档结论基于检索索引命中 + 封装标准整理。受网络限制，上述模型页与厂商页未能逐页打开核验，模型编号与标题来自搜索结果摘要；封装尺寸与 JEDEC 分类为公开标准事实。落地采购前建议自行确认腔位规格。
