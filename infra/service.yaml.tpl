# Plantilla de servicio A2A (backend/frontend). Deploy.sh la renderiza por
# servicio; para el planner en modo distribuido usa otro manifiesto con los
# env de recursos (BACKEND/FRONTEND_AGENT_RESOURCE_NAME).
#
# maxScale=1 + containerConcurrency=1: los agentes son estado en memoria/SSE;
# nunca se escalan a mas de una instancia por build.

apiVersion: serving.knative.dev/v1
kind: Service
metadata:
  name: %NAME%
  labels:
    cloud.googleapis.com/location: %REGION%
spec:
  template:
    metadata:
      annotations:
        autoscaling.knative.dev/maxScale: "1"
        run.googleapis.com/startup-cpu-boost: "true"
    spec:
      containerConcurrency: 1
      timeoutSeconds: 3600
      serviceAccountName: nivel1-builder@%PROJECT%.iam.gserviceaccount.com
      containers:
        - image: %REGION%-docker.pkg.dev/%PROJECT%/%REPO%/%NAME%:%TAG%
          env:
            - name: GOOGLE_CLOUD_PROJECT
              value: %PROJECT%
            - name: GOOGLE_CLOUD_LOCATION
              value: global
            - name: GOOGLE_GENAI_USE_VERTEXAI
              value: "true"
            - name: APPROVAL_MODE
              value: "yes"
            - name: PORT
              value: "8080"
          startupProbe:
            tcpSocket:
              port: 8080
            timeoutSeconds: 300
            periodSeconds: 1
            failureThreshold: 3
          resources:
            limits:
              cpu: "2"
              memory: 4Gi