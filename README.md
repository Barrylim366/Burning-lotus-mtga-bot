# MTGA Bot (CachyOS / Wayland Notes)

Dieser Bot steuert Maus/Tastatur jetzt über ein austauschbares Backend:

- `ydotool` (empfohlen für CachyOS/Wayland)
- `pynput` (klassisch, funktioniert oft besser unter X11/Windows)

## Backend auswählen

Entweder in `calibration_config.json`:

```json
{
  "input_backend": "ydotool"
}
```

Oder per Environment Variable (überschreibt die Config):

```bash
export MTGA_BOT_INPUT_BACKEND=ydotool   # oder: pynput / auto
python ui.py
```

## Player.log Pfad (Steam/Proton)

Standardmäßig versucht die UI den `Player.log` automatisch unter Steam/Proton zu finden.

Optional kannst du den Pfad auch explizit setzen:

- in `calibration_config.json` via `"log_path": "..."`, oder
- für `run_bot.py` per `MTGA_BOT_LOG_PATH`.

## ydotool Voraussetzungen (Wayland)

`ydotool` benötigt den Daemon `ydotoold` und Zugriff auf `/dev/uinput`.

- Stelle sicher, dass `ydotoold` läuft.
- Falls der Socket nicht am Standardpfad liegt, setze `YDOTOOL_SOCKET` entsprechend.
- Wichtig: Wenn du `ydotoold` per `sudo` startest, muss der Socket dem User gehören (sonst kann `ydotool` ggf. nicht verbinden). Fix: `sudo chown $USER:$USER /run/user/$(id -u)/.ydotool_socket`

Wenn das Backend nicht initialisieren kann, bekommst du eine klare Fehlermeldung beim Start.

Hinweis: Auf manchen Wayland-Setups interpretiert `ydotool mousemove --absolute` keine Pixel-Koordinaten (sondern z.B. 0..65535). Der Bot mappt daher intern Pixel-Koordinaten anhand von `screen_bounds`, damit Klickpunkte zuverlässig stimmen.

## Kalibrierung unter Wayland

Globales Maus/Keyboard-Capturing via `pynput` ist unter Wayland oft blockiert.
Im Calibration-Fenster gibt es daher zusätzlich **Capture (slurp)**.

- Installiere `slurp` und nutze den Button, um einen Punkt zu wählen.
