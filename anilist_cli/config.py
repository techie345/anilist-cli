"""Simple JSON-based configuration storage for anilist-cli."""

import json
import os

CONFIG_DIR = os.path.expanduser("~/.config/anilist-cli")
CONFIG_PATH = os.path.join(CONFIG_DIR, "config.json")


def load_config():
    if os.path.exists(CONFIG_PATH):
        try:
            with open(CONFIG_PATH, "r") as f:
                return json.load(f)
        except (json.JSONDecodeError, OSError):
            return {}
    return {}


def save_config(data):
    os.makedirs(CONFIG_DIR, exist_ok=True)
    with open(CONFIG_PATH, "w") as f:
        json.dump(data, f, indent=2)


def get_username():
    return load_config().get("username")


def set_username(username):
    cfg = load_config()
    cfg["username"] = username
    save_config(cfg)
