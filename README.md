# test_1 — 杂项仓库

零散笔记、一次性任务、临时资料的存放处。2026-09-22 做过一次归类整理：根目录只留本索引，
其余文件按主题进目录。

## 目录

| 目录 | 内容 | 状态 |
| --- | --- | --- |
| [`npm-offline/`](npm-offline/README.md) | Hermes 桌面端重建所需的 npm tarball：清单 + 下载/校验脚本 + 本地 registry 服务 + 263 个已校验的 tarball（387.5 MiB） | ✅ 已完成抓取，等接收方 `npm ci` |
| [`hardware/`](hardware/) | [`STM32F407VET6-LQFP100-SMT托盘选型.md`](hardware/STM32F407VET6-LQFP100-SMT托盘选型.md)（JEDEC 华夫盘 / 3D 打印摆放盘 / 回流焊载具）；[`lumenpnp/`](hardware/lumenpnp/README.md)：LumenPnP 贴片机非阻容小批量物料的供料方案 + 打印成本计算脚本与结果 | 参考资料 |
| [`docs/`](docs/) | `omp`（oh-my-pi）斜杠命令速查 v18.2.3 —— 79 个内置命令 | 参考资料 |
| [`notes/`](notes/) | `riscv32-nemu/`：ICS-PA 给 NEMU 加 riscv32 时的反汇编与运行日志 | 调试留档 |
| [`personal/`](personal/) | 个人简历 PDF | 私有资料（注意本仓库为 public） |

## 约定

- 一次性产物可以进本仓库，但请放进上表对应目录，不要再堆根目录。
- 传输类任务（如 npm tarball）请把**清单、脚本、校验报告、产物**放在同一目录，产物 commit 回来，
  对方只靠这一份目录就能复现和核对（见 `npm-offline/`）。
- 二进制/压缩包在 `.gitattributes` 里标了 `binary`：tarball 换个字节 sha512 就不匹配了，
  绝不能让 git 做换行转换。文本文件统一存 LF（`*.ps1` 等 Windows 脚本检出为 CRLF）。

## 整理记录

- 2026-09-22：根目录 9 个文件按主题归入 4 个目录（`npm-offline/`、`hardware/`、`docs/`、`notes/`、`personal/`，用 `git mv` 保留历史）；
  补 `.gitattributes`（换行 + 二进制）；补本索引；
  `npm-offline/README.md` 改写为"任务 + 现状"结构并修正路径；
  新增跨平台下载脚本 `fetch-tarballs.py`（原 PowerShell 脚本保留）；
  完成 263 个 tarball 的抓取与 sha512 校验，产出 `results.tsv`。
- 2026-09-22：新增 `hardware/lumenpnp/` —— 从官方仓库（`opulo-inc/lumenpnp` v4.1.0，`--depth 1` 克隆）
  与 OpenPnP 源码核实后，整理出非阻容 / 小批量物料的供料方案（剪带 / 散料 / 管装 / JEDEC 盘 / 厚料各用什么），
  并给出"买还是打印"的量化依据：新增 `stl-volume.py`（纯标准库，解析二进制 STL 算实体体积与耗材量）
  及其产物 `strip-feeder-print-cost.tsv` —— 官方散料飞达六个规格合计 36.9 g 耗材。
