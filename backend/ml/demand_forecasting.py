from datetime import timedelta
from collections import defaultdict

from sklearn.ensemble import RandomForestRegressor

from backend.app.database import get_database_connection


def get_daily_demand_data():

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

    records = get_daily_demand_data()

    if not records:
        raise ValueError("No warehouse demand data found.")

    product_data = defaultdict(list)

    for row in records:
        product_data[row["product_id"]].append(row)

    training_data = []

    for product_id, rows in product_data.items():

        rows.sort(key=lambda x: x["demand_date"])

        history = []

        for row in rows:

            demand = float(row["outgoing_items"] or 0)

            if len(history) < 7:
                history.append(demand)
                continue

            lag_1 = history[-1]
            lag_7 = history[-7]

            rolling_7 = sum(history[-7:]) / 7

            day_of_week = row["demand_date"].weekday()

            features = [
                lag_1,
                lag_7,
                rolling_7,
                float(row["inventory_level"] or 0),
                float(row["incoming_items"] or 0),
                float(row["forecasted_demand"] or 0),
                day_of_week
            ]

            training_data.append(
                (features, demand)
            )

            history.append(demand)

    if not training_data:
        raise ValueError(
            "Not enough historical data to train Random Forest."
        )

    X = [x[0] for x in training_data]
    y = [x[1] for x in training_data]

    model = RandomForestRegressor(
        n_estimators=150,
        max_depth=12,
        random_state=42,
        n_jobs=1
    )

    model.fit(X, y)

    forecasts = []

    for product_id, rows in product_data.items():

        rows.sort(key=lambda x: x["demand_date"])

        if len(rows) < 7:
            continue

        history = [
            float(row["outgoing_items"] or 0)
            for row in rows
        ]

        last_row = rows[-1]

        current_date = last_row["demand_date"]

        inventory = float(
            last_row["inventory_level"] or 0
        )

        incoming = float(
            last_row["incoming_items"] or 0
        )

        forecasted_demand = float(
            last_row["forecasted_demand"] or 0
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
                forecasted_demand,
                day_of_week
            ]]

            prediction = float(
                model.predict(features)[0]
            )

            prediction = max(0, prediction)

            daily_forecast.append({
                "date": current_date.isoformat(),
                "forecasted_demand": round(
                    prediction,
                    2
                )
            })

            history.append(prediction)

        total_forecast = sum(
            item["forecasted_demand"]
            for item in daily_forecast
        )

        average_daily_demand = sum(
            float(row["outgoing_items"] or 0)
            for row in rows[-7:]
        ) / min(7, len(rows))

        change_percent = 0

        if average_daily_demand > 0:

            previous_30_day_estimate = (
                average_daily_demand * days
            )

            change_percent = (
                (
                    total_forecast
                    - previous_30_day_estimate
                )
                / previous_30_day_estimate
            ) * 100

        forecasts.append({
            "product_id": product_id,
            "current_stock": round(
                inventory,
                2
            ),
            "forecasted_demand_30_days": round(
                total_forecast,
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

    forecasts.sort(
        key=lambda x: x["forecasted_demand_30_days"],
        reverse=True
    )

    return forecasts