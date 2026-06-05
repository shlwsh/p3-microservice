---
name: gitnexus-cursor-mcp-setup
description: >-
  Install and configure GitNexus MCP Server for Cursor on Linux/WSL (nvm, Node 22+).
  Use when the user asks to enable GitNexus MCP, configure ~/.cursor/mcp.json,
  troubleshoot MCP connection, or set up code intelligence after gitnexus analyze.
---

# GitNexus MCP — Cursor 本地安装

在 Cursor 中启用 GitNexus MCP，使 Agent 可调用 `query` / `context` / `impact` 等图谱工具。

## 前置条件

| 项 | 要求 |
|----|------|
| Git 仓库 | 必须在 git 项目根目录操作 |
| Node.js | **≥ 22**（gitnexus 1.6.x 硬性要求；默认 `node` 可能是 20，需用 nvm 切换） |
| 索引 | 先 `analyze`，再配 MCP（顺序不可颠倒） |

## 安装流程

```
- [ ] 1. 确认 Node 版本 ≥ 22
- [ ] 2. 在项目根目录索引仓库
- [ ] 3. 配置 ~/.cursor/mcp.json
- [ ] 4. 安装 Agent Skills（可选但推荐）
- [ ] 5. 验证 MCP 与索引
- [ ] 6. 重启 Cursor
```

### Step 1 — 确认 Node 版本

```bash
node --version          # 若 < 22，用 nvm 切换
nvm install 24 && nvm use 24
which node npx          # 记录绝对路径，后续 MCP 配置要用
```

**WSL + nvm 要点**：Cursor spawn MCP 时不加载 shell profile，默认 PATH 可能指向 Node 20。MCP 配置应使用 **绝对路径**，并在 `env.PATH` 中显式指定 Node 22+ 的 bin 目录。

### Step 2 — 索引仓库

```bash
cd /path/to/repo
npx gitnexus analyze
```

产出：
- `.gitnexus/` — 本地图谱索引（**勿提交 Git**，目录内 `.gitignore` 为 `*`）
- `~/.gitnexus/registry.json` — 全局注册表
- `CLAUDE.md` / `AGENTS.md` — 自动注入 GitNexus 使用段

验证：

```bash
npx gitnexus list
ls .gitnexus/meta.json
```

### Step 3 — 配置 MCP

**方式 A（优先）**：自动 setup

```bash
npx gitnexus setup
```

写入 `~/.cursor/mcp.json` 并将 skills 装到 `~/.cursor/skills/`。

**方式 B（setup 失败或 nvm 环境）**：手动写入 `~/.cursor/mcp.json`

> Cursor **仅支持全局 MCP 配置**，路径固定为 `~/.cursor/mcp.json`。

**Linux / WSL（nvm，推荐）** — 直接指向已安装的 `gitnexus` 二进制，避免 npx 每次下载且规避 Node 版本错配：

```json
{
  "mcpServers": {
    "gitnexus": {
      "command": "/home/<user>/.nvm/versions/node/v24.16.0/bin/gitnexus",
      "args": ["mcp"],
      "env": {
        "PATH": "/home/<user>/.nvm/versions/node/v24.16.0/bin:/usr/bin:/bin"
      }
    }
  }
}
```

若未全局安装，先执行（需 Node 22+）：

```bash
npm install -g gitnexus@latest
```

**Linux / WSL（通用 npx 写法）**：

```json
{
  "mcpServers": {
    "gitnexus": {
      "command": "/home/<user>/.nvm/versions/node/v24.16.0/bin/npx",
      "args": ["-y", "gitnexus@latest", "mcp"],
      "env": {
        "PATH": "/home/<user>/.nvm/versions/node/v24.16.0/bin:/usr/bin:/bin"
      }
    }
  }
}
```

**Windows 原生**：

```json
{
  "mcpServers": {
    "gitnexus": {
      "command": "cmd",
      "args": ["/c", "npx", "-y", "gitnexus@latest", "mcp"]
    }
  }
}
```

将 `<user>` 和 Node 版本号替换为 `which gitnexus` / `which npx` 的实际输出。

### Step 4 — 安装 Skills

Skills 指导 Agent 使用 GitNexus 工具链。来源二选一：

```bash
# 全局（setup 自动完成，或手动复制）
cp -r .claude/skills/gitnexus/gitnexus-* ~/.cursor/skills/

# 项目级（analyze 可能已写入 .cursor/skills/）
ls .cursor/skills/gitnexus-*/
```

6 个技能：`gitnexus-exploring`、`gitnexus-debugging`、`gitnexus-impact-analysis`、`gitnexus-refactoring`、`gitnexus-guide`、`gitnexus-cli`。

### Step 5 — 验证

```bash
# CLI：列出已索引仓库
gitnexus list

# MCP 进程：应打印 "MCP server starting" 后挂起（Ctrl+C 退出）
gitnexus mcp

# 注册表
cat ~/.gitnexus/registry.json
```

在 Cursor 对话中验证：
- “列出所有已索引的 GitNexus 仓库”
- “读取 gitnexus://repo/{name}/context”

### Step 6 — 重启 Cursor

修改 `~/.cursor/mcp.json` 后必须重启 Cursor 或在 Settings → MCP 中重载，确认 `gitnexus` 显示已连接。

## `.gitnexus/` 目录速查

| 文件/目录 | 作用 |
|-----------|------|
| `lbug` | LadybugDB 图数据库（符号、调用关系、执行流） |
| `meta.json` | 索引元数据、统计、文件 hash（增量更新） |
| `parse-cache/` | AST 解析缓存 |
| `.gitignore` | 忽略全部内容，不提交 Git |

## 常见问题

| 现象 | 原因 | 处理 |
|------|------|------|
| `npx gitnexus setup` 网络失败 | npm ECONNRESET / 代理 | 改用手动写 `mcp.json` + `npm install -g gitnexus` |
| MCP 不启动 | Node < 22 | MCP 配置改用 Node 24 绝对路径 |
| MCP 不启动 | PATH 无 nvm | 在 `env.PATH` 中写死 Node bin 目录 |
| `onnxruntime-node` 安装失败 | 可选依赖下载失败 | 全局安装可能仍可用（MCP/analyze 不依赖 embedding）；省略 `--embeddings` |
| Tools 不出现 | 未重启 Cursor | 重启 IDE 或重载 MCP |
| Index is stale | 代码已变更 | `npx gitnexus analyze` 后重启 MCP |
| 多仓库 | 全局注册表 | 各仓库分别 `analyze`；MCP 自动服务全部，查询时指定 `repo` 参数 |

## 索引维护

```bash
npx gitnexus status          # 检查是否过期
npx gitnexus analyze         # 增量更新
npx gitnexus analyze --force # 全量重建
npx gitnexus clean --force   # 清除索引后重建
```

**何时重新 analyze**：大量 refactor、合并 PR、MCP 提示 stale。

## MCP 可用能力（配置成功后）

**Tools**：`list_repos`、`query`、`context`、`impact`、`detect_changes`、`rename`、`cypher`

**Resources**：`gitnexus://repos`、`gitnexus://repo/{name}/context|clusters|processes|process/{name}|schema`

详细用法见 `gitnexus-guide` skill。

## 与本项目的关联

`franka_ros2` 已完成索引示例：
- 注册名：`franka_ros2`
- 索引路径：`.gitnexus/`
- MCP 配置：`~/.cursor/mcp.json`（Node 24 绝对路径）
