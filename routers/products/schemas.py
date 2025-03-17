from pydantic import BaseModel
from typing import Optional, Dict, List
from enum import Enum
from fastapi import Form

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

# Schemas for Product
class ProductCreateJSON(BaseModel):
    name: str
    price: int
    category_id: int
    description: Optional[str] = None
    # customization_options holds actual option values (e.g., {"size": ["S", "M", "L"], "color": ["RED", "BLUE"]})
    customization_options: Optional[Dict[str, List[str]]] = None
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
    average_rating: float
    status: ProductStatusEnum
    main_image_url: str  # ✅ Add this to return main image URL
    side_images_url: Optional[List[str]] = None  # ✅ Add this to return side images URLs

    class Config:
        orm_mode = True

# ✅ Pydantic model for Update (without image handling)
class ProductUpdate(BaseModel):
    name: Optional[str] = None
    price: Optional[int] = None
    category_id: Optional[int] = None
    description: Optional[str] = None
    customization_options: Optional[Dict[str, List[str]]] = None
    status: Optional[ProductStatusEnum] = None

# Schemas for Category
class CategoryCreate(BaseModel):
    name: str
    allowed_customizations: Optional[Dict[CustomizationTypeEnum, List[str]]] = None  # size, color, etc.
    user_customization_options: Optional[List[UserCustomizationTypeEnum]] = None  # text, image, logo

class CategoryUpdate(BaseModel):
    name: Optional[str] = None
    allowed_customizations: Optional[Dict[CustomizationTypeEnum, List[str]]] = None
    user_customization_options: Optional[List[UserCustomizationTypeEnum]] = None

class CategoryResponse(BaseModel):
    id: int
    name: str
    allowed_customizations: Optional[Dict[CustomizationTypeEnum, List[str]]] = None
    user_customization_options: Optional[List[UserCustomizationTypeEnum]] = None

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
