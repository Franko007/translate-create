"""A2A Agent Card for the Planner Agent."""

from a2a.types import AgentCapabilities, AgentCard, AgentSkill

try:
    from vertexai.preview.reasoning_engines.templates.a2a import create_agent_card
except ImportError:  # pragma: no cover
    # Mismo fallback a mano que el repo de referencia (docs/GOTCHAS.md): el
    # helper vive bajo preview y se mueve entre SDKs.
    def create_agent_card(agent_name, description, skills, **kwargs):
        return AgentCard(
            name=agent_name,
            description=description,
            url="http://127.0.0.1:8084",
            version="0.1.0",
            default_input_modes=["text/plain"],
            default_output_modes=["text/plain"],
            capabilities=AgentCapabilities(streaming=True),
            skills=skills,
        )


def create_planner_card() -> AgentCard:
    skill = AgentSkill(
        id="build_vibeathon_mvp",
        name="Generate the vibeathon MVP",
        description=(
            "Coordina a los agentes constructores para GENERAR el MVP de "
            "transcripcion y traduccion simultanea (backend, frontend, qa, docs)."
        ),
        tags=["vibeathon", "transcription", "codegen", "orchestration"],
    )
    card = create_agent_card(
        agent_name="planner_agent",
        description=(
            "Planner Agent - orquesta a los agentes constructores para generar el "
            "proyecto final de la vibeathon a partir del brief. Powered by Gemini."
        ),
        skills=[skill],
    )
    if card.capabilities is None:
        card.capabilities = AgentCapabilities(streaming=True)
    else:
        card.capabilities.streaming = True
    return card