#!/usr/bin/env bash
set -euo pipefail

if [[ $# -eq 0 ]]; then
  echo "Usage: scripts/node-run.sh <script-or-cli> [args...]" >&2
  exit 2
fi

is_supported() {
  local bin="$1"
  local major
  major="$("$bin" -p "process.versions.node.split('.')[0]" 2>/dev/null || true)"
  [[ "$major" =~ ^[0-9]+$ ]] && (( major >= 20 ))
}

pick_node() {
  local candidate
  if command -v node >/dev/null 2>&1; then
    candidate="$(command -v node)"
    if is_supported "$candidate"; then
      echo "$candidate"
      return 0
    fi
  fi

  while IFS= read -r candidate; do
    [[ -x "$candidate" ]] || continue
    if is_supported "$candidate"; then
      echo "$candidate"
      return 0
    fi
  done < <(ls -1d "$HOME"/.nvm/versions/node/v*/bin/node 2>/dev/null | sort -Vr)

  return 1
}

NODE_BIN="$(pick_node)" || {
  echo "No supported Node found (need >=20)." >&2
  exit 1
}

exec "$NODE_BIN" "$@"
