"""Schemas del Docs Agent."""

from pydantic import BaseModel, Field


class DocsReport(BaseModel):
    """Salida del Docs Agent."""

    written_files: list[str] = Field(default_factory=list, description="README, RUNBOOK, GOTCHAS, guion, checklist")
    readme_covers_scaling: bool = Field(default=False)
    honest_limitations: list[str] = Field(default_factory=list, description="limites reconocidos en la doc")
    blockers: list[str] = Field(default_factory=list)
    summary: str = Field(default="")