from fastapi import APIRouter, Depends
from backend.app.database import get_database_connection
from backend.app.auth.dependencies import get_current_user

router = APIRouter()


@router.get("/operations/kpis")
def get_operations_kpis(current_user=Depends(get_current_user)):

    db = get_database_connection()
    cursor = db.cursor(dictionary=True)

    try:

        cursor.execute("""
            SELECT

                /* Unique products */
                COUNT(DISTINCT product_id)
                    AS total_skus,

                /* Dataset records */
                COUNT(*)
                    AS total_records,

                /* Incoming / outgoing */
                COALESCE(SUM(incoming_items), 0)
                    AS total_incoming_items,

                COALESCE(SUM(outgoing_items), 0)
                    AS total_outgoing_items,

                /* Throughput */
                COALESCE(
                    SUM(outgoing_items) /
                    NULLIF(
                        TIMESTAMPDIFF(
                            HOUR,
                            MIN(timestamp),
                            MAX(timestamp)
                        ),
                        0
                    ),
                    0
                ) AS outbound_throughput_per_hour,

                /* Picking */
                COALESCE(
                    AVG(order_picking_time_min),
                    0
                ) AS average_picking_time,

                /* Completion */
                COALESCE(
                    AVG(order_completion_time_min),
                    0
                ) AS average_completion_time,

                /* Queue */
                COALESCE(
                    AVG(order_queue_length),
                    0
                ) AS average_queue_length,

                /* Inventory */
                COALESCE(
                    AVG(inventory_level),
                    0
                ) AS average_inventory_level,

                COALESCE(
                    AVG(forecasted_demand),
                    0
                ) AS average_forecasted_demand,

                /* Storage */
                COALESCE(
                    AVG(storage_utilization_pct),
                    0
                ) AS average_storage_utilization,

                /* Congestion */
                COALESCE(
                    AVG(congestion_level_pct),
                    0
                ) AS average_congestion,

                /* Workers */
                COALESCE(
                    AVG(worker_count),
                    0
                ) AS average_worker_count,

                /* Forklifts */
                COALESCE(
                    AVG(forklift_count),
                    0
                ) AS average_forklift_count,

                COALESCE(
                    AVG(forklift_utilization_pct),
                    0
                ) AS average_forklift_utilization,

                /* Equipment */
                COALESCE(
                    AVG(equipment_health_index),
                    0
                ) AS average_equipment_health,

                COALESCE(
                    AVG(resource_utilization_pct),
                    0
                ) AS average_resource_utilization,

                /* Energy */
                COALESCE(
                    AVG(energy_consumption_kwh),
                    0
                ) AS average_energy_consumption,

                /* Accuracy / Safety */
                COALESCE(
                    AVG(inventory_accuracy_pct),
                    0
                ) AS average_inventory_accuracy,

                COALESCE(
                    AVG(safety_compliance_pct),
                    0
                ) AS average_safety_compliance,

                /* Warehouse activity */
                COALESCE(
                    AVG(warehouse_activity_score),
                    0
                ) AS average_activity_score,

                /* Environment */
                COALESCE(
                    AVG(temperature_c),
                    0
                ) AS average_temperature,

                COALESCE(
                    AVG(humidity_pct),
                    0
                ) AS average_humidity,

                COALESCE(
                    AVG(air_quality_index),
                    0
                ) AS average_air_quality,

                COALESCE(
                    AVG(dust_level_ugm3),
                    0
                ) AS average_dust_level,

                COALESCE(
                    AVG(noise_level_db),
                    0
                ) AS average_noise_level,

                /* Maintenance */
                COALESCE(
                    SUM(
                        CASE
                            WHEN maintenance_alert IS NOT NULL
                            AND LOWER(maintenance_alert)
                                NOT IN (
                                    'none',
                                    'normal',
                                    'no alert',
                                    '0'
                                )
                            THEN 1
                            ELSE 0
                        END
                    ),
                    0
                ) AS maintenance_alert_count

            FROM warehouse_operations
        """)

        kpis = cursor.fetchone()

        return {

            "total_skus":
                int(kpis["total_skus"]),

            "total_records":
                int(kpis["total_records"]),

            "total_incoming_items":
                int(kpis["total_incoming_items"]),

            "total_outgoing_items":
                int(kpis["total_outgoing_items"]),

            "outbound_throughput_per_hour":
                round(
                    float(
                        kpis["outbound_throughput_per_hour"]
                    ),
                    2
                ),

            "average_picking_time":
                round(
                    float(
                        kpis["average_picking_time"]
                    ),
                    2
                ),

            "average_completion_time":
                round(
                    float(
                        kpis["average_completion_time"]
                    ),
                    2
                ),

            "average_queue_length":
                round(
                    float(
                        kpis["average_queue_length"]
                    ),
                    2
                ),

            "average_inventory_level":
                round(
                    float(
                        kpis["average_inventory_level"]
                    ),
                    2
                ),

            "average_forecasted_demand":
                round(
                    float(
                        kpis["average_forecasted_demand"]
                    ),
                    2
                ),

            "average_storage_utilization":
                round(
                    float(
                        kpis["average_storage_utilization"]
                    ),
                    2
                ),

            "average_congestion":
                round(
                    float(
                        kpis["average_congestion"]
                    ),
                    2
                ),

            "average_worker_count":
                round(
                    float(
                        kpis["average_worker_count"]
                    ),
                    2
                ),

            "average_forklift_count":
                round(
                    float(
                        kpis["average_forklift_count"]
                    ),
                    2
                ),

            "average_forklift_utilization":
                round(
                    float(
                        kpis["average_forklift_utilization"]
                    ),
                    2
                ),

            "average_equipment_health":
                round(
                    float(
                        kpis["average_equipment_health"]
                    ),
                    2
                ),

            "average_resource_utilization":
                round(
                    float(
                        kpis["average_resource_utilization"]
                    ),
                    2
                ),

            "average_energy_consumption":
                round(
                    float(
                        kpis["average_energy_consumption"]
                    ),
                    2
                ),

            "average_inventory_accuracy":
                round(
                    float(
                        kpis["average_inventory_accuracy"]
                    ),
                    2
                ),

            "average_safety_compliance":
                round(
                    float(
                        kpis["average_safety_compliance"]
                    ),
                    2
                ),

            "average_activity_score":
                round(
                    float(
                        kpis["average_activity_score"]
                    ),
                    2
                ),

            "average_temperature":
                round(
                    float(
                        kpis["average_temperature"]
                    ),
                    2
                ),

            "average_humidity":
                round(
                    float(
                        kpis["average_humidity"]
                    ),
                    2
                ),

            "average_air_quality":
                round(
                    float(
                        kpis["average_air_quality"]
                    ),
                    2
                ),

            "average_dust_level":
                round(
                    float(
                        kpis["average_dust_level"]
                    ),
                    2
                ),

            "average_noise_level":
                round(
                    float(
                        kpis["average_noise_level"]
                    ),
                    2
                ),

            "maintenance_alert_count":
                int(
                    kpis["maintenance_alert_count"]
                )
        }

    finally:
        cursor.close()
        db.close()