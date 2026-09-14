from fastapi import FastAPI
from backend.app.routes.products import router as products_router

app = FastAPI(
    title="AI/ML Warehouse Digital Twin",
    description="Warehouse Digital Twin and What-If Simulator",
    version="1.0.0"
)


@app.get("/")
def root():
    return {
        "message": "Warehouse Digital Twin API is running"
    }


@app.get("/health")
def health():
    return {
        "status": "healthy"
    }


app.include_router(products_router)