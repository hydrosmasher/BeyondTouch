#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")"
if [[ -n "${BEYONDTOUCH_PYTHON:-}" ]]; then
    task_python="$BEYONDTOUCH_PYTHON"
elif command -v python3.12 >/dev/null 2>&1; then
    task_python="$(command -v python3.12)"
elif [[ -x "$HOME/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/bin/python3" ]]; then
    task_python="$HOME/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/bin/python3"
elif command -v python3 >/dev/null 2>&1 && python3 -c 'import sys;sys.exit(sys.version_info[:2]!=(3,12))'; then
    task_python="$(command -v python3)"
else
    echo "Python 3.12 is needed only to recalculate. Install it from python.org, then rerun."
    echo "To view all 12 saved examples without installing anything, open START_HERE.html."
    exit 2
fi
exec "$task_python" src/run.py "$@"
