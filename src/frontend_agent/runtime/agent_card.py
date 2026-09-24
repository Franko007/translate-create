"""A2A Agent Card for the Frontend Agent.

Cuidado: NO importar vertexai/google-cloud-aiplatform aca. El card se arma a
mano para que el container bindee el puerto en segundos y no reviente el
startupProbe de Cloud Run. vertexai se importa recien en el primer task.
"""

from a2a.types import AgentCapabilities, AgentCard, AgentSkill


def create_frontend_card() -> AgentCard:
    card = AgentCard(
        name="frontend_agent",
        description=(
            "Frontend Agent - implementa la vista de audiencia del MVP de "
            "transcripcion simultanea. Servicio A2A deployable en Cloud Run."
        ),
        url="http://127.0.0.1:8096",
        version="0.1.0",
        default_input_modes=["text/plain"],
        default_output_modes=["text/plain"],
        capabilities=AgentCapabilities(streaming=True),
        skills=[
            AgentSkill(
                id="implement_frontend",
                name="Implement the audience view",
                description=(
                    "Implementa la vista de audiencia del producto generado: selector de "
                    "sesion e idioma y subtitulos en vivo."
                ),
                tags=["frontend", "captions", "codegen"],
            )
        ],
    )
    if card.capabilities is None:
        card.capabilities = AgentCapabilities(streaming=True)
    else:
        card.capabilities.streaming = True
    return card