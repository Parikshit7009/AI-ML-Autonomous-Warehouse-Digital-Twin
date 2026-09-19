from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from backend.app.auth.dependencies import get_current_user
from backend.app.ml.demand_forecasting import generate_demand_forecast


router = APIRouter()


# ============================================================
# DEMAND FORECAST
# ============================================================

@router.get("/forecast/demand")
def demand_forecast(
    current_user=Depends(get_current_user)
):
    try:

        forecasts = generate_demand_forecast(
            days=30
        )

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


# ============================================================
# WHAT-IF REQUEST MODEL
# ============================================================

class WhatIfRequest(BaseModel):

    demand_change: float = 0

    lead_time_days: int = 0

    product_category: str | None = None

    additional_inventory: float = 0


# ============================================================
# WHAT-IF SIMULATION
# ============================================================

@router.post("/forecast/what-if")
def run_what_if(
    scenario: WhatIfRequest,
    current_user=Depends(get_current_user)
):

    try:

        # ----------------------------------------------------
        # LOAD EXISTING FORECAST
        # ----------------------------------------------------

        forecasts = generate_demand_forecast(
            days=30
        )

        if not forecasts:

            raise HTTPException(
                status_code=404,
                detail="No forecast data available."
            )


        # ----------------------------------------------------
        # CURRENT LIMITATION
        # ----------------------------------------------------
        #
        # warehouse product IDs are PROD_XXXXX
        # while products table uses integer IDs.
        #
        # Therefore category filtering is not applied yet.
        #

        filtered = forecasts


        # ----------------------------------------------------
        # BASELINE
        # ----------------------------------------------------

        base_demand = sum(

            float(
                item[
                    "forecasted_demand_30_days"
                ] or 0
            )

            for item in filtered
        )


        base_stock = sum(

            float(
                item[
                    "current_stock"
                ] or 0
            )

            for item in filtered
        )


        base_stockout = sum(

            1

            for item in filtered

            if
            float(
                item[
                    "forecasted_demand_30_days"
                ] or 0
            )
            >
            float(
                item[
                    "current_stock"
                ] or 0
            )
        )


        # ----------------------------------------------------
        # DEMAND CHANGE
        # ----------------------------------------------------

        demand_multiplier = (

            1
            +
            (
                float(
                    scenario.demand_change
                )
                /
                100
            )
        )


        # Prevent negative demand multiplier

        demand_multiplier = max(
            0,
            demand_multiplier
        )


        scenario_demand = (

            base_demand
            *
            demand_multiplier
        )


        # ----------------------------------------------------
        # ADDITIONAL INVENTORY
        # ----------------------------------------------------

        additional_inventory = max(

            0,

            float(
                scenario.additional_inventory
            )
        )


        scenario_stock = (

            base_stock
            +
            additional_inventory
        )


        # ----------------------------------------------------
        # STOCKOUT RE-ESTIMATION
        # ----------------------------------------------------

        additional_share = (

            additional_inventory
            /
            max(
                len(filtered),
                1
            )
        )


        scenario_stockout = 0


        for item in filtered:

            demand = (

                float(
                    item[
                        "forecasted_demand_30_days"
                    ] or 0
                )

                *

                demand_multiplier
            )


            stock = (

                float(
                    item[
                        "current_stock"
                    ] or 0
                )

                +

                additional_share
            )


            if demand > stock:

                scenario_stockout += 1


        # ----------------------------------------------------
        # LEAD TIME IMPACT
        # ----------------------------------------------------

        lead_time_days = max(

            0,

            int(
                scenario.lead_time_days
            )
        )


        lead_time_factor = (

            1
            +
            (
                lead_time_days
                *
                0.02
            )
        )


        # ----------------------------------------------------
        # RESULT
        # ----------------------------------------------------

        return {

            "scenario": {

                "demand_change_percent":
                    scenario.demand_change,

                "lead_time_days":
                    lead_time_days,

                "additional_inventory":
                    additional_inventory,

                "product_category":
                    scenario.product_category
            },


            "baseline": {

                "forecast_demand_30_days":
                    round(
                        base_demand,
                        2
                    ),

                "available_inventory":
                    round(
                        base_stock,
                        2
                    ),

                "stockout_skus":
                    base_stockout
            },


            "scenario_result": {

                "forecast_demand_30_days":
                    round(
                        scenario_demand,
                        2
                    ),

                "available_inventory":
                    round(
                        scenario_stock,
                        2
                    ),

                "stockout_skus":
                    scenario_stockout,

                "lead_time_factor":
                    round(
                        lead_time_factor,
                        3
                    )
            }

        }


    except HTTPException:

        raise


    except Exception as e:

        raise HTTPException(
            status_code=500,
            detail=str(e)
        )