# Checklist MVP (referencia del reviewer)

Verifica los 6 requisitos minimos del brief:

1. Audio en vivo de al menos una fuente (mic, archivo o stream) con audios de
   prueba en el repo y opcion simple de importarlos.
2. Transcripcion en tiempo real del idioma original (es o en).
3. Traduccion en tiempo real de ingles a espanol.
4. Mostrar subtitulos (web, overlay o terminal).
5. Procesar al menos 2 sesiones simultaneas y README que explique como escalar.
6. Repositorio con licencia OSI (Apache 2.0 o MIT) y README con credenciales
   necesarias y pasos para levantar.

La tool `check_mvp_checklist()` escanea el codigo generado de forma
determinista y devuelve si/verificacion por item, incluyendo ausencia de
secretos hardcodeados y exportador SRT/VTT.