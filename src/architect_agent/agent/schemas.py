"""Schemas del Architect Agent."""

from pydantic import BaseModel, Field


class ProjectSpec(BaseModel):
    """Confirmacion de que los contratos quedaron escritos."""

    contracts_written: list[str] = Field(default_factory=list, description="rutas en <out>/spec/")
    latency_budget_s: float = Field(default=8.0, description="presupuesto end-to-end (subtitulo final)")
    hot_path_no_llm: bool = Field(default=True, description="el pipeline no pasa por un orquestador LLM")
    measure_stages: list[str] = Field(default_factory=list, description="etapas con t_* medidos")
    blockers: list[str] = Field(default_factory=list)
    summary: str = Field(default="", description="resumen de la arquitectura acordada")