from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, Form, Query
from fastapi.responses import StreamingResponse, JSONResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import asc, desc, and_
from sqlalchemy.orm import selectinload
from models import Order, OrderItem, OrderCounter, User, UserDetails, Product
from routers.orders.schemas import OrderDetailsResponse, OrderItemResponse, OrderListResponse, OrderCreateJSON
from sqlalchemy import func
from routers.orders.schemas import OrderResponse
from utils.aws import upload_base64_image_to_s3
from utils.order import generate_order_id
from utils.pdf_generator import create_order_pdf_from_db_data
from config import get_db
import json
import base64
from typing import List, Optional
from datetime import datetime, timedelta
from utils.email_helpers import send_owner_email, send_customer_email

orders_router = APIRouter()

# @orders_router.post("/checkout", status_code=status.HTTP_201_CREATED)
# async def place_order_json(
#     order_data: OrderCreateJSON,
#     db: AsyncSession = Depends(get_db)
# ):
#     # Get or create order counter
#     counter_result = await db.execute(select(OrderCounter).limit(1))
#     counter = counter_result.scalar()

#     if not counter:
#         counter = OrderCounter(current_number=1)  
#         db.add(counter)
#         await db.commit()
#         await db.refresh(counter)

#     # Generate order ID
#     order_id = generate_order_id(counter.current_number)
#     counter.current_number += 1
#     await db.commit()

#     # Validate that all products exist before creating the order
#     product_ids = [item.product_id for item in order_data.products]
    
#     # Check if products exist in the database
#     result = await db.execute(
#         select(Product.product_id).where(Product.product_id.in_(product_ids))
#     )
#     existing_product_ids = {prod_id for prod_id in result.scalars().all()}
    
#     # Check if any products are missing
#     missing_products = set(product_ids) - existing_product_ids
#     if missing_products:
#         raise HTTPException(
#             status_code=400, 
#             detail=f"Products with IDs {missing_products} do not exist"
#         )
    
#     # Create new order
#     new_order = Order(
#         order_id=order_id,
#         clerkId=order_data.clerkId,
#         total_price=order_data.total_price,
#         status="placed"
#     )
#     db.add(new_order)
#     await db.flush()  # Get new_order.id for OrderItems

#     # Process each product in the order
#     for item in order_data.products:
#         user_cust_value = None

#         # Handle user customization based on type
#         if item.user_customization_type in ["image", "logo"]:
#             if item.user_customization_value:
#                 # Upload base64 image to S3
#                 s3_url = await upload_base64_image_to_s3(
#                     item.user_customization_value, 
#                     file_extension=item.image_extension,
#                     folder="orders"
#                 )
#                 user_cust_value = s3_url
#             else:
#                 raise HTTPException(status_code=400, detail="Missing base64 image data for product.")
        
#         elif item.user_customization_type == "text":
#             user_cust_value = item.user_customization_value

#         # Create order item
#         order_item = OrderItem(
#             order_id=new_order.id,
#             product_id=item.product_id,
#             quantity=item.quantity,
#             selected_customizations=item.selected_customizations,
#             user_customization_type=item.user_customization_type,
#             user_customization_value=user_cust_value,
#             individual_price=item.individual_price
#         )
#         db.add(order_item)

#     await db.commit()
#     await db.refresh(new_order)

#     # Send email to the owner
#     await send_owner_email(new_order.order_id, order_data.total_price, order_data.clerkId, db)

#     # Send email to the customer
#     await send_customer_email(new_order.order_id, order_data.clerkId, order_data.total_price, db)

#     return {"message": "Order placed successfully", "order_id": new_order.order_id}

