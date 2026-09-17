from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pathlib import Path

from backend.app.routes.orders import router as orders_router
from backend.app.routes.products import router as products_router
from backend.app.routes.inventory import router as inventory_router
from backend.app.routes.robots import router as robots_router
from backend.app.routes.auth import router as auth_router
from backend.app.routes.operations import router as operations_router
from backend.app.routes.forecast import router as forecast_router



app = FastAPI(
    title="AI/ML Warehouse Digital Twin",
    description="Warehouse Digital Twin and What-If Simulator",
    version="1.0.0"
)


# Frontend location
BASE_DIR = Path(__file__).resolve().parents[2]
FRONTEND_DIR = BASE_DIR / "Frontend"


# Serve frontend files
app.mount(
    "/static",
    StaticFiles(directory=FRONTEND_DIR),
    name="static"
)


# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
def serve_login():
    return FileResponse(
        FRONTEND_DIR / "login.html"
    )


@app.get("/dashboard")
def serve_dashboard():
    return FileResponse(
        FRONTEND_DIR / "Dashboard.html"
    )

# Health check
@app.get("/health")
def health():
    return {
        "status": "healthy"
    }


# API routes
app.include_router(products_router)
app.include_router(inventory_router)
app.include_router(orders_router)
app.include_router(robots_router)
app.include_router(auth_router)
app.include_router(operations_router)
app.include_router(forecast_router)

