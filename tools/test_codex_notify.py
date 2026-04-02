from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parents[1]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from Controller.Utilities.input_controller import create_input_controller
from tools.bot_supervisor import notify_codex
from vision.vision import VisionEngine


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Test only the Codex stuck notifier.")
    parser.add_argument(
        "--template",
        default=str(ROOT_DIR / "codex_window.png"),
        help="Path to the Codex chat input template image.",
    )
    parser.add_argument(
        "--input-backend",
        default="auto",
        help="Input backend to use (auto, pynput, pyautogui, ...).",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    payload = notify_codex(
        input_controller=create_input_controller(args.input_backend),
        vision=VisionEngine(),
        template_path=str(args.template),
    )
    print(json.dumps(payload, indent=2))
    return 0 if payload.get("ok") else 1


if __name__ == "__main__":
    raise SystemExit(main())
