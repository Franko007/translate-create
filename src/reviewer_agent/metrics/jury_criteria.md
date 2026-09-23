# Criterios del jurado (referencia del reviewer)

| Criterio | Pregunta rectora | Señales en el codigo generado |
|---|---|---|
| Calidad | ¿Transcripcion precisa incluso con terminos tecnicos? | glosario, verbatim vs transcriptos, providers |
| Latencia | ¿Subtitulos con retraso aceptable? | t_audio_in/t_emitted, medicion por etapa, budget |
| Escalabilidad | ¿Muchas sesiones sin costos prohibitivos? | worker por sesion, redis/pubsub opcional, contenedores |
| Despliegue | ¿Simple de operar durante un evento? | docker compose, .env.example, RUNBOOK |
| Innovacion | ¿Features creativas de valor? | SRT/VTT, panel latencia, OBS, multi-idioma |

El reviewer combina `score_project()` (deterministico, mvp + extras) con
juicio LLM sobre estas dimensiones y devuelve correcciones PRIORIZADAS.