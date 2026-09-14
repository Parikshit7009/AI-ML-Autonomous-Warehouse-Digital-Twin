from pydantic import BaseModel, Field


class ProductCreate(BaseModel):
    product_id: int
    product_name: str
    brand: str | None = None
    category: str | None = None
    sub_category: str | None = None
    price: float | None = Field(default=None, ge=0)
    rating: float | None = Field(default=None, ge=0, le=5)
    review_count: int | None = Field(default=None, ge=0)
    stock_status: str | None = None
    tags: str | None = None
    description: str | None = None