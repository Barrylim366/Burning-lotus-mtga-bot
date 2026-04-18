#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
VENV_DIR="$ROOT_DIR/.venv"
PYTHON_BIN="${PYTHON_BIN:-python3}"
VENV_PYTHON="$VENV_DIR/bin/python"
REQ_FILE="$ROOT_DIR/requirements.txt"
MARKER="$VENV_DIR/.requirements.installed"

if ! command -v "$PYTHON_BIN" >/dev/null 2>&1; then
  echo "[ERROR] $PYTHON_BIN nicht gefunden. Bitte Python 3.10 oder neuer installieren." >&2
  exit 1
fi

if [[ ! -d "$VENV_DIR" ]]; then
  echo "[INFO] Erstelle virtuelle Umgebung in $VENV_DIR"
  "$PYTHON_BIN" -m venv "$VENV_DIR"
fi

if [[ ! -x "$VENV_PYTHON" ]]; then
  echo "[ERROR] Venv-Python nicht gefunden: $VENV_PYTHON" >&2
  exit 1
fi

if [[ ! -f "$MARKER" || "$REQ_FILE" -nt "$MARKER" ]]; then
  echo "[INFO] Installiere Abhaengigkeiten aus requirements.txt"
  "$VENV_PYTHON" -m pip install --upgrade pip
  "$VENV_PYTHON" -m pip install -r "$REQ_FILE"
  touch "$MARKER"
fi

exec "$VENV_PYTHON" "$ROOT_DIR/ui.py"
