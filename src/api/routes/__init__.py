"""Routes package for Pocket Portals API.

Aggregates all route modules and exports a combined router.
"""

from fastapi import APIRouter

from src.api.routes.adventure import mount_static_files
from src.api.routes.adventure import router as adventure_router
from src.api.routes.agents import router as agents_router
from src.api.routes.combat import router as combat_router
from src.api.routes.health import router as health_router

# Create main router that includes all sub-routers
router = APIRouter()

# Include all route modules
router.include_router(health_router)
router.include_router(adventure_router)
router.include_router(combat_router)
router.include_router(agents_router)

__all__ = [
    "mount_static_files",
    "router",
    "health_router",
    "adventure_router",
    "combat_router",
    "agents_router",
]
