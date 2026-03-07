@echo off
setlocal EnableExtensions EnableDelayedExpansion

cd /d "%~dp0"

echo [1/4] Checking Nuitka installation...
python -m pip show nuitka >nul 2>&1
if errorlevel 1 (
  echo Nuitka not found. Installing Nuitka build dependencies...
  python -m pip install nuitka ordered-set zstandard
  if errorlevel 1 (
    echo Failed to install Nuitka dependencies.
    exit /b %errorlevel%
  )
)

echo [2/4] Preparing data include arguments...
set "DATA_ARGS="
set "DATA_ARGS=!DATA_ARGS! --include-data-dir=assets=assets"
set "DATA_ARGS=!DATA_ARGS! --include-data-dir=images=images"
set "DATA_ARGS=!DATA_ARGS! --include-data-dir=Buttons=Buttons"
set "DATA_ARGS=!DATA_ARGS! --include-data-files=cards.json=cards.json"
set "DATA_ARGS=!DATA_ARGS! --include-data-files=cards_metadata.json=cards_metadata.json"
set "DATA_ARGS=!DATA_ARGS! --include-data-files=missing_cards.json=missing_cards.json"
set "DATA_ARGS=!DATA_ARGS! --include-data-files=scryfall_cache.json=scryfall_cache.json"
set "DATA_ARGS=!DATA_ARGS! --include-data-files=scryfall_oracle_cache.json=scryfall_oracle_cache.json"
set "DATA_ARGS=!DATA_ARGS! --include-data-files=scryfall_bulk_metadata.json=scryfall_bulk_metadata.json"
set "SANITIZED_CONFIG=%CD%\_build_calibration_config.json"
powershell -NoProfile -ExecutionPolicy Bypass -Command ^
  "$p = Join-Path (Get-Location) 'calibration_config.json';" ^
  "if (Test-Path $p) {" ^
  "  $raw = Get-Content -Raw -Path $p | ConvertFrom-Json;" ^
  "  if ($null -eq $raw.managed_accounts) { $raw | Add-Member -NotePropertyName managed_accounts -NotePropertyValue @() -Force } else { $raw.managed_accounts = @() };" ^
  "  $raw | ConvertTo-Json -Depth 100 | Set-Content -Encoding UTF8 -Path '%SANITIZED_CONFIG%';" ^
  "} else {" ^
  "  '{}' | Set-Content -Encoding UTF8 -Path '%SANITIZED_CONFIG%';" ^
  "}"
set "DATA_ARGS=!DATA_ARGS! --include-data-files=%SANITIZED_CONFIG%=calibration_config.json"
set "DATA_ARGS=!DATA_ARGS! --include-data-files=config/public_key.jwk=config/public_key.jwk"
if exist "recorded_actions_records.json" (
  set "DATA_ARGS=!DATA_ARGS! --include-data-files=recorded_actions_records.json=recorded_actions_records.json"
) else (
  echo ERROR: recorded_actions_records.json not found.
  echo This customer build is expected to ship with recorded actions.
  exit /b 1
)

echo [3/4] Building BurningLotusBot.exe with Nuitka (standalone)...
python -m nuitka ^
  --standalone ^
  --remove-output ^
  --assume-yes-for-downloads ^
  --windows-console-mode=disable ^
  --enable-plugin=tk-inter ^
  --output-dir=dist_nuitka ^
  --output-filename=BurningLotusBot.exe ^
  --windows-icon-from-ico=burning_lotus_icon.ico ^
  !DATA_ARGS! ^
  ui.py

if errorlevel 1 (
  echo Standard compiler path failed. Retrying with Zig backend...
  python -m nuitka ^
    --standalone ^
    --remove-output ^
    --assume-yes-for-downloads ^
    --windows-console-mode=disable ^
    --enable-plugin=tk-inter ^
    --zig ^
    --output-dir=dist_nuitka ^
    --output-filename=BurningLotusBot.exe ^
    --windows-icon-from-ico=burning_lotus_icon.ico ^
    !DATA_ARGS! ^
    ui.py
  if errorlevel 1 (
    echo Nuitka build failed including Zig fallback.
    exit /b %errorlevel%
  )
)

echo [4/4] Build complete.
echo Executable: dist_nuitka\ui.dist\BurningLotusBot.exe
echo.
echo Copy the whole folder "dist_nuitka\ui.dist" to another Windows laptop.
if exist "%SANITIZED_CONFIG%" del /f /q "%SANITIZED_CONFIG%" >nul 2>&1

endlocal
