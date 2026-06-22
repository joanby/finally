# FinAlly — Estación de trabajo de trading con IA

Una estación de trabajo de trading con IA visualmente impresionante que transmite datos de mercado en tiempo real, simula operaciones de cartera e integra un asistente de chat LLM capaz de analizar posiciones y ejecutar operaciones mediante lenguaje natural.

Desarrollada íntegramente por agentes de codificación como proyecto final de un curso de programación de IA con agentes.

## Funcionalidades

- **Precios en tiempo real** vía SSE con animaciones de destello verde/rojo
- **Cartera simulada**: $10.000 en efectivo virtual, órdenes de mercado, ejecuciones instantáneas
- **Visualizaciones de la cartera**: mapa de calor (treemap), gráfico de pérdidas y ganancias, tabla de posiciones
- **Asistente de chat con IA**: analiza las posiciones, sugiere y ejecuta operaciones automáticamente
- **Gestión de la lista de seguimiento**: seguimiento manual o mediante IA de los valores
- **Estética oscura de la terminal**: diseño denso en datos inspirado en Bloomberg

## Arquitectura

Un único contenedor Docker que sirve todo en el puerto 8000:

- **Frontend**: Next.js (exportación estática) con TypeScript y Tailwind CSS
- **Backend**: FastAPI (Python/uv) con transmisión SSE
- **Base de datos**: SQLite con inicialización diferida
- **IA**: LiteLLM → OpenRouter (inferencia Cerebras) con salidas estructuradas
- **Datos de mercado**: Integrados Simulador GBM (predeterminado) o API de Massive (opcional)

## Inicio rápido

```bash
# Clonar y configurar
cp .env.example .env
# Añadir tu OPENROUTER_API_KEY a .env

# Ejecutar con Docker
docker build -t finally .

docker run -v finally-data:/app/db -p 8000:8000 --env-file .env finally

# Abrir http://localhost:8000
```

## Variables de entorno

| Variable | Obligatoria | Descripción |

|---|---|---|

| `OPENROUTER_API_KEY` | Sí | Clave API de OpenRouter para chat con IA |

| `MASSIVE_API_KEY` | No | Clave de Massive (Polygon.io) para datos de mercado reales; omitir para usar el simulador |

| `LLM_MOCK` | No | Establecer `true` para respuestas simuladas de LLM deterministas (pruebas) |

## Estructura del proyecto

``` finalmente/
├── frontend/ # Exportación estática de Next.js
├── backend/ # Proyecto uv de FastAPI
├── planning/ # Documentación del proyecto y contratos de agentes
├── test/ # Pruebas E2E de Playwright
├── db/ # Montaje de volumen SQLite (tiempo de ejecución)
└── scripts/ # Ayudantes de inicio/parada
```

## Licencia

Ver [LICENSE](LICENSE).
