from __future__ import annotations

"""Fabrica de modelos de chat multi-provedor (OpenAI / Anthropic / Google Gemini / DeepSeek).

O restante do pipeline RAG usa apenas a interface `BaseChatModel.invoke(...)`, que
e identica entre os provedores. Assim, trocar de provedor exige mudar somente o
ponto de construcao (chat_service) e nada no fluxo de resposta.

Dois cuidados importantes (verificados no LangChain 1.x):
1. `init_chat_model` infere `gemini*` como `google_vertexai` (exige projeto GCP +
   credenciais ADC). Aqui forcamos `google_genai` para usar a API do Google AI
   Studio (Dev API), que so precisa de `GOOGLE_API_KEY`.
2. `AIMessage.content` pode vir como `str` (OpenAI) OU como lista de blocos
   (Anthropic/Gemini). `to_text()` normaliza para texto puro.
"""

from typing import Any

try:  # LangChain 1.x
    from langchain.chat_models import init_chat_model
except Exception:  # pragma: no cover - fallback para layouts alternativos
    from langchain.chat_models.base import init_chat_model


# Apelidos aceitos -> id canonico usado por init_chat_model (model_provider).
_PROVIDER_ALIASES: dict[str, str] = {
    "openai": "openai",
    "gpt": "openai",
    "azure_openai": "azure_openai",
    "anthropic": "anthropic",
    "claude": "anthropic",
    "google": "google_genai",
    "google_genai": "google_genai",
    "googleai": "google_genai",
    "gemini": "google_genai",
    "deepseek": "deepseek",
    "ds": "deepseek",
}


def infer_provider(model: str) -> str:
    """Infere o provedor a partir do id do modelo.

    Cobre os prefixos usados no projeto; para Gemini devolve `google_genai`
    (nao `google_vertexai`) de proposito, evitando a exigencia de GCP/ADC.
    """
    m = (model or "").strip().lower()
    if m.startswith(("gpt-", "gpt3", "gpt4", "o1", "o3", "o4", "chatgpt")):
        return "openai"
    if m.startswith("claude"):
        return "anthropic"
    if m.startswith("gemini") or m.startswith("models/gemini"):
        return "google_genai"
    if m.startswith("deepseek"):
        return "deepseek"
    # Default conservador: mantem o comportamento OpenAI historico do projeto.
    return "openai"


def resolve_provider(model: str, provider: str | None = None) -> str:
    """Resolve o provedor: usa `provider` explicito (normalizado) ou infere."""
    if provider:
        key = provider.strip().lower()
        return _PROVIDER_ALIASES.get(key, key)
    return infer_provider(model)


def build_chat_model(
    model: str,
    temperature: float = 0.0,
    provider: str | None = None,
    reasoning_effort: str | None = None,
    **kwargs: Any,
):
    """Constroi um chat model do LangChain para OpenAI/Anthropic/Google.

    Retorna um `BaseChatModel` cujo `.invoke(...)` e compativel com o antigo
    `ChatOpenAI`, mantendo o pipeline RAG agnostico de provedor.

    Alguns modelos mais novos (ex.: Claude Sonnet 5) rejeitam `temperature`
    explicito com erro 400 ("temperature is deprecated for this model").
    Como isso so e validado pela API no primeiro `.invoke()` (nao na construcao
    do client), a funcao devolve um wrapper fino que tenta com `temperature` e,
    se a API recusar especificamente por causa dele, tenta de novo sem o
    parametro -- sem exigir uma lista manual de quais modelos aceitam ou nao.

    O mesmo vale para `reasoning_effort`: so e enviado a modelos de raciocinio
    da OpenAI (ver `supports_reasoning_effort`), e se a API recusar o valor
    (ex.: "minimal" num modelo que nao o aceita) o wrapper descarta o
    parametro em vez de deixar a etapa falhar em silencio.

    Timeout: provedores compativeis com a API OpenAI, incluindo DeepSeek,
    aceitam `timeout`. Sem um teto explicito, uma chamada de avaliacao pode
    ficar presa por tempo indefinido em instabilidade de rede/provedor.
    """
    kwargs.setdefault("timeout", 120)
    resolved = resolve_provider(model, provider)

    # Cada parametro opcional comeca ligado e e desligado de vez na primeira
    # recusa da API. A ordem importa pouco: cada recusa desliga um so.
    use = {
        "temperature": True,
        "reasoning_effort": bool(reasoning_effort) and supports_reasoning_effort(model, resolved),
    }

    def _build():
        extra: dict[str, Any] = {}
        if use["temperature"]:
            extra["temperature"] = temperature
        if use["reasoning_effort"]:
            extra["reasoning_effort"] = reasoning_effort
        return init_chat_model(model, model_provider=resolved, **kwargs, **extra)

    current = _build()

    class _ParamFallbackModel:
        def __getattr__(self, name: str) -> Any:
            return getattr(current, name)

        def invoke(self, *args: Any, **inv_kwargs: Any) -> Any:
            nonlocal current
            while True:
                try:
                    return current.invoke(*args, **inv_kwargs)
                except Exception as exc:
                    text = str(exc).lower()
                    dropped = next(
                        (p for p in ("temperature", "reasoning_effort") if use[p] and p.split("_")[0] in text),
                        None,
                    )
                    if dropped is None:
                        raise
                    use[dropped] = False
                    current = _build()

    return _ParamFallbackModel()


_REASONING_MODEL_PREFIXES = ("gpt-5", "o1", "o3", "o4")


def supports_reasoning_effort(model: str, provider: str) -> bool:
    """`reasoning_effort` so existe nos modelos de raciocinio da OpenAI.

    Enviado para Anthropic/DeepSeek ou para um gpt-4*, o parametro seria
    rejeitado ou ignorado; por isso nem e repassado nesses casos.
    """
    m = (model or "").strip().lower()
    return provider == "openai" and m.startswith(_REASONING_MODEL_PREFIXES)


def to_text(response: Any) -> str:
    """Converte a resposta do LLM em texto puro.

    OpenAI devolve `content` como str; Anthropic/Gemini podem devolver uma lista
    de blocos. Sem essa normalizacao, um `.strip()` sobre lista lancaria excecao
    e a resposta seria descartada silenciosamente.
    """
    content = getattr(response, "content", response)
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        parts: list[str] = []
        for block in content:
            if isinstance(block, str):
                parts.append(block)
            elif isinstance(block, dict):
                text = block.get("text")
                if text is None and block.get("type") == "text":
                    text = block.get("content")
                if isinstance(text, str):
                    parts.append(text)
        return "".join(parts)
    return "" if content is None else str(content)
