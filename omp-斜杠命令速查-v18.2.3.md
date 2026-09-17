# omp 斜杠命令速查（v18.2.3）

> 生成日期：2026-09-17  
> 来源：本机源码树 `E:\Desktop\oh-my-pi`，`packages/coding-agent/package.json` 版本 **18.2.3**，与运行中的 `omp/18.2.3` 同版；
> 命令清单由 `src/slash-commands/builtin-{modes,collaboration,session,lifecycle,marketplace,control}.ts` 的注册表解析生成，非文档摘抄。  
> 共 **79** 个内置命令，其中 **27** 个带文本 handle（ACP/IDE 客户端可见），其余 52 个是 TUI 专有。

## 0. `/` 菜单是怎么拼出来的

`packages/coding-agent/src/modes/interactive-mode.ts:1285` 的拼装顺序（`init()` 再把文件命令异步补上）：

```ts
this.#pendingSlashCommands = [
  ...builtinCommands,   // 内置注册表，名字 + 别名全部预占
  ...hookCommands,      // hooks 里 registerCommand 注册的
  ...customCommands,    // TypeScript 自定义命令 + MCP prompt 命令
  ...skillCommandList,  // /skill:<name>，由 skills.enableSkillCommands 控制（默认 true）
];
// init() → refreshSlashCommandState() 追加文件命令
```

行为要点：

| 行为 | 说明 |
|---|---|
| 子命令下拉 | `/mcp`、`/memory`、`/todo`、`/security`、`/marketplace` 输完空格弹二级补全；无子命令但带参数的（如 `/model`、`/move`）显示暗色 ghost 提示（`inlineHint`） |
| 描述文本 | 内置用注册表 `description`；`/skill:*` 与文件命令用 frontmatter `description`，没有就取正文第一行（截 60 字 + `...`） |
| 图标 | 按类别取 glyph（action / model / plan / skill / mcp / prompt…），菜单里可一眼区分类型 |
| **未知 `/xxx` 不报错** | 没有任何处理器认领时，原文（含斜杠）当普通 prompt 发给模型 |
| `allowArgs: false` 的命令跟了参数 | dispatch 返回 false，整句也会**漏下去当普通 prompt** |
| 命名冲突 | 优先级 `native 100` → `omp-plugins 90` → `claude 80` → `claude-plugins`/`agents`/`codex 70` → `opencode 55`，同级先注册者胜；被遮蔽项只在 Extension 面板标 `_shadowed` |
| collab 访客 | 会话变更类内置命令对访客显示 host-only，只放行纯本地/只读命令 |

## 1. 命令清单（按作用分组）

“可见性”列：`ACP` = 有文本 handle，IDE/ACP 客户端也能调用；`TUI` = 只在交互式终端里有效。

### 模式开关（改 agent 的工作方式，不是换模型）

| 命令 | 别名 | 作用 | 子命令 | 可见性 |
|---|---|---|---|---|
| `/plan` | — | 开关 plan 模式：先出计划、审过再动手（可带 <prompt> 直接开一轮） | — | TUI |
| `/plan-review` | — | 重新打开最近一份计划的审阅界面（仅 plan 模式下） | — | TUI |
| `/vibe` | — | 开关 vibe 模式：活直接派给常驻 fast/good worker 会话，工具集只读 | — | TUI |
| `/goal` | — | 开关 goal 模式：给本会话挂一个常驻自主目标 | `set` 设置或替换目标、`show` 查看当前目标、`pause` 暂停当前目标、`resume` 恢复被暂停的目标、`drop` 丢弃当前目标、`budget` 调整 token 预算 | TUI |
| `/guided-goal` | — | 让 agent 在对话里访谈你，访谈完自动建 goal | — | TUI |
| `/loop` | — | 开关 loop 模式：下一条 prompt 在每次 yield 后自动重发；可 [count\|duration] / --until 'cmd' / --while 'cmd' 设边界，Esc 中止本轮 | — | TUI |
| `/queue` | — | 把一条消息排到 agent yield 之后再发 | — | TUI |
| `/prewalk` | — | 装/重启一次性模型交接（先弱模型跑、再切强模型） | `restart` 回到 @default 并重新把交接装到 @smol | ACP |
| `/skillful` | — | 开关「把技能清单写进系统提示」（只影响本会话） | `on` 本次会话把技能清单写进提示、`off` 本次会话不写技能清单、`status` 查看技能清单状态 | TUI |
| `/extended-context` | — | 开关扩展上下文窗口（影响计费档） | `on` 启用更大上下文窗口、`off` 用默认/标准计费档上下文、`status` 查看扩展上下文状态 | TUI |
| `/computer` | — | 开关原生 computer-use 的 eval prelude | `on` 本次会话启用 computer use、`off` 本次会话禁用 computer use、`status` 查看 computer use 状态 | TUI |
| `/fast` | — | 开关优先服务档（OpenAI service_tier=priority / Anthropic speed=fast） | `on` 开启 fast、`off` 关闭 fast、`status` 查看 fast 状态 | TUI |

