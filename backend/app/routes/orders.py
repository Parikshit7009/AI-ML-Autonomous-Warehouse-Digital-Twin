from fastapi import APIRouter, HTTPException
from backend.app.database import get_database_connection

router = APIRouter()


@router.get("/orders")
def get_orders():

    db = get_database_connection()
    cursor = db.cursor(dictionary=True)

    cursor.execute("""
        SELECT
            o.order_id,
            o.product_id,
            p.product_name,
            o.quantity,
            o.status,
            o.order_date
        FROM orders o
        JOIN products p
        ON o.product_id = p.product_id
        ORDER BY o.order_date DESC
    """)

    orders = cursor.fetchall()

    cursor.close()
    db.close()

    return orders


@router.get("/orders/summary")
def get_order_summary():

    db = get_database_connection()
    cursor = db.cursor(dictionary=True)

    cursor.execute("""
        SELECT
            COUNT(*) AS total_orders,

            SUM(status = 'Received') AS received,
            SUM(status = 'Shipped') AS shipped,
            SUM(status = 'Returned') AS returned,
            SUM(status = 'Cancelled') AS cancelled

        FROM orders
    """)

    summary = cursor.fetchone()

    cursor.close()
    db.close()

    return summary