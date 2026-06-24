import json

SYSTEM_PROMPT = """Eres FinAlly, un asistente de trading con IA dentro de una estación \
de trading simulada. Tienes acceso al estado actual de la cartera del usuario.

- Analiza la composición de la cartera, la concentración de riesgo y el P&L.
- Sugiere operaciones con tu razonamiento.
- Ejecuta operaciones cuando el usuario lo solicite o esté de acuerdo.
- Gestiona la watchlist de forma proactiva si el usuario lo pide.
- Sé conciso y básate en los datos de la cartera en tus respuestas.
- Responde siempre con el JSON estructurado solicitado."""


def build_messages(
    user_message: str, portfolio_context: dict, history: list[dict]
) -> list[dict]:
    """Construye la lista de mensajes para LiteLLM: sistema + contexto + historial + mensaje."""
    context_message = (
        "Estado actual de la cartera (JSON):\n" + json.dumps(portfolio_context)
    )
    messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "system", "content": context_message},
    ]
    messages.extend(history)
    messages.append({"role": "user", "content": user_message})
    return messages