### 模型与供应商

| 命令 | 别名 | 作用 | 子命令 | 可见性 |
|---|---|---|---|---|
| `/model` | — | 本会话换模型（无参显示当前选择） | — | TUI |
| `/switch` | — | 同上（快捷键 alt+p）；接受模糊 id、provider/id、@角色、:档位 | — | TUI |
| `/setup` | — | 打开供应商/登录/网页搜索配置向导 | `providers` 配置登录与网页搜索供应商 | TUI |
| `/login` | — | OAuth 登录供应商 | — | TUI |
| `/logout` | — | 登出 OAuth 供应商 | — | TUI |
| `/usage` | — | 查看供应商配额与限速 | `show` 查看供应商配额与限速、`reset` 消耗一次已存的 Codex 限速重置 | ACP |
| `/live` | — | 启动 Codex 后端的实时语音模式 | — | TUI |

### 上下文与会话生命周期

| 命令 | 别名 | 作用 | 子命令 | 可见性 |
|---|---|---|---|---|
| `/new` | — | 开新会话 | — | TUI |
| `/clear` | — | 就地清空对话上下文（会话本身保留） | — | TUI |
| `/delete` | — | 删掉当前会话并开一个新的 | — | TUI |
| `/compact` | — | 手动压缩上下文 | — | TUI |
| `/shake` | — | 从上下文里丢重内容 | `elide` 剥掉工具结果 + 大块（默认）、`images` 剥掉图片块、`thinking` 丢全部思考块 | ACP |
| `/handoff` | — | 把会话总结成交接文档，并就地压缩 | — | ACP |
| `/fresh` | — | 重置供应商侧流状态，但不改本地记录 | — | ACP |
| `/retry` | — | 重跑上一次失败的 turn | — | ACP |
| `/resume` | — | 切到别的会话（恢复） | — | TUI |
| `/pin` | — | 把会话钉在 resume 列表顶部 | — | ACP |
| `/rename` | — | 重命名当前会话（不给标题则自动生成） | — | ACP |
| `/move` | — | 把当前会话迁到别的目录 | — | ACP |
| `/wt` | — | 把本会话移进一个新 worktree（带改动） | — | ACP |
| `/session` | — | 会话管理子命令 | `info` 查看会话信息与统计、`delete` 删除当前会话并回到选择器、`pin` 把当前 provider 钉到某个已存 OAuth 账号 | ACP |
| `/branch` | — | 回退到某条历史消息，旧路径保留为分支 | — | TUI |
| `/fork` | — | 从某条历史消息开新 fork | — | TUI |
| `/tree` | — | 在会话树里切换分支 | — | TUI |
| `/export` | — | 导出会话为 HTML 文件 | — | ACP |
| `/dump` | — | 复制完整 transcript 到剪贴板（并把裸 LLM 请求 JSON 落 tmp） | — | ACP |
| `/trace` | — | 在 stats 面板打开本会话 trace | — | ACP |
| `/share` | — | 生成加密分享链接（分享服务器或 secret gist） | — | ACP |
| `/copy` | — | 从对话里挑文本或代码复制 | — | TUI |
| `/open` | — | 打开对话里最后一个链接（或用 /copy 挑一个） | — | TUI |

### 协作与共享

| 命令 | 别名 | 作用 | 子命令 | 可见性 |
|---|---|---|---|---|
| `/collab` | — | 通过 relay 实时共享会话 | `view` 只读观战链接（访客只能看不能提问）、`list` 列本机活着的 Collab host（不含链接）、`status` 查看链接与参与者、`stop` 停止共享 | TUI |
| `/join` | — | 加入别人共享的 collab 会话 | — | TUI |
| `/leave` | — | 退出 collab 会话 | — | TUI |
| `/btw` | — | 问一个独立旁路问题，或浏览本会话的 BTW 历史 | — | TUI |
| `/tan` | — | 把跑题的活派给一个完整后台 agent（不污染主上下文） | — | TUI |

### 待办与工作区

