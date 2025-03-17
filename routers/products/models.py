# products/models.py
import enum
from sqlalchemy import Column, Integer, String, Float, ForeignKey, TIMESTAMP, UniqueConstraint, Enum as SQLAlchemyEnum
from sqlalchemy.sql import func
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()

# Enum for product status.
class ProductStatus(enum.Enum):
    in_stock = "in_stock"
    out_of_stock = "out_of_stock"
    discontinued = "discontinued"

# Enum for allowed customization types.
class CustomizationType(enum.Enum):
    size = "size"
    color = "color"

class UserCustomizationType(str, enum.Enum):
    text = "text"
    image = "image"
    logo = "logo"

# Category model.
class Category(Base):
    __tablename__ = "categories"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, nullable=False)
    allowed_customizations = Column(JSONB(SQLAlchemyEnum(CustomizationType, name="customization_type_enum")), nullable=True)  # size, color, etc.
    user_customization_options = Column(JSONB(SQLAlchemyEnum(UserCustomizationType, name="user_customization_type_enum")), nullable=True)  # text, image, logo
    created_at = Column(TIMESTAMP, server_default=func.now())

# Product model.
class Product(Base):
    __tablename__ = "products"
    id = Column(Integer, primary_key=True, index=True)
    product_id = Column(String, unique=True, index=True, nullable=False)
    main_image_url = Column(String, nullable=False)
    side_images_url = Column(JSONB, nullable=True)
    name = Column(String, nullable=False)
    price = Column(Integer, nullable=False)
    category_id = Column(Integer, ForeignKey("categories.id", ondelete="CASCADE"), nullable=False)
    description = Column(String, nullable=True)
    customization_options = Column(JSONB, nullable=True)
    status = Column(SQLAlchemyEnum(ProductStatus), nullable=False, default=ProductStatus.in_stock)
    average_rating = Column(Float, default=0)
    created_at = Column(TIMESTAMP, server_default=func.now())

# ProductReview model.
class ProductReview(Base):
    __tablename__ = "product_reviews"
    id = Column(Integer, primary_key=True, index=True)
    clerkId = Column(String, nullable=False)
    user_name = Column(String, nullable=False)
    product_id = Column(String, ForeignKey("products.product_id"), nullable=False)
    rating = Column(Integer, nullable=False)
    review_text = Column(String, nullable=True)
    created_at = Column(TIMESTAMP, server_default=func.now())
    __table_args__ = (UniqueConstraint('clerkId', 'product_id', name='_clerk_product_uc'),)
