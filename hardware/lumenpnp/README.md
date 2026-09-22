# LumenPnP 非阻容 / 小批量物料的供料方案

**结论先行**：非阻容、小批量物料（IC、连接器、模块、二三极管……），**硬件全部自己 3D 打印，不需要买任何"托盘"**。
官方那套散料编带飞达（strip feeder）的 STL 就在仓库发布包里，六个规格合计约 **37 g 耗材**。

---

## 0. 先分清："托盘"在贴片机语境下不是一种东西

| 名称 | 是什么 | 在 LumenPnP 上对应 |
| --- | --- | --- |
| **暂存板 staging plate** | 机器台面：120 × 600 mm PCB，带孔阵（孔距 15 mm）用于装飞达、机器件、夹具 | 复刻机自带，**不是物料托盘**，别买错 |
| **编带散料飞达 strip feeder** | 手动飞达，卡住剪下的料带，靠视觉对料带孔取料 | 来料是**剪带**时用 |
| **散料托盒 loose parts tray** | 多格浅盘，散料倒在格里，靠 `AdvancedLoosePartFeeder` 视觉找料 | 来料是**散装**时用 |
| **JEDEC 矩阵托盘（华夫盘）** | 来料本身（QFP/QFN/BGA 常用）+ 防静电可烘烤 | 用元件自带的盘，配 `ReferenceTrayFeeder` |
| **电动 Photon 飞达** | 自动供带，只支持 8 / 12 mm 料带 | 阻容跑量时买 |

---

## 1. 按来料形态选方案

| 来料形态 | 方案 | 取货方式 | 买 / 打印 |
| --- | --- | --- | --- |
| **剪带** 8–44 mm（几颗也放） | 官方散料编带飞达，8 / 12 / 16 / 24 / 32 mm + **可调版**，90° / 180° 装在暂存板孔阵上 | 视觉对料带定位孔，静止取料 | **打印** |
| **完全散料**（掉料、散装袋料） | OpenPnP 内置 `AdvancedLoosePartFeeder`（视觉自动找位置 + 判极性）+ 九格散料托盒（每格 16 mm，装前导轨，取料高度与飞达一致，实测可识别 0402，免支撑） | 视觉识别 | **打印** |
| **管装**（DIP / SOP tube） | OpenPnP 内置 `ReferenceTubeFeeder`（固定点取料，配振动管更佳） | 固定坐标 | 打印管座 |
| **矩阵盘**（JEDEC tray / QFP、BGA、QFN） | OpenPnP 内置 `ReferenceTrayFeeder` / `ReferenceRotatedTrayFeeder`（2D 阵列，增量取料，无视觉，限 90° 对齐） | 行列坐标 | 不用买：用元件自带的 JEDEC 盘 / 吸塑盘，要定位就打印个定位框 |
| **厚料 / 大料 / 非标间距**（> 6.5 mm 厚、> 32 mm 宽、非 4 mm 间距） | OpenPnP 内置 `ReferencePushPullFeeder`（视觉 + EIA-481）或 `BlindsFeeder`（OpenSCAD 参数化，可整排打印） | 视觉 + 手动/推拉供带 | 打印 / 零硬件成本 |

### 官方 strip feeder 的硬指标（Opulo 商品页）

- 容量：8 mm = 3 条、12 mm = 3 条、16 mm = 2 条、24 mm = 1 条、32 mm = 1 条、可调（32 mm+）= 1 条
- 最大料带厚度 **6.5 mm**，长 120 mm，随附暂存板安装五金
- 单机料号上限：散料飞达方案 **79 个**；电动飞达方案 50 个（且只支持 8 / 12 mm）

---

## 2. 买还是打印：算一遍

打印成本用 `stl-volume.py` 从官方 STL 直接算（实体体积 → 按 2–3 圈墙 + 20% 填充估挤出量，密度 1.24 g/cm³）：

