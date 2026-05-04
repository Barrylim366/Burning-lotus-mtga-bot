# Changelog

Developer notes and change history. For the current state of each feature see the README.

## Account Switching

- Account switching uses recorded logout replay first, then `ESC -> LOG_OUT_BTN -> LOG_OUT_OK_BTN` as fallback. Fallback targets are mapped through the detected `arena_region` so the sequence stays window-relative instead of clicking raw desktop coordinates.
- The account-switch flow verifies logout via fresh `Player.log` login-screen markers before typing credentials. If logout does not actually reach the login screen, the switch aborts with a debug bundle instead of typing into the still-open home/options UI. The built-in fallback also retries visible `log_out_btn.png` / `okay_btn.png` templates before giving up.
- Post-match dismiss and other home/options UI actions use the detected MTGA window center or the last good cached `arena_region` as fallback. This avoids raw desktop clicks like `(1280, 720)` when the Arena window is shifted on the monitor.
- Logout confirm (`OK`) no longer relies on full-screen `okay_btn.png` matching first. The mapped `log_out_ok_btn` click has priority, and any image-based confirmation retry is limited to a small region around the expected dialog button to avoid false positives on the Home/Play button.
- The logout dialog buttons use the same low-level click injection pattern as record playback (`move -> left_down -> left_up`) instead of the generic `left_click(1)` helper.
- If the client is in the Store scene during fallback logout, the bot logs the last scene and presses ESC twice to reach the options menu.
- Login wait before typing credentials: 5 seconds. Post-login wait before running the recorded action: 20 seconds.

## UI

- Main window uses a ttk-based dark theme with centralized design tokens in `MTGBotUI._build_ui_theme()`.
- Single accent color (`#C8141E`), system-first font stack (`Segoe UI Variable`/`Segoe UI`/`Inter`/`Arial`).
- UI scale is calculated automatically on each startup based on current screen resolution.
- Main menu buttons are canvas-rendered with rounded edges, inner shadow, rim/shadow/glow effects, and body color `#3D130E`.
- Stop button enabled only while the bot runs; uses a subtle red background treatment.
- **Current Session** and **Settings** are the only submenu entries in the main menu.
- Current session stats (`X Min till Account Switch`, `Games played`, `Win`) live in the **Current Session** subwindow.
- Settings, Record Actions, and Calibrate open as subwindows to the right of or below the main window with ~5 mm / ~0.4 cm gaps.
- **Calibrate** lives inside **Settings** and uses a split `Capture` / `Verify` layout.
- **Manage Accounts** uses a canvas-first layout with translucent group boxes (yellow border, dark-red RGBA fill) for accounts list, play-order, and switch-time areas. Credentials stored per-account under `Accounts/<folder>/credentials.json`.
- Password fields in **Manage Accounts** are masked (`*`) while typing.
- Play order is a 5-slot priority list (dropdowns).
- Window icon uses `images/ui_symbol.png` instead of a black placeholder.
- Loading bar with label `Loading Carddata` shown during bot startup.
- Bottom footer bar with `Keep Window on Top` checkbox, flush to window edges.
- `Status: Stopped` uses `#ffb02a`.
- Main menu window position fixed at `x=18, y=24`; non-resizable.
- UI Scale slider (50%–120%) in **Settings → User Interface**; applied immediately without restart.

## Window / Arena Detection

- Primary detection per platform: Win32 client rectangle (Windows), `xwininfo -tree -root` (Linux/XWayland), anchor template search (macOS/fallback).
- Session `arena_region` is stored and re-acquired on repeated verification failures.
- During combat, hand interaction, and SelectN flows the controller reuses the last known good `arena_region` instead of falling back to raw desktop coordinates.
- `AssignDamage Done` first template-matches `Buttons/assign_damage_done.png` in the lower center of the arena before falling back to a saved coordinate.
- Opponent avatar targeting uses the same 1920-relative mapping path as other calibrated points.

## Decision Safety / SelectN

- Bot defers decisions while `pendingMessageCount > 0` or while the stack contains objects.
- PayCosts prompts with non-mana cost selection handled via `GREMessageType_PayCostsReq`.
- `DeclareAttackersReq` clears any stale pay-cost pause immediately.
- DeclareAttack arms a bounded `COMBAT_RECOVERY_ARMED` fallback (up to 2 forced `all_attack + submit` attempts).
- SelectN prompts wait 3 seconds before selection; submission retried with rate limiting; progress logged.
- Resolution SelectN uses double-click on first attempt; retries if selected card remains in hand.
- Sacrifice-style SelectN can select battlefield permanents by hover-scanning the lower battlefield region.
- Resolution SelectN skips the stack-clear wait if the request already points at concrete candidates.
- Failed battlefield SelectN scans write a `debug/hand-select-<timestamp>/` bundle.
- Own timer parsed from `Player.log` timer data; transitions logged as `MY_TIMER_START/WARNING/CRITICAL/STOP`.

## Casting Logic

- Cast feasibility based on effective action mana costs (`availableActions[].manaCost`); discounts respected.
- Maximizes total mana spent per turn; prefers single higher-cost spell over multiple cheaper ones when mana is equal.
- CMC tie-break: creature → instant → sorcery → enchantment → other.
- Multi-spell plans validated against color requirements.
- Convoke supported (untapped creatures as colored mana sources).
- Heavily discounted high-mana-value spells prioritized when castable.

## Card Data

- On startup: exports MTGA's local card DB to `runtime/cache/cards.json` if the source file changed (supports Linux/macOS/Windows Steam paths, SQLite and gzip/JSON formats).
- Scryfall bulk delta check fetches new Arena IDs and merges missing entries without overwriting known cards.
- `runtime/cache/missing_cards.json` tracks cards seen in matches but not in the local DB; resolved individually from Scryfall on next startup.
- First-run seed from `data/cards.json` if no cache exists yet.

## Logs / Diagnostics

- `bot.log` stored at `runtime/logs/bot.log`; falls back to local `./bot.log` if that path is not writable.
- Full game-state snapshots stay in `bot.log`; not echoed to stdout.
- Hover logs suppressed by default; enabled only during selection scans.
- One-line match summary logged at match completion.
- Startup logs: `UI start: init controller ...`, `UI start: game.start() begin/completed`, queue target details.
- Coordinate mapping: direct 1920-relative inside `arena_region`; no legacy `screen_bounds` scaling.
- Debug bundles saved under `runtime/debug/` for: keep-click failures, logout-click failures, hand-select stalls, navigation verification failures.
- The entire `runtime/` tree is gitignored.

## Quest-Based Deck Selection

- After account switch: clicks Play → Find Match → Historic Play → My Decks via image matching, then parses quests from `Player.log`.
- Guild/color quests matched to deck image filename (e.g. `RG.png`, `WU.png`).
- Creature quests → `C.png`; `Quest_Fatal_Push` → `B.png`; `Quest_Raiding_Party` → `C.png`.
- Random deck selected if no quests are active.
- If the target deck image is missing the bot retries across other account folders and logs mismatches in `bot.log`.
