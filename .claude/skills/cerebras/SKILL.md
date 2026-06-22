--- 
name: cerebras-inference
description: Utilice esta función para escribir código que llame a un LLM usando LiteLLM y OpenRouter con el proveedor de inferencia Cerebras.
---

# Llamada a un LLM a través de Cerebras

Estas instrucciones le permiten escribir código para llamar a un LLM con Cerebras como proveedor de inferencia.

Este método utiliza LiteLLM y OpenRouter.

## Configuración

La clave API de OpenRouter (OPENROUTER_API_KEY) debe estar configurada en el archivo .env y cargada como variable de entorno.

El proyecto uv debe incluir litellm y pydantic.

`uv add litellm pydantic`

## Fragmentos de código

Utiliza el código como estos ejemplos para usar Cerebras.

### Importaciones y constantes

```python
from litellm import completion
MODEL = "openrouter/openai/gpt-oss-120b"
EXTRA_BODY = {"provider": {"order": ["cerebras"]}}
```
### Código para llamar a través de Cerebras para una respuesta de texto

```python
response = completion(model=MODEL, messages=messages, reasoning_effort="low", extra_body=EXTRA_BODY)
result = response.choices[0].message.content
```

### Código para llamar a través de Cerebras para una respuesta de salida estructurada

```python
response = completion(model=MODEL, messages=messages, response_format=MyBaseModelSubclass, reasoning_effort="low", extra_body=EXTRA_BODY)
result = response.choices[0].message.content
result_as_object = MyBaseModelSubclass.model_validate_json(result)
```
