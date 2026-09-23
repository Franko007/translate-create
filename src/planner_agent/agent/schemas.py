"""Schemas del planner (orquestador)."""

from pydantic import BaseModel, Field


class BuildReport(BaseModel):
    """Structured output del planner al terminar la corrida."""

    status: str = Field(description="ok | rejected | budget_exhausted | needs_human_approval")
    iterations_used: int = Field(default=1, ge=1, description="iteraciones de correccion usadas")
    scores: dict[str, float] = Field(default_factory=dict, description="puntaje por criterio del reviewer")
    mvp_check: dict = Field(default_factory=dict, description="resultado del checklist MVP")
    files_generated: list[str] = Field(default_factory=list, description="archivos generados en OUT_DIR")
    blockers: list[str] = Field(default_factory=list, description="problemas que impiden el OK")
    recommendations: list[str] = Field(default_factory=list, description="proximos pasos")
    summary: str = Field(default="", description="resumen de la corrida")