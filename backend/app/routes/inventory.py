from fastapi import APIRouter, HTTPException, Depends

from backend.app.database import get_database_connection
from backend.app.auth.dependencies import get_current_user


router = APIRouter()


# Get all inventory
@router.get("/inventory")
def get_inventory(
    current_user=Depends(get_current_user)
):
    db = get_database_connection()
    cursor = db.cursor(dictionary=True)

    try:
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

        return inventory

    finally:
        cursor.close()
        db.close()


# Get inventory for a specific product
@router.get("/inventory/{product_id}")
def get_product_inventory(
    product_id: int,
    current_user=Depends(get_current_user)
):
    db = get_database_connection()
    cursor = db.cursor(dictionary=True)

    try:
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

    finally:
        cursor.close()
        db.close()

    if inventory is None:
        raise HTTPException(
            status_code=404,
            detail="Inventory not found for this product"
        )

    return inventory