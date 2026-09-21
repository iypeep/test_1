# 我缺的东西：Hermes 桌面端重建所需的 290 个 npm 包

> 写给中午要帮我打包的你。**结论在最上面，做完这一件事就行。**

## 一、你只需要做这一件事

1. 在**能访问 npm registry** 的机器/网络（自己的电脑、手机热点、VPN 都行）上，把本仓库 clone 下来。
2. 运行同目录下的脚本（会下载 290 个包并逐个校验 sha512）：

   ```powershell
   powershell -ExecutionPolicy Bypass -File .\fetch-tarballs.ps1
   ```

   - 如果只能访问镜像（例如 npmmirror），加个参数即可，内容仍由 sha512 保证正确：
     ```powershell
     powershell -ExecutionPolicy Bypass -File .\fetch-tarballs.ps1 -Registry https://registry.npmmirror.com
     ```
   - 产物落在 `tarballs/` 目录（按 registry 的原始路径结构存放）。
   - 结束时打印 `verified: 290 / 290`。如果有 `FAILED`，**重跑一次脚本**即可补齐。

3. 把生成的整个 `tarballs/` 目录 commit 并 push 回本仓库，然后跟我说一声。

**或者更省事（完全不用传文件）**：如果能让那台办公机访问 npm registry（公司 VPN / 内网 npm 镜像地址），把镜像地址告诉我就行 —— 我在这边直接 `hermes desktop --force-build`。本仓库什么都不用放。

## 二、背景（30 秒）

- Hermes 主程序**已经更新完成**：`v0.18.0 → v0.21.3 (2026.9.14)`，Python 依赖、gateway、skills、配置迁移全部完成，`hermes --version` 已验证。
- **只剩桌面 App（Electron）的重新打包**：`npm ci` 需要从 registry 取 290 个包，而这台办公机的网络把 npm registry 全封了：

  | 目标 | 结果 |
  | --- | --- |
  | registry.npmmirror.com / registry.npmjs.org / yarnpkg / taobao / 腾讯云 / 华为云 / jsdelivr / unpkg | ❌ 连接被重置 或 DNS 解析失败 |
  | github.com（含 codeload / api）、pypi.org | ✅ 可达（所以 Python 依赖才能装上） |

- 本机 npm 缓存 3.4 GB 里**已经有 1113 个包**，**只缺下面这 290 个**。

## 三、为什么必须下载"原始发布版 tarball"

`package-lock.json` 为每个包记录了 `resolved`（下载 URL）和 `integrity`（sha512）。`npm ci` 会逐个校验摘要。

所以**不能用 `npm pack <包>@<版本>` 重新打包**——重新打包出来的 tarball 字节不同、sha512 不匹配，安装会被拒绝。
必须按清单里的 URL 原样下载。

## 四、仓库里的文件

| 文件 | 说明 |
| --- | --- |
| `missing-npm-tarballs.txt` | **清单**：290 行，每行 `包名@版本 <TAB> 下载URL <TAB> sha512-...` |
| `fetch-tarballs.ps1` | **下载脚本**（Windows）：读清单 → 下载 → 校验 → 按 registry 路径落到 `tarballs/` |
| `serve-tarballs.py` | 收到文件后我这边用它把 `tarballs/` 起成本地 registry（放这里只是让流程透明） |
| `tarballs/` | **你运行脚本后产生的产物**（我真正需要的东西） |

清单统计：

- 共 **290** 个：`node_modules/`（仓库根）254 个、`apps/desktop/` 18 个、`web/` 16 个、`tests-js/` 2 个
- 其中带 scope 的（`@xxx/yyy`）154 个，非 scope 136 个
- 落盘示例（URL 路径即目录结构）：
  `https://registry.npmjs.org/@babel/code-frame/-/code-frame-8.0.0.tgz` → `tarballs/@babel/code-frame/-/code-frame-8.0.0.tgz`

## 五、macOS / Linux 等价做法（不想用 PowerShell 的话）

```bash
while IFS=$'\t' read -r name url integ; do
  rel="${url#https://registry.npmjs.org/}"
  dest="tarballs/$rel"
  mkdir -p "$(dirname "$dest")"
  curl -fsSL "$url" -o "$dest" || { echo "FAIL $name"; continue; }
  got="sha512-$(openssl dgst -sha512 -binary "$dest" | openssl base64 -A)"
  [ "$got" = "$integ" ] || echo "MISMATCH $name"
done < missing-npm-tarballs.txt
```

## 六、我收到之后会做什么

1. `git clone` 本仓库，取出 `tarballs/`。
2. 本地起 registry：`python serve-tarballs.py 4873`。
3. 在 Hermes 源码根目录执行：
   ```powershell
   $env:LOCALAPPDATA\hermes\node\npm.cmd ci --include=dev --registry http://127.0.0.1:4873 --replace-registry-host=always
   ```
4. `hermes desktop --force-build`（重新打包 `apps/desktop/release/win-unpacked`）。
5. 启动桌面 App 验证 + 把结果告诉你。

> 这套离线机制我已经在本机**验证过**：让 lockfile 指向 `registry.npmjs.org` 的包，用本地静态 registry + `--replace-registry-host=always` 能装成功，且 integrity 校验通过。

## 七、不需要你提供的（本机已确认具备）

- **Electron 40.10.2**（`electron-v40.10.2-win32-x64.zip`，138 MB）已在 `$env:LOCALAPPDATA\electron\Cache`。
- Node/npm：Hermes 自带 `$env:LOCALAPPDATA\hermes\node`（node v22.23.2 + npm 10.9.8，满足仓库 `engines` 约束）。
- electron-builder 的打包工具（app-builder/nsis 等）从 GitHub Releases 拉取，GitHub 可达。

## 八、备注与风险

- 这 290 个都是**公开 npm 包**，无任何私有/敏感内容；仓库体积预计几十 MB（单文件远小于 GitHub 100 MB 限制）。
- 若某些包带 postinstall 且需要额外二进制（node-pty / esbuild / electron-winstaller 之类），它们走的也是 GitHub Releases（可达），必要时我会单独反馈。
- 桌面 App 现在**没有被破坏**：7/28 的旧构建仍在原地、今天已验证能用新后端正常启动；这次重建只是把 Electron shell 从 0.17.0 升到 0.17.6+。
