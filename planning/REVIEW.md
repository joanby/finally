# Revisión de planning/PLAN.md

Feedback sobre la especificación del proyecto FinAlly. Organizado por sección del PLAN.md, seguido de oportunidades de simplificación.

## 6. Datos de Mercado

- **Correlación entre tickers**: el plan dice que los movimientos están "correlacionados (ej. tecnológicas se mueven juntas)" pero no especifica el mecanismo (¿un factor de mercado común + ruido idiosincrático por sector? ¿matriz de correlación fija?). Sin esto, dos implementaciones del simulador podrían divergir en comportamiento. Vale la pena fijar el algoritmo (aunque sea simple) antes de implementar.
- **Precio semilla para tickers nuevos**: "se le asigna también un precio semilla realista (generado de forma plausible)" — ¿cómo? Opciones: rango fijo aleatorio (ej. $10–$500), hash del ticker, o llamada a la API de Massive una vez para obtener el precio real incluso en modo simulador. Esto afecta directamente la UX (un ticker nuevo con precio absurdo se nota).
- **Validación de tickers**: no se especifica qué pasa si el usuario añade un ticker inválido/inexistente (ej. "ZZZZZ"). En modo simulador, ¿se acepta cualquier string? En modo Massive, ¿se valida contra la API antes de aceptarlo en la watchlist?
- **Batching de la API de Massive**: con 10 tickers en la watchlist por defecto y un límite de 5 llamadas/min en el tier gratuito, ¿la API de Massive soporta consultar múltiples símbolos en una sola llamada? Si no, el sondeo de 10 tickers cada 15s no es viable con ese límite — esto debería confirmarse antes de construir el cliente.

## 7. Base de Datos

- **Cálculo de `avg_cost`**: no se especifica el método (promedio ponderado vs FIFO) para recalcular `avg_cost` en `positions` tras compras/ventas parciales. Asumo promedio ponderado (el más simple), pero conviene dejarlo explícito en el plan para evitar ambigüedad al implementar.
- **Ventas en corto**: el esquema permite `quantity REAL`, pero no se dice explícitamente si se prohíbe vender más de lo que se posee (short selling). Lo menciona la sección 12 (tests) como caso límite a probar, pero la sección 7 no lo declara como regla de negocio.
- **Concurrencia SQLite**: hay una tarea en segundo plano (simulador/poller) escribiendo en la caché de precios y otra (`portfolio_snapshots` cada 30s) escribiendo en SQLite, además de las peticiones API normales. SQLite con escrituras concurrentes puede dar `database is locked`. Vale la pena mencionar explícitamente el uso de modo WAL (`PRAGMA journal_mode=WAL`) en el plan, ya que es la mitigación estándar y barata.
- **Primer snapshot de cartera**: si `portfolio_snapshots` solo se registra cada 30s (más al ejecutar una operación), el gráfico de P&L estará vacío o con un único punto durante los primeros 30 segundos tras un arranque limpio. ¿Se debería insertar un snapshot inicial al arrancar el backend (o al primer acceso del usuario) para evitar un gráfico vacío en la demo?

## 8. Endpoints de la API

- **Falta un GET para el historial de chat**: hay `POST /api/chat` pero no `GET /api/chat` (o similar) para recuperar `chat_messages` al cargar la página. Sin él, el panel de chat siempre arranca vacío aunque haya historial persistido en SQLite — ¿es eso intencional, o falta el endpoint en la tabla?

## 9. Integración con el LLM

- **Manejo de fallos del proveedor**: no se especifica qué responde `/api/chat` si OpenRouter/Cerebras no responde o tarda demasiado (timeout, 5xx). Dado que las operaciones se ejecutan automáticamente sin confirmación, sería bueno aclarar que si el LLM falla, simplemente no se ejecuta ninguna operación y se devuelve un mensaje de error — para que quede explícito que nunca se ejecuta nada sin una respuesta JSON válida y completa del modelo.

## 10. Diseño del Frontend

- **Sparklines sin historial al recargar**: como el sparkline se acumula solo desde el SSE tras la carga de página, al refrescar el navegador todos los sparklines empiezan vacíos y tardan en "llenarse" otra vez. Esto es coherente con la decisión de diseño documentada, pero merece una nota explícita de que es un trade-off aceptado (en lugar de algo a corregir después).

## Oportunidades de Simplificación

- **`users_profile` como tabla**: para un único usuario fijo (`"default"`), una tabla completa con su propio esquema es probablemente más ceremonia de la necesaria hoy. Es una decisión deliberada para soportar multiusuario futuro sin migración, así que se puede mantener, pero vale la pena confirmar que el costo de mantenimiento adicional (lazy init, seed) compensa frente a, por ejemplo, una fila única hardcodeada hasta que el multiusuario sea real.
- **Interfaz común simulador/Massive**: bien planteada (sección 6). Si ambas implementaciones exponen exactamente la misma forma de datos, se podría simplificar aún más definiendo ya en el plan la firma exacta del método compartido (ej. `get_prices(tickers: list[str]) -> dict[str, PriceTick]`), evitando que cada agente de implementación invente una interfaz distinta.
- **`watchlist_changes` y `trades` como arrays separados en la salida del LLM**: funcionalmente correcto, pero si en el futuro se añaden más tipos de "acciones" del LLM, esta forma crecerá con un array nuevo por tipo. No es necesario cambiarlo ahora (son solo dos tipos), pero si se prevé añadir más, una lista única de `actions` con un campo `type` discriminador sería más fácil de extender sin tocar el esquema repetidamente.
