# Burning Lotus Bot
<img width="429" height="823" alt="githubscreen" src="https://github.com/user-attachments/assets/ac3ec57b-45de-4a22-aebe-0bcb3db90ae0" />


Automated MTGA bot for Quests and daylie wins with UI, account switching feature, and quest-based deck selection. Feel free to inspect the code, request a new feature/report a bug via Github Issue or open a pull request.
## Requirements

- **OS**: Windows 10/11, macOS 12+, or Linux (X11 or Wayland; tested on Debian and CachyOS)
- Python 3.10+
- MTG Arena installed (Windows: Steam / Wizards installer. macOS: Crossover or compatible. Linux: Wine/Proton via Steam or Lutris.)
- The launcher scripts install the Python packages from `requirements.txt` automatically (`pyautogui` for mouse/keyboard input, `pynput` as listener for user inputs, `numpy`, `Pillow` for UI things, `opencv-python` for template matching, `mss` as dedicated screenshot library).
- OS-/Python-level components are still your responsibility:
  - macOS: supported path is Python 3.13 with Tk support
  - Linux: `tkinter` plus the window-detection / screenshot tools listed below

MTGA in-game settings (required for all platforms):

- `Options -> View Account -> Detailed Logs (Plugin Support)`: **ON**
  *(the bot reads a`Player.log` for its primary state; with detailed logs off it will not function)*
- `Options -> Video -> Language`: **English**
- `Options -> Video -> Display Mode`: **Windowed**
- `Options -> Video -> Resolution`: **any exact 16:9 windowed size**
- OS display scaling: **100%**

Input backend:

- Default is `auto`.
- On macOS, `auto` prefers `pyautogui` (more stable than global `pynput` hooks).
- Optional override via env: `MTGA_BOT_INPUT_BACKEND=auto|pyautogui|pynput|ydotool`.

## Quick Start

The fastest path on each platform is the provided launcher. It creates a local virtual environment, installs the Python packages from `requirements.txt`, and starts the UI once the required OS-/Python-level dependencies are already present.

### Windows

1. Install Python 3.10+ from python.org (tick "Add python.exe to PATH").
2. Double-click `start_ui.bat`.

The script creates `.venv` and installs dependencies on first run.

### macOS

Supported macOS path: Python 3.13 with Tk.

1. Install one of these:
   - easiest supported path: Python 3.13 from python.org
   - Homebrew path: `brew install python@3.13 python-tk@3.13`
2. Optional preflight check: run `./doctor.command`.
3. Double-click `start_ui.command` (or run `./start_ui.command` in Terminal).
   - The launcher prefers Python 3.13 automatically when it is available.
   - If an old `.venv-macos` was created from a broken Python build without Tk, the launcher recreates it automatically.
4. macOS permission prompts — grant both to the **Terminal** app you launched from **and** to the Python binary inside `.venv-macos`:
   - `System Settings -> Privacy & Security -> Accessibility` (input control)
   - `System Settings -> Privacy & Security -> Screen Recording` (image matching)
5. If you want to override the interpreter manually, launch with `PYTHON_BIN=/path/to/python3.13 ./start_ui.command`.

### Linux

1. Install Python 3.10+ plus a few OS-level packages (the launcher warns if any are missing and prints the exact command for your distro):

   | Purpose | Arch / CachyOS | Debian / Ubuntu | Fedora | openSUSE |
   |---|---|---|---|---|
   | tkinter UI | `tk` | `python3-tk` | `python3-tkinter` | `python3-tk` |
   | MTGA window detection | `xorg-xwininfo` | `x11-utils` | `xorg-x11-utils` | `xwininfo` |
   | Screenshot (KDE) | `spectacle` | `kde-spectacle` | `spectacle` | `spectacle` |
   | Screenshot (GNOME) | `gnome-screenshot` | `gnome-screenshot` | `gnome-screenshot` | `gnome-screenshot` |
   | Screenshot (wlroots/Sway/Hyprland) | `grim` | `grim` | `grim` | `grim` |
   | Screenshot (X11 fallback) | `scrot` | `scrot` | `scrot` | `scrot` |

   On KDE/GNOME systems the screenshot tool is usually preinstalled. Install at least one matching your desktop.