见 `strip-feeder-print-cost.tsv`：六件合计 **≈ 37 g**，按 ¥60/kg 计 **≈ ¥2.2**。

| 项目 | 打印 | 购买 |
| --- | --- | --- |
| 散料编带飞达 ×6 规格 | 37 g 耗材 ≈ ¥2 | $9.99 / 个 ≈ $60 + 美国发货国际运费/关税，1 周交期 |
| 散料托盒（九格） | 几十克耗材 | 官方无此商品 |
| 管座 / 托盘定位框 | 几十克耗材 | 官方无此商品 |
| 五金（M3 蝶形螺母、M3×8/10 螺栓、M5 T 型螺母） | 打印不了 | **淘宝买**，几元钱 |

**唯一值得花钱的地方**：五金。次选是电动 Photon 飞达（€83/个，5-pack €413.95），只在 8 / 12 mm 阻容跑量时考虑。

> 暂存板（$70）不是托盘，是机器台面，复刻机自带；不足时才补，且只影响台面数量，不影响供料方式。

---

## 3. 取源（中国网络注意）

| 内容 | 地址 |
| --- | --- |
| 官方源码 | `https://github.com/opulo-inc/lumenpnp`（**历史 3.7 GB，必须 `git clone --depth 1`**） |
| 官方 STL 包 | `https://github.com/opulo-inc/lumenpnp/releases/download/v4.1.0/LumenPnP-STLs-v4.1.0.zip`（143 MB / 45 个 STL，**已按打印方向摆好**，散料飞达全含） |
| 可打印件源文件 | 仓库内 `pnp/cad/FDM/*.FCStd`（FreeCAD，可改尺寸；含 8/12/16/24/32 mm + 可调散料飞达） |
| OpenPnP 官方机器配置 | 仓库内 `openpnp/machine.xml` |
| 同页其它资产 | `LumenPnP-Config-v4-1.zip`、`LumenPnP-BOM-v*.zip`、`LumenPnP-PCBs-*.zip`、`v4-lumenpnp-firmware-00.bin` |
| 中文复刻教程全集 | 本项目外部：`E:\LumenPnP贴片机\`（`index.md` 为总目录；含《LumenPnPV4完全复刻指南-Lonly版》《BOM汇总》《散料飞达》《暂存板》分册） |

GitHub 直连被墙时走代理（本机 Clash，`127.0.0.1:7897`，已配 git 全局 `http.proxy` / `https.proxy`）。

## 4. 建议打印顺序

8 mm 飞达 ×2–3 → 12 mm → 16 mm → **可调版 adj**（一件覆盖 32–44 mm，最划算）→ 九格散料托盒 ×2（可拼接）。

注意：飞达打印件**必须平**（官方出厂用花岗岩平台检平，翘曲直接报废）；PLA / PETG 均可，0.2 mm 层高。

---

## 数据来源

- 仓库与发布包：`github.com/opulo-inc/lumenpnp`（v4.1.0，2026-02-25 发布）
- 价格与容量：`opulo.io/products/lumenpnp-strip-feeder`（$9.99、条数、6.5 mm / 120 mm）、`opulo.io/products/staging-plate`（$70）、opulo.io 套餐页（Feeder 5-Pack €413.95）
- OpenPnP 内置供料器类：`github.com/openpnp/openpnp` → `src/main/java/org/openpnp/machine/reference/feeder/`（`AdvancedLoosePartFeeder`、`ReferenceTrayFeeder`、`ReferenceRotatedTrayFeeder`、`ReferenceTubeFeeder`、`ReferencePushPullFeeder`、`BlindsFeeder`）
- 九格散料托盒：`makerworld.com/en/models/1451430-lumenpnp-loose-parts-feeder`
- 中文复刻指南（79 个料号上限、8–44 mm 料带宽度）：`E:\LumenPnP贴片机\LumenPnPV4完全复刻指南-Lonly版.md`
