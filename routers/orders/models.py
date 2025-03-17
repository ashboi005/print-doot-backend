from sqlalchemy import Column, Integer, String, ForeignKey, JSON, TIMESTAMP, func
from sqlalchemy.orm import relationship
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()

class Order(Base):
    __tablename__ = "orders"

    id = Column(Integer, primary_key=True, index=True)
    order_id = Column(String, unique=True, index=True)  # PRNTDT-AAA00001
    clerkId = Column(String, index=True) 
    total_price = Column(Integer, nullable=False)
    status = Column(String, default="placed")  # placed, paid, shipped, etc.
    created_at = Column(TIMESTAMP, server_default=func.now())

    # ✅ Receipt relation
    receipt_id = Column(Integer, ForeignKey("receipts.id", ondelete="SET NULL"), nullable=True)

    items = relationship("OrderItem", back_populates="order")
    receipt = relationship("Receipt", back_populates="orders")


class OrderItem(Base):
    __tablename__ = "order_items"

    id = Column(Integer, primary_key=True, index=True)
    order_id = Column(Integer, ForeignKey("orders.id", ondelete="CASCADE"))
    product_id = Column(Integer, nullable=False)
    quantity = Column(Integer, nullable=False)
    selected_customizations = Column(JSON, nullable=True)  # size, color, etc.
    user_customization_type = Column(String, nullable=True)  # text/image/logo
    user_customization_value = Column(String, nullable=True)  # text or S3 URL
    individual_price = Column(Integer, nullable=False)

    order = relationship("Order", back_populates="items")


class OrderCounter(Base):
    __tablename__ = "order_counter"
    id = Column(Integer, primary_key=True, index=True)
    current_number = Column(Integer, default=1)


# ✅ Receipt Model
class Receipt(Base):
    __tablename__ = "receipts"

    id = Column(Integer, primary_key=True, index=True)
    payment_reference = Column(String, unique=True, nullable=True)  # e.g., Razorpay payment id
    amount_paid = Column(Integer, nullable=True)
    created_at = Column(TIMESTAMP, server_default=func.now())

    orders = relationship("Order", back_populates="receipt")
