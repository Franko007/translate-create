#!/usr/bin/env bash
# =============================================================================
# Deploy del Nivel 1 en Cloud Run (proyecto high-magpie-509513-b6)
#
#   bash infra/deploy.sh setup      # APIs + SA + repo + bucket (una vez)
#   bash infra/deploy.sh build      # compila las 4 imagenes y las sube
#   bash infra/deploy.sh services   # OPCIONAL: servicios A2A (backend/frontend/planner)
#   bash infra/deploy.sh run        # ejecuta el job que genera el MVP en el bucket
#   bash infra/deploy.sh pull       # descarga generated/ del bucket y lo zipea
#
# Requiere: gcloud + gsutil autenticados (gcloud auth login; gcloud auth
# application-default login) y docker disponible para Cloud Build.
# =============================================================================
set -euo pipefail

PROJECT_ID="${PROJECT_ID:-high-magpie-509513-b6}"
REGION="${REGION:-us-central1}"
REPO="${REPO:-agents}"
BUCKET="${BUCKET:-${PROJECT_ID}-mvp}"
TAG="${TAG:-$(date +%Y%m%d%H%M%S)}"
SA="nivel1-builder"
SA_EMAIL="${SA}@${PROJECT_ID}.iam.gserviceaccount.com"
REPO_URL="${REGION}-docker.pkg.dev/${PROJECT_ID}/${REPO}"
JOB_IMAGE="${REPO_URL}/job:${TAG}"
OUT="generated/nerdearla-subtitles"
MOUNT="/mnt/outs"

die() { echo "ERROR: $1" >&2; exit 1; }

require() { command -v "$1" >/dev/null 2>&1 || die "falta '$1' en PATH (instala cloud SDK)"; }

g() { echo "  gcloud $*"; gcloud "$@" --project="$PROJECT_ID" --quiet; }

setup() {
  require gcloud
  g config set project "$PROJECT_ID"
  echo ">> Habilitando APIs..."
  g services enable run.googleapis.com artifactregistry.googleapis.com aiplatform.googleapis.com cloudbuild.googleapis.com logging.googleapis.com

  echo ">> Artifact Registry: ${REPO_URL}"
  g artifacts repositories describe "$REPO" --location="$REGION" >/dev/null 2>&1 \
    || g artifacts repositories create "$REPO" \
         --repository-format=docker --location="$REGION" --description="Nivel1 agents"

  echo ">> Bucket: gs://${BUCKET}"
  gsutil ls "gs://${BUCKET}" >/dev/null 2>&1 || gsutil mb -l "$REGION" "gs://${BUCKET}"

  echo ">> Service account ${SA_EMAIL}"
  g iam service-accounts describe "$SA_EMAIL" >/dev/null 2>&1 \
    || g iam service-accounts create "$SA" --display-name="Nivel1 agents builder"
  for role in roles/aiplatform.user roles/logging.logWriter roles/storage.objectAdmin; do
    g projects add-iam-policy-binding "$PROJECT_ID" \
      --member="serviceAccount:${SA_EMAIL}" --role="$role" \
      --condition=None >/dev/null 2>&1 || true
  done
  echo ">> (opcional) dar de alta la SA en Cloud Run billing no hace falta."
  echo "setup OK. bucket=gs://${BUCKET}  sa=${SA_EMAIL}"
}

build() {
  require gcloud
  echo ">> Cloud Build (targets: planner, backend, frontend, job) tag=${TAG}"
  g builds submit . --config infra/cloudbuild.yaml \
    --substitutions "_REGION=${REGION},_REPO=${REPO},_TAG=${TAG},_PROJECT_ID=${PROJECT_ID}"
  echo "build OK. Imagen del job: ${JOB_IMAGE}"
}

render() {
  local src="$1" dst="$2"
  sed -e "s|%PROJECT%|${PROJECT_ID}|g" \
      -e "s|%REGION%|${REGION}|g" \
      -e "s|%BUCKET%|${BUCKET}|g" \
      -e "s|%REPO%|${REPO}|g" \
      -e "s|%TAG%|${TAG}|g" \
      "$src" > "$dst"
  echo "  render -> ${dst}"
}

