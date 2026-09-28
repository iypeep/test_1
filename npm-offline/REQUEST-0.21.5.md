# 需要带回的东西：Hermes 0.21.3 → 0.21.5（只需 4 个 npm tarball）

> 目标机（办公机）网络现状，已实测：
>
> | 目标 | 结果 |
> |---|---|
> | `registry.npmjs.org` / `registry.npmmirror.com` / 华为云 / 腾讯云 / USTC / 阿里云 / registry.yarnpkg.com / 清华 tuna / cdn.npmmirror.com | ❌ 全 `000`（连接重置/DNS 失败） |
> | 9 个常见本地代理端口（7897/7890/10809/10808/1080/8888/3128/8080/2080） | ❌ 全 `000` |
> | `github.com` / `api.github.com` | ✅ 通（代码、tag、electron-builder 工具链都能自己拉） |
> | `pypi.org` | ✅ 通（Python 依赖能自己装） |
>
> 所以**代码和 Python 侧我自己能搞定，只缺下面 4 个 npm 包。**

---

## 一、结论：只缺 4 个包

`v2026.9.14 (0.21.3)` → `v2026.9.24 (0.21.5)` 的 `package-lock.json` 逐条比对结果：

- 条目数 `1417 → 1422`（+5，其中 `@types/proxy-from-env` 本机已有）
- 两版共有条目**版本差异 0 条**
- 本机 checkout 相对 0.21.5：**只缺 4 个包**

| 包 | 版本 | 为什么需要 |
|---|---|---|
| `@novnc/novnc` | 1.7.0 | `apps/desktop` 直接依赖（VNC 查看器） |
| `dbus-native` | 0.15.2 | `apps/desktop` 直接依赖 |
| `xml2js` | 0.6.2 | `dbus-native` 依赖 |
| `xmlbuilder` | 11.0.1 | `xml2js` / `plist` 依赖 |

这 4 个既**不在本仓库现有的 263 个 tarball 里**，也**不在本机 npm 缓存里**（已按 sha512 算过 cacache 路径确认）。

可直接追加到 `npm-offline/missing-npm-tarballs.txt`（`名称@版本 <TAB> URL <TAB> integrity`）：

```
@novnc/novnc@1.7.0	https://registry.npmjs.org/@novnc/novnc/-/novnc-1.7.0.tgz	sha512-ucEJOx4T2avIRCleodk7YobZj5O2Ga2AeLfQ69A/yjG9HHba2+PDgwSkN3FttrmG+70ZGx21sElNFouK13RzyA==
dbus-native@0.15.2	https://registry.npmjs.org/dbus-native/-/dbus-native-0.15.2.tgz	sha512-J1IBi4LmbqrFhroN66Dj1tCCTP6TVbZgUKhWQZf3uS6t93yRWEcRRDjOZV9N6boGRhOp/BOjLliFm9vWu1QZOA==
xml2js@0.6.2	https://registry.npmjs.org/xml2js/-/xml2js-0.6.2.tgz	sha512-T4rieHaC1EXcES0Kxxj4JWgaUQHDk+qwHcYOCFHfiwKz7tOVPLq7Hjq9dM1WCMhylqMEfP7hMcOIChvotiZegA==
xmlbuilder@11.0.1	https://registry.npmjs.org/xmlbuilder/-/xmlbuilder-11.0.1.tgz	sha512-fDlsI/kFEx7gLvbecc0/ohLG50fugQp8ryHzMTuW9vSa1GJ0XYWKnhsUx7oie3G98+r56aTQIUB4kht42R3JvA==
```

---

## 二、有网络时怎么做

### 方式 A（推荐，只补 4 个文件）

把 4 个 tarball 按「URL 去掉 `https://registry.npmjs.org/`」的路径放进仓库：

```
npm-offline/tarballs/@novnc/novnc/-/novnc-1.7.0.tgz
npm-offline/tarballs/dbus-native/-/dbus-native-0.15.2.tgz
npm-offline/tarballs/xml2js/-/xml2js-0.6.2.tgz
npm-offline/tarballs/xmlbuilder/-/xmlbuilder-11.0.1.tgz
```

命令（Git Bash / WSL / macOS / Linux 均可）：

