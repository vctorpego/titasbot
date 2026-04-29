from app.infrastructure.net_env import clear_broken_local_proxy
from app.presentation.http_server import main


if __name__ == "__main__":
    clear_broken_local_proxy()
    main()
