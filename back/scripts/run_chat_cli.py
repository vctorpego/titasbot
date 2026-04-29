from __future__ import annotations

from pathlib import Path

from dotenv import load_dotenv

from app.infrastructure.net_env import clear_broken_local_proxy
from app.infrastructure.settings import get_settings
from app.presentation.cli_chat import run_chat


def main() -> None:
    clear_broken_local_proxy()
    env_path = Path(__file__).resolve().parents[1] / ".env"
    load_dotenv(dotenv_path=env_path)
    settings = get_settings()
    run_chat(settings)


if __name__ == "__main__":
    main()
