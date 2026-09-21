import csv
import mysql.connector
from pathlib import Path
from datetime import datetime


# ============================================================
# PATH
# ============================================================

BASE_DIR = Path(__file__).resolve().parents[1]
CSV_FILE = BASE_DIR / "data" / "iot_warehouse_optimization_dataset.csv"


# ============================================================
# MYSQL CONNECTION
# ============================================================

db = mysql.connector.connect(
    host="localhost",
    user="root",
    password="1638",
    database="warehouse_twin"
)

cursor = db.cursor()


# ============================================================
# CSV COLUMNS
# ============================================================

columns = [
    "record_id",
    "timestamp",
    "warehouse_id",
    "zone_id",
    "rack_id",
    "product_id",
    "rfid_read_count",
    "inventory_level",
    "inventory_movement",
    "incoming_items",
    "outgoing_items",
    "inventory_accuracy_pct",
    "forecasted_demand",
    "storage_utilization_pct",
    "storage_allocation_score",
    "available_storage_space_pct",
    "order_queue_length",
    "order_picking_time_min",
    "packing_time_min",
    "order_completion_time_min",
    "conveyor_speed_mps",
    "conveyor_vibration_mmps",
    "motor_temperature_c",
    "equipment_load_pct",
    "energy_consumption_kwh",
    "machine_runtime_hr",
    "sensor_battery_pct",
    "equipment_health_index",
    "maintenance_alert",
    "worker_count",
    "worker_movement_index",
    "forklift_count",
    "forklift_utilization_pct",
    "congestion_level_pct",
    "obstacle_detection",
    "safety_compliance_pct",
    "warehouse_activity_score",
    "temperature_c",
    "humidity_pct",
    "air_quality_index",
    "dust_level_ugm3",
    "lighting_lux",
    "noise_level_db",
    "predicted_equipment_failure",
    "resource_utilization_pct",
    "warehouse_operation_status"
]


# ============================================================
# DATA TYPE GROUPS
# ============================================================

integer_columns = {
    "record_id",
    "rfid_read_count",
    "inventory_level",
    "inventory_movement",
    "incoming_items",
    "outgoing_items",
    "forecasted_demand",
    "order_queue_length",
    "worker_count",
    "forklift_count"
}


decimal_columns = {
    "inventory_accuracy_pct",
    "storage_utilization_pct",
    "storage_allocation_score",
    "available_storage_space_pct",
    "order_picking_time_min",
    "packing_time_min",
    "order_completion_time_min",
    "conveyor_speed_mps",
    "conveyor_vibration_mmps",
    "motor_temperature_c",
    "equipment_load_pct",
    "energy_consumption_kwh",
    "machine_runtime_hr",
    "sensor_battery_pct",
    "equipment_health_index",
    "worker_movement_index",
    "forklift_utilization_pct",
    "congestion_level_pct",
    "safety_compliance_pct",
    "warehouse_activity_score",
    "temperature_c",
    "humidity_pct",
    "air_quality_index",
    "dust_level_ugm3",
    "lighting_lux",
    "noise_level_db",
    "predicted_equipment_failure",
    "resource_utilization_pct"
}


# ============================================================
# VALUE CONVERSION
# ============================================================

def convert_value(column, value):

    # Empty CSV value -> SQL NULL
    if value is None or value.strip() == "":
        return None

    value = value.strip()

    # Timestamp
    if column == "timestamp":
        try:
            parsed = datetime.fromisoformat(
                value.replace("Z", "+00:00")
            )

            # MySQL DATETIME does not need timezone information
            if parsed.tzinfo is not None:
                parsed = parsed.replace(tzinfo=None)

            return parsed

        except ValueError:
            print(f"Warning: Invalid timestamp: {value}")
            return None

    # Integer
    if column in integer_columns:
        try:
            return int(float(value))
        except ValueError:
            print(
                f"Warning: Invalid integer for {column}: {value}"
            )
            return None

    # Decimal / floating-point
    if column in decimal_columns:
        try:
            return float(value)
        except ValueError:
            print(
                f"Warning: Invalid decimal for {column}: {value}"
            )
            return None

    # Text
    return value


