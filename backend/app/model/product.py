from fastapi import APIRouter
from backend.app.database import db

router = APIRouter()


@router.get("/products")
def get_products():

    cursor = db.cursor(dictionary=True)

    cursor.execute("SELECT * FROM products")

    products = cursor.fetchall()

    cursor.close()

    return products