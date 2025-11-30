## Projekt-Spezifikation (aktueller Stand)

Ein modularer Python-Bot für Magic: The Gathering Arena, fokussiert auf tägliche Quests. Architektur orientiert sich an MTGAI, bleibt aber leicht erweiterbar für neue Deck-Strategien oder Quest-Typen.

### Architektur
- `log_parser.py`: Tailed `Player.log`, liefert strukturierte Events (Quests, Queue/Mitreinkommen, Match-Start/-Ende, Turn, Hand-Updates über grpIds). Heuristik klassifiziert Quests in `play_games`, `cast_spells`, `combat`.
- `game_model.py`: `GameState` als einfache State-Machine (Phasen idle/queued/in_match/exiting), Quest-Fortschritt (`QuestProgress`), Turn-Zähler, Hand-Zusammenfassung optional via `card_db`. Tracking von Hand-Kept, Match-ID, aktiven Quests.
- `quest_ai.py`: Strategy-Pattern mit Default-Strategien:
  - `play_games`: queue → keep hand → einfache Land/Spell/Attack-Flows, ggf. surrender ab Turn 4.
  - `cast_spells`: priorisiert Spell-Casts (mit Farbhinweis), surrender kurz vor Abschluss.
  - `combat`: bevorzugt Attack-All.
  - Plugin-Hook `register_strategy` für weitere Deck/Quest-Strategien; `MonoRedAggroStrategy` als Beispiel in `strategies.py`.
- `ui_controller.py`: Wrapper um `pyautogui`, optional `ydotool` auf Wayland. Features: Dry-Run-Modus (default), Bildsuche für benannte Targets (`image_dir`), relative Klick-Heuristiken, leichte Randomisierung, Tastenevents, Land/Spell/Attack-Flows. Erkennt manuelle Mausbewegung und pausiert Bot-Aktionen für konfigurierbare 7s. Unterstützt `click_region` für fenstergebundene Koordinaten.
- `main.py`: Lädt Config, Karten-DB (optional), Decks, initialisiert `GameState`, `QuestAI`, `UIController`. Folgt Logs in einer Schleife, wendet Events auf den State an, wählt Actions aus der AI, führt sie über UI aus. Fallback: erzwingt Keep-Hand nach Queue-Timer.

### Konfiguration (siehe `config.example.json`)
- Wichtige Felder: `log_path`, `player_name`, `default_deck`, `deck_strategy`, `default_strategy`, `default_color`, `image_dir`, `dry_run`, `poll_interval`, `image_confidence`, `decks_path`, `log_level`, `click_region` (optional), `cards_path` (optional), `user_mouse_pause_seconds` (Standard 7.0s).
- Deck-Definitionen in `decks.example.json`; Karten-DB optional über `cards.json` zur Handbewertung.

### Ausführung und Tests
- Start: `python -m mtga_bot.main --config config.json` (Dry-Run standardmäßig aktiv, für echte Eingaben `dry_run: false` setzen).
- Tests: `python -m unittest` (Parser/GameState-Abdeckung).

### Erweiterbarkeit / TODO
- Weitere Deck-Strategien per `register_strategy`.
- Feinere UI-Bildtargets und regionspezifische Klicks.
- Bessere Quest-Klassifizierung und Multi-Quest-Priorisierung.