2. Run the launcher:

   ```
   ./start_ui.sh
   ```

  On first run the script creates `.venv`, installs Python dependencies, and starts the UI once the listed Linux packages are installed.

3. MTGA must run through Wine/Proton (via Steam or Lutris). Under Wayland this goes through XWayland automatically, which is what the detection layer expects.

### Manual start (any platform)

If you prefer to manage the virtual environment yourself:

```
python -m venv .venv
.venv/bin/pip install -r requirements.txt      # Windows: .venv\Scripts\pip
.venv/bin/python ui.py                          # Windows: .venv\Scripts\python ui.py
```

Windows quick test for built-in account switch flow (without starting a full match loop manually):
- Double-click `test_logout_record.bat` in the repo root.
- It runs the current built-in full account-switch path from code (logout + login + post-login handling).
- For logout-only testing, run: `python tools/test_builtin_logout.py`
- The active controller flow in `Controller/MTGAController/Controller.py` again includes queue spam, post-match dismissal, and built-in account switching as one continuous runtime path.
- Account switching uses recorded logout replay first, then `ESC -> LOG_OUT_BTN -> LOG_OUT_OK_BTN` as fallback. Fallback targets are mapped through the detected `arena_region` so the sequence stays window-relative instead of clicking raw desktop coordinates.
- The account-switch flow now verifies logout via fresh `Player.log` login-screen markers before typing credentials. If logout does not actually reach the login screen, the switch aborts with a debug bundle instead of typing into the still-open home/options UI. The built-in fallback also retries visible `log_out_btn.png` / `okay_btn.png` templates before giving up.
- Post-match dismiss and other home/options UI actions now use the detected MTGA window center or the last good cached `arena_region` as fallback. This avoids raw desktop clicks like `(1280, 720)` when the Arena window is shifted on the monitor.
- Logout confirm (`OK`) no longer relies on full-screen `okay_btn.png` matching first. The mapped `log_out_ok_btn` click now has priority, and any image-based confirmation retry is limited to a small region around the expected dialog button to avoid false positives on the Home/Play button.
- The logout dialog buttons now use the same low-level click injection pattern as record playback (`move -> left_down -> left_up`) instead of the generic `left_click(1)` helper, because the confirm dialog was visibly hovered but sometimes did not register the click.

## UI Updates