| 命令 | 别名 | 作用 | 子命令 | 可见性 |
|---|---|---|---|---|
| `/todo` | — | 查看/修改 agent 的 todo 列表 | `edit` 在 $EDITOR 里编辑（Markdown 往返）、`copy` 复制 todo 为 Markdown、`expand` 在 HUD 展开每个阶段与任务、`collapse` 恢复 HUD 的有界预览、`export` 把 todo 写成 Markdown 文件（默认 TODO.md）、`import` 从 Markdown 文件替换 todo（默认 TODO.md）、`append` 追加任务；阶段模糊匹配或自动创建、`start` 标记任务 in_progress（模糊匹配）、`done` 标记任务/阶段/全部完成（模糊匹配）、`drop` 标记任务/阶段/全部放弃（模糊匹配）、`rm` 删除任务/阶段/全部（模糊匹配） | TUI |
| `/add-dir` | — | 给本会话加一个工作区目录（多根） | — | ACP |
| `/remove-dir` | — | 从本会话移除一个工作区目录 | — | ACP |
| `/dirs` | — | 列出本会话的工作区目录 | — | ACP |
| `/context` | — | 显示上下文占用估算明细 | — | TUI |
| `/tools` | — | 列出当前对 agent 可见的工具 | — | TUI |

### 集成：MCP / SSH / 插件

| 命令 | 别名 | 作用 | 子命令 | 可见性 |
|---|---|---|---|---|
| `/mcp` | — | MCP 服务器全生命周期管理 | `add` 新增 MCP 服务器、`list` 列出全部已配 MCP 服务器、`remove` 移除 MCP 服务器、`test` 测试到某服务器的连通、`reauth` 为某服务器重做 OAuth 授权、`unauth` 移除某服务器的 OAuth 授权、`enable` 启用某 MCP 服务器、`disable` 禁用某 MCP 服务器、`smithery-search` 搜 Smithery 注册表并部署 MCP 服务器、`smithery-login` 登录 Smithery 并缓存 API key、`smithery-logout` 删除缓存的 Smithery API key、`reconnect` 重连指定 MCP 服务器、`reload` 强制重载 MCP 运行时工具、`resources` 列出已连服务器提供的资源、`prompts` 列出已连服务器提供的 prompt、`notifications` 查看通知能力与订阅、`help` 显示用法说明 | ACP |
| `/ssh` | — | 管理 ssh:// 主机（我读远端文件就走这个） | `add` 新增 SSH 主机、`list` 列出全部已配 SSH 主机、`remove` 移除 SSH 主机、`help` 显示用法说明 | ACP |
| `/plugins` | — | 查看与管理已安装插件（npm + marketplace） | `list` 列出全部已装插件（npm + marketplace）、`enable` 启用某市场插件、`disable` 禁用某市场插件 | ACP |
| `/marketplace` | — | 管理插件市场源与已装插件 | `add` 新增市场源、`remove` 移除市场源、`update` 更新市场目录、`list` 列出已配市场、`discover` 浏览可用插件、`install` 安装插件（无参开交互浏览器）、`uninstall` 卸载插件（无参开选择器）、`installed` 列出已装市场插件、`upgrade` 升级过期插件、`help` 显示用法指南 | ACP |
| `/reload-plugins` | — | 重载全部插件（skills / commands / hooks / tools / agents / MCP） | — | ACP |

### 安全与诊断面板

| 命令 | 别名 | 作用 | 子命令 | 可见性 |
|---|---|---|---|---|
| `/security` | — | OMP 原生安全扫描：出计划、跑扫描、看状态/历史、渲染结果、导入 SARIF、导出报告、逐条取证、跨扫描比对、写处置结论 | `plan` 创建不可变的安全扫描计划、`scan` 启动已计划或新计划的扫描、`status` 查看扫描操作状态、`cancel` 取消正在跑的扫描、`scans` 列出本项目已存扫描、`show` 渲染 scan 或 security:// 资源、`import` 导入 SARIF 或 Codex Security bundle、`export` 导出规范 bundle / SARIF / 报告、`validate` 用 OMP 原生工具复核单条 finding、`compare` 跨两次扫描比对 finding 血缘、`disposition` 带理由写下 finding 处置结论 | ACP |
| `/memory` | — | 记忆后端运维（注入内容/统计/诊断/整合/mental model） | `view` 查看当前记忆注入内容、`stats` 记忆后端统计、`diagnose` 跑记忆后端诊断、`queue` 查看待整合的记忆 delta、`sync` 立刻跑记忆整合、`clear` 清空持久化记忆数据与产物、`reset` clear 的别名、`enqueue` 排队一次记忆整合维护、`rebuild` enqueue 的别名、`mm list` 列出当前 bank 上的 mental model、`mm show` 查看单个 mental model（需 id）、`mm refresh` 整 bank 或单个刷新自动刷新模型、`mm history` diff 某 mental model 的变更历史、`mm seed` 补齐缺失的内置 mental model、`mm delete` 从 bank 删除某 mental model（需 id）、`mm reload` 重新拉取缓存的 <mental_models> 块 | ACP |
| `/stats` | — | 打开本地 stats 面板 | — | ACP |
| `/changelog` | — | 查看变更日志 | `full` 看完整变更日志 | ACP |
| `/hotkeys` | — | 列出全部快捷键 | — | TUI |
| `/jobs` | — | 查看后台异步任务状态 | — | TUI |
| `/debug` | — | 打开调试工具选择器 | — | TUI |
| `/extensions` | — | 打开 Extension 控制中心（含被遮蔽的命令条目） | — | TUI |
| `/agents` | — | 打开 agent hub（逐 agent 的模型、prewalk、advisor） | — | TUI |
| `/hub` | — | 打开实时 Agent Hub | — | TUI |
| `/git` | — | 打开 git UI（分栏 diff、暂存、提交编辑） | — | TUI |
| `/cleanse` | — | 用加权并行子 agent 检测并修项目诊断问题 | — | TUI |
| `/omfg` | — | 把一句抱怨锻成 TTSR 规则，阻止该行为复发 | — | TUI |
| `/force` | — | 强制下一轮只用某个工具 | — | TUI |

