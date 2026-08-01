"""
main.py — Sentinel AI Governance Platform — FastAPI application entry point.
"""
from __future__ import annotations

import time
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse, RedirectResponse, JSONResponse
import uvicorn

from app.config import settings
from app.core.logger import app_logger, log_request, log_response
from app.core.exceptions import SentinelBaseException, to_http_exception


# ── Lifespan: startup + shutdown ──────────────────────────────
@asynccontextmanager
async def lifespan(app: FastAPI):
    app_logger.info("Sentinel AI starting up…")
    # ── Init DB tables ────────────────────────────────────────
    try:
        from app.database.init_db import init_db
        await init_db(seed=False)   # set seed=True on first run
        app_logger.info("Database initialised.")
    except Exception as exc:
        app_logger.error("Database init failed", extra={"error": str(exc)})

    yield

    app_logger.info("Sentinel AI shutting down.")


# ── Application factory ───────────────────────────────────────
app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="Enterprise AI Governance Platform — PS-9.1 Graduated Autonomy Engine",
    docs_url="/api/docs" if settings.DEBUG else None,
    redoc_url="/api/redoc" if settings.DEBUG else None,
    lifespan=lifespan,
)

# ── CORS ──────────────────────────────────────────────────────
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Request logging middleware ────────────────────────────────
@app.middleware("http")
async def logging_middleware(request: Request, call_next):
    start    = time.monotonic()
    log_request(request.method, str(request.url.path))
    response = await call_next(request)
    duration = (time.monotonic() - start) * 1000
    log_response(request.method, str(request.url.path), response.status_code, duration)
    return response

# ── Domain exception handler ──────────────────────────────────
@app.exception_handler(SentinelBaseException)
async def sentinel_exception_handler(request: Request, exc: SentinelBaseException):
    http_exc = to_http_exception(exc)
    return JSONResponse(
        status_code=http_exc.status_code,
        content={"detail": http_exc.detail},
    )

# ── Static files ──────────────────────────────────────────────
app.mount(
    "/static",
    StaticFiles(directory=str(settings.STATIC_DIR)),
    name="static",
)

# ── Jinja2 templates ──────────────────────────────────────────
templates = Jinja2Templates(directory=str(settings.TEMPLATES_DIR))

# ── HTML page routes ──────────────────────────────────────────
@app.get("/",          response_class=HTMLResponse, include_in_schema=False)
async def root(request: Request):
    return RedirectResponse(url="/dashboard")

@app.get("/login",     response_class=HTMLResponse, include_in_schema=False)
async def login_page(request: Request):
    return templates.TemplateResponse("login.html", {"request": request})

@app.get("/dashboard", response_class=HTMLResponse, include_in_schema=False)
async def dashboard_page(request: Request):
    return templates.TemplateResponse("dashboard.html", {"request": request})

@app.get("/assistant", response_class=HTMLResponse, include_in_schema=False)
async def assistant_page(request: Request):
    return templates.TemplateResponse("assistant.html", {"request": request})

@app.get("/governance",response_class=HTMLResponse, include_in_schema=False)
async def governance_page(request: Request):
    return templates.TemplateResponse("governance.html", {"request": request})

@app.get("/review",    response_class=HTMLResponse, include_in_schema=False)
async def review_page(request: Request):
    return templates.TemplateResponse("review.html", {"request": request})

@app.get("/audit",     response_class=HTMLResponse, include_in_schema=False)
async def audit_page(request: Request):
    return templates.TemplateResponse("audit_logs.html", {"request": request})

@app.get("/analytics", response_class=HTMLResponse, include_in_schema=False)
async def analytics_page(request: Request):
    return templates.TemplateResponse("analytics.html", {"request": request})

@app.get("/settings",  response_class=HTMLResponse, include_in_schema=False)
async def settings_page(request: Request):
    return templates.TemplateResponse("settings.html", {"request": request})

@app.get("/profile",   response_class=HTMLResponse, include_in_schema=False)
async def profile_page(request: Request):
    return templates.TemplateResponse("profile.html", {"request": request})

@app.get("/logout",    include_in_schema=False)
async def logout():
    response = RedirectResponse(url="/login")
    response.delete_cookie("sentinel_token")
    return response

# ── Auth routes ───────────────────────────────────────────────
from typing import Optional
from fastapi import Depends, Header
from app.repositories.employee_repository import EmployeeRepository
from app.core.security import verify_password, create_access_token
from app.dependencies import get_db
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel

class LoginRequest(BaseModel):
    username: str
    password: str

@app.post("/api/v1/auth/login", tags=["Auth"], summary="Login with username + password")
async def login(payload: LoginRequest, db: AsyncSession = Depends(get_db)):
    repo = EmployeeRepository(db)
    employee = await repo.get_by_username(payload.username)
    if employee is None or not verify_password(payload.password, employee.hashed_password):
        return JSONResponse(status_code=401, content={"detail": {"code": "AUTH_ERROR", "message": "Invalid credentials"}})
    if not employee.is_active:
        return JSONResponse(status_code=403, content={"detail": {"code": "AUTHZ_ERROR", "message": "Account is disabled"}})
    await repo.update_last_login(employee.employee_id)
    token = create_access_token(
        subject=employee.username,
        extra={"role": employee.role, "dept": employee.department, "name": employee.full_name},
    )
    return {"access_token": token, "token_type": "bearer", "user": {"name": employee.full_name, "role": employee.role}}

@app.get("/api/v1/auth/me", tags=["Auth"], summary="Get current user profile")
async def get_me(
    db: AsyncSession = Depends(get_db),
    authorization: Optional[str] = Header(default=None),
):
    from app.dependencies import get_optional_user
    if not authorization:
        return JSONResponse(status_code=401, content={"detail": "Not authenticated"})
    from app.core.security import extract_token, decode_access_token
    try:
        token   = extract_token(authorization)
        payload = decode_access_token(token)
        repo    = EmployeeRepository(db)
        emp     = await repo.get_by_username(payload["sub"])
        if not emp:
            return JSONResponse(status_code=404, content={"detail": "User not found"})
        return {
            "name":       emp.full_name,
            "role":       emp.role,
            "department": emp.department,
            "email":      emp.email,
            "username":   emp.username,
        }
    except Exception as e:
        return JSONResponse(status_code=401, content={"detail": str(e)})

# ── API routers ───────────────────────────────────────────────
from app.api.api import api_router
app.include_router(api_router, prefix="/api/v1")

# ── WebSocket routers ─────────────────────────────────────────
from app.websocket.events import router as ws_router
app.include_router(ws_router)

# ── System health ─────────────────────────────────────────────
@app.get("/health", tags=["System"], summary="Health check")
async def health():
    return {
        "status":  "ok",
        "app":     settings.APP_NAME,
        "version": settings.APP_VERSION,
    }

# ── Dev runner ────────────────────────────────────────────────
if __name__ == "__main__":
    uvicorn.run(
        "app.main:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=settings.DEBUG,
        log_level="debug" if settings.DEBUG else "info",
        ws_ping_interval=20,
        ws_ping_timeout=30,
    )
