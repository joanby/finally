import os

from .client import call_llm
from .mock import mock_chat_response
from .models import ChatResult, TradeAction, WatchlistChange
from .prompt import build_messages

__all__ = [
    "ChatResult",
    "TradeAction",
    "WatchlistChange",
    "generate_chat_response",
]


def generate_chat_response(
    user_message: str, portfolio_context: dict, history: list[dict]
) -> ChatResult:
    """Genera la respuesta del asistente para un mensaje de chat.

    Módulo puro: no toca la BD ni ejecuta operaciones, solo devuelve el plan
    estructurado (ver planning/team_contract.md). Síncrona; el llamador (Backend)
    la invoca en threadpool.

    Si la env LLM_MOCK es "true", devuelve una respuesta determinista sin red
    (ver `mock.mock_chat_response`). En caso contrario llama al LLM real vía
    LiteLLM/OpenRouter con Cerebras como proveedor de inferencia.
    """
    if os.environ.get("LLM_MOCK", "false").lower() == "true":
        return mock_chat_response(user_message)

    messages = build_messages(user_message, portfolio_context, history)
    return call_llm(messages)
