# Brief: Subtítulos en vivo para la vibeathon

> Contrato de entrada del Nivel 1. Los agentes constructores leen este brief y
> generan el repositorio del MVP (Nivel 2) dentro de `<out>/nerdearla-subtitles/`.

## Contexto

Nerdearla, la mayor conferencia tech de Argentina, busca que **cien mil personas
no hablantes de inglés puedan seguir las charlas en español en vivo**. El
entregable es un producto de **transcripción y traducción simultánea** que
genere subtítulos en tiempo real: transcripción exacta del audio original (es o
en) y traducción en vivo al español.

## Qué construir

Un pipeline de audio a subtítulos y un servicio que:

1. Reciba audio en vivo de al menos una fuente (micrófono, archivo o stream) e
   incluya audios de prueba en el repo con una opción simple de importarlos.
2. Transcriba en tiempo real en el idioma original (es o en).
3. Traduzca en tiempo real (inglés a español).
4. Muestre los subtítulos en vivo (una vista web, overlay OBS u otro).
5. Procese al menos **2 sesiones simultáneas** y documente cómo escalar a más.
6. Es un repo con licencia OSI (Apache 2.0 o MIT), README con credenciales,
   `.env.example`, y una demo reproducible de 1–2 minutos.

## Stack sugerido (no obligatorio)

- Python backend con streaming por sesión (asyncio/websocket) y *hot path*
  **sin LLM orquestador**: audio -> VAD (budget ~3 s) -> STT -> traducción ->
  emisión. `SPEECH_PROVIDER` configurable (gemini | whisper | mock) para bajos
  costos y pruebas offline.
- Emisión de subtítulos por WebSocket/SSE agrupada por `session_id` + `lang`
  con texto parcial (`is_final=false`) y final (`is_final=true`).
- Frontend liviano SIN framework: selector de sesión e idioma, subtítulos en
  vivo y panel de monitoreo de latencia.

## Criterios de evaluación del jurado (objetivo ≥ 85/100)

| Criterio | Peso | Qué mira el jurado |
|---|---|---|
| Calidad | 25 % | Transcripción precisa incluso con términos técnicos (glosario), mejora continua |
| Latencia | 20 % | Subtítulos con retraso aceptable (budget por etapa, no caro) |
| Escalabilidad | 20 % | Muchas sesiones sin costo prohibitivo (worker por sesión, prohibido LLM en hot path) |
| Despliegue | 15 % | Simple de operar durante un evento (docker, RUNBOOK, `.env.example`) |
| Innovación | 20 % | Features creativas de valor (SRT/VTT, panel de latencia, OBS, multi-idioma) |

## Requisito no negociable (bloqueante del MVP)

El **hot path** del producto (audio -> subtítulo) **no debe pasar por un LLM ni
por agentes**; debe ser un pipeline de streaming por sesión. El **sistema de
agentes solo construye**; el producto que generan corre standalone.

## Entregables del MVP (contracts que fija architect)

- `spec/ARCHITECTURE.md`, `spec/INTERFACES.md`, `spec/MESSAGE_SCHEMA.json`,
  `spec/tasks.json`: contratos que consumen backend/frontend/qa.
- Entrypoint de demo exigido: `demo/main.py --sessions N` con líneas de salida
  `METRIC <clave>=<valor>` (al menos `sessions_ok`, `errors`, latencia por etapa).
- Tests deterministas sin red y README honesto que explique el escalado.