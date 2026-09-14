from fastapi import APIRouter, HTTPException
from backend.app.database import get_database_connection

router = APIRouter()


@router.get("/inventory")
def get_inventory():
    db = get_database_connection()
    cursor = db.cursor(dictionary=True)

    cursor.execute("""
        SELECT
            i.inventory_id,
            i.product_id,
            p.product_name,
            i.quantity,
            i.warehouse_location,
            i.reorder_level,
            i.last_updated
        FROM inventory i
        JOIN products p
        ON i.product_id = p.product_id
    """)

    inventory = cursor.fetchall()

    cursor.close()
    db.close()

    return inventory


@router.get("/inventory/{product_id}")
def get_product_inventory(product_id: int):
    db = get_database_connection()
    cursor = db.cursor(dictionary=True)

    cursor.execute("""
        SELECT
            i.inventory_id,
            i.product_id,
            p.product_name,
            i.quantity,
            i.warehouse_location,
            i.reorder_level,
            i.last_updated
        FROM inventory i
        JOIN products p
        ON i.product_id = p.product_id
        WHERE i.product_id = %s
    """, (product_id,))

    inventory = cursor.fetchone()

    cursor.close()
    db.close()

    if inventory is None:
        raise HTTPException(
            status_code=404,
            detail="Inventory not found for this product"
        )

    return inventory