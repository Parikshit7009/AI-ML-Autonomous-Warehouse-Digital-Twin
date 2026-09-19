from datetime import timedelta
from collections import defaultdict
import warnings
import time

from sklearn.ensemble import RandomForestRegressor

from backend.app.database import get_database_connection


# ============================================================
# FORECAST CACHE
# ============================================================

_FORECAST_CACHE = None
_FORECAST_CACHE_TIME = 0
_FORECAST_CACHE_TTL = 300  # 5 minutes


# ============================================================
# SUPPRESS SCIKIT-LEARN WARNING
# ============================================================

warnings.filterwarnings("ignore")


# ============================================================
# GET DAILY DEMAND DATA
# ============================================================

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
            GROUP BY
                product_id,
                DATE(timestamp)
            ORDER BY
                product_id,
                demand_date
        """)

        records = cursor.fetchall()

        print(
            f"Loaded {len(records)} daily demand records."
        )

        return records

    finally:

        cursor.close()
        db.close()


# ============================================================
# FAST RANDOM FOREST PREDICTION
# ============================================================

def fast_random_forest_predict(model, features):

    """
    Predict using all decision trees directly.

    This avoids RandomForestRegressor.predict()
    because of the Python 3.13 / joblib issue.
    """

    if not features:
        return []

    predictions = []

    for tree in model.estimators_:

        tree_predictions = tree.predict(features)

        predictions.append(tree_predictions)

    # Average prediction from all trees
    final_predictions = []

    number_of_trees = len(predictions)

    for index in range(len(features)):

        total = 0.0

        for tree_prediction in predictions:

            total += float(tree_prediction[index])

        final_predictions.append(
            total / number_of_trees
        )

    return final_predictions


# ============================================================
# GENERATE DEMAND FORECAST
# ============================================================

def generate_demand_forecast(days=30):

    global _FORECAST_CACHE
    global _FORECAST_CACHE_TIME

    # ========================================================
    # CHECK CACHE
    # ========================================================

    current_time = time.time()

    if (
        _FORECAST_CACHE is not None
        and current_time - _FORECAST_CACHE_TIME
        < _FORECAST_CACHE_TTL
    ):

        print("==========================================")
        print("Using cached demand forecast")
        print("==========================================")

        return _FORECAST_CACHE

    print("==========================================")
    print("Generating new demand forecast")
    print("==========================================")

    # ========================================================
    # LOAD DATA
    # ========================================================

    records = get_daily_demand_data()

    if not records:

        raise ValueError(
            "No warehouse demand data found."
        )

    # ========================================================
    # GROUP DATA BY SKU
    # ========================================================

    product_data = defaultdict(list)

    for row in records:

        product_data[
            row["product_id"]
        ].append(row)

    total_skus = len(product_data)

    print(
        f"Found {total_skus} unique SKUs."
    )

    # ========================================================
    # PREPARE MACHINE LEARNING DATA
    # ========================================================

    X = []
    y = []

    for product_id, rows in product_data.items():

        rows.sort(
            key=lambda x:
            x["demand_date"]
        )

        history = []

        for row in rows:

            demand = float(
                row["outgoing_items"] or 0
            )

            # Need at least 7 previous observations
            if len(history) < 7:

                history.append(
                    demand
                )

                continue

            # ------------------------------------------------
            # FEATURES
            # ------------------------------------------------

            previous_day_demand = (
                history[-1]
            )

            previous_week_demand = (
                history[-7]
            )

            weekly_average = (
                sum(history[-7:])
                / 7
            )

            inventory_level = float(
                row["inventory_level"] or 0
            )

            incoming_items = float(
                row["incoming_items"] or 0
            )

            existing_forecast = float(
                row["forecasted_demand"] or 0
            )

            day_of_week = (
                row["demand_date"].weekday()
            )

            features = [

                previous_day_demand,

                previous_week_demand,

                weekly_average,

                inventory_level,

                incoming_items,

                existing_forecast,

                day_of_week
            ]

            X.append(features)

            y.append(demand)

            history.append(demand)

    # ========================================================
    # VALIDATE TRAINING DATA
    # ========================================================

    if len(X) < 10:

        raise ValueError(
            "Not enough historical data to train Random Forest."
        )

    print(
        f"Training Random Forest with "
        f"{len(X)} samples..."
    )

    # ========================================================
    # RANDOM FOREST MODEL
    # ========================================================

    model = RandomForestRegressor(

        n_estimators=30,

        max_depth=8,

        random_state=42,

        n_jobs=1
    )

    # ========================================================
    # TRAIN MODEL
    # ========================================================

    model.fit(
        X,
        y
    )

    print(
        "Random Forest training completed."
    )

    # ========================================================
    # GENERATE FORECASTS
    # ========================================================

    forecasts = []

    print(
        f"Generating {days}-day forecasts "
        f"for {total_skus} SKUs..."
    )

    for product_index, (
        product_id,
        rows
    ) in enumerate(
        product_data.items(),
        start=1
    ):

        rows.sort(
            key=lambda x:
            x["demand_date"]
        )

        # ----------------------------------------------------
        # SKIP SKU WITH INSUFFICIENT HISTORY
        # ----------------------------------------------------

        if len(rows) < 7:
            continue

        # ----------------------------------------------------
        # HISTORICAL DEMAND
        # ----------------------------------------------------

        historical_demand = []

        for row in rows:

            historical_demand.append({

                "date":
                    row[
                        "demand_date"
                    ].isoformat(),

                "demand":
                    round(
                        float(
                            row[
                                "outgoing_items"
                            ] or 0
                        ),
                        2
                    )
            })

        # ----------------------------------------------------
        # DEMAND HISTORY FOR MODEL
        # ----------------------------------------------------

        history = [

            float(
                row["outgoing_items"] or 0
            )

            for row in rows
        ]

        # ----------------------------------------------------
        # LATEST DATA
        # ----------------------------------------------------

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

        # ====================================================
        # BUILD ALL FUTURE FEATURES FIRST
        # ====================================================

        future_features = []

        future_dates = []

        temp_history = history.copy()

        temp_date = current_date

        for day_number in range(days):

            temp_date += timedelta(days=1)

            previous_day_demand = (
                temp_history[-1]
            )

            previous_week_demand = (
                temp_history[-7]
            )

            weekly_average = (
                sum(temp_history[-7:])
                / 7
            )

            day_of_week = (
                temp_date.weekday()
            )

            features = [

                previous_day_demand,

                previous_week_demand,

                weekly_average,

                inventory,

                incoming,

                existing_forecast,

                day_of_week
            ]

            future_features.append(
                features
            )

            future_dates.append(
                temp_date
            )

            # Temporary placeholder.
            # It will be replaced with the actual
            # prediction after batch prediction.
            temp_history.append(
                weekly_average
            )

        # ====================================================
        # BATCH RANDOM FOREST PREDICTION
        # ====================================================

        predictions = fast_random_forest_predict(
            model,
            future_features
        )

        # ====================================================
        # BUILD DAILY FORECAST
        # ====================================================

        daily_forecast = []

        # Reset history for recursive prediction
        recursive_history = history.copy()

        for day_index in range(days):

            current_prediction = predictions[
                day_index
            ]

            current_prediction = max(
                0.0,
                current_prediction
            )

            current_prediction = round(
                current_prediction,
                2
            )

            forecast_date = future_dates[
                day_index
            ]

            daily_forecast.append({

                "date":
                    forecast_date.isoformat(),

                "forecasted_demand":
                    current_prediction
            })

            recursive_history.append(
                current_prediction
            )

        # ====================================================
        # TOTAL FORECAST
        # ====================================================

        total_forecast = sum(

            item[
                "forecasted_demand"
            ]

            for item in daily_forecast
        )

        # ====================================================
        # RECENT 7-DAY DEMAND
        # ====================================================

        recent_demands = [

            float(
                row[
                    "outgoing_items"
                ] or 0
            )

            for row in rows[-7:]
        ]

        if recent_demands:

            average_daily_demand = (

                sum(
                    recent_demands
                )

                /

                len(
                    recent_demands
                )
            )

        else:

            average_daily_demand = 0.0

        # ====================================================
        # HISTORICAL 30-DAY BASELINE
        # ====================================================

        historical_30_day_demand = (

            average_daily_demand
            *
            days
        )

        # ====================================================
        # DEMAND CHANGE %
        # ====================================================

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

            change_percent = 0.0

        # ====================================================
        # FINAL SKU RESULT
        # ====================================================

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

            "historical_demand":
                historical_demand,

            "forecast":
                daily_forecast
        })

        # ----------------------------------------------------
        # PROGRESS
        # ----------------------------------------------------

        if (

            product_index % 25 == 0

            or

            product_index == total_skus

        ):

            print(

                f"Forecasted "
                f"{product_index}/"
                f"{total_skus} SKUs..."
            )

    # ========================================================
    # SORT BY FORECASTED DEMAND
    # ========================================================

    forecasts.sort(

        key=lambda item:
        item[
            "forecasted_demand_30_days"
        ],

        reverse=True
    )

    # ========================================================
    # SAVE TO CACHE
    # ========================================================

    _FORECAST_CACHE = forecasts

    _FORECAST_CACHE_TIME = time.time()

    # ========================================================
    # COMPLETE
    # ========================================================

    print(
        "=========================================="
    )

    print(
        "Forecast generation completed."
    )

    print(
        f"Generated forecasts for "
        f"{len(forecasts)} SKUs."
    )

    print(
        "Forecast cached for 5 minutes."
    )

    print(
        "=========================================="
    )

    return forecasts