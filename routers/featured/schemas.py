from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime

# Base schemas
class ProductIdList(BaseModel):
    product_ids: List[str]

class FeaturedProductBase(BaseModel):
    product_id: str
    created_at: Optional[datetime] = None

    class Config:
        orm_mode = True

# Banner schemas
class BannerCreate(BaseModel):
    image: str  # Base64 encoded image
    image_extension: str = "jpg"
    display_order: Optional[int] = 0
    active: Optional[int] = 1

class BannerResponse(BaseModel):
    id: int
    image_url: str
    display_order: int
    active: int
    created_at: datetime

    class Config:
        orm_mode = True

class BannerListResponse(BaseModel):
    total: int
    banners: List[BannerResponse]

class BannerUpdate(BaseModel):
    display_order: Optional[int] = None
    active: Optional[int] = None

# Shop by need schemas
class ShopByNeedCreate(BaseModel):
    product_id: str
    need: str

class ShopByNeedUpdate(BaseModel):
    product_id: Optional[str] = None
    need: Optional[str] = None

class ShopByNeedResponse(FeaturedProductBase):
    id: int
    need: str
    # Product details will be included

class ShopByNeedBulkCreate(BaseModel):
    need: str
    product_ids: List[str]

# Featured product response including product details
class FeaturedProductResponse(FeaturedProductBase):
    id: int
    # The following fields will be populated from the Product model
    name: Optional[str] = None
    price: Optional[int] = None
    description: Optional[str] = None
    main_image_url: Optional[str] = None
    category_name: Optional[str] = None
    average_rating: Optional[float] = None

# Response lists
class BestSellingListResponse(BaseModel):
    total: int
    products: List[FeaturedProductResponse]

class OnSaleListResponse(BaseModel):
    total: int
    products: List[FeaturedProductResponse]

class TrendingListResponse(BaseModel):
    total: int
    products: List[FeaturedProductResponse]

class NewArrivalsListResponse(BaseModel):
    total: int
    products: List[FeaturedProductResponse]

class ShopByNeedListResponse(BaseModel):
    total: int
    products: List[FeaturedProductResponse]

# Need options response
class NeedResponse(BaseModel):
    need: str
    count: int

class NeedsListResponse(BaseModel):
    total: int
    needs: List[NeedResponse]