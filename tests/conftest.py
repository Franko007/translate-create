"""Configuracion de tests offline (sin red, sin LLM).

Redirige OUT_DIR a un directorio temporal ANTES de que se importe src.config,
y limpia el sandbox entre tests. Nunca toca la carpeta generated/ real.
"""

from __future__ import annotations

import os
import shutil
import tempfile

import pytest

_TMP = tempfile.mkdtemp(prefix="nivel1_test_")
os.environ["OUT_DIR"] = os.path.join(_TMP, "generated")
os.environ["APPROVAL_MODE"] = "ask"  # determinismo: tests nunca corren comandos
os.environ["MAX_FIX_ITERATIONS"] = "3"
os.environ["MAX_TOKENS_BUDGET"] = "200000"


@pytest.fixture(autouse=True)
def _clean_sandbox():
    from src.config import OUT_DIR
    if OUT_DIR.exists():
        shutil.rmtree(OUT_DIR, ignore_errors=True)
    yield
    if OUT_DIR.exists():
        shutil.rmtree(OUT_DIR, ignore_errors=True)