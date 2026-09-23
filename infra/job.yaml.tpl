# Plantilla del Cloud Run Job que GENERA el MVP (los 7 agentes corren adentro).
# Lo renderiza deploy.sh (reemplaza %PROJECT%, %REGION%, %BUCKET%, %TAG%).
#
# Referencia: external/multi-agent team. Env vars criticas:
#   - OUT_DIR sobre un volumen GCS: el filesystem de Cloud Run es efimero.
#   - GOOGLE_GENAI_USE_VERTEXAI=true => Vertex AI con la SA del job (sin API key).
#   - APPROVAL_MODE=yes => headless (qa no se traba pidiendo aprobacion humana).

apiVersion: run.googleapis.com/v1
kind: Job
metadata:
  name: generate-mvp
  labels:
    cloud.googleapis.com/location: %REGION%
spec:
  template:
    spec:
      template:
        spec:
          restartPolicy: Never
          timeoutSeconds: 3600
          serviceAccountName: nivel1-builder@%PROJECT%.iam.gserviceaccount.com
          containers:
            - image: %REGION%-docker.pkg.dev/%PROJECT%/agents/job:%TAG%
              env:
                - name: GOOGLE_CLOUD_PROJECT
                  value: %PROJECT%
                - name: GOOGLE_CLOUD_LOCATION
                  value: global
                - name: GOOGLE_GENAI_USE_VERTEXAI
                  value: "true"
                - name: APPROVAL_MODE
                  value: "yes"
                - name: MAX_FIX_ITERATIONS
                  value: "3"
                - name: MAX_TOKENS_BUDGET
                  value: "200000"
                - name: OUT_DIR
                  value: /mnt/outs/generated/nerdearla-subtitles
              volumeMounts:
                - name: outs
                  mountPath: /mnt/outs
          volumes:
            - name: outs
              gcs:
                bucket: %BUCKET%
                readOnly: false