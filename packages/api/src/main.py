"""
FastAPI application entry point
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .admin import setup_admin
from .core.config import settings
from .middleware.audit import AuditMiddleware
from .routes import admin as admin_routes
from .routes import (
    applications,
    audit,
    auth,
    chat,
    decisions,
    documents,
    health,
    loans,
    notifications,
    servicer,
    ws,
)
from .services.websocket_manager import manager as ws_manager

app = FastAPI(
    title="MortgageAI API",
    description="AI-powered mortgage loan origination and approval platform",
    version="0.1.0",
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_HOSTS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(health.router, prefix="/health", tags=["health"])
app.include_router(auth.router, prefix="/api/v1/auth", tags=["auth"])
app.include_router(loans.router, prefix="/api/v1/loans", tags=["loans"])
app.include_router(applications.router, prefix="/api/v1/applications", tags=["applications"])
app.include_router(decisions.router, prefix="/api/v1/applications", tags=["decisions"])
app.include_router(
    documents.router,
    prefix="/api/v1/applications/{application_id}/documents",
    tags=["documents"],
)
app.include_router(servicer.router, prefix="/api/v1/servicer", tags=["servicer"])
app.include_router(notifications.router, prefix="/api/v1/notifications", tags=["notifications"])
app.include_router(audit.router, prefix="/api/v1/audit-logs", tags=["audit"])
app.include_router(chat.router, prefix="/api/v1/chat", tags=["chat"])
app.include_router(ws.router, prefix="/api/v1/ws", tags=["websocket"])
app.include_router(admin_routes.router, prefix="/api/v1/admin", tags=["admin"])

# Audit middleware — logs mutating requests to the audit_log table
app.add_middleware(AuditMiddleware)


@app.on_event("startup")
async def startup_ws():
    await ws_manager.start()


@app.on_event("shutdown")
async def shutdown_ws():
    await ws_manager.stop()

# Setup SQLAdmin dashboard at /admin
setup_admin(app)


@app.get("/")
async def root() -> dict[str, str]:
    """Root endpoint"""
    return {"message": "Welcome to MortgageAI API"}
