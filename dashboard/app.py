"""Dashboard application skeleton."""

from fastapi import FastAPI


def create_app() -> FastAPI:
    """Create and return the FastAPI application instance."""
    app = FastAPI()
    return app

