from fastapi import APIRouter
from backend.app.database import get_database_connection

router = APIRouter()


@router.get("/products")
def get_products():

    db = get_database_connection()

    cursor = db.cursor(dictionary=True)

    cursor.execute("SELECT * FROM products")

    products = cursor.fetchall()

    cursor.close()
    db.close()

    return products