The main window now uses a ttk-based dark theme with centralized design tokens in `MTGBotUI._build_ui_theme()`:
- Start page uses a full-canvas background image loaded from `images/background`
- Single accent color (`#C8141E`)
- System-first font stack (`Segoe UI Variable`/`Segoe UI`/`Inter`/`Arial`)
- UI scale is calculated automatically on each startup based on current screen resolution and applied to the main window and subwindows.
- Compact hierarchy: centered logo, title, and uniform button grid
- Main window/start title now reads `Burning Lotus`
- Main menu buttons are canvas-rendered (no ttk widget box) with rounded edges, subtle inner shadow, stronger visibility (rim/shadow/glow), and fixed body color `#3D130E` slightly more transparent
- Stop button enabled only while the bot runs
- Status shown as plain text (no box background, no border frame)
- No inner center card is rendered on the start page (logo/title/buttons are placed directly on the background)
- Stop button uses a subtle red background treatment
- Button focus outline is neutralized (no red focus ring on the last clicked button)
- Manage Accounts now uses the same background image source as the main UI (`images/background` / `images/background.png`)
- Manage Accounts panel colors now follow the main UI palette (`bg/surface/surface_2/border/text`) with a subtle pseudo-transparency blend against the background image
- Manage Accounts container borders were tuned from cool-blue to warm red tones; panel blend opacity was reduced for a lighter translucent look on the fire background
- Main menu keeps **Current Session** and **Settings** as the only submenu entries
- **Current Session** opens in the same submenu position logic as **Settings** (below main window, ~5 mm gap, aligned X)
- Current session stats (`X Min till Account Switch`, `Games played`, `Win`) were moved out of **Settings** into **Current Session**
- Settings window keeps the main menu visual language: same background image source, centered title, and canvas-rendered action buttons using the shared main button skins
- Settings window size/position follows submenu behavior (`460x430`, opens below main with ~5 mm gap, aligned to main window X)
- **Calibrate** now lives inside **Settings**
- Calibrate uses a background-scene layout like Settings/Record Actions (no large dark outer frame), keeps glow-style action buttons, and opens to the right of Settings with ~0.4 cm gap
- Calibrate follows a split `Capture` / `Verify` scene layout with a vertical divider, `Last Captured` coordinate card, dedicated `Status` card, and footer action row (`Saved Buttons`, `Back`)
- Calibrate remains a fallback path for manual coordinate capture when the automatic arena detection/verification path is not enough
- Current Session window was restyled to the same fire/main theme (background image, unified panel colors, styled Back button) and now opens aligned below the main window
- Current Session no longer uses a large dark container frame; stats and Back are rendered directly on the background scene, and the dark box-frame around Back was removed
- Current Session stats are now grouped inside a bordered feature-card (`#320a02` fill, `#ff9318` border) with title/body typography aligned to the provided feature-box style
- Current Session card was refined to only show the three session lines (title removed), with rounded corners and semi-transparent dark fill (~44% target opacity)
- Current Session now uses the non-rounded feature-card style again, with no card title and all three stat lines shown in yellow inside the bordered card
- Current Session stats-card background now uses RGBA alpha rendering (`(50,10,2,210)`) to match the Back button's translucent intensity more closely
- Fixed Current Session stats text anchoring so the first line is fully inside the card and no longer clipped at the top
- Record Actions window now matches Settings layout more closely: title/buttons are rendered directly on the background scene (no outer dark container), using the same canvas glow-button skins as the main/settings UI
- Record Actions background now refreshes on canvas resize to prevent bottom strip artifacts during first paint
- Record Actions now opens to the right of Settings with ~0.4 cm gap and the same window size (`460x430`), while still clamping to visible screen bounds
- `Show Records` window is now larger and resizable so per-record action buttons (`Test Action`, `Delete`) remain visible across UI scales.
- **Manage Accounts** was rebuilt to match the provided reference design (fire/red split layout)
- Manage Accounts now opens aligned below Settings and uses tuned action-button border styling consistent with the updated submenu look
- Manage Accounts outer shell frames were removed for the switch row, accounts wrapper, and play-order wrapper; only inner functional/table/widget frames remain
- Remaining dark outer blocks in Manage Accounts were removed by blending wrapper rows/labels with the background image so only intended interactive/table elements remain framed
- Manage Accounts was further flattened: table/details row borders and entry highlight frames were removed so the view reads mostly as text on background
- All six Manage Accounts action buttons now use the same shared submenu button style as the other windows (`Secondary.TButton`)
- Manage Accounts controls were flattened further: buttons are now text-only (no box), and combobox/input field borders were removed to eliminate remaining dark/red frame artifacts
- Manage Accounts buttons now use the same main UI glow-button styles (`Primary.TButton` for save actions, `Secondary.TButton` for neutral actions)
- Manage Accounts background patch blending for wrapper blocks/headings was removed to eliminate rectangular color artifacts on the fire background
- Manage Accounts rows now use subtle dark list cards with a clearer selected-row highlight instead of heavy section boxes
- Manage Accounts list rows/inputs were flattened further: row borders and input/dropdown frames are removed for a cleaner, less boxed appearance
- Manage Accounts account-row selection is now indicated by text emphasis/color instead of a framed row border
- Manage Accounts uses a clickable account table plus inline `Name` / `Email` / `Password` editor fields below the table instead of a separate side editor
- Manage Accounts now uses a canvas-first scene layout (like the main window) for titles/table text and button placement, removing large frame-based panel backgrounds
- Manage Accounts default window size was increased to `900x980` to avoid right/bottom clipping with the canvas layout
- Manage Accounts action buttons are now flat no-border buttons (no glow-frame outline) to remove remaining visible button borders
- Manage Accounts buttons are now canvas-rendered rounded dark-red translucent controls (matching the other windows' rounded behavior) while keeping the prior button size footprint
- Manage Accounts input fields (`Switch account`, `Name`, `Email`, `Password`) and `Remember password` checkbox now share the same dark-red control tone as the play-order dropdowns
- Fixed Manage Accounts entry rendering so those fields now actually use `entry_bg` (dark-red) instead of falling back to the window background
- Manage Accounts now includes two feature-style translucent group boxes (yellow border, dark-red RGBA fill) around the accounts list area and the account play-order area
- Manage Accounts no longer shows the `Active` marker and no longer includes the old right-side `Account Details` editor section
- Manage Accounts window width is now compact and sized to the left-side content area with a small margin
- Manage Accounts now has a dedicated top `Switch account` group box in the same yellow bordered translucent style as the other manage groups
- The top switch action button was renamed to `Save Time` and moved to the lower-left area inside that switch group box
- `Save Accounts` was moved up to sit fully inside the accounts group box, and the play-order group box was enlarged so `Save Order` and `Close` are fully inside
- Switch group height was increased and `Save Time` moved lower to avoid overlap with the switch label line
- Manage Accounts window was widened slightly and group boxes are now inset with more symmetric left/right spacing
- Saving accounts creates/updates one folder per account under `Accounts/` and writes `credentials.json` inside that folder
- Account credentials are no longer stored in `runtime/config/calibration_config.json`; `Manage Accounts` reloads them from the per-account `Accounts/<folder>/credentials.json` files
- Row selection is clickable; the selected row gets highlight and its values are editable in the inline detail fields below the table
- Password fields in **Manage Accounts** are masked (`*`) while typing
- `Save Row` updates the selected row in memory, `Save Accounts` persists all valid rows to config/folders
- Play order is now shown as a 5-slot priority list (dropdowns) under the table section
- Manage Accounts window width is auto-fitted to content with a small right margin
- The former global dark content wrapper around all Manage Accounts blocks was removed; sections are now laid directly on the background with only left padding
- The headings `Manage Accounts` and `Accounts (max 10)` are now plain text on background (their dark title containers were removed)
- Heading labels in Manage Accounts now use cropped background-image patches (no solid color fill) to avoid visible red/dark heading blocks
- Manage Accounts background refresh no longer runs continuously on `<Configure>`; heading/background patching is applied on startup to prevent layout drift
- Heading labels no longer use fixed character widths; a delayed final background patch refresh avoids clipped text and stale border artifacts
- Manage Accounts minimum window height was increased to `900` to keep the full content visible without bottom clipping
- Buttons were reverted to the classic UI styling and original color direction
- Main menu window size is fixed (width and height are both non-resizable)
- Main menu top-left corner is fixed at screen coordinates `x=18`, `y=24`; Settings follows the main window position
- Window icon (top-left title bar) now uses a small `images/ui_symbol.png` logo instead of a black placeholder box
- During bot startup, the UI shows an indeterminate loading bar with the label `Loading Carddata` until initialization finishes
- Fixed a startup regression in `ui.py` caused by a mismatched theme token in the loading bar style
- `Status: Stopped` now uses `#ffb02a`
- Main UI now includes a bottom footer bar with the `Keep Window on Top` checkbox; the bar is flush to the left/right/bottom edges, the checkbox is centered with a yellow `X` indicator, and it does not overlap with the startup `Loading Carddata` area
- Main UI top spacing was tightened by about 1 cm so the logo sits higher with less empty space above it

Standalone runnable UI example (single file): `burning_lotus_ui_example.py`.

### First Start Requirements (Out-of-the-Box Mode)

On first launch, the UI asks you to confirm these required settings:

- `Options -> View Account -> Detailed Logs (Plugin Support)`: **ON**
- `Options -> Video -> Language`: **English**
- `Options -> Video -> Display Mode`: **Windowed**
- `Options -> Video -> Resolution`: **any exact 16:9 windowed size**
- OS display scaling: **100%**

Once the platform prerequisites are installed, the bot can run without manual coordinate calibration using:

- **Player.log as primary state source** (`Log = State`)
- **Vision checks only as verification gates** (`Vision = Verify`)

The runtime tries to locate MTGA dynamically:

- First via OS window rectangle detection
  - Windows: Win32 client rectangle (no border-offset heuristics)
  - Linux: `xwininfo -tree -root` (works on X11 and XWayland / Wayland via Wine or Proton)
  - macOS and fallback: full-screen anchor template search
- Then verifies/fallbacks with visual anchor checks
- Stores a session `arena_region` and re-acquires it on repeated verification failures
- During combat, if live re-acquire fails briefly, the controller now reuses the last known good `arena_region` instead of sending blind desktop clicks
- During normal in-game hand interaction, the controller now also reuses the last known good `arena_region` if live re-acquire fails, so regular cast/play scans do not drop back to raw desktop coordinates mid-match
- During active `SelectN` / target-selection flows, the controller now also reuses the last known good `arena_region` if live re-acquire fails, so hand scans stay window-relative instead of falling back to raw desktop coordinates
- `AssignDamage Done` now first template-matches `Buttons/assign_damage_done.png` in the lower center of the detected arena and only falls back to the saved click target if the image click does not clear `Step_CombatDamage`; it still writes an `assign-damage-<timestamp>/` debug bundle with full-screen, arena crop, focus crop, and state JSON when damage assignment remains stuck
- Opponent avatar target selection uses the same direct 1920-relative mapping path as other calibrated points (`_map_abs_point_to_arena`), without avatar-specific fallback heuristics


2) Use **Settings -> Calibrate** only if manual coordinate fallback is needed:
   - **Optional** for normal usage.
   - Use this only as advanced/support fallback when repeated button verification fails.
   - Windows/Linux: calibration uses `pynput`.
   - macOS: calibration uses stable polling mode (no global `pynput` hook) with `Enter` to save and `Esc` to cancel.
   - Required: keep_hand, queue_button, next, concede, attack_all, opponent_avatar, hand_scan_p1, hand_scan_p2, assign_damage_done
   - Logout flow uses: log_out_btn, log_out_ok_btn

