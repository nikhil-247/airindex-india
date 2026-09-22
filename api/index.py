"""Vercel entrypoint for the AirIndex FastAPI application."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from airindex.api.app import app  # noqa: E402

__all__ = ["app"]
