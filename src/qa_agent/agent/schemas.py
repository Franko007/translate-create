"""Schemas del QA Agent."""

from pydantic import BaseModel, Field


class TestRunReport(BaseModel):
    """Salida del QA al terminar de testear y correr la demo."""

    tests_written: list[str] = Field(default_factory=list, description="archivos en <out>/tests/")
    tests_ok: bool = Field(default=False)
    test_output: str = Field(default="", description="tail del comando pytest")
    demo_ok: bool = Field(default=False)
    demo_metrics: dict = Field(default_factory=dict, description="metricas METRIC de la demo")
    demo_latency_by_stage: dict = Field(default_factory=dict)
    failures: list[str] = Field(default_factory=list, description="fallas con logs concretos")
    recommendations: list[str] = Field(default_factory=list)
    needs_approval: bool = Field(default=False)
    summary: str = Field(default="")