@orders_router.get("/user/{clerkId}", response_model=List[OrderResponse])
async def get_orders_by_user(
    clerkId: str,
    limit: int = Query(10, ge=1, le=100),
    offset: int = Query(0, ge=0),
    sort: str = Query("desc", regex="^(asc|desc)$"),
    db: AsyncSession = Depends(get_db)
):
    sort_order = asc(Order.created_at) if sort == "asc" else desc(Order.created_at)

    result = await db.execute(
        select(Order)
        .options(selectinload(Order.items)) 
        .where(Order.clerkId == clerkId)
        .order_by(sort_order)
        .offset(offset)
        .limit(limit)
    )
    orders = result.scalars().all()
    return orders

@orders_router.get("/{order_id}", response_model=OrderDetailsResponse)
async def get_order_by_id(
    order_id: str,
    db: AsyncSession = Depends(get_db)
):
    # Fetch the order with items
    result = await db.execute(
        select(Order)
        .options(selectinload(Order.items))
        .where(Order.order_id == order_id)
    )
    order = result.scalar()
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")

    # Fetch the user with details
    user_result = await db.execute(
        select(User)
        .where(User.clerkId == order.clerkId)
        .options(selectinload(User.details))
    )
    user = user_result.scalar()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    # Convert SQLAlchemy objects to dictionaries first
    order_dict = {
        "order_id": order.order_id,
        "clerkId": order.clerkId,
        "total_price": order.total_price,
        "status": order.status,
        "created_at": order.created_at,
        "receipt_id": order.receipt_id,
        "items": [
            {
                "product_id": item.product_id,
                "quantity": item.quantity,
                "selected_customizations": item.selected_customizations,
                "user_customization_type": item.user_customization_type,
                "user_customization_value": item.user_customization_value,
                "individual_price": item.individual_price
            }
            for item in order.items
        ]
    }

    # Create the response
    response = OrderDetailsResponse(
        **order_dict,
        user_name=f"{user.first_name} {user.last_name}",
        email=user.email,
        phone_number=user.phone_number,
        address=user.details.address if user.details else None,
        city=user.details.city if user.details else None,
        state=user.details.state if user.details else None,
        country=user.details.country if user.details else None,
        pin_code=user.details.pin_code if user.details else None,
    )

    return response

@orders_router.get("/admin/orders", response_model=OrderListResponse)
async def get_all_orders(
    limit: int = Query(10, ge=1, le=100),
    offset: int = Query(0, ge=0),
    sort: str = Query("desc", regex="^(asc|desc)$"),
    db: AsyncSession = Depends(get_db)
):
    sort_order = asc(Order.created_at) if sort == "asc" else desc(Order.created_at)

    total_result = await db.execute(select(func.count(Order.id)))
    total = total_result.scalar()

    # Get paginated orders
    result = await db.execute(
        select(Order)
        .options(
            selectinload(Order.items),   
            selectinload(Order.receipt) 
        )
        .order_by(sort_order)
        .offset(offset)
        .limit(limit)
    )
    orders = result.scalars().all()
    
    return {"total": total, "orders": orders}

