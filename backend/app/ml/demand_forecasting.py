from datetime import timedelta
from collections import defaultdict
import warnings

from sklearn.ensemble import RandomForestRegressor

from backend.app.database import get_database_connection


warnings.filterwarnings("ignore")


def get_daily_demand_data():

    print("Loading warehouse demand data...")

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

        records = cursor.fetchall()

        print(
            f"Loaded {len(records)} daily demand records."
        )

        return records

    finally:

        cursor.close()
        db.close()


def generate_demand_forecast(days=30):

    records = get_daily_demand_data()

    if not records:

        raise ValueError(
            "No warehouse demand data found."
        )

    # --------------------------------------------------
    # GROUP DATA BY SKU
    # --------------------------------------------------

    product_data = defaultdict(list)

    for row in records:

        product_data[
            row["product_id"]
        ].append(row)

    print(
        f"Found {len(product_data)} unique SKUs."
    )

    # --------------------------------------------------
    # CREATE TRAINING DATA
    # --------------------------------------------------

    X = []
    y = []

    for product_id, rows in product_data.items():

        rows.sort(
            key=lambda x: x["demand_date"]
        )

        history = []

        for row in rows:

            demand = float(
                row["outgoing_items"] or 0
            )

            if len(history) < 7:

                history.append(demand)

                continue

            features = [

                # Previous day demand
                history[-1],

                # Demand 7 days ago
                history[-7],

                # 7-day moving average
                sum(history[-7:]) / 7,

                # Current inventory
                float(
                    row["inventory_level"] or 0
                ),

                # Incoming stock
                float(
                    row["incoming_items"] or 0
                ),

                # Existing forecast
                float(
                    row["forecasted_demand"] or 0
                ),

                # Day of week
                row["demand_date"].weekday()
            ]

            X.append(features)

            y.append(demand)

            history.append(demand)

    if len(X) < 10:

        raise ValueError(
            "Not enough historical data to train Random Forest."
        )

    print(
        f"Training Random Forest with {len(X)} samples..."
    )

    # --------------------------------------------------
    # RANDOM FOREST
    # --------------------------------------------------

    model = RandomForestRegressor(

        n_estimators=30,

        max_depth=8,

        random_state=42,

        n_jobs=1
    )

    model.fit(X, y)

    print(
        "Random Forest training completed."
    )

    # --------------------------------------------------
    # GENERATE FORECASTS
    # --------------------------------------------------

    forecasts = []

    total_products = len(product_data)

    print(
        f"Generating {days}-day forecasts for "
        f"{total_products} SKUs..."
    )

    for product_index, (
        product_id,
        rows
    ) in enumerate(
        product_data.items(),
        start=1
    ):

        rows.sort(
            key=lambda x: x["demand_date"]
        )

        if len(rows) < 7:

            continue

        # ----------------------------------------------
        # HISTORICAL DEMAND
        # ----------------------------------------------

        history = [

            float(
                row["outgoing_items"] or 0
            )

            for row in rows
        ]

        latest = rows[-1]

        current_date = (
            latest["demand_date"]
        )

        inventory = float(
            latest["inventory_level"] or 0
        )

        incoming = float(
            latest["incoming_items"] or 0
        )

        existing_forecast = float(
            latest["forecasted_demand"] or 0
        )

        # ----------------------------------------------
        # PREPARE ALL 30 FEATURES FIRST
        # ----------------------------------------------

        feature_rows = []

        future_dates = []

        temp_history = history.copy()

        temp_date = current_date

        for _ in range(days):

            temp_date += timedelta(days=1)

            future_dates.append(
                temp_date
            )

            feature_rows.append([

                temp_history[-1],

                temp_history[-7],

                sum(
                    temp_history[-7:]
                ) / 7,

                inventory,

                incoming,

                existing_forecast,

                temp_date.weekday()
            ])

            # Temporary value.
            # Updated after prediction.
            temp_history.append(
                temp_history[-1]
            )

        # ----------------------------------------------
        # PREDICT
        # ----------------------------------------------

        daily_forecast = []

        temp_history = history.copy()

        for i in range(days):

            features = [
                feature_rows[i]
            ]

            prediction = float(
                model.predict(
                    features
                )[0]
            )

            prediction = max(
                0,
                prediction
            )

            daily_forecast.append({

                "date":
                    future_dates[i].isoformat(),

                "forecasted_demand":
                    round(
                        prediction,
                        2
                    )
            })

            # Update recursive history
            temp_history.append(
                prediction
            )

            if len(temp_history) > 100:

                temp_history.pop(0)

            # Update following feature rows
            if i + 1 < days:

                feature_rows[i + 1][0] = (
                    prediction
                )

                feature_rows[i + 1][1] = (
                    temp_history[-7]
                )

                feature_rows[i + 1][2] = (
                    sum(
                        temp_history[-7:]
                    ) / 7
                )

        # ----------------------------------------------
        # TOTAL FORECAST
        # ----------------------------------------------

        total_forecast = sum(

            item[
                "forecasted_demand"
            ]

            for item in daily_forecast
        )

        # ----------------------------------------------
        # RECENT DEMAND
        # ----------------------------------------------

        recent_demands = [

            float(
                row["outgoing_items"] or 0
            )

            for row in rows[-7:]
        ]

        if recent_demands:

            average_daily_demand = (
                sum(recent_demands)
                /
                len(recent_demands)
            )

        else:

            average_daily_demand = 0

        historical_30_day_demand = (
            average_daily_demand
            * days
        )

        # ----------------------------------------------
        # CHANGE %
        # ----------------------------------------------

        if historical_30_day_demand > 0:

            change_percent = (

                (
                    total_forecast
                    -
                    historical_30_day_demand
                )

                /

                historical_30_day_demand

            ) * 100

        else:

            change_percent = 0

        # ----------------------------------------------
        # RESULT
        # ----------------------------------------------

        forecasts.append({

            "product_id":
                product_id,

            "current_stock":
                round(
                    inventory,
                    2
                ),

            "forecasted_demand_30_days":
                round(
                    total_forecast,
                    2
                ),

            "average_daily_demand":
                round(
                    average_daily_demand,
                    2
                ),

            "change_percent":
                round(
                    change_percent,
                    2
                ),

            "forecast":
                daily_forecast
        })

        # ----------------------------------------------
        # PROGRESS
        # ----------------------------------------------

        if (
            product_index % 25 == 0
            or
            product_index == total_products
        ):

            print(
                f"Forecasted "
                f"{product_index}/"
                f"{total_products} SKUs..."
            )

    # --------------------------------------------------
    # SORT BY DEMAND
    # --------------------------------------------------

    forecasts.sort(

        key=lambda item:
            item[
                "forecasted_demand_30_days"
            ],

        reverse=True
    )

    print(
        f"Forecast generation completed. "
        f"Generated {len(forecasts)} SKUs."
    )

    return forecasts