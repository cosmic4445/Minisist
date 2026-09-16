  <p align="center">
  <img src="assets/Logo.png" width="100">     
</p> 

A small, rounded assistant menu pinned to the bottom-right of your screen, toggled with a global hotkey (default `Alt+Z`). Slides up from the bottom, plays a mini boot animation, then fades in your apps and system shortcuts plus live Memory/CPU stats.

## Setup

1. Install [Python 3.10+](https://python.org) if you don't have it.
2. Open a terminal and use
   ```
   cd C:\Users\YOURUSER\Downloads\Minisist
   ```
4. Install dependencies:
   ```
   pip install -r requirements.txt
   ```
5. Run it:
   ```
   python main.py
   ```
6. Press `Alt+Z` anywhere on your desktop to open the menu.

**Note:** the `keyboard` library sometimes needs the terminal/script run as Administrator to recognize hotkeys on Windows, especially if another app on screen is running. If `Alt+Z` doesn't respond, try running your terminal as Administrator.

# How to package into a EXE

This folder includes `assets/icon.ico` (a matching app icon) and `version.txt` (Windows version resource info) so the packaged `.exe` looks and identifies itself properly.

Install pyinstaller
```
pip install pyinstaller
```
How to package
```
pyinstaller --noconsole --onefile --name Minisist --icon assets/icon.ico --version-file version.txt main.py
```

The `.exe` shows up at `dist/Minisist.exe`.



