"""Health check endpoint for Pocket Portals API."""

from fastapi import APIRouter, Depends, Request

from src.api.models import HealthResponse
from src.api.rate_limiting import require_rate_limit
from src.config.settings import settings

router = APIRouter(tags=["health"])


@router.get("/health", response_model=HealthResponse)
async def health_check(
    request: Request,
    _rate_limit: None = Depends(require_rate_limit("default")),
) -> HealthResponse:
    """Health check endpoint."""
    return HealthResponse(status="healthy", environment=settings.environment)
