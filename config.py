import json
import os

APP_DIR = os.path.join(os.environ.get('APPDATA', os.path.expanduser('~')), 'Minisist')
CONFIG_PATH = os.path.join(APP_DIR, 'config.json')

DEFAULT_CONFIG = {
    'hotkey': 'alt+z',
    'accent_color': '#22c55e',
    'background_color': '#0a0a0a',
    'apps': [],
    'performance_mode': False,
    'start_with_windows': False
}


def load_config():
    os.makedirs(APP_DIR, exist_ok=True)
    if not os.path.exists(CONFIG_PATH):
        save_config(DEFAULT_CONFIG)
        return dict(DEFAULT_CONFIG)
    try:
        with open(CONFIG_PATH, 'r', encoding='utf-8') as f:
            data = json.load(f)
        merged = dict(DEFAULT_CONFIG)
        merged.update(data)
        return merged
    except Exception:
        return dict(DEFAULT_CONFIG)


def save_config(config):
    os.makedirs(APP_DIR, exist_ok=True)
    with open(CONFIG_PATH, 'w', encoding='utf-8') as f:
        json.dump(config, f, indent=2)
