# 离线包传递：Hermes 桌面端重建所需的 npm tarball

> 这是 `test_1` 仓库里的一个一次性任务目录。**结论在最上面。**

## 〇、当前状态：已完成 ✅（2026-09-22 由助手方机器抓取）

| 项目 | 结果 |
| --- | --- |
| 清单行数 | 290 行 |
| **唯一包数** | **263 个**（清单里 27 行是重复条目——同一包出现在多个 workspace 的统计里，落盘后是同一个文件） |
| 校验结果 | **verified: 290 / 290 行，263 / 263 个文件 sha512 全部匹配，0 失败** |
| 总体积 | **387.5 MiB**（263 个 `.tgz`，最大单文件 16.8 MiB：`mermaid-11.16.1.tgz`，远低于 GitHub 100 MB 限制） |
| 来源 | `registry.npmmirror.com` 直连 267 个 + 本地已有的 23 个（重复条目命中同一路径）；官方 `registry.npmjs.org` 直连在本机被重置，故镜像为主、代理兜底 |
| 耗时 | 39 秒（16 并发） |
| 逐包明细 | [`results.tsv`](results.tsv)（包名 / 来源 / 字节数 / 失败原因） |

**接收方现在只需要**：`git clone` 本仓库 → `python npm-offline/serve-tarballs.py 4873` → 在 Hermes 源码根目录 `npm ci --registry http://127.0.0.1:4873 --replace-registry-host=always`（见第六节）。本目录不需要再跑下载脚本。

---

## 一、原始需求（保留原文）

1. 在**能访问 npm registry** 的机器/网络（自己的电脑、手机热点、VPN 都行）上，把本仓库 clone 下来。
2. 在本目录下运行下载脚本（会下载 290 行清单并逐个校验 sha512）：

   ```powershell
   powershell -ExecutionPolicy Bypass -File .\fetch-tarballs.ps1
   ```

   - 只能访问镜像时加参数即可，内容仍由 sha512 保证正确：
     ```powershell
     powershell -ExecutionPolicy Bypass -File .\fetch-tarballs.ps1 -Registry https://registry.npmmirror.com
     ```
   - 产物落在 `tarballs/` 目录（按 registry 的原始路径结构存放）。
   - 结束时打印 `verified: 290 / 290`。如果有 `FAILED`，**重跑一次脚本**即可补齐（已校验过的文件会跳过）。

3. 把生成的整个 `tarballs/` 目录 commit 并 push 回本仓库。

**或者更省事（完全不用传文件）**：如果能让那台办公机访问 npm registry（公司 VPN / 内网 npm 镜像地址），把镜像地址告诉我 —— 我在这边直接 `hermes desktop --force-build`，本仓库什么都不用放。

## 二、背景（30 秒）

- Hermes 主程序**已经更新完成**：`v0.18.0 → v0.21.3 (2026.9.14)`，Python 依赖、gateway、skills、配置迁移全部完成，`hermes --version` 已验证。
- **只剩桌面 App（Electron）的重新打包**：`npm ci` 需要从 registry 取这些包，而那台办公机的网络把 npm registry 全封了：

  | 目标 | 结果 |
  | --- | --- |
  | registry.npmmirror.com / registry.npmjs.org / yarnpkg / taobao / 腾讯云 / 华为云 / jsdelivr / unpkg | ❌ 连接被重置 或 DNS 解析失败 |
  | github.com（含 codeload / api）、pypi.org | ✅ 可达（所以 Python 依赖才能装上） |

- 本机 npm 缓存 3.4 GB 里**已经有 1113 个包**，只缺清单里的这些。

## 三、为什么必须下载"原始发布版 tarball"

`package-lock.json` 为每个包记录了 `resolved`（下载 URL）和 `integrity`（sha512）。`npm ci` 会逐个校验摘要。

所以**不能用 `npm pack <包>@<版本>` 重新打包**——重新打包出来的 tarball 字节不同、sha512 不匹配，安装会被拒绝。必须按清单里的 URL 原样下载。

## 四、本目录的文件

