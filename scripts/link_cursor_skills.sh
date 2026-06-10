#!/usr/bin/env bash
# 将 .agent/skills/ 完整镜像到 .cursor/skills/（逐项符号链接），使 Cursor 自动发现项目技能。
# 注：gitnexus 技能包由 `npx gitnexus analyze` 写入 .claude/skills/gitnexus/；
#     .agent/skills/gitnexus 为指向该目录的符号链接，本脚本会一并镜像到 .cursor/skills/。
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
SRC="$ROOT/.agent/skills"
DST="$ROOT/.cursor/skills"

if [[ ! -d "$SRC" ]]; then
  echo "错误: 未找到技能源目录 $SRC" >&2
  exit 1
fi

mkdir -p "$DST"

# 确保 gitnexus 技能包链接存在（权威目录：.claude/skills/gitnexus/）
GITNEXUS_SRC="$ROOT/.claude/skills/gitnexus"
GITNEXUS_LINK="$SRC/gitnexus"
if [[ -d "$GITNEXUS_SRC" ]]; then
  ln -sfn "../../.claude/skills/gitnexus" "$GITNEXUS_LINK"
fi

# 清空 .cursor/skills/，仅保留目录本身
shopt -s dotglob nullglob
for entry in "$DST"/*; do
  rm -rf "$entry"
done

linked=0
for entry in "$SRC"/*; do
  name="$(basename "$entry")"
  target="../../.agent/skills/$name"
  link="$DST/$name"
  ln -s "$target" "$link"
  echo "→ $name"
  linked=$((linked + 1))
done

echo ""
echo "已链接 $linked 项 → .cursor/skills/（与 .agent/skills/ 一致）"
echo "重启 Cursor 或新开 Agent 会话后生效。"
