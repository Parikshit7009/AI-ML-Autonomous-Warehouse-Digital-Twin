from fastapi import APIRouter, HTTPException, status
from backend.app.database import get_database_connection
from backend.app.schemas.product import ProductCreate

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


@router.get("/products/{product_id}")
def get_product(product_id: int):
    db = get_database_connection()
    cursor = db.cursor(dictionary=True)

    query = "SELECT * FROM products WHERE product_id = %s"
    cursor.execute(query, (product_id,))
    product = cursor.fetchone()

    cursor.close()
    db.close()

    if product is None:
        return {
            "message": "Product not found"
        }

    return product


@router.post("/products", status_code=status.HTTP_201_CREATED)
def create_product(product: ProductCreate):
    db = get_database_connection()
    cursor = db.cursor()

    query = """
    INSERT INTO products (
        product_id,
        product_name,
        brand,
        category,
        sub_category,
        price,
        rating,
        review_count,
        stock_status,
        tags,
        description
    )
    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
    """

    values = (
        product.product_id,
        product.product_name,
        product.brand,
        product.category,
        product.sub_category,
        product.price,
        product.rating,
        product.review_count,
        product.stock_status,
        product.tags,
        product.description
    )

    try:
        cursor.execute(query, values)
        db.commit()

    except Exception:
        db.rollback()
        raise HTTPException(
            status_code=409,
            detail="Product with this ID already exists"
        )

    finally:
        cursor.close()
        db.close()

    return {
        "message": "Product created successfully",
        "product_id": product.product_id
    }