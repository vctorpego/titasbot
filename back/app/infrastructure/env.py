from __future__ import annotations

from pathlib import Path

from dotenv import load_dotenv


def project_root() -> Path:
    return Path(__file__).resolve().parents[2]


def load_project_env() -> Path:
    env_path = project_root() / ".env"
    load_dotenv(dotenv_path=env_path)
    return env_path