```bash
cd test_1/npm-offline
while IFS=$'\t' read -r name url integ; do
  integ="${integ%$'\r'}"
  rel="${url#https://registry.npmjs.org/}"
  mkdir -p "tarballs/$(dirname "$rel")"
  curl -fsSL "$url" -o "tarballs/$rel" || { echo "FAIL $name"; continue; }
  got="sha512-$(openssl dgst -sha512 -binary "tarballs/$rel" | openssl base64 -A)"
  [ "$got" = "$integ" ] && echo "OK $name" || echo "MISMATCH $name"
done <<'EOF'
@novnc/novnc@1.7.0	https://registry.npmjs.org/@novnc/novnc/-/novnc-1.7.0.tgz	sha512-ucEJOx4T2avIRCleodk7YobZj5O2Ga2AeLfQ69A/yjG9HHba2+PDgwSkN3FttrmG+70ZGx21sElNFouK13RzyA==
dbus-native@0.15.2	https://registry.npmjs.org/dbus-native/-/dbus-native-0.15.2.tgz	sha512-J1IBi4LmbqrFhroN66Dj1tCCTP6TVbZgUKhWQZf3uS6t93yRWEcRRDjOZV9N6boGRhOp/BOjLliFm9vWu1QZOA==
xml2js@0.6.2	https://registry.npmjs.org/xml2js/-/xml2js-0.6.2.tgz	sha512-T4rieHaC1EXcES0Kxxj4JWgaUQHDk+qwHcYOCFHfiwKz7tOVPLq7Hjq9dM1WCMhylqMEfP7hMcOIChvotiZegA==
xmlbuilder@11.0.1	https://registry.npmjs.org/xmlbuilder/-/xmlbuilder-11.0.1.tgz	sha512-fDlsI/kFEx7gLvbecc0/ohLG50fugQp8ryHzMTuW9vSa1GJ0XYWKnhsUx7oie3G98+r56aTQIUB4kht42R3JvA==
EOF

git add npm-offline/tarballs
git commit -m "npm-offline: add 0.21.5 delta tarballs (@novnc/novnc, dbus-native, xml2js, xmlbuilder)"
git push
```

> 若 `curl` 直连 npmjs 不通，加镜像：把 URL 的 `registry.npmjs.org` 换成 `registry.npmmirror.com`（内容仍由上面的 sha512 保证正确）。

### 方式 B（省事版，全量重抓）

先把上面 4 行追加进 `missing-npm-tarballs.txt`，然后：

```bash
cd test_1
python npm-offline/fetch-tarballs.py                       # 镜像优先
python npm-offline/fetch-tarballs.py --proxy http://127.0.0.1:7897   # 需要时加代理
git add npm-offline && git commit -m "refresh tarballs for 0.21.5" && git push
```

---

## 三、我拿到之后会做什么（不需要你操作）

1. `git clone` 本仓库 → `python npm-offline/serve-tarballs.py 4873`
2. `hermes-agent` 里：`git fetch --tags && git checkout v2026.9.24`
3. `npm ci --include=dev --registry http://127.0.0.1:4873 --replace-registry-host=always`
4. `hermes desktop --force-build`（重建 `apps/desktop/release/win-unpacked`）
5. 校验 `install-stamp.json` 的 commit/版本，启动桌面 App 验证
6. Python 依赖：pypi 通，走更新器自带步骤或 `uv pip sync`

> 更新前必须先停掉占用 venv 的进程（桌面后端、gateway、agent 会话）——
> Hermes 的 `update` 针对 Windows 的 `.pyd` 锁做的是 **fail-closed**：
> venv 被占用时直接 `exit 2`，不做事。上一次（09-28 19:17）就是这样被拒的。

---

## 四、已确认「不需要你带」的东西

- **代码 / tag**：GitHub 通，`git fetch --tags` 已能拿到 `v2026.9.24`
- **Python 依赖**：`pypi.org` → 200
- **Electron 40.10.2 的 `win32-x64` zip**：已在 `%LOCALAPPDATA%\electron\Cache`
- **electron-builder / app-builder 工具**：走 GitHub Releases，可达；且 `electron-builder@26.15.3` 两版一致
- **本机 npm 缓存**：已有 1113 个包，配合仓库现有 263 个 tarball，覆盖 0.21.3 的全部依赖

---

## 五、顺带说明：桌面 App 显示 `v0.17.6` ≠ Hermes 不是 0.21

- `Hermes Desktop v0.17.6` 是 **Electron 外壳自己的版本号**：`apps/desktop/package.json` 的 `version`，
  由 `electron/main.ts` 的 `desktopVersion: app.getVersion()` 渲染。
  **0.21.5 里这个号同样是 0.17.6**，更新完也不会变成 0.21 —— 它不是 agent 版本。
- Hermes **本体**版本是 **0.21.3**：`hermes --version` 输出
  `Hermes Agent v0.21.3 (2026.9.14)`；应用内「设置 → 关于/版本与更新」里的**「后端版本」**即此值。
- 状态栏 `落后 main 5765 个提交` 是拿本地 checkout 与 `origin/main` 比较 ——
  CLI/git 安装默认跟踪 `main`（未发布的开发分支，上游 `pyproject` 版本是 `0.0.0`），
  所以这个数字**永远非零**，不代表安装坏了。
- 0.21 线上更新的版本：`v2026.9.21 = 0.21.4`、`v2026.9.24 = 0.21.5`；本机 = 0.21.3。