# ============================================================
# LOAD CSV
# ============================================================

print("=" * 60)
print("WAREHOUSE OPERATIONS DATA IMPORT")
print("=" * 60)

print()
print("Loading CSV...")
print(f"File: {CSV_FILE}")

if not CSV_FILE.exists():
    print("ERROR: CSV file not found.")
    cursor.close()
    db.close()
    raise SystemExit(1)


data = []

try:

    with open(
        CSV_FILE,
        "r",
        encoding="utf-8-sig",
        newline=""
    ) as file:

        reader = csv.DictReader(file)

        # ----------------------------------------------------
        # Check CSV headers
        # ----------------------------------------------------

        csv_columns = reader.fieldnames

        if csv_columns is None:
            print("ERROR: CSV file has no headers.")
            raise SystemExit(1)

        csv_columns = [column.strip() for column in csv_columns]

        print()
        print(f"CSV columns found: {len(csv_columns)}")
        print(f"Required columns: {len(columns)}")

        missing_columns = [
            column
            for column in columns
            if column not in csv_columns
        ]

        if missing_columns:

            print()
            print("ERROR: Missing columns in CSV:")

            for column in missing_columns:
                print(f"  - {column}")

            raise SystemExit(1)

        # ----------------------------------------------------
        # Read rows
        # ----------------------------------------------------

        for row_number, row in enumerate(reader, start=2):

            try:

                values = tuple(
                    convert_value(
                        column,
                        row.get(column)
                    )
                    for column in columns
                )

                data.append(values)

            except Exception as error:

                print(
                    f"Error processing CSV row {row_number}: "
                    f"{error}"
                )

                raise

except Exception as error:

    print()
    print("ERROR while reading CSV:")
    print(error)

    cursor.close()
    db.close()

    raise SystemExit(1)


# ============================================================
# VALIDATION
# ============================================================

print()
print(f"Rows found: {len(data)}")
print(f"Columns found: {len(columns)}")

if len(data) == 0:

    print("ERROR: No data found in CSV.")

    cursor.close()
    db.close()

    raise SystemExit(1)


# Check first row
print()
print("Validating parameter count...")

expected_parameters = len(columns)
actual_parameters = len(data[0])

print(f"Expected parameters per row: {expected_parameters}")
print(f"Actual parameters in first row: {actual_parameters}")

if expected_parameters != actual_parameters:

    print()
    print("ERROR: Column/value count mismatch.")

    cursor.close()
    db.close()

    raise SystemExit(1)


# ============================================================
# GENERATE SQL AUTOMATICALLY
# ============================================================

# IMPORTANT:
# This creates exactly 46 placeholders because there are
# exactly 46 columns.

placeholders = ", ".join(["%s"] * len(columns))

query = f"""
INSERT INTO warehouse_operations (
    {", ".join(columns)}
)
VALUES (
    {placeholders}
)
"""


# ============================================================
# SQL VALIDATION
# ============================================================

sql_placeholder_count = query.count("%s")

print()
print(f"SQL columns: {len(columns)}")
print(f"SQL placeholders: {sql_placeholder_count}")

if sql_placeholder_count != len(columns):

    print()
    print("ERROR: SQL placeholder count does not match columns.")

    cursor.close()
    db.close()

    raise SystemExit(1)


# ============================================================
# IMPORT
# ============================================================

print()
print("Importing data into MySQL...")
print("Please wait...")

try:

    # Import in batches instead of sending all 15,000
    # records at once.

    batch_size = 1000

    total_imported = 0

    for start in range(0, len(data), batch_size):

        batch = data[start:start + batch_size]

        cursor.executemany(
            query,
            batch
        )

        total_imported += len(batch)

        print(
            f"Imported {total_imported}/{len(data)} records..."
        )

    db.commit()

    print()
    print("=" * 60)
    print("IMPORT SUCCESSFUL")
    print("=" * 60)
    print(f"Successfully imported: {total_imported} records")


except Exception as error:

    db.rollback()

    print()
    print("=" * 60)
    print("IMPORT FAILED")
    print("=" * 60)
    print("Error:")
    print(error)

    raise


finally:

    cursor.close()
    db.close()


print()
print("Import process completed.")