### 杂项控制

| 命令 | 别名 | 作用 | 子命令 | 可见性 |
|---|---|---|---|---|
| `/settings` | — | 打开设置菜单 | — | TUI |
| `/browser` | — | 切浏览器 eval-prelude 有头/无头 | `headless` 切无头模式、`visible` 切有头模式 | TUI |
| `/advisor` | — | 第二模型顾问：每轮审阅并注入提示 | `on` 启用顾问、`off` 关闭顾问、`status` 查看顾问状态、`dump` 复制顾问的 transcript 到剪贴板、`configure` 打开顾问配置器 | TUI |
| `/pause` | — | 全局冻结：主 agent、子 agent、advisor 都停在下一个安全点（在飞调用跑完、不中断） | — | TUI |
| `/exit` | — | 退出应用 | — | TUI |
| `/quit` | — | 退出应用 | — | TUI |
| `/restart` | — | 用同样启动参数重启 omp 并恢复本会话 | — | TUI |

## 2. 本机菜单的实际构成

- 内置命令：79 个（上表）。
- `/skill:<技能名>`：默认开启（`skills.enableSkillCommands` 默认 `true`），本会话 10 个技能各一条。
- 文件命令：**无**。以下目录都不存在——`~/.omp/agent/commands`、`~/.omp/commands`、`~/.claude/commands`、`~/.codex/commands`、`~/.agents/commands`、`~/.config/opencode/commands`。
- 插件命令：**无**。唯一已装插件 `frontend-design@claude-plugins-official` 只有 `skills/`，没有 `commands/`（见 `~/.claude/plugins/installed_plugins.json`）。
- hooks / 自定义命令：均未配置。

## 附录 A：注册表原文（英文 `description`）

