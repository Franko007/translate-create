"""Schemas del Reviewer Agent."""

from pydantic import BaseModel, Field


class ReviewFinding(BaseModel):
    """Una correccion priorizada."""

    severity: str = Field(description="critico | alto | medio | bajo")
    area: str = Field(description="archivo o area del producto")
    issue: str = Field(description="que falta o esta mal")
    how_to_fix: str = Field(description="correccion accionable")
    how_to_verify: str = Field(description="como probar la correccion")


class ReviewReport(BaseModel):
    """Veredicto del reviewer sobre el proyecto generado."""

    overall_score: float = Field(ge=0.0, le=100.0)
    dimensions: dict[str, float] = Field(
        default_factory=dict,
        description="scores por dimension (calidad, latencia, escalabilidad, despliegue, innovacion)",
    )
    mvp_check: dict = Field(default_factory=dict, description="resultado de check_mvp_checklist()")
    approved: bool = Field(default=False, description="overall_score >= 85 y sin blockers")
    blockers: list[str] = Field(default_factory=list)
    corrections: list[ReviewFinding] = Field(default_factory=list, description="priorizadas")
    summary: str = Field(default="")