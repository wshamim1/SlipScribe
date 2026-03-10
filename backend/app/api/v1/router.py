"""
Main API router
Includes all API endpoint routers
"""
from fastapi import APIRouter

from app.api.v1.endpoints import receipts, search, dashboard, insights, exports

api_router = APIRouter()

# Include endpoint routers
api_router.include_router(
    receipts.router,
    prefix="/receipts",
    tags=["receipts"]
)

api_router.include_router(
    search.router,
    prefix="/search",
    tags=["search"]
)

api_router.include_router(
    dashboard.router,
    prefix="/dashboard",
    tags=["dashboard"]
)

api_router.include_router(
    insights.router,
    prefix="/insights",
    tags=["insights"]
)

api_router.include_router(
    exports.router,
    prefix="/exports",
    tags=["exports"]
)
