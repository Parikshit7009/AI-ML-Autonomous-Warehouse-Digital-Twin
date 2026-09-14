from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from backend.app.routes.orders import router as orders_router
from backend.app.routes.products import router as products_router
from backend.app.routes.inventory import router as inventory_router


app = FastAPI(
    title="AI/ML Warehouse Digital Twin",
    description="Warehouse Digital Twin and What-If Simulator",
    version="1.0.0"
)


# CORS configuration
# Allows the frontend Dashboard.html to communicate with FastAPI
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Root API
@app.get("/")
def root():
    return {
        "message": "Warehouse Digital Twin API is running"
    }


# Health check
@app.get("/health")
def health():
    return {
        "status": "healthy"
    }


# Product routes
app.include_router(products_router)


# Inventory routes
app.include_router(inventory_router)

#Orders routes
app.include_router(orders_router)
