"""Simple Tkinter launcher to start/stop the MTGA bot."""
from __future__ import annotations

import subprocess
import sys
from argparse import ArgumentParser
import os
import tkinter as tk
from pathlib import Path
from typing import Optional

# Path to the config used to start the bot; adjust if needed.
DEFAULT_CONFIG = "config.json"
LOG_PATH = "bot_gui_subprocess.log"


class BotController:
    def __init__(self, base_dir: Path, status_var: tk.StringVar) -> None:
        self.base_dir = base_dir
        self.status_var = status_var
        self.process: Optional[subprocess.Popen] = None
        self._log_handle = None

    def start_bot(self) -> None:
        if self.process and self.process.poll() is None:
            self.status_var.set("Bot already running.")
            return

        env = os.environ.copy()
        env["PYTHONUNBUFFERED"] = "1"

        if getattr(sys, "frozen", False):
            # When packaged (e.g., PyInstaller), reuse the same executable with a bot-only flag.
            cmd = [sys.executable, "--run-bot", "--config", DEFAULT_CONFIG]
        else:
            # Prefer the repo's virtualenv python if present.
            venv_python = self._find_venv_python()
            interpreter = venv_python or sys.executable
            cmd = [
                interpreter,
                "-m",
                "mtga_bot.main",
                "--config",
                DEFAULT_CONFIG,
            ]
        try:
            self._log_handle = Path(self.base_dir / LOG_PATH).open("a", encoding="utf-8")
            log_path = Path(self.base_dir / LOG_PATH).resolve()
            self.process = subprocess.Popen(
                cmd,
                cwd=self.base_dir,
                stdout=self._log_handle,
                stderr=subprocess.STDOUT,
                env=env,
            )
            self.status_var.set(
                f"Bot started. Using {cmd[0]} | Logs -> {log_path}"
            )
            # If the process exits immediately, surface the return code.
            self.process.poll()
            if self.process.returncode is not None:
                self.status_var.set(
                    f"Bot exited immediately (code {self.process.returncode}). Check logs -> {log_path}"
                )
        except Exception as exc:
            self.process = None
            if self._log_handle:
                self._log_handle.close()
                self._log_handle = None
            self.status_var.set(f"Failed to start bot: {exc}")

    def stop_bot(self) -> None:
        if not self.process:
            self.status_var.set("Bot is not running.")
            return
        if self.process.poll() is not None:
            self.status_var.set("Bot already stopped.")
            self.process = None
            return
        try:
            self.process.terminate()
            self.process.wait(timeout=5)
            self.status_var.set("Bot stopped.")
        except Exception as exc:
            self.status_var.set(f"Failed to stop bot: {exc}")
        finally:
            self.process = None
            if self._log_handle:
                try:
                    self._log_handle.close()
                except Exception:
                    pass
                self._log_handle = None

    def _find_venv_python(self) -> Optional[str]:
        posix_path = self.base_dir / ".venv" / "bin" / "python"
        windows_path = self.base_dir / ".venv" / "Scripts" / "python.exe"
        if posix_path.exists():
            return str(posix_path)
        if windows_path.exists():
            return str(windows_path)
        return None


def create_window(base_dir: Path) -> tk.Tk:
    window = tk.Tk()
    window.title("MTGA Bot Launcher")

    status_var = tk.StringVar(value="Idle.")
    controller = BotController(base_dir, status_var)

    tk.Label(window, text="MTGA Bot Launcher").pack(pady=(10, 5))

    button_frame = tk.Frame(window)
    button_frame.pack(pady=5)

    tk.Button(button_frame, text="Start Bot", width=12, command=controller.start_bot).pack(
        side=tk.LEFT, padx=5
    )
    tk.Button(button_frame, text="Stop Bot", width=12, command=controller.stop_bot).pack(
        side=tk.LEFT, padx=5
    )

    tk.Label(window, textvariable=status_var, fg="blue").pack(pady=(5, 10))

    def on_close() -> None:
        controller.stop_bot()
        window.destroy()

    window.protocol("WM_DELETE_WINDOW", on_close)
    return window


def parse_args() -> ArgumentParser:
    parser = ArgumentParser(description="MTGA bot GUI launcher")
    parser.add_argument(
        "--run-bot",
        action="store_true",
        help="Internal flag: run the bot CLI instead of the GUI.",
    )
    parser.add_argument(
        "--config",
        default=DEFAULT_CONFIG,
        help="Path to config JSON (used with --run-bot).",
    )
    return parser


def main() -> None:
    parser = parse_args()
    args = parser.parse_args()

    if args.run_bot:
        # Run the bot directly (no GUI) when invoked with --run-bot.
        from mtga_bot.main import run_bot  # Local import to keep GUI light.

        run_bot(Path(args.config).expanduser())
        return

    if getattr(sys, "frozen", False):
        base_dir = Path(sys.executable).resolve().parent
    else:
        base_dir = Path(__file__).resolve().parent
    window = create_window(base_dir)
    window.mainloop()


if __name__ == "__main__":
    main()
