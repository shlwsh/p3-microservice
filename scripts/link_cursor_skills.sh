#!/usr/bin/env bash
# 将 .agent/skills/ 链接到 .cursor/skills/，使 Cursor Agent 自动发现项目技能。
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
SRC="$ROOT/.agent/skills"
DST="$ROOT/.cursor/skills"

mkdir -p "$DST"

linked=0
for skill_dir in "$SRC"/*/; do
  [ -f "${skill_dir}SKILL.md" ] || continue
  name="$(basename "$skill_dir")"
  target="../../.agent/skills/$name"
  link="$DST/$name"

  if [ -L "$link" ]; then
    current="$(readlink "$link")"
    if [ "$current" = "$target" ]; then
      echo "✓ $name (已链接)"
      linked=$((linked + 1))
      continue
    fi
    rm "$link"
  elif [ -e "$link" ]; then
    echo "⚠ 跳过 $name：$link 已存在且非符号链接" >&2
    continue
  fi

  ln -s "$target" "$link"
  echo "→ $name"
  linked=$((linked + 1))
done

echo ""
echo "已链接 $linked 个技能 → .cursor/skills/"
echo "重启 Cursor 或新开 Agent 会话后生效。"
