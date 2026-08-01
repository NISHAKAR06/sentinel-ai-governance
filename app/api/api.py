"""
api.py — Aggregates all API routers under /api/v1.
"""
from fastapi import APIRouter

from app.api.chat_routes       import router as chat_router
from app.api.governance_routes import router as governance_router
from app.api.review_routes     import router as review_router
from app.api.execution_routes  import router as execution_router
from app.api.dashboard_routes  import router as dashboard_router
from app.api.analytics_routes  import router as analytics_router
from app.api.settings_routes   import router as settings_router
from app.api.audit_routes      import router as audit_router
from app.api.profile_routes    import router as profile_router

api_router = APIRouter()

api_router.include_router(chat_router,       prefix="/chat",       tags=["Chat"])
api_router.include_router(governance_router, prefix="/governance", tags=["Governance"])
api_router.include_router(review_router,     prefix="/review",     tags=["Review"])
api_router.include_router(execution_router,  prefix="/execution",  tags=["Execution"])
api_router.include_router(dashboard_router,  prefix="/dashboard",  tags=["Dashboard"])
api_router.include_router(analytics_router,  prefix="/analytics",  tags=["Analytics"])
api_router.include_router(settings_router,   prefix="/settings",   tags=["Settings"])
api_router.include_router(audit_router,      prefix="/audit",      tags=["Audit"])
api_router.include_router(profile_router,    prefix="/profile",    tags=["Profile"])