3) Current Session:
   - Opens a session window with live stats in green text:
     `X Min till Account Switch`, `Games played`, `Win`.

4) Settings:
   - **Manage Accounts** opens a window for:
     - **Switch account (min)**
     - Up to **10 accounts** (`Name`, `Email`, `Password`) with clickable row selection and inline detail fields below the table
     - **Account Play Order** (up to 10 positions)
   - Use **Save Row** to update the currently selected row in memory.
   - Use **Save Accounts** to create/update account folders and credentials JSONs.
   - Use **Save Order** to persist the play order.
   - **Record Action** opens a window for **Record** (uses F8 to stop) and **Show Records**.
     Saved records include per-action timestamps (`ts`) in `runtime/records/recorded_actions_records.json`.
  - Includes **Calibrate** and **User Interface** buttons.
  - Opening any Settings subwindow (**Manage Accounts**, **Record Action**, **Calibrate**, **User Interface**) temporarily replaces the Settings window at the same screen position.
  - **User Interface** opens a settings window with:
    - `UI Scale` slider (50%..120%)
    - `UI Scale` control is vertically centered/lower in the panel for clearer spacing
    - scale controls remain inside the highlighted yellow framed card (matching Current Session style)
  - On `Save`, UI scale is applied immediately in-app (no restart required).
  - Subwindow minimum sizes are now derived from actual visible content bounds to avoid clipping without forcing oversized windows.

