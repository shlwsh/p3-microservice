# 本仓库配置（franka_ros2 / paper1）

复制技能到其他项目时，请改写本文件或新建 `config.local.md`（见 [README.md](README.md)）。

| 变量 | 值 | 说明 |
|------|-----|------|
| **PAPER1_ROOT** | `doctor/paper1` | 相对**工作区根目录**的论文与实验路径 |
| **主稿英文** | `{PAPER1_ROOT}/latex/main.tex` | 盲审主语言默认英文 |
| **主稿中文** | `{PAPER1_ROOT}/latex/main-zh.tex` | 预检可选中英数字对照 |
| **评审输出** | `{PAPER1_ROOT}/reviews/{run_id}/` | `run_id` = `YYYYMMDD-HHmmss` |
| **目标期刊** | IEEE RA-L / RCIM | 编辑审查篇幅依据 |

## 解析规则（执行 Agent）

1. 工作区根 = 含 `.cursor/skills/` 或 `colcon`/`package.xml` 的仓库根（用户打开的根目录）。  
2. 所有路径 = `工作区根` + 上表相对路径。  
3. 若用户消息中指定了论文目录（如「论文在 `thesis/ch1`」），则以用户为准覆盖 `PAPER1_ROOT`。
