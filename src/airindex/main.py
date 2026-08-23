"""FastAPI application entry point."""

from fastapi import FastAPI

from airindex import __version__
from airindex.config import get_settings

settings = get_settings()

app = FastAPI(
    title=settings.app_name,
    version=__version__,
    description="Real-time airfare intelligence and CPI augmentation platform for India.",
)


@app.get("/health", tags=["system"])
async def health() -> dict[str, str]:
    """Return a lightweight liveness response."""

    return {
        "status": "ok",
        "service": settings.app_name,
        "version": __version__,
    }


@app.get("/", tags=["system"])
async def root() -> dict[str, str]:
    """Return basic service metadata."""

    return {
        "service": settings.app_name,
        "version": __version__,
        "docs": "/docs",
        "health": "/health",
    }