5) Start Bot.
  - Before the bot starts, the app checks that MTGA is visible in a windowed exact `16:9` client area and that OS display scaling is `100%`.
   - On Linux, detection uses `xwininfo` (X11/XWayland) plus anchor verification. On Windows, it uses the Win32 client rectangle. On macOS, detection falls back to anchor-based full-screen search.
   - If that check fails, the app writes an Arena setup debug bundle with diagnostics and screenshots.

Stop bot any time with **Mouse Wheel**.

## Account Switching

- Accounts are managed via **Settings -> Manage Accounts**.
- Each account is saved in its own folder under `Accounts/` and includes `credentials.json` in this format:
  - `{ "<AccountName>": { "email": "...", "pw": "..." } }`
- `runtime/config/calibration_config.json` no longer stores managed account credentials; the UI reloads accounts by scanning the account folders.
- `Accounts/` is gitignored by default so local account folders are not pushed to GitHub.
- Switch happens when the timer expires and the bot reaches a safe screen.
- Logout/login uses recorded action sequence + credentials injection.
- If the client is in the Store scene during fallback logout, the bot logs the last scene and presses ESC twice to reach the options menu.
- SelectN stack/trigger selections are delayed while `pendingMessageCount > 0` or the bot is not the decision player to avoid hover spam.
- SelectN stack/trigger selections map ability instance IDs to their parent card IDs for hover-based selection when needed.
- Login wait before typing credentials: 5 seconds.
- Post-login wait before running the recorded action: 20 seconds.
- Order follows **Account Play Order** in Settings; the first entry is used as the next switch target.
  After each switch, the bot advances to the next entry in the list.
  Changing the order resets the cycle to the first entry.
  The cycle index is treated as the next position to use (not the last used one).

