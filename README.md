# Burning Lotus Bot
<img width="429" height="823" alt="githubscreen" src="https://github.com/user-attachments/assets/ac3ec57b-45de-4a22-aebe-0bcb3db90ae0" />

Automated MTGA bot for daily quests and win rewards. Supports multiple accounts, quest-based deck selection, and runs on Windows, macOS, and Linux from a single codebase. Feel free to inspect the code, request a feature, or report a bug via GitHub Issues or open a pull request.

## Requirements

- **OS**: Windows 10/11, macOS 12+, or Linux (X11 or Wayland; tested on Debian and CachyOS)
- **Python**: 3.10+
- **MTG Arena**: installed and running
  - Windows: Steam or Wizards installer
  - macOS: Crossover or compatible Wine layer
  - Linux: Wine/Proton via Steam or Lutris

Python dependencies are installed automatically by the launcher scripts:

| Package | Purpose |
|---|---|
| `pyautogui` | Mouse/keyboard input (default backend) |
| `pynput` | Global input listener (hotkeys, macro recording) |
| `mss` | Fast screen capture |
| `opencv-python` | Template matching |
| `Pillow` | UI rendering |
| `numpy` | Numerical arrays (shared data format between mss and OpenCV) |

### Required MTGA settings (all platforms)

- `Options -> View Account -> Detailed Logs (Plugin Support)`: **ON** *(required — the bot reads `Player.log` as its primary state source)*
- `Options -> Video -> Language`: **English**
- `Options -> Video -> Display Mode`: **Windowed**
- `Options -> Video -> Resolution`: **any exact 16:9 windowed size**
- OS display scaling: **100%**

## Quick Start

Each platform has a launcher script that creates a virtual environment, installs dependencies, and starts the UI.

### Windows

1. Install Python 3.10+ from python.org (tick "Add python.exe to PATH").
2. Double-click `start_ui.bat`.

### macOS

1. Install Python 3.13 (recommended):
   - python.org installer, **or**
   - `brew install python@3.13 python-tk@3.13`
2. Optional preflight check: `./doctor.command`
3. Double-click `start_ui.command` (or run `./start_ui.command` in Terminal).
4. Grant permissions to the Terminal app **and** the Python binary inside `.venv-macos`:
   - `System Settings -> Privacy & Security -> Accessibility`
   - `System Settings -> Privacy & Security -> Screen Recording`

### Linux

1. Install Python 3.10+ and OS-level packages:

   | Purpose | Arch / CachyOS | Debian / Ubuntu | Fedora | openSUSE |
   |---|---|---|---|---|
   | tkinter UI | `tk` | `python3-tk` | `python3-tkinter` | `python3-tk` |
   | MTGA window detection | `xorg-xwininfo` | `x11-utils` | `xorg-x11-utils` | `xwininfo` |
   | Screenshot (KDE) | `spectacle` | `kde-spectacle` | `spectacle` | `spectacle` |
   | Screenshot (GNOME) | `gnome-screenshot` | `gnome-screenshot` | `gnome-screenshot` | `gnome-screenshot` |
   | Screenshot (wlroots/Sway/Hyprland) | `grim` | `grim` | `grim` | `grim` |
   | Screenshot (X11 fallback) | `scrot` | `scrot` | `scrot` | `scrot` |

   The launcher warns if any required package is missing and prints the exact install command for your distro.

2. Run `./start_ui.sh`.

3. MTGA must run through Wine/Proton (Steam or Lutris). Under Wayland it goes through XWayland automatically.

### Manual start (any platform)

```bash
python -m venv .venv
.venv/bin/pip install -r requirements.txt   # Windows: .venv\Scripts\pip
.venv/bin/python ui.py                       # Windows: .venv\Scripts\python ui.py
```

## Configuration

### Input backend

The bot auto-selects the best available input backend per platform:

| Platform | Default | Fallback |
|---|---|---|
| Linux | `ydotool` (if installed) | `pynput` |
| macOS | `pyautogui` | `pynput` |
| Windows | `pyautogui` | `pynput` |

