from pydantic import BaseModel
from typing import Optional, Dict, List, Union
from enum import Enum
from datetime import datetime


class UserCustomizationEnum(str, Enum):
    text = "text"
    image = "image"
    logo = "logo"


class OrderItemCreate(BaseModel):
    product_id: str
    quantity: int
    selected_customizations: Optional[Dict[str, Dict[str, str]]] = None
    user_customization_type: UserCustomizationEnum
    user_customization_value: Optional[str]  # Optional if image/logo uploaded separately
    individual_price: int


class OrderItemWithBase64(BaseModel):
    product_id: str
    quantity: int
    selected_customizations: Optional[Dict[str, Dict[str, str]]] = None
    user_customization_type: UserCustomizationEnum
    user_customization_value: Optional[str] = None  # Text or base64 image
    image_extension: Optional[str] = "jpg"  # Only used for image/logo types
    individual_price: int


class OrderCreate(BaseModel):
    clerkId: str  # ✅ clerkId
    products: List[OrderItemCreate]
    total_price: int


class OrderCreateJSON(BaseModel):
    clerkId: str
    products: List[OrderItemWithBase64]
    total_price: int


# ✅ Response schemas
class OrderItemResponse(BaseModel):
    product_id: str
    quantity: int
    selected_customizations: Optional[Dict[str, Dict[str, str]]] = None
    user_customization_type: UserCustomizationEnum
    user_customization_value: Optional[str]
    individual_price: int

    class Config:
        orm_mode = True


class OrderResponse(BaseModel):
    order_id: str
    clerkId: str  # ✅ clerkId
    total_price: int
    status: str
    created_at: datetime
    items: List[OrderItemResponse]
    receipt_id: Optional[int] = None

    class Config:
        orm_mode = True


class OrderDetailsResponse(OrderResponse):
    user_name: str
    email: str
    phone_number: str
    address: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None
    country: Optional[str] = None
    pin_code: Optional[str] = None

    class Config:
        orm_mode = True

# For orders
class OrderListResponse(BaseModel):
    total: int
    orders: List[OrderResponse]