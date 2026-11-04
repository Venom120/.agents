#!/usr/bin/env bash
# Idempotent: make <target-dir>/<skill> a link to ~/.agents/skills/<skill>.
#   Windows (Git Bash/MSYS): directory junction via mklink /J (no admin rights needed)
#   macOS / Linux:           symbolic link via ln -s
# Usage: link-skill.sh <skill-name> [target-skills-dir]   (default target: ~/.claude/skills)
# Rollback: Windows: cmd //c "rmdir $(cygpath -w <link>)"   |   macOS/Linux: rm <link>   (never touches the source)
set -euo pipefail
skill="$1"; target="${2:-$HOME/.claude/skills}"
src="$HOME/.agents/skills/$skill"
[ -d "$src" ] || { echo "MISSING source: $src" >&2; exit 1; }
mkdir -p "$target"
link="$target/$skill"
case "$(uname -s)" in
  MINGW*|MSYS*|CYGWIN*)
    if [ -e "$link" ] || [ -L "$link" ]; then
      if cmd //c "dir /AL $(cygpath -w "$target")" 2>/dev/null | grep -q "<JUNCTION> *$skill "; then echo "ok (already linked) $skill"; exit 0; fi
      echo "SKIP $skill: $link exists and is not a junction" >&2; exit 2
    fi
    cmd //c "mklink /J $(cygpath -w "$link") $(cygpath -w "$src")" >/dev/null && echo "linked $skill" ;;
  *)
    if [ -L "$link" ]; then
      [ "$(readlink "$link")" = "$src" ] && { echo "ok (already linked) $skill"; exit 0; }
      echo "SKIP $skill: $link is a symlink to another target" >&2; exit 2
    fi
    [ -e "$link" ] && { echo "SKIP $skill: $link exists and is not a symlink" >&2; exit 2; }
    ln -s "$src" "$link" && echo "linked $skill" ;;
esac
