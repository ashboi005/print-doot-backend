from .smtp import send_email
from routers.crud import get_email_by_clerkId
from fastapi import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from models import Product
from models import OrderItem
from sqlalchemy.future import select
from models import Order
import sqlalchemy as sa


async def send_owner_email(order_id: str, total_price: int):
    owner_email = "printdootweb@gmail.com"
    if not owner_email:
        raise HTTPException(status_code=404, detail="Owner email not found.")

    subject = f"New Order Placed: {order_id}"
    body = f"""
    <h3>An order has been placed with the following details:</h3>
    <p>Order ID: {order_id}</p>
    <p>Total Price: {total_price}</p>
    <p>Click <a href="http://printdoot.com/order/{order_id}">here</a> to view the order details.</p>
    """
    send_email(owner_email, subject, body)


async def send_customer_email(custom_order_id: str, clerk_id: str, total_price: int, db: AsyncSession):
    # Fetch customer email using clerkId
    customer_email = await get_email_by_clerkId(db, clerk_id)
    if not customer_email:
        raise HTTPException(status_code=404, detail="Customer email not found.")

    # Fetch the Order record by the custom order_id (the string)
    order_result = await db.execute(
        sa.select(Order).filter(Order.order_id == custom_order_id)
    )
    order_obj = order_result.scalar()
    if not order_obj:
        raise HTTPException(status_code=404, detail="Order not found.")

    # Now use the primary key (order_obj.id) to fetch order items
    items_result = await db.execute(
        sa.select(OrderItem).filter(OrderItem.order_id == order_obj.id)
    )
    order_items = items_result.scalars().all()

    # Start building the email body
    subject = f"Order Confirmation: {custom_order_id}"
    body = f"""
    <h3>Thank you for your order!</h3>
    <p>Your order has been successfully placed. Here are the details:</p>
    <p>Order ID: {custom_order_id}</p>
    <p>Total Price: {total_price}</p>
    <p>Click <a href="http://printdoot.com/order/{custom_order_id}">here</a> to track your order.</p>
    <h4>Order Items:</h4>
    <ul>
    """

    # Add each order item with product details
    for item in order_items:
        # Fetch product details based on product_id
        product_result = await db.execute(sa.select(Product).filter(Product.product_id == item.product_id))
        product = product_result.scalar()

        if product:
            body += f"""
            <li>
                <strong>Product Name:</strong> {product.name} <br>
                <strong>Description:</strong> {product.description} <br>
                <strong>Price:</strong> {item.individual_price} <br>
                <strong>Quantity:</strong> {item.quantity} <br>
                <strong>Customization:</strong> {item.user_customization_type}: {item.user_customization_value} <br>
                <strong>Image:</strong> <img src="{product.main_image_url}" alt="{product.name}" width="100" height="100"> <br>
            </li>
            """

    body += "</ul>"

    # Send the email using your helper function (assuming send_email is defined)
    send_email(customer_email, subject, body)
