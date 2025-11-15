"""
FastAPI Backend for Server Building Dashboard
Implements SAML2 authentication and all required API endpoints
"""
from fastapi import FastAPI, Depends, HTTPException, status, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import RedirectResponse
from fastapi.security import HTTPBearer
from contextlib import asynccontextmanager
from datetime import datetime, timedelta
import secrets
import time

from app.config import settings
from app.auth import saml_auth, get_current_user
from app.models import User
from app.routers import build, preconfig, assign, server
from app.middleware import SecurityHeadersMiddleware, RateLimitMiddleware
from app.logger import (
    app_logger,
    auth_logger,
    api_logger,
    log_startup,
    log_request,
    log_auth_event,
    log_error
)

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan events"""
    log_startup()
    app_logger.info(f"CORS Origins: {settings.CORS_ORIGINS}")
    yield
    app_logger.info("Shutting down Server Building Dashboard Backend")

# Initialize FastAPI app
app = FastAPI(
    title="Server Building Dashboard API",
    version="1.0.0",
    description="API for server build monitoring and management",
    lifespan=lifespan,
    docs_url="/api/docs" if settings.ENVIRONMENT == "development" else None,
    redoc_url="/api/redoc" if settings.ENVIRONMENT == "development" else None,
)

# Request logging middleware
@app.middleware("http")
async def log_requests(request: Request, call_next):
    """Log all requests with timing"""
    start_time = time.time()

    # Get client IP
    client_ip = request.client.host if request.client else "unknown"
    if forwarded_for := request.headers.get("X-Forwarded-For"):
        client_ip = forwarded_for.split(",")[0].strip()

    # Process request
    response = await call_next(request)

    # Calculate duration
    duration_ms = (time.time() - start_time) * 1000

    # Log the request
    log_request(
        endpoint=request.url.path,
        method=request.method,
        status_code=response.status_code,
        duration_ms=duration_ms,
        client_ip=client_ip
    )

    return response

# Add security headers middleware
app.add_middleware(SecurityHeadersMiddleware)

# Add rate limiting middleware
app.add_middleware(RateLimitMiddleware)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["*"],
    expose_headers=["*"],
    max_age=3600,
)

# Include routers
app.include_router(build.router, prefix="/api", tags=["build"])
app.include_router(preconfig.router, prefix="/api", tags=["preconfig"])
app.include_router(assign.router, prefix="/api", tags=["assign"])
app.include_router(server.router, prefix="/api", tags=["server"])

# Health check endpoint
@app.get("/health", tags=["health"])
async def health_check():
    """Health check endpoint for monitoring"""
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "version": "1.0.0"
    }

# Authentication endpoints
@app.get("/saml/login", tags=["auth"])
async def saml_login(request: Request):
    """Initiate SAML login"""
    try:
        log_auth_event("SAML login initiated", details="Redirecting to IDP")
        auth_request = saml_auth.prepare_auth_request(request)
        return RedirectResponse(
            url=auth_request['url'],
            status_code=status.HTTP_302_FOUND
        )
    except Exception as e:
        log_error(e, context="SAML login initialization")
        log_auth_event("SAML login failed", success=False, details=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="SAML authentication initialization failed"
        )

@app.post("/auth/callback", tags=["auth"])
async def saml_callback(request: Request, response: Response):
    """Handle SAML callback"""
    try:
        form_data = await request.form()
        saml_response = form_data.get("SAMLResponse")

        if not saml_response:
            log_auth_event("SAML callback failed", success=False, details="Missing SAMLResponse")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Missing SAMLResponse"
            )

        user_data = saml_auth.process_saml_response(saml_response, request)

        # Create session token
        session_token = secrets.token_urlsafe(32)

        # Store session (in production, use Redis or similar)
        saml_auth.store_session(session_token, user_data)

        # Set secure cookie
        response.set_cookie(
            key="session_token",
            value=session_token,
            httponly=True,
            secure=settings.ENVIRONMENT == "production",
            samesite="lax",
            max_age=settings.SESSION_LIFETIME_SECONDS,
            domain=settings.COOKIE_DOMAIN
        )

        log_auth_event("User authenticated", user_email=user_data.get('email'), success=True)

        # Redirect to frontend
        return RedirectResponse(
            url=f"{settings.FRONTEND_URL}/auth/callback",
            status_code=status.HTTP_302_FOUND
        )

    except Exception as e:
        log_error(e, context="SAML callback processing")
        log_auth_event("SAML authentication failed", success=False, details=str(e))
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="SAML authentication failed"
        )

@app.get("/me", tags=["auth"])
async def get_me(current_user: User = Depends(get_current_user)):
    """Get current user information"""
    return current_user

@app.post("/logout", tags=["auth"])
async def logout(response: Response, current_user: User = Depends(get_current_user)):
    """Logout and clear session"""
    # Clear session cookie
    response.delete_cookie(
        key="session_token",
        domain=settings.COOKIE_DOMAIN
    )

    log_auth_event("User logged out", user_email=current_user.email, success=True)

    return {"status": "success", "message": "Logged out successfully"}

# Root endpoint
@app.get("/", tags=["root"])
async def root():
    """Root endpoint"""
    return {
        "name": "Server Building Dashboard API",
        "version": "1.0.0",
        "status": "running"
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.ENVIRONMENT == "development",
        log_level="info"
    )