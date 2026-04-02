from __future__ import annotations

import sys
import time
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parents[1]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

import bot_logger
from AI.DummyAI import DummyAI
from Controller.MTGAController.Controller import Controller
from Game import Game
from licensing.validator import require_license_or_block
from ui import ConfigManager, _app_path
from vision.window_locator import run_arena_setup_check


def main() -> int:
    license_result = require_license_or_block()
    if not license_result.valid:
        print(f"License check failed [{license_result.code}]: {license_result.message}")
        return 1

    config_manager = ConfigManager()
    result = run_arena_setup_check(
        assets_dir=_app_path("assets", "assert"),
        expected_size=(1920, 1080),
        write_debug_on_fail=True,
    )
    if not result.ok:
        print(result.message)
        if result.debug_dir:
            print(f"Debug bundle: {result.debug_dir}")
        return 1

    log_path = config_manager.get_log_path()
    click_targets = config_manager.get_click_targets()
    screen_bounds = config_manager.get_screen_bounds()
    input_backend = config_manager.get_input_backend()
    account_switch_minutes = config_manager.get_account_switch_minutes()
    account_cycle_index = config_manager.get_account_cycle_index()
    account_play_order = config_manager.get_account_play_order()

    bot_logger.log_info(
        "UI-path runner: init controller log_path={} screen_bounds={} input_backend={} account_switch_minutes={}".format(
            log_path,
            screen_bounds,
            input_backend,
            account_switch_minutes,
        )
    )

    controller = Controller(
        log_path=log_path,
        screen_bounds=screen_bounds,
        click_targets=click_targets,
        input_backend=input_backend,
        account_switch_minutes=account_switch_minutes,
        account_cycle_index=account_cycle_index,
        account_play_order=account_play_order,
    )
    ai = DummyAI()
    game = Game(controller, ai)
    bot_logger.log_info("UI-path runner: game.start() begin")
    game.start()
    bot_logger.log_info("UI-path runner: game.start() completed")

    try:
        while True:
            time.sleep(1.0)
    except KeyboardInterrupt:
        pass
    finally:
        try:
            game.stop()
        except Exception:
            pass
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
