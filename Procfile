# Google Cloud Buildpacks (gcloud run deploy --source .) necesita un Procfile
# para saber como arrancar. Deploying el servicio A2A del planner:
web: python -m src.planner_agent.runtime.local_server
# Para backend/frontend cambiar el modulo: src.backend_agent.runtime.local_server
# Para el job no se usa este Procfile (CDM dockerfile: scripts/build_project.py)