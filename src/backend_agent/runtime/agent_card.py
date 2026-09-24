"""A2A Agent Card for the Backend Agent."""

from a2a.types import AgentCapabilities, AgentSkill


def _create_agent_card(
    agent_name: str,
    description: str,
    skills: list[AgentSkill],
    url: str = "http://127.0.0.1:8095",
):
    """Igual que planner: vertexai se importa recien aca (startup rapido)."""
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


def create_backend_card() -> None:
    skill = AgentSkill(
        id="implement_backend",
        name="Implement the transcription backend",
        description=(
            "Implementa el pipeline de audio->subtitulo, los proveedores de STT/"
            "traduccion y el servidor multi-sesion del producto generado."
        ),
        tags=["backend", "transcription", "codegen"],
    )
    return _create_agent_card(
        agent_name="backend_agent",
        description=(
            "Backend Agent - implementa el backend del MVP de transcripcion "
            "simultanea. Servicio A2A deployable en Cloud Run."
        ),
        skills=[skill],
    )