@orders_router.get("/admin/orders/pdf")
async def generate_orders_pdf(
    db: AsyncSession = Depends(get_db),
    from_date: Optional[datetime] = None
):
    """
    Generate a PDF report of all orders or orders from a specific date
    Returns base64 encoded PDF string in JSON response
    
    Args:
        from_date: Optional date filter to get orders from this date onward
    """
    # Build the base query to fetch orders with items
    query = select(Order).options(
        selectinload(Order.items)
    ).order_by(Order.created_at.desc())
    
    # Apply date filter if provided
    if from_date:
        query = query.filter(Order.created_at >= from_date)
    
    # Execute query to get orders
    orders_result = await db.execute(query)
    orders = orders_result.scalars().all()
    
    if not orders:
        raise HTTPException(status_code=404, detail="No orders found for the given criteria")
    
    # Get all unique clerkIds from orders
    clerk_ids = {order.clerkId for order in orders}
    
    # Fetch all users related to these orders
    users_result = await db.execute(
        select(User).where(User.clerkId.in_(clerk_ids))
    )
    users = {user.clerkId: user for user in users_result.scalars().all()}
    
    # Fetch all user details
    user_details_result = await db.execute(
        select(UserDetails).where(UserDetails.clerkId.in_(clerk_ids))
    )
    user_details = {detail.clerkId: detail for detail in user_details_result.scalars().all()}
    
    # Get all product IDs from order items
    product_ids = set()
    for order in orders:
        for item in order.items:
            product_ids.add(item.product_id)
    
    # Fetch all products
    products_result = await db.execute(
        select(Product).where(Product.product_id.in_(product_ids))
    )
    products = {product.product_id: product for product in products_result.scalars().all()}
    
    # Generate the PDF
    pdf_buffer = create_order_pdf_from_db_data(orders, users, user_details, products)
    
    # Create a filename with date range
    if from_date:
        today = datetime.now()
        filename = f"orders_{from_date.strftime('%Y%m%d')}_to_{today.strftime('%Y%m%d')}.pdf"
    else:
        filename = f"orders_all_{datetime.now().strftime('%Y%m%d')}.pdf"
    
    # Convert PDF buffer to base64 string
    pdf_bytes = pdf_buffer.getvalue()
    base64_pdf = base64.b64encode(pdf_bytes).decode('utf-8')
    
    # Return JSON with base64 string
    return {
        "filename": filename,
        "content_type": "application/pdf",
        "pdf_data": base64_pdf
    }

@orders_router.get("/admin/orders/pdf/recent")
async def generate_recent_orders_pdf(
    days: int = Query(30, ge=1, le=365),
    db: AsyncSession = Depends(get_db)
):
    """
    Generate a PDF report of orders from the last X days
    Returns base64 encoded PDF string in JSON response
    
    Args:
        days: Number of days to look back (default: 30)
    """
    # Calculate date from X days ago
    from_date = datetime.now() - timedelta(days=days)
    
    # Reuse the main PDF generation route
    return await generate_orders_pdf(db=db, from_date=from_date)

@orders_router.get("/admin/orders/{order_id}/pdf")
async def generate_single_order_pdf(
    order_id: str,
    db: AsyncSession = Depends(get_db)
):
    """
    Generate a PDF report for a single order by its ID
    Returns base64 encoded PDF string in JSON response
    
    Args:
        order_id: The unique order ID to generate a PDF for
    """
    # Fetch the order with items
    order_result = await db.execute(
        select(Order)
        .options(selectinload(Order.items))
        .where(Order.order_id == order_id)
    )
    order = order_result.scalar()
    
    if not order:
        raise HTTPException(status_code=404, detail=f"Order with ID {order_id} not found")
    
    # Get the customer details
    user_result = await db.execute(
        select(User).where(User.clerkId == order.clerkId)
    )
    user = user_result.scalar()
    
    if not user:
        # If user doesn't exist, proceed with empty user info
        users = {}
    else:
        users = {user.clerkId: user}
    
    # Get user details if available
    user_details_result = await db.execute(
        select(UserDetails).where(UserDetails.clerkId == order.clerkId)
    )
    user_details = {detail.clerkId: detail for detail in user_details_result.scalars().all()}
    
    # Get all product IDs from order items
    product_ids = {item.product_id for item in order.items}
    
    # Fetch all products
    products_result = await db.execute(
        select(Product).where(Product.product_id.in_(product_ids))
    )
    products = {product.product_id: product for product in products_result.scalars().all()}
    
    # Generate the PDF with just this order
    pdf_buffer = create_order_pdf_from_db_data([order], users, user_details, products)
    
    # Create a filename
    filename = f"order_{order_id}_{datetime.now().strftime('%Y%m%d')}.pdf"
    
    # Convert PDF buffer to base64 string
    pdf_bytes = pdf_buffer.getvalue()
    base64_pdf = base64.b64encode(pdf_bytes).decode('utf-8')
    
    # Return JSON with base64 string
    return {
        "filename": filename,
        "content_type": "application/pdf",
        "pdf_data": base64_pdf
    }

