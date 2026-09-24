"""A2A Agent Card for the Backend Agent.

Cuidado: NO importar vertexai/google-cloud-aiplatform aca. El card se arma a
mano para que el container bindee el puerto en segundos y no reviente el
startupProbe de Cloud Run. vertexai se importa recien en el primer task.
"""

from a2a.types import AgentCapabilities, AgentCard, AgentSkill


def create_backend_card() -> AgentCard:
    card = AgentCard(
        name="backend_agent",
        description=(
            "Backend Agent - implementa el backend del MVP de transcripcion "
            "simultanea. Servicio A2A deployable en Cloud Run."
        ),
        url="http://127.0.0.1:8095",
        version="0.1.0",
        default_input_modes=["text/plain"],
        default_output_modes=["text/plain"],
        capabilities=AgentCapabilities(streaming=True),
        skills=[
            AgentSkill(
                id="implement_backend",
                name="Implement the transcription backend",
                description=(
                    "Implementa el pipeline de audio->subtitulo, los proveedores de STT/"
                    "traduccion y el servidor multi-sesion del producto generado."
                ),
                tags=["backend", "transcription", "codegen"],
            )
        ],
    )
    if card.capabilities is None:
        card.capabilities = AgentCapabilities(streaming=True)
    else:
        card.capabilities.streaming = True
    return card