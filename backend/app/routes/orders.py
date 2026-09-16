from fastapi import APIRouter, HTTPException, Depends
from backend.app.database import get_database_connection
from backend.app.auth.dependencies import get_current_user

router = APIRouter()


# Get all orders
@router.get("/orders")
def get_orders(
    current_user=Depends(get_current_user)
):
    db = get_database_connection()
    cursor = db.cursor(dictionary=True)

    try:
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

        return orders

    finally:
        cursor.close()
        db.close()


# Get a single order
@router.get("/orders/{order_id}")
def get_order(
    order_id: int,
    current_user=Depends(get_current_user)
):
    db = get_database_connection()
    cursor = db.cursor(dictionary=True)

    try:
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
            WHERE o.order_id = %s
        """, (order_id,))

        order = cursor.fetchone()

    finally:
        cursor.close()
        db.close()

    if order is None:
        raise HTTPException(
            status_code=404,
            detail="Order not found"
        )

    return order


# Create a new order
@router.post("/orders")
def create_order(
    product_id: int,
    quantity: int,
    status: str = "Received",
    current_user=Depends(get_current_user)
):
    allowed_statuses = [
        "Received",
        "Shipped",
        "Returned",
        "Cancelled"
    ]

    if status not in allowed_statuses:
        raise HTTPException(
            status_code=400,
            detail="Invalid order status"
        )

    if quantity <= 0:
        raise HTTPException(
            status_code=400,
            detail="Quantity must be greater than 0"
        )

    db = get_database_connection()
    cursor = db.cursor()

    try:
        # Check that product exists
        cursor.execute(
            "SELECT product_id FROM products WHERE product_id = %s",
            (product_id,)
        )

        product = cursor.fetchone()

        if product is None:
            raise HTTPException(
                status_code=404,
                detail="Product not found"
            )

        cursor.execute("""
            INSERT INTO orders
            (product_id, quantity, status)
            VALUES (%s, %s, %s)
        """, (
            product_id,
            quantity,
            status
        ))

        db.commit()

        order_id = cursor.lastrowid

        return {
            "message": "Order created successfully",
            "order_id": order_id
        }

    finally:
        cursor.close()
        db.close()