#!/usr/bin/env bash
# Idempotent: make a harness commands folder a link to ~/.agents/commands (whole-folder link, so new commands are shared at once).
#   Windows (Git Bash/MSYS): directory junction via mklink /J (no admin rights needed)   macOS / Linux: ln -s
# Usage: link-commands.sh [target-commands-dir]   (default: ~/.claude/commands; OpenCode: ~/.config/opencode/commands)
# Refuses a target that holds real files: move them into ~/.agents/commands first.
# Rollback: Windows: cmd //c "rmdir $(cygpath -w <target>)"   |   macOS/Linux: rm <target>   (never touches the source)
set -euo pipefail
target="${1:-$HOME/.claude/commands}"; src="$HOME/.agents/commands"
[ -d "$src" ] || { echo "MISSING source: $src" >&2; exit 1; }
mkdir -p "$(dirname "$target")"
case "$(uname -s)" in
  MINGW*|MSYS*|CYGWIN*)
    if [ -e "$target" ]; then
      if cmd //c "dir /AL $(cygpath -w "$(dirname "$target")")" 2>/dev/null | grep -q "<JUNCTION> *$(basename "$target") "; then echo "ok (already linked) $target"; exit 0; fi
      [ -z "$(ls -A "$target")" ] && cmd //c "rmdir $(cygpath -w "$target")" || { echo "SKIP: $target has real files; move them to $src first" >&2; exit 2; }
    fi
    cmd //c "mklink /J $(cygpath -w "$target") $(cygpath -w "$src")" >/dev/null && echo "linked $target" ;;
  *)
    if [ -L "$target" ]; then [ "$(readlink "$target")" = "$src" ] && { echo "ok (already linked) $target"; exit 0; }; echo "SKIP: $target links elsewhere" >&2; exit 2; fi
    if [ -d "$target" ]; then [ -z "$(ls -A "$target")" ] && rmdir "$target" || { echo "SKIP: $target has real files; move them to $src first" >&2; exit 2; }; fi
    ln -s "$src" "$target" && echo "linked $target" ;;
esac
