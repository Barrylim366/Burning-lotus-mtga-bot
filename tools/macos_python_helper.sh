#!/bin/bash

python_version() {
  local python_bin="$1"
  "$python_bin" -c 'import sys; print(f"{sys.version_info.major}.{sys.version_info.minor}")'
}

python_has_tk() {
  local python_bin="$1"
  "$python_bin" -c "import tkinter" >/dev/null 2>&1
}

resolve_python_candidate() {
  local candidate="$1"
  if [[ "$candidate" == */* ]]; then
    if [ -x "$candidate" ]; then
      printf '%s\n' "$candidate"
      return 0
    fi
    return 1
  fi
  command -v "$candidate" 2>/dev/null
}

select_macos_python() {
  local resolved=""
  local candidate=""

  if [ -n "${PYTHON_BIN:-}" ]; then
    resolved="$(resolve_python_candidate "$PYTHON_BIN" || true)"
    if [ -z "$resolved" ]; then
      echo "Configured PYTHON_BIN not found: $PYTHON_BIN" >&2
      return 1
    fi
    if python_has_tk "$resolved"; then
      printf '%s\n' "$resolved"
      return 0
    fi
    echo "Configured PYTHON_BIN has no tkinter support: $resolved" >&2
    return 1
  fi

  for candidate in \
    "/usr/local/opt/python@3.13/bin/python3.13" \
    "/opt/homebrew/opt/python@3.13/bin/python3.13" \
    "python3.13" \
    "python3"; do
    resolved="$(resolve_python_candidate "$candidate" || true)"
    if [ -n "$resolved" ] && python_has_tk "$resolved"; then
      printf '%s\n' "$resolved"
      return 0
    fi
  done

  return 1
}

macos_python_install_hint() {
  if command -v brew >/dev/null 2>&1; then
    cat <<'EOF'
No supported Python with tkinter was found.

Supported macOS path:
  brew install python@3.13 python-tk@3.13

Then run ./start_ui.command again.
Alternative: install Python 3.13 from python.org.
EOF
    return
  fi

  cat <<'EOF'
No supported Python with tkinter was found.

Install Python 3.13 with tkinter support, then run ./start_ui.command again.
Recommended: Python 3.13 from python.org.
EOF
}