services() {
  require gcloud
  local plan_yaml="$(mktemp).yaml"
  render infra/service.yaml.tpl "$plan_yaml"
  echo ">> Deploy services backend/frontend/planner (tag=${TAG})"
  for name in backend frontend planner; do
    sed -e "s|%NAME%|${name}|g" "$plan_yaml" > "/tmp/${name}.service.yaml"
    g run services replace "/tmp/${name}.service.yaml" --region "$REGION"
  done
  # planner distribuido: apuntar a backend/frontend via env
  local be_url fe_url
  be_url="$(g run services describe backend --region="$REGION" --format='value(status.url)')"
  fe_url="$(g run services describe frontend --region="$REGION" --format='value(status.url)')"
  python3 - "$be_url" "$fe_url" "${REGION}" "${PROJECT_ID}" "${TAG}" "${REPO}" <<'PY'
import sys
be, fe, region, project, tag, repo = sys.argv[1:]
yaml = f"""apiVersion: serving.knative.dev/v1
kind: Service
metadata:
  name: planner
  labels:
    cloud.googleapis.com/location: {region}
spec:
  template:
    spec:
      containerConcurrency: 1
      timeoutSeconds: 3600
      serviceAccountName: nivel1-builder@{project}.iam.gserviceaccount.com
      containers:
        - image: {region}-docker.pkg.dev/{project}/{repo}/planner:{tag}
          env:
            - name: GOOGLE_CLOUD_PROJECT
              value: {project}
            - name: GOOGLE_CLOUD_LOCATION
              value: global
            - name: GOOGLE_GENAI_USE_VERTEXAI
              value: "true"
            - name: APPROVAL_MODE
              value: "yes"
            - name: BACKEND_AGENT_RESOURCE_NAME
              value: {be}
            - name: FRONTEND_AGENT_RESOURCE_NAME
              value: {fe}
"""
open("/tmp/planner.dist.yaml", "w").write(yaml)
PY
  g run services replace /tmp/planner.dist.yaml --region "$REGION"
  echo "services OK. Planner URL: $(g run services describe planner --region="$REGION" --format='value(status.url)')"
}

run_job() {
  require gcloud
  render infra/job.yaml.tpl /tmp/generate-mvp.yaml
  echo ">> Deploy + ejecutar job generate-mvp (OUT=$MOUNT/$OUT)"
  g run jobs replace /tmp/generate-mvp.yaml --region "$REGION"
  g run jobs execute generate-mvp --region "$REGION" --wait
  echo "job OK. Verifica: gs://${BUCKET}/${OUT}/.build_logs/build_report.md"
}

pull() {
  require gsutil
  local dst="${1:-downloads}"
  mkdir -p "$dst"
  echo ">> Descargando gs://${BUCKET}/${OUT} -> ${dst}/"
  gsutil -m cp -r "gs://${BUCKET}/${OUT}" "$dst/"
  pushd "$dst/$(basename "$OUT")" >/dev/null 2>&1 || true
  popd >/dev/null 2>&1 || true
  (cd "$dst" && python3 -m zipfile -c nerdearla-subtitles.zip nerdearla-subtitles) 2>/dev/null \
    || (cd "$dst" && zip -qr nerdearla-subtitles.zip nerdearla-subtitles) \
    || echo "Zip manual: comprime ${dst}/nerdearla-subtitles"
  echo "pull OK: ${dst}/nerdearla-subtitles/  (+ ${dst}/nerdearla-subtitles.zip)"
}

cmd="${1:-help}"
case "$cmd" in
  setup)   setup ;;
  build)   build ;;
  services) services ;;
  run)     run_job ;;
  pull)    pull "${2:-downloads}" ;;
  *) echo "uso: $0 {setup|build|services|run|pull}";;
esac