- `/security` — Plan, run, inspect, import, and compare OMP-native security scans
- `/settings` — Open settings menu
- `/setup` — Open provider setup
- `/plan` — Toggle plan mode (agent plans before executing)
- `/plan-review` — Re-open the plan review for the latest plan (plan mode only)
- `/vibe` — Toggle vibe mode (direct persistent fast/good worker sessions; read-only toolset)
- `/goal` — Toggle goal mode (persistent autonomous objective for this session)
- `/guided-goal` — Have the agent interview you in chat, then set up goal mode
- `/loop` — Toggle loop mode. While enabled, the next prompt you send re-submits after every yield. Bound it with a count/duration, or gate it with `--until '<cmd>'` / `--while '<cmd>'` — the command's exit status decides whether the next iteration runs. Esc cancels the current iteration; /loop again to disable.
- `/queue` — Queue a message for after the agent yields
- `/model` — Switch model for this session
- `/switch` — Switch model for this session (same as alt+p); accepts fuzzy ids, provider/id, @role, :level
- `/fast` — Toggle priority service tier (OpenAI service_tier=priority, Anthropic speed=fast)
- `/skillful` — Toggle listing available skills in the system prompt (session only)
- `/extended-context` — Toggle extended context windows
- `/computer` — Toggle the native computer-use eval prelude for this session
- `/prewalk` — Arm or restart a one-shot model handoff
- `/advisor` — Toggle the advisor (a second model that reviews each turn and injects notes)
- `/export` — Export session to HTML file
- `/trace` — Open this session's trace in the stats dashboard
- `/dump` — Copy session transcript to clipboard (and write LLM request JSON to tmp)
- `/share` — Share session via an encrypted link (share server or secret gist)
- `/collab` — Share this session live via a relay
- `/join` — Join a shared collab session
- `/leave` — Leave the collab session
- `/browser` — Toggle browser eval-prelude headless vs visible mode
- `/copy` — Pick text or code from the conversation to copy
- `/open` — Open the last link from the conversation in your browser (or pick one with /copy)
- `/todo` — View or modify the agent's todo list
- `/session` — Session management commands
- `/jobs` — Show async background jobs status
- `/usage` — Show provider usage and limits
- `/stats` — Launch the local stats dashboard
- `/changelog` — Show changelog entries
- `/hotkeys` — Show all keyboard shortcuts
- `/tools` — Show tools currently visible to the agent
- `/context` — Show estimated context usage breakdown
- `/extensions` — Open Extension Control Center dashboard
- `/agents` — Open the agents hub (per-agent model, prewalk, and advisor)
- `/git` — Open the git UI (split diff viewer, staging, commit composer)
- `/hub` — Open the live Agent Hub
- `/branch` — Rewind to a previous message, keeping the old path as a branch
- `/fork` — Create a new fork from a previous message
- `/tree` — Navigate session tree (switch branches)
- `/login` — Login with OAuth provider
- `/logout` — Logout from OAuth provider
- `/mcp` — Manage MCP servers (add, list, remove, test)
- `/ssh` — Manage SSH hosts (add, list, remove)
- `/new` — Start a new session
- `/fresh` — Reset provider stream state without changing the local transcript
- `/clear` — Clear the conversation context in place, keeping the session
- `/delete` — Delete the current session and start a new one
- `/compact` — Manually compact the session context
- `/shake` — Drop heavy content from context (tool results, large blocks)
- `/handoff` — Summarize the session into a handoff document and compact in place
- `/resume` — Resume a different session
- `/pin` — Pin or unpin a session at the top of the resume list
- `/btw` — Ask a side question, or browse this session's BTW history
- `/tan` — Run a full background agent on tangential work
- `/omfg` — Forge a TTSR rule from a complaint to stop a recurring behavior
- `/cleanse` — Detect and fix project diagnostics with weighted parallel subagents
- `/retry` — Retry the last failed agent turn
- `/debug` — Open debug tools selector
- `/memory` — Inspect and operate memory maintenance
- `/rename` — Rename the current session (omit title to generate)
- `/move` — Move the current session to a different directory
- `/wt` — Move this session into a new worktree, changes included
- `/add-dir` — Add a workspace directory to this session (multi-root)
- `/remove-dir` — Remove a workspace directory from this session
- `/dirs` — List this session's workspace directories
- `/exit` — Exit the application
- `/restart` — Restart omp with the same launch flags, resuming this session
- `/marketplace` — Manage marketplace plugin sources and installed plugins
- `/plugins` — View and manage installed plugins
- `/reload-plugins` — Reload all plugins (skills, commands, hooks, tools, agents, MCP)
- `/force` — Force next turn to use a specific tool
- `/live` — Start Codex-backed realtime voice mode
- `/pause` — Freeze all agents (main, subagents, advisor) until resumed
- `/quit` — Quit the application

## 附录 B：怎么自行重新导出

```bash
# 1) 确认源码树版本与运行版本一致
jq -r .version /e/Desktop/oh-my-pi/packages/coding-agent/package.json   # 期望 18.2.3
omp --version                                                        # 期望 omp/18.2.3

# 2) 命令注册表就这几处
ls /e/Desktop/oh-my-pi/packages/coding-agent/src/slash-commands/builtin-*.ts
#   builtin-modes.ts        模式/模型类
#   builtin-session.ts      诊断面板/MCP/SSH 之外的会话类
#   builtin-lifecycle.ts    上下文与会话生命周期
#   builtin-collaboration.ts 协作/顾问/导出
#   builtin-marketplace.ts  插件与市场
#   builtin-control.ts      强制工具/语音/暂停/退出

# 3) 看某条命令到底干什么，搜索 handle: 或 handleTui:
grep -n 'name: "compact"' -A 40 /e/Desktop/oh-my-pi/packages/coding-agent/src/slash-commands/builtin-lifecycle.ts
```

## 附录 C：与文档的差异提示

- `omp://slash-command-internals.md` 描述机制（发现、去重、展开语义），**不含命令清单**；命令清单只有源码里有。
- 源码树与运行版本必须同版，否则命令集可能不同——升级后重新跑一遍本表的生成脚本。
