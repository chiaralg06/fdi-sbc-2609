"""Punto de entrada del proyecto: `uv run -m sbc`."""

import runpy
import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RAIZ))

runpy.run_path(str(RAIZ / "main.py"), run_name="__main__")
