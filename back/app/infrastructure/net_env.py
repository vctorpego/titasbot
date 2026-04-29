from __future__ import annotations

import os


def clear_broken_local_proxy() -> None:
    """
    Remove proxies locais claramente inválidos (ex.: 127.0.0.1:9),
    que impedem acesso à OpenAI e ao tiktoken CDN.
    """
    keys = ("HTTP_PROXY", "HTTPS_PROXY", "ALL_PROXY", "http_proxy", "https_proxy", "all_proxy")
    bad_tokens = ("127.0.0.1:9", "localhost:9")

    for key in keys:
        value = os.getenv(key, "")
        lower = value.lower().strip()
        if lower and any(tok in lower for tok in bad_tokens):
            os.environ.pop(key, None)

