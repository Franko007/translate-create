"""A2A Agent Card for the Planner Agent."""

from a2a.types import AgentCapabilities, AgentSkill


def _create_agent_card(
    agent_name: str,
    description: str,
    skills: list[AgentSkill],
    url: str = "http://127.0.0.1:8084",
):
    """Usa el helper de vertexai si esta; si no, arma el AgentCard a mano.

    El import de vertexai vive DENTRO de la funcion: importarlo al modulo
    demoraria el bind del puerto en Cloud Run (startup probe).
    """
    try:
        from vertexai.preview.reasoning_engines.templates.a2a import create_agent_card
        return create_agent_card(agent_name=agent_name, description=description, skills=skills)
    except ImportError:  # pragma: no cover
        from a2a.types import AgentCard
        return AgentCard(
            name=agent_name,
            description=description,
            url=url,
            version="0.1.0",
            default_input_modes=["text/plain"],
            default_output_modes=["text/plain"],
            capabilities=AgentCapabilities(streaming=True),
            skills=skills,
        )


def create_planner_card() -> None:
    skill = AgentSkill(
        id="build_vibeathon_mvp",
        name="Generate the vibeathon MVP",
        description=(
            "Coordina a los agentes constructores para GENERAR el MVP de "
            "transcripcion y traduccion simultanea (backend, frontend, qa, docs)."
        ),
        tags=["vibeathon", "transcription", "codegen", "orchestration"],
    )
    card = _create_agent_card(
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