| 文件 | 说明 |
| --- | --- |
| `missing-npm-tarballs.txt` | **清单**：290 行，每行 `包名@版本 <TAB> 下载URL <TAB> sha512-…` |
| `fetch-tarballs.ps1` | 下载脚本（Windows / PowerShell）：读清单 → 下载 → 校验 → 按 registry 路径落到 `tarballs/` |
| `fetch-tarballs.py` | 下载脚本（跨平台，纯标准库，**本次实际用的是它**）：并发 + 镜像优先 + 代理兜底 + 断点续跑 |
| `serve-tarballs.py` | 收到文件后由接收方把 `tarballs/` 起成本地静态 registry |
| `tarballs/` | **产物**：263 个 `.tgz`，路径即 registry 原始路径结构 |
| `results.tsv` | 校验明细（本次抓取的逐包来源与字节数） |

清单统计（按行）：`node_modules/`（仓库根）254、`apps/desktop/` 18、`web/` 16、`tests-js/` 2；
带 scope 的（`@xxx/yyy`）154、非 scope 136。落盘示例：

```
https://registry.npmjs.org/@babel/code-frame/-/code-frame-8.0.0.tgz
  → tarballs/@babel/code-frame/-/code-frame-8.0.0.tgz
```

**重跑下载脚本时**（例如清单更新后）：

```bash
cd test_1            # 仓库根
python npm-offline/fetch-tarballs.py                                   # 镜像优先，直连
python npm-offline/fetch-tarballs.py --proxy http://127.0.0.1:7897     # 追加代理兜底
```

> 脚本默认相对**自身所在目录**读清单、写 `tarballs/`，所以在任何 cwd 下都能跑。

## 五、macOS / Linux 等价做法（不想用 PowerShell 的话）

上面的 `fetch-tarballs.py` 本身就是跨平台的，只有标准库依赖。若要手写 shell 版，注意两点：

```bash
while IFS=$'\t' read -r name url integ; do
  integ="${integ%$'\r'}"            # 清单在 Windows 上会被 checkout 成 CRLF，不剥 \r 会误报 MISMATCH
  rel="${url#https://registry.npmjs.org/}"
  dest="tarballs/$rel"
  mkdir -p "$(dirname "$dest")"
  curl -fsSL "$url" -o "$dest" || { echo "FAIL $name"; continue; }
  got="sha512-$(openssl dgst -sha512 -binary "$dest" | openssl base64 -A)"
  [ "$got" = "$integ" ] || echo "MISMATCH $name"
done < npm-offline/missing-npm-tarballs.txt
```

## 六、接收方拿到之后做什么

1. `git clone` 本仓库，取出 `npm-offline/tarballs/`。
2. 本地起 registry：`python npm-offline/serve-tarballs.py 4873`。
3. 在 Hermes 源码根目录执行：
   ```powershell
   $env:LOCALAPPDATA\hermes\node\npm.cmd ci --include=dev --registry http://127.0.0.1:4873 --replace-registry-host=always
   ```
4. `hermes desktop --force-build`（重新打包 `apps/desktop/release/win-unpacked`）。
5. 启动桌面 App 验证。

> 这套离线机制已在本机**验证过**：让 lockfile 指向 `registry.npmjs.org` 的包，用本地静态 registry + `--replace-registry-host=always` 能装成功，且 integrity 校验通过。

## 七、不需要接收方提供的（本机已确认具备）

- **Electron 40.10.2**（`electron-v40.10.2-win32-x64.zip`，138 MB）已在 `$env:LOCALAPPDATA\electron\Cache`。
- Node/npm：Hermes 自带 `$env:LOCALAPPDATA\hermes\node`（node v22.23.2 + npm 10.9.8，满足仓库 `engines` 约束）。
- electron-builder 的打包工具（app-builder/nsis 等）从 GitHub Releases 拉取，GitHub 可达。

## 八、备注与风险

- 这些包都是**公开 npm 包**，无私有/敏感内容。
- **实际体积是 387.5 MiB，不是最初估计的"几十 MB"** —— 因为 `package-lock.json` 里含其它平台的 optional 二进制（`@tauri-apps/cli-linux-*`、`@rolldown/binding-linux-ppc64-gnu` 等，合计约 60 MB）。`npm ci` 会校验这些条目，所以本次**一个都没裁**，全量抓取最稳。
- 若某些包带 postinstall 且需要额外二进制（node-pty / esbuild / electron-winstaller 之类），它们走 GitHub Releases（可达），失败时单独反馈。
- 桌面 App 现在**没有被破坏**：7/28 的旧构建仍在原地、当天已验证能用新后端正常启动；这次重建只是把 Electron shell 从 0.17.0 升到 0.17.6+。
