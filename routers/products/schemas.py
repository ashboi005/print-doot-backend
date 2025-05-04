from pydantic import BaseModel, root_validator
from typing import Optional, Dict, List, Union
from enum import Enum
from fastapi import Form
from datetime import datetime

# Enum for product status in schemas.
class ProductStatusEnum(str, Enum):
    in_stock = "in_stock"
    out_of_stock = "out_of_stock"
    discontinued = "discontinued"

# Enum for allowed customization types in schemas.
class CustomizationTypeEnum(str, Enum):
    size = "size"
    color = "color"

# Enum for user customizations in schemas
class UserCustomizationTypeEnum(str, Enum):
    text = "text"
    image = "image"
    logo = "logo"

# Schema for dimensions
class ProductDimensions(BaseModel):
    length: float
    breadth: float
    height: float

# Schema for bulk price range item
class BulkPriceItem(BaseModel):
    min_quantity: int
    max_quantity: Optional[int] = None  # Optional upper limit, if None it means "and above"
    price: int

# Schemas for Product
class ProductCreateJSON(BaseModel):
    name: str
    price: int
    category_id: int
    product_id: Optional[str] = None  # Optional field for admin to provide custom product ID
    description: Optional[str] = None
    # customization_options holds actual option values (e.g., {"size": ["S:#size_S", "M:#size_M"], "color": ["RED:#FF0000", "BLUE:#0000FF"]})
    customization_options: Optional[Dict[str, Dict[str, str]]] = None
    # bulk_prices holds quantity-price pairs as a list of objects with integer quantities and prices
    bulk_prices: Optional[List[BulkPriceItem]] = None
    dimensions: Optional[ProductDimensions] = None
    weight: Optional[int] = None  # Weight in grams
    material: Optional[str] = None  # Material the product is made of
    status: ProductStatusEnum

class ProductCreateForm:
    def __init__(
        self,
        name: str = Form(...),
        price: int = Form(...),
        category_id: int = Form(...),
        description: Optional[str] = Form(None),
        customization_options: Optional[str] = Form(None),  # JSON string
        status: ProductStatusEnum = Form(...),
    ):
        self.name = name
        self.price = price
        self.category_id = category_id
        self.description = description
        self.customization_options = customization_options
        self.status = status


class ProductResponse(BaseModel):
    product_id: str
    name: str
    price: int
    description: Optional[str] = None
    bulk_prices: Optional[List[BulkPriceItem]] = None
    dimensions: Optional[ProductDimensions] = None
    weight: Optional[int] = None  # Weight in grams
    material: Optional[str] = None  # Material the product is made of
    average_rating: float
    status: ProductStatusEnum
    main_image_url: str
    side_images_url: Optional[List[str]] = None
    category_name: Optional[str] = None  # New field to return the category name

    class Config:
        orm_mode = True

    @root_validator(pre=True)
    def set_category_name(cls, values):
        # If values is not a dict, convert it using __dict__
        if not isinstance(values, dict):
            values = values.__dict__
        category = values.get("category")
        if category:
            if isinstance(category, dict):
                values["category_name"] = category.get("name")
            elif hasattr(category, "name"):
                values["category_name"] = category.name
        return values



# ✅ Pydantic model for Update (without image handling)
class ProductUpdate(BaseModel):
    name: Optional[str] = None
    price: Optional[int] = None
    category_id: Optional[int] = None
    description: Optional[str] = None
    customization_options: Optional[Dict[str, Dict[str, str]]] = None
    bulk_prices: Optional[List[BulkPriceItem]] = None
    dimensions: Optional[ProductDimensions] = None
    weight: Optional[int] = None
    material: Optional[str] = None
    status: Optional[ProductStatusEnum] = None

# Schemas for Category
class CategoryCreate(BaseModel):
    name: str
    allowed_customizations: Optional[Dict[CustomizationTypeEnum, Dict[str, str]]] = None  # e.g. {"color": {"RED": "#FF0000", "BLUE": "#0000FF"}}
    image: Optional[str] = None  # Base64 encoded image
    image_extension: Optional[str] = "jpg"  # Image extension (jpg, png, etc.)

class CategoryUpdate(BaseModel):
    name: Optional[str] = None
    allowed_customizations: Optional[Dict[CustomizationTypeEnum, Dict[str, str]]] = None  # e.g. {"color": {"RED": "#FF0000", "BLUE": "#0000FF"}}
    image: Optional[str] = None  # Base64 encoded image
    image_extension: Optional[str] = "jpg"  # Image extension (jpg, png, etc.)

class CategoryResponse(BaseModel):
    id: int
    name: str
    allowed_customizations: Optional[Dict[CustomizationTypeEnum, Dict[str, str]]] = None
    image_url: Optional[str] = None

    class Config:
        orm_mode = True

# Schemas for Product Review
class ProductReviewCreate(BaseModel):
    clerkId: str
    product_id: str  # Custom product ID from the Product model
    rating: int
    review_text: Optional[str] = None

class ProductReviewResponse(BaseModel):
    id: int
    clerkId: str
    user_name: str
    product_id: str
    rating: int
    review_text: Optional[str] = None

    class Config:
        orm_mode = True


class ProductListResponse(BaseModel):
    total: int
    products: List[ProductResponse]

class CategoryListResponse(BaseModel):
    total: int
    categories: List[CategoryResponse]

# Schema for base64 encoded product images
class ProductImageBase64(BaseModel):
    main_image: Optional[str] = None  # Base64 encoded image string
    main_image_extension: Optional[str] = "jpg"  # Can be jpg, jpeg, png, webp, etc.
    side_images: Optional[List[str]] = None  # List of base64 encoded image strings
    side_images_extensions: Optional[List[str]] = None  # List of file extensions for each side image

# Schemas for Coupon
class CouponCreate(BaseModel):
    code: str
    discount_percentage: int
    applicable_categories: Optional[List[int]] = None
    applicable_products: Optional[List[str]] = None
    expires_at: Optional[datetime] = None

class CouponUpdate(BaseModel):
    code: Optional[str] = None
    discount_percentage: Optional[int] = None
    applicable_categories: Optional[List[int]] = None
    applicable_products: Optional[List[str]] = None
    active: Optional[int] = None
    expires_at: Optional[datetime] = None

class CouponResponse(BaseModel):
    id: int
    code: str
    discount_percentage: int
    applicable_categories: Optional[List[int]] = None
    applicable_products: Optional[List[str]] = None
    active: int
    created_at: datetime
    expires_at: Optional[datetime] = None

    class Config:
        orm_mode = True

class CouponListResponse(BaseModel):
    total: int
    coupons: List[CouponResponse]

class CouponVerifyRequest(BaseModel):
    code: str
    category_id: Optional[int] = None
    product_id: Optional[str] = None

class CouponVerifyResponse(BaseModel):
    valid: bool
    discount_percentage: Optional[int] = None
    message: Optional[str] = None
