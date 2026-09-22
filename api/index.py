"""Vercel entrypoint for the AirIndex FastAPI application."""

from airindex.api.app import app

__all__ = ["app"]
