# Minisist

A small, rounded assistant menu pinned to the bottom-right of your screen, toggled with a global hotkey (default `Alt+Z`). Slides up from the bottom, plays a mini boot animation, then fades in your apps and system shortcuts plus live Memory/CPU stats.

## Setup

1. Install [Python 3.10+](https://python.org) if you don't have it.
2. Open a terminal in this folder.
3. Install dependencies:
   ```
   pip install -r requirements.txt
   ```
4. Run it:
   ```
   python main.py
   ```
5. Press `Alt+Z` anywhere on your desktop to open the menu.

**Note:** the `keyboard` library sometimes needs the terminal/script run as Administrator to catch global hotkeys reliably on Windows, especially if another app on screen is running elevated. If `Alt+Z` doesn't respond, try running your terminal as Administrator.

## Using it

- **Memory / CPU**: live usage readouts at the top, refreshed every 1.5 seconds while the menu is open.
- **Apps box**: contains an "Other Apps" box (your custom-added apps) plus quick-launch buttons for File Explorer, Task Manager, Control Panel, and Windows Settings.
- **Settings**: click the ⚙ icon to switch the menu into an inline settings view (no separate window) — click `←` to go back.
  - **Hotkey**: click the box, press your new combo (e.g. `ctrl+shift+space`), then Save.
  - **Colors**: Accent and Background — restyle the menu immediately and also color the boot animation.
  - **Preview Startup Animation**: replays the boot animation with your currently selected colors.
  - **PC Performance Mode**: when on, the menu's widgets are fully torn down when you close it and rebuilt fresh the next time you open it — lighter on your PC at idle, at the cost of rebuilding on each open (rebuild happens instantly, right before the boot animation plays).
  - **Start with Windows**: launches Minisist automatically at login (adds/removes itself from the Windows Registry Run key).
  - **Other Apps**: add or remove apps shown in the main menu.
- The app also lives in your system tray (a small colored dot in your chosen accent color) — right-click for Open Menu / Settings / Quit.
- Click outside the menu, or it closes on its own when it loses focus.

## Packaging as a standalone .exe

This folder includes `assets/icon.ico` (a matching app icon) and `version.txt` (Windows version resource info) so the packaged `.exe` looks and identifies itself properly.

```
pip install pyinstaller
pyinstaller --noconsole --onefile --name Minisist --icon assets/icon.ico --version-file version.txt main.py
```

The `.exe` shows up at `dist/Minisist.exe`.

Notes:
- `--noconsole` hides the terminal window — also hides the debug prints (hotkey registration, performance mode messages). Drop it temporarily if you need to troubleshoot.
- `--onefile` bundles everything into one `.exe` at the cost of a slightly slower startup (it unpacks to a temp folder each launch). Use `--onedir` instead if you'd rather have a folder with faster startup.
- If you edit `main.py`/`config.py` and rebuild, delete the `build/` and `dist/` folders first to avoid PyInstaller using stale cached files.
- The "Start with Windows" setting stores whichever path you ran when you last checked the box. If you rebuild the `.exe` and move it somewhere new, toggle the setting off and back on so it points at the new location.

## Notes

- Built for Windows (uses `rundll32`/`shutdown`-style commands, and the Registry Run key for autostart).
- Settings and your app list persist in `%APPDATA%\Minisist\config.json`.
- The logo is drawn entirely in code (no image assets) for the in-app animation, so color changes apply instantly everywhere. The `.exe` icon itself (`assets/icon.ico`) is a static file since Windows doesn't support animated taskbar/tray icons.
