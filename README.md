# MTGA Bot

Automated MTGA bot with UI, calibration, account switching, and quest-based deck selection.

## Requirements

- Windows 10/11
- Python 3.10+
- MTG Arena installed (Steam)
- Python packages:
  - pyautogui
  - opencv-python (needed for image matching confidence)
  - pillow
  - pynput

Install packages:

```
pip install pyautogui opencv-python pillow pynput
```

## Quick Start

1) Start the UI:

```
python ui.py
```

2) Calibrate buttons via **Calibrate**:
   - Required: keep_hand, queue_button, next, concede, attack_all, opponent_avatar, hand_scan_p1, hand_scan_p2, assign_damage_done
   - Logout flow uses: log_out_btn, log_out_ok_btn

3) Settings:
   - **Switch account (min)**: minutes until switch; 0 disables.
   - **Account Play Order**: order of Acc_1/Acc_2/Acc_3. Empty entries are ignored.
   - **Record Action**: record account switch flow (uses F8 to stop recording).
   - **Show Records**: review/test/delete recorded actions.

4) Start Bot.

Stop bot any time with **Mouse Wheel Down**.

## Account Switching

- Accounts are defined in `credentials.txt` (do not commit secrets).
- Switch happens when the timer expires and the bot reaches a safe screen.
- Logout/login uses recorded action sequence + credentials injection.
- Order follows **Account Play Order** in Settings; if empty, default order is used.

## Quest-Based Deck Selection

After account switch the bot:
1) clicks Play -> Find Match -> Historic Play -> My Decks (image matching)
2) parses quests from `Player.log`
3) selects a deck image from `Acc_1/Acc_2/Acc_3` folder that best matches quest colors

Deck images are matched by filename letters (e.g. `RG.png`, `WU.png`, `R.png`).

## Card Data Updates

On startup:
- MTGA card DB export refreshes `cards.json` if the local MTGA data changed.
- Scryfall bulk delta check fetches new Arena IDs and merges missing cards.

Fallback:
- `missing_cards.json` tracks cards encountered in matches but not in `cards.json`.

## Logs

- `bot.log` – main bot debug
- `human.log` – high-level actions
- `bot_gui_subprocess.log` – UI subprocess log (if used)

