# models.py
from sqlalchemy import Column, Integer, String, Float, ForeignKey, Enum, TIMESTAMP, UniqueConstraint
from sqlalchemy.orm import relationship
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.dialects.postgresql import JSONB
import enum
from sqlalchemy import func

Base = declarative_base()

# Enum for User Roles
class UserRole(enum.Enum):
    USER = "USER"
    ADMIN = "ADMIN"

# Enum for Product Status
class ProductStatus(enum.Enum):
    in_stock = "in_stock"
    out_of_stock = "out_of_stock"
    discontinued = "discontinued"

# Enum for allowed customization types
class CustomizationType(enum.Enum):
    size = "size"
    color = "color"

# Enum for User Customization Types
class UserCustomizationType(str, enum.Enum):
    text = "text"
    image = "image"
    logo = "logo"

# Category Model
class Category(Base):
    __tablename__ = "categories"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, nullable=False)
    allowed_customizations = Column(JSONB, nullable=True)
    user_customization_options = Column(JSONB, nullable=True)
    created_at = Column(TIMESTAMP, server_default=func.now())

# Product Model
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
    status = Column(Enum(ProductStatus), nullable=False, default=ProductStatus.in_stock)
    average_rating = Column(Float, default=0)
    created_at = Column(TIMESTAMP, server_default=func.now())

    category = relationship("Category")
    order_items = relationship("OrderItem", back_populates="product")

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

# User Model
class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    clerkId = Column(String, unique=True, nullable=False)
    first_name = Column(String, nullable=False)
    last_name = Column(String, nullable=False)
    email = Column(String, unique=True, nullable=False)
    phone_number = Column(String, unique=True, nullable=False)
    role = Column(Enum(UserRole), default=UserRole.USER, nullable=False)
    details = relationship("UserDetails", back_populates="user", uselist=False, cascade="all, delete-orphan")

# UserDetails Model
class UserDetails(Base):
    __tablename__ = "user_details"
    id = Column(Integer, primary_key=True, index=True)
    clerkId = Column(String, ForeignKey("users.clerkId"), unique=True)
    user = relationship("User", back_populates="details")
    address = Column(String, nullable=True)
    city = Column(String, nullable=True)
    state = Column(String, nullable=True)
    country = Column(String, nullable=True)
    pin_code = Column(String, nullable=True)

# Order Model
class Order(Base):
    __tablename__ = "orders"
    id = Column(Integer, primary_key=True, index=True)
    order_id = Column(String, unique=True, index=True)
    clerkId = Column(String, index=True)
    total_price = Column(Integer, nullable=False)
    status = Column(String, default="placed")
    created_at = Column(TIMESTAMP, server_default=func.now())
    receipt_id = Column(Integer, ForeignKey("receipts.id", ondelete="SET NULL"), nullable=True)

    items = relationship("OrderItem", back_populates="order")
    receipt = relationship("Receipt", back_populates="orders")

# OrderItem Model
class OrderItem(Base):
    __tablename__ = "order_items"
    id = Column(Integer, primary_key=True, index=True)
    order_id = Column(Integer, ForeignKey("orders.id", ondelete="CASCADE"))
    product_id = Column(String, ForeignKey("products.product_id"), nullable=False)
    quantity = Column(Integer, nullable=False)
    selected_customizations = Column(JSONB, nullable=True)
    user_customization_type = Column(String, nullable=True)
    user_customization_value = Column(String, nullable=True)
    individual_price = Column(Integer, nullable=False)

    order = relationship("Order", back_populates="items")
    product = relationship("Product", back_populates="order_items")

# OrderCounter Model
class OrderCounter(Base):
    __tablename__ = "order_counter"
    id = Column(Integer, primary_key=True, index=True)
    current_number = Column(Integer, default=1)

# Receipt Model
class Receipt(Base):
    __tablename__ = "receipts"
    id = Column(Integer, primary_key=True, index=True)
    payment_reference = Column(String, unique=True, nullable=True)
    amount_paid = Column(Integer, nullable=True)
    created_at = Column(TIMESTAMP, server_default=func.now())

    orders = relationship("Order", back_populates="receipt")

