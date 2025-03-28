from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, Form, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import asc, desc
from sqlalchemy.orm import selectinload
from models import Order, OrderItem, OrderCounter, User
from routers.orders.schemas import OrderDetailsResponse, OrderItemResponse, OrderListResponse
from sqlalchemy import func
from routers.orders.schemas import OrderResponse
from utils.aws import upload_image_to_s3
from utils.order import generate_order_id  
from config import get_db
import json
from typing import List
from utils.email_helpers import send_owner_email, send_customer_email

orders_router = APIRouter()

@orders_router.post("/checkout", status_code=status.HTTP_201_CREATED)
async def place_order(
    clerkId: str = Form(...),
    total_price: int = Form(...),
    products: str = Form(...),
    files: List[UploadFile] = File(None),
    db: AsyncSession = Depends(get_db)
):
    counter_result = await db.execute(select(OrderCounter).limit(1))
    counter = counter_result.scalar()

    if not counter:
        counter = OrderCounter(current_number=1)  
        db.add(counter)
        await db.commit()
        await db.refresh(counter)

    order_id = generate_order_id(counter.current_number)

    counter.current_number += 1
    await db.commit()  

    products_data = json.loads(products)

    new_order = Order(
        order_id=order_id,
        clerkId=clerkId,
        total_price=total_price,
        status="placed"
    )
    db.add(new_order)
    await db.flush()  # Get new_order.id for OrderItems

    file_index = 0  # Index to map files to products

    for item in products_data:
        user_cust_value = None

        # ✅ Handle user customization image/logo
        if item['user_customization_type'] in ["image", "logo"]:
            if files and len(files) > file_index:
                s3_url = await upload_image_to_s3(files[file_index], folder="orders")
                user_cust_value = s3_url
                file_index += 1
            else:
                raise HTTPException(status_code=400, detail="Missing image/logo file for product.")

        # ✅ Handle user customization text
        elif item['user_customization_type'] == "text":
            user_cust_value = item.get("user_customization_value")

        # ✅ Create order item
        order_item = OrderItem(
            order_id=new_order.id,
            product_id=item['product_id'],
            quantity=item['quantity'],
            selected_customizations=item.get('selected_customizations'),
            user_customization_type=item['user_customization_type'],
            user_customization_value=user_cust_value,
            individual_price=item['individual_price']
        )
        db.add(order_item)

    await db.commit()
    await db.refresh(new_order)

    # Send email to the owner
    await send_owner_email(new_order.order_id, total_price)

    # Send email to the customer
    await send_customer_email(new_order.order_id, clerkId, total_price, db)

    return {"message": "Order placed successfully", "order_id": new_order.order_id}



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