from datetime import timedelta
from collections import defaultdict

from sklearn.ensemble import RandomForestRegressor

from backend.app.database import get_database_connection


def get_daily_demand_data():
    """Load daily warehouse demand data from MySQL."""

    db = get_database_connection()
    cursor = db.cursor(dictionary=True)

    try:
        cursor.execute("""
            SELECT
                product_id,
                DATE(timestamp) AS demand_date,
                SUM(outgoing_items) AS outgoing_items,
                AVG(inventory_level) AS inventory_level,
                SUM(incoming_items) AS incoming_items,
                AVG(forecasted_demand) AS forecasted_demand
            FROM warehouse_operations
            GROUP BY product_id, DATE(timestamp)
            ORDER BY product_id, demand_date
        """)

        return cursor.fetchall()

    finally:
        cursor.close()
        db.close()


def generate_demand_forecast(days=30):
    """
    Train a Random Forest model using warehouse demand history
    and generate a future demand forecast.
    """

    records = get_daily_demand_data()

    if not records:
        raise ValueError("No warehouse operation data found.")

    # Group records by warehouse SKU
    product_data = defaultdict(list)

    for row in records:
        product_data[row["product_id"]].append(row)

    # ---------------------------------------------------------
    # BUILD TRAINING DATA
    # ---------------------------------------------------------

    X = []
    y = []

    for product_id, rows in product_data.items():

        rows.sort(key=lambda x: x["demand_date"])

        history = []

        for row in rows:

            demand = float(row["outgoing_items"] or 0)

            # Need at least 7 previous observations
            if len(history) < 7:
                history.append(demand)
                continue

            lag_1 = history[-1]
            lag_7 = history[-7]

            rolling_7 = sum(history[-7:]) / 7

            inventory = float(
                row["inventory_level"] or 0
            )

            incoming = float(
                row["incoming_items"] or 0
            )

            existing_forecast = float(
                row["forecasted_demand"] or 0
            )

            day_of_week = row["demand_date"].weekday()

            features = [
                lag_1,
                lag_7,
                rolling_7,
                inventory,
                incoming,
                existing_forecast,
                day_of_week
            ]

            X.append(features)
            y.append(demand)

            history.append(demand)

    if len(X) < 10:
        raise ValueError(
            "Not enough historical data to train Random Forest."
        )

    # ---------------------------------------------------------
    # TRAIN RANDOM FOREST
    # ---------------------------------------------------------

    model = RandomForestRegressor(
        n_estimators=150,
        max_depth=12,
        random_state=42,
        n_jobs=-1
    )

    model.fit(X, y)

    # ---------------------------------------------------------
    # GENERATE FUTURE FORECAST
    # ---------------------------------------------------------

    forecasts = []

    for product_id, rows in product_data.items():

        rows.sort(key=lambda x: x["demand_date"])

        if len(rows) < 7:
            continue

        history = [
            float(row["outgoing_items"] or 0)
            for row in rows
        ]

        latest = rows[-1]

        current_date = latest["demand_date"]

        inventory = float(
            latest["inventory_level"] or 0
        )

        incoming = float(
            latest["incoming_items"] or 0
        )

        existing_forecast = float(
            latest["forecasted_demand"] or 0
        )

        daily_forecast = []

        for _ in range(days):

            current_date += timedelta(days=1)

            lag_1 = history[-1]

            lag_7 = history[-7]

            rolling_7 = sum(history[-7:]) / 7

            day_of_week = current_date.weekday()

            features = [[
                lag_1,
                lag_7,
                rolling_7,
                inventory,
                incoming,
                existing_forecast,
                day_of_week
            ]]

            prediction = float(
                model.predict(features)[0]
            )

            # Demand cannot be negative
            prediction = max(0, prediction)

            daily_forecast.append({
                "date": current_date.isoformat(),
                "forecasted_demand": round(
                    prediction,
                    2
                )
            })

            # Use prediction for the next day's lag features
            history.append(prediction)

        total_demand = sum(
            item["forecasted_demand"]
            for item in daily_forecast
        )

        average_daily_demand = (
            sum(
                float(row["outgoing_items"] or 0)
                for row in rows[-7:]
            )
            / min(7, len(rows))
        )

        historical_30_day_estimate = (
            average_daily_demand * days
        )

        if historical_30_day_estimate > 0:

            change_percent = (
                (
                    total_demand
                    - historical_30_day_estimate
                )
                / historical_30_day_estimate
            ) * 100

        else:
            change_percent = 0

        forecasts.append({
            "product_id": product_id,
            "current_stock": round(
                inventory,
                2
            ),
            "forecasted_demand_30_days": round(
                total_demand,
                2
            ),
            "average_daily_demand": round(
                average_daily_demand,
                2
            ),
            "change_percent": round(
                change_percent,
                2
            ),
            "forecast": daily_forecast
        })

    # Highest predicted demand first
    forecasts.sort(
        key=lambda item:
            item["forecasted_demand_30_days"],
        reverse=True
    )

    return forecasts