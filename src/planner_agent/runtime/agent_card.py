"""A2A Agent Card for the Planner Agent.

Cuidado: NO importar vertexai/google-cloud-aiplatform aca. El card se arma a
mano (misma forma que el helper de vertexai) para que el container bindee el
puerto en segundos y no reviente el startupProbe de Cloud Run. vertexai se
importa recien en el primer task (agent_executor).
"""

from a2a.types import AgentCapabilities, AgentCard, AgentSkill


def create_planner_card() -> AgentCard:
    card = AgentCard(
        name="planner_agent",
        description=(
            "Planner Agent - orquesta a los agentes constructores para generar el "
            "proyecto final de la vibeathon a partir del brief. Powered by Gemini."
        ),
        url="http://127.0.0.1:8084",
        version="0.1.0",
        default_input_modes=["text/plain"],
        default_output_modes=["text/plain"],
        capabilities=AgentCapabilities(streaming=True),
        skills=[
            AgentSkill(
                id="build_vibeathon_mvp",
                name="Generate the vibeathon MVP",
                description=(
                    "Coordina a los agentes constructores para GENERAR el MVP de "
                    "transcripcion y traduccion simultanea (backend, frontend, qa, docs)."
                ),
                tags=["vibeathon", "transcription", "codegen", "orchestration"],
            )
        ],
    )
    if card.capabilities is None:
        card.capabilities = AgentCapabilities(streaming=True)
    else:
        card.capabilities.streaming = True
    return card