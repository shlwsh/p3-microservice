#!/bin/bash
# WSL 调用 Windows Git Credential Manager（路径含空格，供 git -c credential.helper 使用）

GCM_EXE="/mnt/c/Program Files/Git/mingw64/bin/git-credential-manager.exe"

if [[ -x "$GCM_EXE" ]]; then
  exec "$GCM_EXE" "$@"
fi

echo "git-credential-gcm.sh: GCM not available (non-WSL or Windows Git not installed)" >&2
exit 1