## Quest-Based Deck Selection

After account switch the bot:
1) clicks Play -> Find Match -> Historic Play -> My Decks (image matching)
2) parses quests from `Player.log`
3) selects a deck image from the switched account's folder that best matches quest colors
   - If no guild/color quest exists but a creature quest is present, it selects `C.png`
   - If no guild/color quest exists and `Quests/Quest_Fatal_Push` is active, it selects `B.png`
   - If no guild/color quest exists and `Quests/Quest_Raiding_Party` is active, it selects `C.png`
   - If no quests are available, it selects a random deck image
   - If a forced file (`B.png`/`C.png`) is not present, it falls back to the existing selection logic

Deck images are matched by filename letters (e.g. `RG.png`, `WU.png`, `R.png`).
Creature quests use `C.png`.
If the planned account deck image is not found after login, the bot retries deck selection
across other configured account folders and logs account/deck mismatches in `bot.log`.
`Buttons` is kept in Git, but its contents are ignored (see `.gitignore`). Keep your local images there.

## Casting Logic

In main phases the bot tries to use as much available mana as possible across all castable spells:
- Cast feasibility is based on effective action mana costs (`availableActions[].manaCost`), so discounted costs are respected correctly.
- It chooses casts that maximize total paid mana this turn.
- If multiple options spend the same total, it prefers a single higher-cost spell
  over multiple cheaper spells.
- If CMC is tied, it prefers: creature -> instant -> sorcery -> enchantment -> other.
- Multi-spell plans are validated against color requirements, not just CMC.
 - Convoke is supported using untapped creatures as colored mana sources.
- Heavily discounted high-mana-value spells are prioritized when castable.

## Decision Safety

The bot defers decisions while the game reports pending messages to avoid acting
mid-resolution or while the UI is still busy.
It also auto-confirms mana payment prompts when MTGA requests pay costs.
PayCosts prompts with non-mana cost selection (for example discard-a-card while casting)
are now handled directly via `GREMessageType_PayCostsReq` cost selection, instead of relying
only on `SelectNReq`.
When `GREMessageType_DeclareAttackersReq` arrives, any temporary pay-cost pause window is
cleared immediately so combat prompts are not blocked by stale pay-cost timing.
DeclareAttack prompts now arm a bounded combat-recovery fallback (`COMBAT_RECOVERY_ARMED`),
which can force `all_attack + submit` up to two times if the bot is still stuck on
`Phase_Combat / Step_DeclareAttack`.
Combat-recovery events are logged with explicit markers:
`COMBAT_RECOVERY_ARMED`, `COMBAT_RECOVERY_ATTEMPT`, `COMBAT_RECOVERY_CLEAR`.
If the bot is paused by a PayCosts prompt and no new game-state message arrives, it now
automatically retries the decision loop shortly after the pause window so `Next/Pass`
does not get stuck.
In main phases, decisions are also deferred while the stack contains objects.
If the bot is the decision player, `pendingMessageCount` is zero, and a `Pass` action is available, it will still resolve priority even with stack objects present.
On its own turn, the bot waits 2 seconds once per turn before starting actions like hovering, casting, or clicking.
SelectN prompts wait 3 seconds before the bot starts selecting cards.
While a SelectN selection is in progress, other decisions are paused to avoid extra clicks.
SelectN pauses and clears are logged in `bot.log` to trace when decisions resume.
SelectN submission is always attempted with a forced click, with retries logged if needed.
SelectN prompts pause decisions for a short window after submit, and retries are rate-limited to avoid duplicate submits while discards resolve.
If the local seat ID is temporarily unknown, stack resolution can still proceed when a Pass action is available.
SelectN submissions are only clicked when a selection is active, and the bot will retry submit if the selected card(s) remain in hand. It also retries the submit click a few times if the prompt doesn't advance. Hand-selection fallback scans above the hand are enabled only for discard prompts.
Resolution-based SelectN prompts use a double-click on the first attempt and allow retries even when `pendingMessageCount > 0`.
If the selected card remains in hand, resolution SelectN will re-select and re-submit a few times before giving up.
If `Buttons/submit_btn.png` exists, Submit clicks use image matching before falling back to the calibrated coordinate.
Resolution SelectN waits for the stack to clear before starting selection.
Discard (SelectN) prompts allow a single delayed retry when hand zone data is missing and avoid aggressive reselect loops.
SelectN pending-state clear is now robustly initialized before early abort branches, avoiding handler crashes during discard/stack prompts.
SelectN resolution waits for the stack to clear, but has a timeout to avoid indefinite stalls and clears on match end/reset.
If SelectN IDs are not in hand, the bot can now fall back to pending/stack item scanning.
Sacrifice-style SelectN prompts can now also select local battlefield permanents by hover-scanning the lower battlefield region instead of aborting when the requested IDs are not in hand.
Resolution SelectN only waits for stack-clear as a fallback now; if the request already points at concrete hand, prompt, or battlefield candidates, the controller proceeds immediately instead of burning the rope.
Failed battlefield SelectN scans write the same `debug/hand-select-<timestamp>/` bundle used for hand-scan failures so sacrifice prompts can be debugged from screenshots and state dumps.

