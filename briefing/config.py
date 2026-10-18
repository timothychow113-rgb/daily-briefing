"""Loads the YAML config files and environment secrets."""

from __future__ import annotations

import os
from pathlib import Path

import yaml
from dotenv import load_dotenv

CONFIG_DIR = Path("config")


def load_yaml(name: str) -> dict:
    with open(CONFIG_DIR / name) as f:
        return yaml.safe_load(f) or {}


def require_env(name: str) -> str:
    """Read a secret from the environment (or a local .env). Fails clearly if missing."""
    load_dotenv()
    value = os.environ.get(name)
    if not value:
        raise SystemExit(f"Missing environment variable {name}. See .env.example.")
    return value
