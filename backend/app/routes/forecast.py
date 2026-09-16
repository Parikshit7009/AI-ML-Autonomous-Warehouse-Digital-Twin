from fastapi import APIRouter, Depends, HTTPException

from backend.app.auth.dependencies import get_current_user
from backend.app.ml.demand_forecasting import generate_demand_forecast


router = APIRouter()


@router.get("/forecast/demand")
def demand_forecast(
    current_user=Depends(get_current_user)
):
    try:
        forecasts = generate_demand_forecast(days=30)

        return {
            "model": "RandomForestRegressor",
            "forecast_horizon_days": 30,
            "sku_count": len(forecasts),
            "forecasts": forecasts
        }

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=str(e)
        )