Own timer ("sand clock") status is parsed from `Player.log` game-state timer data (only for
the local player seat, not opponent timers).
Timer transitions are logged as:
`MY_TIMER_START`, `MY_TIMER_WARNING`, `MY_TIMER_CRITICAL`, `MY_TIMER_STOP`.

## Card Data Updates

On startup:
- MTGA card DB export refreshes `runtime/cache/cards.json` if the local MTGA data changed.
- Raw card-data discovery supports common Linux Steam paths, macOS Steam install paths, and Windows Steam install paths.
- Scryfall bulk delta check fetches new Arena IDs and merges missing cards.
If `runtime/cache/cards.json` is missing on first run, it is seeded from the repo copy of `data/cards.json` or generated automatically.

Fallback:
- `runtime/cache/missing_cards.json` tracks cards encountered in matches but not in `runtime/cache/cards.json`.
- Other local cache files such as `scryfall_cache.json`, `scryfall_oracle_cache.json`, and `scryfall_bulk_metadata.json` also live under `runtime/cache/`.

## Logs

- `bot.log` - main bot debug
  - Stored at `runtime/logs/bot.log`
  - If writing there fails, logger falls back to local `./bot.log` without stopping the bot.
  - Full parsed game-state snapshots stay in `bot.log`; they are no longer echoed to process `stdout`.
  - The whole local `runtime/` tree is ignored in Git, including logs, cache files and debug bundles.
- `bot_gui_subprocess.log` - UI subprocess log (if used)
- `Player.log` default path (auto-detected):
  - macOS: `~/Library/Logs/Wizards Of The Coast/MTGA/Player.log`
  - Windows: `C:/Users/<YourUser>/AppData/LocalLow/Wizards Of The Coast/MTGA/Player.log`
  - Linux/Proton: `~/.local/share/Steam/steamapps/compatdata/2141910/pfx/drive_c/users/steamuser/AppData/LocalLow/Wizards Of The Coast/MTGA/Player.log`
- Startup validation now requires an existing `Player.log`:
  - UI startup prompts for manual file selection if auto-detection fails.
  - CLI startup (`run_bot.py`) exits early with a clear error if the file does not exist.
