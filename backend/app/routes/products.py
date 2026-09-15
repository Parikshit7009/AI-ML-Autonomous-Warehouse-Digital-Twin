from fastapi import APIRouter, HTTPException, status, Depends

from backend.app.database import get_database_connection
from backend.app.schemas.product import ProductCreate
from backend.app.auth.dependencies import get_current_user


router = APIRouter()


# Get all products
@router.get("/products")
def get_products(
    current_user=Depends(get_current_user)
):
    db = get_database_connection()
    cursor = db.cursor(dictionary=True)

    try:
        cursor.execute("SELECT * FROM products")
        products = cursor.fetchall()
        return products

    finally:
        cursor.close()
        db.close()


# Get single product
@router.get("/products/{product_id}")
def get_product(
    product_id: int,
    current_user=Depends(get_current_user)
):
    db = get_database_connection()
    cursor = db.cursor(dictionary=True)

    try:
        query = """
            SELECT *
            FROM products
            WHERE product_id = %s
        """

        cursor.execute(query, (product_id,))
        product = cursor.fetchone()

    finally:
        cursor.close()
        db.close()

    if product is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Product not found"
        )

    return product


# Create product
@router.post(
    "/products",
    status_code=status.HTTP_201_CREATED
)
def create_product(
    product: ProductCreate,
    current_user=Depends(get_current_user)
):
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
        VALUES (
            %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s
        )
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
            status_code=status.HTTP_409_CONFLICT,
            detail="Product with this ID already exists"
        )

    finally:
        cursor.close()
        db.close()

    return {
        "message": "Product created successfully",
        "product_id": product.product_id
    }