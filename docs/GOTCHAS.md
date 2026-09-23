# GOTCHAS — trampas conocidas del Nivel 1

## Deploy/entorno

- `vertexai.init` solo se ejecuta si `GOOGLE_CLOUD_PROJECT` está seteado; con
  `GEMINI_API_KEY` el SDK usa Gemini API por defecto. Si mezclas ambos, Vertex
  gana y la key API se ignora (silencio).
- Los `local_server.py` setean `GOOGLE_GENAI_USE_VERTEXAI=true` por default;
  para forzar API key, setealos antes de levantar el server.
- `run_command` usa `shell=True` en Windows; solo se aceptan prefijos whitelist.
  Ningún comando con `sudo`, `curl`, `rm -rf` o `&& rm` pasa aunque venga
  "disfrazado".

## Sandbox / generación

- Los scopes de escritura están fijados por build, no por el LLM. Un agente que
  intente escribir fuera de su scope recibe `ValueError` determinista.
- `write_file` SIEMPRE sobrescribe; `apply_patch` exige que el archivo exista y
  que el ancla exista una vez. Los archivos nuevos van con `write_file`, los
  retoques con `apply_patch` (leer antes con `read_file`).
- El prefix `.build_logs/` se usa para `run.log`; `list_tree` y el MVP scan lo
  ignoran a proposito (no es parte del producto). El LLM no debería escribirlo.
- `run_demo` ejecuta el harness con `sys.executable` (no `python` de PATH):
  sobrevive a entornos donde el intérprete solo vive en el venv de `uv`.
- `list_tree` ignora `__pycache__` y `.git`, pero cualquier otro archivo del
  sandbox cuenta para `file_count` (el reviewer valida coherencia, no tam).

## Modelos y presupuestos

- Los modelos por rol están separados: codegen (backend/frontend) usa el modelo
  de codigo; el resto usa el liviano. No los instancies por nombre hardcodeado;
  usa `AGENT_MODELS[<agent>]`.
- `BudgetTracker.start_iteration` permite `iteration <= max_fix_iterations`
  (1-based). El planner que re-despache un fix después del tope debe setear
  `status=budget_exhausted`.
- El hot path del PRODUCTO generado no debe incluir ningún LLM/agente; si un
  contrato de architect propone eso, el reviewer lo marca blocker crítico.

## QA / demo

- `run_demo` valida el contrato `demo/main.py --sessions N` y la presencia de
  audios en `samples/` ANTES de ejecutar; con fallo temprano no ejecuta nada.
- Para `APPROVAL_MODE=ask`, `run_command` de un comando whitelist devuelve
  `approved:false` sin correr; el agente debe reportar `needs_human_approval`.
- Los tests del Nivel 1 (tests/) son offline de propósito: no importan
  `vertexai`/`google.adk` (evitar importorskip innecesario al agregar tests
  nuevos sobre los agentes).

## Windows

- Los comandos del Makefile usan `uv run`; en PowerShell usá `make build` vía
  git-bash o `uv run python scripts/build_project.py` directamente.
- Los `subprocess` dentro del sandbox toman `cwd=<out>`; rutas largas/con
  espacios en `OUT_DIR` pueden romper `shell=True`: preferí `OUT_DIR` corto.
- `uv run --no-project --with pytest python -m pytest tests/... -q` corre los
  tests offline sin instalar deps pesadas; si hay pyproject detectado usá
  `--no-project` como ahí.