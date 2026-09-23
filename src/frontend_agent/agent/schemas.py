"""Schemas del Frontend Agent."""

from pydantic import BaseModel, Field


class FrontendReport(BaseModel):
    """Salida del frontend luego de implementar la vista."""

    written_files: list[str] = Field(default_factory=list, description="archivos en <out>/frontend/")
    entrypoint: str = Field(default="static/index.html", description="pagina principal")
    endpoints_used: list[str] = Field(default_factory=list, description="ws/sse del contrato")
    language_selector: bool = Field(default=True)
    blockers: list[str] = Field(default_factory=list)
    summary: str = Field(default="", description="resumen de la vista implementada")