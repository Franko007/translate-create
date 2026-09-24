# Deploy en Google Cloud Run

Proyecto: `high-magpie-509513-b6` (region `europe-west1`). Los
agentes ya viven en este repo; el deploy compila 4 imagenes y las corre en
Cloud Run. El que te interesa para "correr los agentes y que generen el MVP"
es el **job `generate-mvp`**: en una sola ejecucion corre el planner + los
sub-agentes (architect, backend, frontend, qa, reviewer, docs) con backend/
frontend como `AgentTool` local, escribe el MVP en una **carpeta montada de
GCS**, y vos lo bajas en zip.

## 0. Prerequisitos

```bash
gcloud auth login
gcloud auth application-default login
gcloud config set project high-magpie-509513-b6
gsutil config   # si nunca lo usaste
```

## 1. Setup una vez (APIs + SA + Artifact Registry + bucket)

```bash
bash infra/deploy.sh setup
```

`setup` crea la SA `nivel1-builder` con `roles/aiplatform.user`
(Vertex AI), `roles/logging.logWriter` y `roles/storage.objectAdmin`, el repo
`agents` en Artifact Registry y el bucket `high-magpie-509513-b6-mvp`.

## 2. Compilar y subir las imagenes (planner/backend/frontend/job)

```bash
bash infra/deploy.sh build
```

Cloud Build tarda varios minutos (google-cloud-aiplatform + adk son grandes).

## 3. Correr los agentes: generar el MVP

```bash
bash infra/deploy.sh run
```

- Deploya el job `generate-mvp` (`infra/job.yaml.tpl`) y lo ejecuta.
- `OUT_DIR=/mnt/outs/generated/nerdearla-subtitles` sobre el bucket GCS
  (filesystem efimero de Cloud Run + volumen persistente).
- Los agentes llaman a Vertex AI con la SA del job (`GOOGLE_GENAI_USE_VERTEXAI
  =true`), sin API key. `APPROVAL_MODE=yes` para headless.
- La corrida tarda minutos-horas segun el presupuesto; timeout 3600 s.
- Artefactos: `gs://high-magpie-509513-b6-mvp/generated/nerdearla-subtitles/`.

## 4. Bajar el MVP generado y comprimirlo en zip

```bash
bash infra/deploy.sh pull          # -> downloads/nerdearla-subtitles/ + .zip
bash infra/deploy.sh pull mi/carpeta
```

Consulta rapida desde el bucket:

```bash
gsutil -m cp -r gs://high-magpie-509513-b6-mvp/generated/nerdearla-subtitles ./downloads/
```

## (Opcional) Topologia distribuida con servicios A2A

Si queres backend/frontend como servicios separados (permiten re-escalarlos o
ponerlos en zonas distintas):

```bash
bash infra/deploy.sh setup && bash infra/deploy.sh build && bash infra/deploy.sh services
```

Deploya `backend`, `frontend` y `planner` como servicios Cloud Run
(maxScale=1, concurrency=1). El planner se re-deploya con
`BACKEND_AGENT_RESOURCE_NAME`/`FRONTEND_AGENT_RESOURCE_NAME` apuntando a las
URLs de los otros servicios. Despues disparas un build desde tu maquina:

```bash
uv run python scripts/send_task.py --url https://planner-xxxx.a.run.app --output build_report.json
```

Nota: en este modo los servicios no escriben nada a disco; si queres que el
MVP persista, montales el mismo volumen GCS en el job (paso 3) o usa el job
con `OUT_DIR` como arriba.

## Despliegue manual suave (muy basico, sin jobs)

```bash
docker build --target job -t gcr.io/high-magpie-509513-b6/generate-mvp .
docker push gcr.io/high-magpie-509513-b6/generate-mvp
gcloud run jobs create generate-mvp \
  --image=gcr.io/high-magpie-509513-b6/generate-mvp \
  --region=europe-west1 --service-account=nivel1-builder \
  --set-env-vars=GOOGLE_CLOUD_PROJECT=high-magpie-509513-b6,GOOGLE_CLOUD_LOCATION=global,GOOGLE_GENAI_USE_VERTEXAI=true,APPROVAL_MODE=yes,MAX_FIX_ITERATIONS=3,MAX_TOKENS_BUDGET=200000,OUT_DIR=/mnt/outs/generated/nerdearla-subtitles
gcloud run jobs update generate-mvp \
  --add-volume=outs=bucket=high-magpie-509513-b6-mvp \
  --add-volume-mount=outs=/mnt/outs
gcloud run jobs execute generate-mvp --wait
```

## Costos y limites

- Limits de imagen: ~2 GiB de RAM que proponemos por instancia; ahorra con
  `--memory=1Gi --cpu=1` si el build no completa por timeout antes que por RAM.
- El build consume varias llamadas a Gemini: controla el costo con
  `MAX_TOKENS_BUDGET` y modelos livianos (`PLANNER_MODEL=gemini-3.5-flash` para
  mas calidad del orquestador o el default).
- El job tiene timeout 3600 s; si se agota, subi `timeoutSeconds` en el yaml o
  reduci `MAX_FIX_ITERATIONS`.

## Troubleshooting

### "The user-provided container failed to start and listen on PORT=8080"

Causa: el container tardaba en bindear el puerto porque importaba ADK/vertexai
antes de levantar uvicorn y Cloud Run cortaba el startup.

Fixes ya aplicados en el repo:
- Los executors (`src/*/runtime/agent_executor.py`) importan
  `vertexai`/`google.adk` recien en el primer task (lazy); el server bindea en
  `0.0.0.0:$PORT` en segundos.
- Los `agent_card.py` YA NO importan vertexai: el AgentCard se arma a mano con
  `a2a.types` (misma forma que el helper de `vertexai.preview...`). En el
  path de startup solo quedan imports livianos (uvicorn, a2a-sdk, pydantic).
- `infra/service.yaml.tpl` suma `startupProbe` TCP (timeout 300 s) y
  `run.googleapis.com/startup-cpu-boost: "true"`.

Si deployas un servicio a mano (no via `deploy.sh services`) dale memoria
suficiente: el primer task importa ADK/vertexai y usa 1-2 GiB.

```bash
gcloud run services update <servicio> --memory=2Gi --cpu=2 --region europe-west1
```

Despues de tocar codigo recorda recompilar con un tag nuevo y redeployar:

```bash
bash infra/deploy.sh build        # genera un TAG nuevo (fecha/hora)
bash infra/deploy.sh services     # redeploya con la nueva imagen
```

### Si deployas con "gcloud run deploy --source ." (Buildpacks)

Una imagen `cloud-run-source-deploy/...` en el servicio indica que se uso
source-deploy, no nuestro Dockerfile. Ese flujo necesita `Procfile` + 
`requirements.txt` en la raiz (ya estan en el repo). El Procfile arranca el
planner; para otro agente cambia el modulo.

```bash
gcloud run deploy develop1 --source . \
  --region europe-west1 --port=8080 --cpu=2 --memory=2Gi \
  --service-account=nivel1-builder@high-magpie-509513-b6.iam.gserviceaccount.com
```

Mirar logs del servicio:

```bash
gcloud run services logs read <backend|frontend|planner> --region europe-west1 --limit 50
```