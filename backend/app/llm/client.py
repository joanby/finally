from litellm import completion

from .models import ChatResult

MODEL = "openrouter/openai/gpt-oss-120b"
EXTRA_BODY = {"provider": {"order": ["cerebras"]}}


def call_llm(messages: list[dict]) -> ChatResult:
    """Llama al modelo vía LiteLLM/OpenRouter con Cerebras, pidiendo salida estructurada."""
    response = completion(
        model=MODEL,
        messages=messages,
        response_format=ChatResult,
        reasoning_effort="low",
        extra_body=EXTRA_BODY,
    )
    result = response.choices[0].message.content
    return ChatResult.model_validate_json(result)
