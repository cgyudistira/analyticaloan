"""
API Gateway Service
Centralized entry point for all microservices
Features: Routing, Rate Limiting, Authentication, CORS
"""
from fastapi import FastAPI, Request, HTTPException, Depends, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
import httpx
import os
from dotenv import load_dotenv
from typing import Optional
import time
from datetime import datetime

load_dotenv()

# =============================================================================
# CONFIGURATION
# =============================================================================

# Service endpoints (from environment or defaults)
SERVICE_ENDPOINTS = {
    "auth": os.getenv("AUTH_SERVICE_URL", "http://localhost:8001"),
    "application": os.getenv("APPLICATION_SERVICE_URL", "http://localhost:8002"),
    "document": os.getenv("DOCUMENT_SERVICE_URL", "http://localhost:8003"),
    "underwriting": os.getenv("UNDERWRITING_SERVICE_URL", "http://localhost:8004"),
    "scoring": os.getenv("SCORING_SERVICE_URL", "http://localhost:8005"),
}

# Rate limiting configuration
RATE_LIMIT_PER_MINUTE = os.getenv("RATE_LIMIT_PER_MINUTE", "60/minute")
RATE_LIMIT_PER_HOUR = os.getenv("RATE_LIMIT_PER_HOUR", "1000/hour")

# =============================================================================
# APP INITIALIZATION
# =============================================================================

app = FastAPI(
    title="AnalyticaLoan API Gateway",
    description="Centralized API Gateway for all microservices",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

# Rate limiter
limiter = Limiter(key_func=get_remote_address)
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=os.getenv("CORS_ORIGINS", "*").split(","),
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS", "PATCH"],
    allow_headers=["*"],
    expose_headers=["X-Request-ID", "X-RateLimit-Limit", "X-RateLimit-Remaining"],
)

# HTTP client for proxying requests
http_client = httpx.AsyncClient(timeout=30.0)

# =============================================================================
# MIDDLEWARE
# =============================================================================

@app.middleware("http")
async def add_request_id(request: Request, call_next):
    """Add unique request ID to all requests"""
    request_id = f"req_{int(time.time() * 1000)}"
    request.state.request_id = request_id
    
    response = await call_next(request)
    response.headers["X-Request-ID"] = request_id
    return response

@app.middleware("http")
async def log_requests(request: Request, call_next):
    """Log all incoming requests"""
    start_time = time.time()
    
    # Log request
    print(f"[{datetime.utcnow().isoformat()}] {request.method} {request.url.path} - START")
    
    response = await call_next(request)
    
    # Log response
    duration = time.time() - start_time
    print(f"[{datetime.utcnow().isoformat()}] {request.method} {request.url.path} - "
          f"STATUS: {response.status_code} - DURATION: {duration:.3f}s")
    
    return response

# =============================================================================
# HELPER FUNCTIONS
# =============================================================================

async def proxy_request(
    service_name: str,
    path: str,
    method: str,
    headers: dict,
    body: Optional[bytes] = None,
    query_params: Optional[dict] = None
) -> tuple[int, dict, bytes]:
    """
    Proxy request to backend service
    
    Args:
        service_name: Name of the service (auth, application, etc.)
        path: Request path
        method: HTTP method
        headers: Request headers
        body: Request body (optional)
        query_params: Query parameters (optional)
    
    Returns:
        Tuple of (status_code, headers, body)
    """
    if service_name not in SERVICE_ENDPOINTS:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Service '{service_name}' not found"
        )
    
    service_url = SERVICE_ENDPOINTS[service_name]
    url = f"{service_url}{path}"
    
    # Remove host header to avoid conflicts
    proxy_headers = {k: v for k, v in headers.items() if k.lower() != "host"}
    
    try:
        response = await http_client.request(
            method=method,
            url=url,
            headers=proxy_headers,
            content=body,
            params=query_params,
        )
        
        return response.status_code, dict(response.headers), response.content
    
    except httpx.RequestError as e:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Service '{service_name}' is unavailable: {str(e)}"
        )

# =============================================================================
# ROUTES
# =============================================================================

@app.get("/")
async def root():
    """Gateway health check"""
    return {
        "service": "AnalyticaLoan API Gateway",
        "version": "1.0.0",
        "status": "running",
        "services": {
            name: {"url": url, "status": "configured"}
            for name, url in SERVICE_ENDPOINTS.items()
        }
    }

@app.get("/health")
async def health_check():
    """Detailed health check of all services"""
    health_status = {"gateway": "healthy", "services": {}}
    
    for service_name, service_url in SERVICE_ENDPOINTS.items():
        try:
            response = await http_client.get(f"{service_url}/health", timeout=5.0)
            health_status["services"][service_name] = {
                "status": "healthy" if response.status_code == 200 else "unhealthy",
                "response_time_ms": response.elapsed.total_seconds() * 1000
            }
        except Exception as e:
            health_status["services"][service_name] = {
                "status": "unreachable",
                "error": str(e)
            }
    
    # Overall status
    all_healthy = all(
        svc.get("status") == "healthy" 
        for svc in health_status["services"].values()
    )
    health_status["overall"] = "healthy" if all_healthy else "degraded"
    
    return health_status

