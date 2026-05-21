from __future__ import annotations

from app.infrastructure.env import load_project_env
from app.infrastructure.net_env import clear_broken_local_proxy
from app.infrastructure.settings import get_settings
from app.presentation.cli_chat import run_chat


def main() -> None:
    clear_broken_local_proxy()
    load_project_env()
    settings = get_settings()
    run_chat(settings)


if __name__ == "__main__":
    main()
