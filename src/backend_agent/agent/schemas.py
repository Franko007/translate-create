"""Schemas del Backend Agent."""

from pydantic import BaseModel, Field


class BackendReport(BaseModel):
    """Salida del backend luego de implementar (o corregir) el codigo."""

    written_files: list[str] = Field(default_factory=list, description="archivos en <out>/backend/")
    providers: list[str] = Field(default_factory=list, description="gemini | whisper | mock")
    sessions_supported: int = Field(default=2, ge=1, description="sesiones simultaneas")
    implements_message_schema: bool = Field(default=True)
    measured_stages: list[str] = Field(default_factory=list, description="t_* medidos")
    blockers: list[str] = Field(default_factory=list)
    summary: str = Field(default="", description="resumen de la implementacion")