- Hover logs are suppressed by default and only enabled during selection scans.
- A one-line match summary is logged at match completion.
- Startup diagnostics now include:
  - `UI start: init controller ...`
  - `UI start: game.start() begin/completed`
  - `Queue target details` including target source, detected `arena_region`, configured `screen_bounds`, and configured click target.
  - Queue click selection is now template-first (`Buttons/play_btn.png` in MTGA ROI), then coordinate fallback.
  - 1920-only mode: loaded click targets must be 1920x1080 coordinates; non-1920 values are ignored and replaced with defaults.
  - Coordinate mapping is now direct 1920-relative inside `arena_region` (no legacy `screen_bounds` scaling and no queue-offset translation).
  - Mulligan clicks (`KEEP_HAND` / `MULLIGAN`) now log raw vs mapped target and are mapped relative to detected `arena_region`.
  - Opponent avatar targeting (`select_target` + retry offsets) now always maps calibrated `opponent_avatar` relative to detected `arena_region` (no absolute desktop click).
  - Opponent avatar targeting now first rebases legacy absolute coordinates via the calibrated `queue_button` anchor (reconstruct old window origin, then map to current arena), which matches the same relative-conversion principle used for other controls.
  - Logout fallback clicks (`LOG_OUT_BTN`, `LOG_OUT_OK_BTN`) now prefer mapping from a runtime `Play`-button template origin (detected before `ESC`), then fall back to queue-anchor/arena mapping.
  - Account-switch logout now uses a built-in mapped sequence (independent from recorded-action replay): two short focus clicks, one `ESC`, mapped `LOG_OUT_BTN`, then mapped `LOG_OUT_OK_BTN` with tuned delays.
  - If a `Logout` record exists, its first click (`log_out_focus`) and last two clicks (`log_out_btn`, `log_out_ok_btn`) are seeded once as baseline logout coordinates (and written to `runtime/config/calibration_config.json`), then normal mapped clicking is used afterward.
  - Seeded logout clicks from recorded actions are converted into 1920-relative window coordinates (using legacy `queue_button` origin reconstruction when needed) before runtime mapping.
  - For logout targets, 1920-relative values are mapped directly to current `arena_region`; queue-anchor rebase is only used for true legacy absolute targets to avoid mixed-space drift.
  - Fixed init-order bug: loaded/seeded logout coordinates are no longer overwritten by hardcoded defaults later in `Controller` startup.
  - Logout click injection now mirrors Record Action playback style (explicit `left_down`/`left_up`) for better consistency with `Test Action`.
  - Hand scan points (`hand_scan_p1/p2`) are treated as direct 1920-space targets; if loaded values are outside 1920x1080 they are replaced with 1920 defaults before runtime mapping.
  - Bottom-right actions (`RESOLVE` / `SUBMIT_SELECTION` / `ATTACK_ALL`) and `ASSIGN_DAMAGE_DONE` now also use mapped coordinates instead of fixed desktop absolute points.
  - `KEEP_HAND` uses only the configured keep-hand coordinate and maps it relative to detected `arena_region` (no template matching).
  - After each mulligan click, a keep-click debug bundle is saved under `runtime/debug/keep-click-<timestamp>/` with:
    - `keep_click_state.json` (raw/mapped points, source, arena region, correction, state)
    - `full_screen_after_click.png`
    - `arena_region_after_click.png` (if arena window was detected)
    - `click_focus_after_click.png` (crop around clicked position)
  - During account-switch fallback logout, each logout click saves a debug bundle under `runtime/debug/logout-click-<timestamp>/` with:
    - `logout_click_state.json` (raw/mapped points, source, arena region, state)
    - `full_screen_after_click.png`
    - `arena_region_after_click.png` (if arena window was detected)
    - `logout_focus_after_click.png` (crop around clicked position)
  - When `SelectN` / discard hand scanning stalls, the controller saves a debug bundle under `runtime/debug/hand-select-<timestamp>/` with:
    - `hand_select_state.json` (card id, scan bounds, current hover/cursor, arena regions, pending SelectN state)
    - `log_tail.txt`
    - `full_screen.png`
    - `arena_region.png` (if arena window was detected)
    - `scan_focus.png` (crop around the current scan position)
  - The same `hand-select-<timestamp>` bundle is now also written for normal cast/play hand-scan failures (`SCAN_FAILED` / `SCAN_STOPPED`), not only `SelectN`

### Navigation Debug Artifacts

When post-login navigation verification repeatedly fails, the bot saves a debug bundle in:

- `runtime/debug/<timestamp>/`

Bundle contents:

- `state.json` (reason, parsed bot state, arena region)
- `log_tail.txt` (latest log lines)
- `arena_region.png` (captured MTGA window region)
- `full_screen.png` (full-screen capture)

## See also on
[elitepvpers](https://www.elitepvpers.com/)
