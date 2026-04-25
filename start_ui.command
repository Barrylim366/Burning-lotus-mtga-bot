#!/bin/bash
set -euo pipefail

REPO_DIR="$(cd "$(dirname "$0")" && pwd)"
VENV_DIR="$REPO_DIR/.venv-macos"
VENV_PYTHON="$VENV_DIR/bin/python"
REQ_FILE="$REPO_DIR/requirements.txt"
MARKER="$VENV_DIR/.requirements.installed"
HELPER_FILE="$REPO_DIR/tools/macos_python_helper.sh"

alert_warning() {
  local msg="$1"
  osascript -e "display alert \"Burning Lotus Bot\" message \"$msg\" as warning" >/dev/null 2>&1 || true
  echo "$msg" >&2
}

if [ ! -f "$HELPER_FILE" ]; then
  alert_warning "Hilfsdatei fehlt: tools/macos_python_helper.sh"
  exit 1
fi

# shellcheck source=/dev/null
. "$HELPER_FILE"

backup_venv() {
  local backup_dir="$REPO_DIR/.venv-macos-backup-$(date +%Y%m%d-%H%M%S)"
  mv "$VENV_DIR" "$backup_dir"
}

venv_has_tk() {
  [ -x "$VENV_PYTHON" ] && "$VENV_PYTHON" -c "import tkinter" >/dev/null 2>&1
}

SELECTED_PYTHON="$(select_macos_python || true)"
if [ -z "$SELECTED_PYTHON" ]; then
  alert_warning "$(macos_python_install_hint)"
  exit 1
fi

if [ -d "$VENV_DIR" ] && ! venv_has_tk; then
  backup_venv
fi

if [ ! -d "$VENV_DIR" ]; then
  "$SELECTED_PYTHON" -m venv "$VENV_DIR" || {
    alert_warning "Konnte virtuelle Umgebung nicht erstellen: $VENV_DIR"
    exit 1
  }
fi

if [ ! -x "$VENV_PYTHON" ]; then
  alert_warning "Python venv fehlt: .venv-macos/bin/python"
  exit 1
fi

if ! venv_has_tk; then
  alert_warning "Die virtuelle Umgebung hat keine tkinter-Unterstuetzung. Bitte .venv-macos loeschen und den Launcher erneut starten."
  exit 1
fi

if [ ! -f "$MARKER" ] || [ "$REQ_FILE" -nt "$MARKER" ]; then
  "$VENV_PYTHON" -m pip install --upgrade pip || {
    alert_warning "Konnte pip in .venv-macos nicht aktualisieren."
    exit 1
  }
  "$VENV_PYTHON" -m pip install -r "$REQ_FILE" || {
    alert_warning "Konnte erforderliche Pakete nicht installieren."
    exit 1
  }
  touch "$MARKER"
fi

cd "$REPO_DIR"
exec "$VENV_PYTHON" ui.py