# =============================================================================
# SERVICE ROUTES (Proxying)
# =============================================================================

@app.api_route("/api/v1/auth/{path:path}", methods=["GET", "POST", "PUT", "DELETE", "PATCH"])
@limiter.limit(RATE_LIMIT_PER_MINUTE)
async def proxy_auth(request: Request, path: str):
    """Proxy to Auth Service"""
    status_code, headers, body = await proxy_request(
        service_name="auth",
        path=f"/{path}",
        method=request.method,
        headers=dict(request.headers),
        body=await request.body(),
        query_params=dict(request.query_params)
    )
    
    return JSONResponse(
        content=body.decode() if body else None,
        status_code=status_code,
        headers={k: v for k, v in headers.items() if k.lower() not in ["content-length", "transfer-encoding"]}
    )

@app.api_route("/api/v1/applications/{path:path}", methods=["GET", "POST", "PUT", "DELETE", "PATCH"])
@limiter.limit(RATE_LIMIT_PER_MINUTE)
async def proxy_applications(request: Request, path: str):
    """Proxy to Application Service"""
    status_code, headers, body = await proxy_request(
        service_name="application",
        path=f"/{path}",
        method=request.method,
        headers=dict(request.headers),
        body=await request.body(),
        query_params=dict(request.query_params)
    )
    
    return JSONResponse(
        content=body.decode() if body else None,
        status_code=status_code,
        headers={k: v for k, v in headers.items() if k.lower() not in ["content-length", "transfer-encoding"]}
    )

@app.api_route("/api/v1/documents/{path:path}", methods=["GET", "POST", "PUT", "DELETE", "PATCH"])
@limiter.limit(RATE_LIMIT_PER_MINUTE)
async def proxy_documents(request: Request, path: str):
    """Proxy to Document Service"""
    status_code, headers, body = await proxy_request(
        service_name="document",
        path=f"/{path}",
        method=request.method,
        headers=dict(request.headers),
        body=await request.body(),
        query_params=dict(request.query_params)
    )
    
    return JSONResponse(
        content=body.decode() if body else None,
        status_code=status_code,
        headers={k: v for k, v in headers.items() if k.lower() not in ["content-length", "transfer-encoding"]}
    )

@app.api_route("/api/v1/underwriting/{path:path}", methods=["GET", "POST", "PUT", "DELETE", "PATCH"])
@limiter.limit(RATE_LIMIT_PER_MINUTE)
async def proxy_underwriting(request: Request, path: str):
    """Proxy to Underwriting Service"""
    status_code, headers, body = await proxy_request(
        service_name="underwriting",
        path=f"/{path}",
        method=request.method,
        headers=dict(request.headers),
        body=await request.body(),
        query_params=dict(request.query_params)
    )
    
    return JSONResponse(
        content=body.decode() if body else None,
        status_code=status_code,
        headers={k: v for k, v in headers.items() if k.lower() not in ["content-length", "transfer-encoding"]}
    )

@app.api_route("/api/v1/scoring/{path:path}", methods=["GET", "POST", "PUT", "DELETE", "PATCH"])
@limiter.limit(RATE_LIMIT_PER_MINUTE)
async def proxy_scoring(request: Request, path: str):
    """Proxy to Scoring Service"""
    status_code, headers, body = await proxy_request(
        service_name="scoring",
        path=f"/{path}",
        method=request.method,
        headers=dict(request.headers),
        body=await request.body(),
        query_params=dict(request.query_params)
    )
    
    return JSONResponse(
        content=body.decode() if body else None,
        status_code=status_code,
        headers={k: v for k, v in headers.items() if k.lower() not in ["content-length", "transfer-encoding"]}
    )

# =============================================================================
# ERROR HANDLERS
# =============================================================================

@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    """Custom HTTP exception handler"""
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": exc.detail,
            "status_code": exc.status_code,
            "request_id": getattr(request.state, "request_id", None)
        }
    )

@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    """General exception handler"""
    print(f"ERROR: {str(exc)}")
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "error": "Internal server error",
            "status_code": 500,
            "request_id": getattr(request.state, "request_id", None)
        }
    )

# =============================================================================
# STARTUP/SHUTDOWN
# =============================================================================

@app.on_event("startup")
async def startup_event():
    """Run on application startup"""
    print("=" * 60)
    print("API Gateway started successfully")
    print("=" * 60)
    print("Service Endpoints:")
    for name, url in SERVICE_ENDPOINTS.items():
        print(f"  - {name}: {url}")
    print("=" * 60)

@app.on_event("shutdown")
async def shutdown_event():
    """Run on application shutdown"""
    await http_client.aclose()
    print("API Gateway shutting down")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000, reload=True)
