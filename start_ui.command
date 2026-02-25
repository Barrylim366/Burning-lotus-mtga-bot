#!/bin/bash
set -euo pipefail

REPO_DIR="$(cd "$(dirname "$0")" && pwd)"
VENV_DIR="$REPO_DIR/.venv-macos"
PYTHON_BIN="${PYTHON_BIN:-python3}"
VENV_PYTHON="$VENV_DIR/bin/python"

alert_warning() {
  local msg="$1"
  osascript -e "display alert \"Burning Lotus Bot\" message \"$msg\" as warning" >/dev/null 2>&1 || true
  echo "$msg" >&2
}

if ! command -v "$PYTHON_BIN" >/dev/null 2>&1; then
  alert_warning "Python 3 nicht gefunden. Bitte Python 3 installieren."
  exit 1
fi

if [ ! -d "$VENV_DIR" ]; then
  "$PYTHON_BIN" -m venv "$VENV_DIR" || {
    alert_warning "Konnte virtuelle Umgebung nicht erstellen: $VENV_DIR"
    exit 1
  }
fi

if [ ! -x "$VENV_PYTHON" ]; then
  alert_warning "Python venv fehlt: .venv-macos/bin/python"
  exit 1
fi

if ! "$VENV_PYTHON" -m pip show pynput pyautogui opencv-python pillow cryptography >/dev/null 2>&1; then
  "$VENV_PYTHON" -m pip install --upgrade pip || {
    alert_warning "Konnte pip in .venv-macos nicht aktualisieren."
    exit 1
  }
  "$VENV_PYTHON" -m pip install pynput pyautogui opencv-python pillow cryptography || {
    alert_warning "Konnte erforderliche Pakete nicht installieren."
    exit 1
  }
fi

cd "$REPO_DIR"
exec "$VENV_PYTHON" ui.py