Override via environment variable: `MTGA_BOT_INPUT_BACKEND=auto|pyautogui|pynput|ydotool`

`ydotool` requires `ydotoold` daemon to be running and is recommended for Linux Wayland sessions.

### Calibration (optional)

The bot locates the MTGA window automatically on startup — no manual calibration needed in most cases.

Use **Settings → Calibrate** only if the bot repeatedly fails to click the right spots. Calibration captures 1920x1080-relative coordinates and maps them to the actual window position at runtime.

## Features

### Account Switching

Accounts are stored as folders under `Accounts/` (gitignored by default):

```
Accounts/
  MyAccount/
    credentials.json   →   { "MyAccount": { "email": "...", "pw": "..." } }
  AltAccount/
    credentials.json
```

Manage accounts via **Settings → Manage Accounts**. Set a switch timer and play order. When the timer expires and the bot is at a safe screen, it logs out, switches account, and resumes.

### Quest-Based Deck Selection

After each account switch the bot picks a deck based on active quests. Place deck screenshot images in the account folder named by color letters:

- `RG.png`, `WU.png`, `B.png`, `R.png` etc. — matched to quest colors
- `C.png` — used for creature-type quests
- Random fallback if no quest matches

### Casting Logic

The bot maximizes mana usage each turn:
- Prefers the highest-value spell(s) that spend the most mana
- Respects color requirements and discounted costs
- Type priority when CMC is tied: creature → instant → sorcery → enchantment
- Supports Convoke (untapped creatures as mana sources)

### Stopping the bot

Scroll **Mouse Wheel down** at any time to stop the bot immediately.

## Architecture

The codebase is split into clearly separated layers:

```
ui.py / run_bot.py          ← Entry points (UI or CLI)
        │
        ▼
    Game.py                 ← Session manager: connects Controller and AI,
                              handles match lifecycle (start → end → restart)
        │
   ┌────┴────┐
   ▼         ▼
Controller   DummyAI        ← AI decides what to play (generate_move / generate_keep)
   │
   ├── LogReader            ← Reads Player.log continuously, parses GRE messages
   ├── state_machine        ← Tracks bot state: HOME / IN_GAME / PLAY_MENU / ...
   ├── actions              ← Declarative action specs (navigate, click, verify)
   ├── vision               ← Screen capture (mss) + template matching (OpenCV)
   │    └── window_locator  ← Finds the MTGA window (Win32 / xwininfo / anchor search)
   └── input_controller     ← Sends mouse/keyboard input (pyautogui / pynput / ydotool)
```

**Key design principle:** `Player.log` is the primary state source — the bot reads what MTGA reports rather than inferring state from screenshots. Vision is used only to verify that clicks landed and to locate buttons when coordinates are uncertain.

**Card data** (`AI/Utilities/CardInfo.py`) is loaded from a local export of MTGA's own card database and delta-synced with the Scryfall API for missing entries.

Both `Controller` and `AI` follow an interface pattern (`ControllerInterface.py` / `AIInterface.py`) that decouples `Game.py` from the concrete implementations — making it straightforward to swap in a different AI or add a non-MTGA controller.

## Logs & Troubleshooting

| File | Location | Purpose |
|---|---|---|
| `bot.log` | `runtime/logs/bot.log` | Main bot debug log |
| `Player.log` | Auto-detected per OS (see below) | MTGA game log — primary state source |

`Player.log` default paths:
- **Windows**: `C:/Users/<YourUser>/AppData/LocalLow/Wizards Of The Coast/MTGA/Player.log`
- **macOS**: `~/Library/Logs/Wizards Of The Coast/MTGA/Player.log`
- **Linux/Proton**: `~/.local/share/Steam/steamapps/compatdata/2141910/pfx/drive_c/users/steamuser/AppData/LocalLow/Wizards Of The Coast/MTGA/Player.log`

If auto-detection fails, the UI prompts for a manual file selection on startup.

When something goes wrong the bot saves debug bundles under `runtime/debug/<timestamp>/` containing screenshots, the log tail, and a state dump. The entire `runtime/` tree is gitignored.

## See also on
[elitepvpers](https://www.elitepvpers.com/)
