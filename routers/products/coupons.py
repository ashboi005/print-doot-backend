from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from typing import List, Optional
from sqlalchemy import func
from datetime import datetime

from models import Coupon
from routers.products.schemas import (
    CouponCreate, 
    CouponUpdate, 
    CouponResponse, 
    CouponListResponse,
    CouponVerifyRequest,
    CouponVerifyResponse
)
from config import get_db

coupons_router = APIRouter()

# Admin-only: Create a new coupon
@coupons_router.post("/admin/coupons", response_model=CouponResponse, status_code=status.HTTP_201_CREATED)
async def create_coupon(coupon: CouponCreate, db: AsyncSession = Depends(get_db)):
    # Check if coupon code already exists
    result = await db.execute(select(Coupon).filter(Coupon.code == coupon.code))
    existing_coupon = result.scalars().first()
    
    if existing_coupon:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Coupon code '{coupon.code}' already exists"
        )
    
    # Create new coupon
    new_coupon = Coupon(
        code=coupon.code,
        discount_percentage=coupon.discount_percentage,
        applicable_categories=coupon.applicable_categories,
        applicable_products=coupon.applicable_products,
        expires_at=coupon.expires_at
    )
    
    db.add(new_coupon)
    await db.commit()
    await db.refresh(new_coupon)
    
    return new_coupon

# Admin-only: Get all coupons
@coupons_router.get("/admin/coupons", response_model=CouponListResponse)
async def get_all_coupons(db: AsyncSession = Depends(get_db)):
    # Get total count
    total_result = await db.execute(select(func.count(Coupon.id)))
    total = total_result.scalar()
    
    # Get all coupons
    result = await db.execute(select(Coupon))
    coupons = result.scalars().all()
    
    return {"total": total, "coupons": coupons}

# Admin-only: Get a specific coupon by ID
@coupons_router.get("/admin/coupons/{coupon_id}", response_model=CouponResponse)
async def get_coupon(coupon_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Coupon).filter(Coupon.id == coupon_id))
    coupon = result.scalars().first()
    
    if not coupon:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Coupon not found"
        )
    
    return coupon

# Admin-only: Update an existing coupon
@coupons_router.put("/admin/coupons/{coupon_id}", response_model=CouponResponse)
async def update_coupon(coupon_id: int, coupon_update: CouponUpdate, db: AsyncSession = Depends(get_db)):
    # Check if coupon exists
    result = await db.execute(select(Coupon).filter(Coupon.id == coupon_id))
    coupon = result.scalars().first()
    
    if not coupon:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Coupon not found"
        )
    
    # If code is being changed, check if the new code already exists
    if coupon_update.code and coupon_update.code != coupon.code:
        code_check = await db.execute(select(Coupon).filter(Coupon.code == coupon_update.code))
        existing_code = code_check.scalars().first()
        
        if existing_code:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Coupon code '{coupon_update.code}' already exists"
            )
    
    # Update fields
    update_data = coupon_update.dict(exclude_unset=True)
    for key, value in update_data.items():
        setattr(coupon, key, value)
    
    await db.commit()
    await db.refresh(coupon)
    
    return coupon

# Admin-only: Delete a coupon
@coupons_router.delete("/admin/coupons/{coupon_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_coupon(coupon_id: int, db: AsyncSession = Depends(get_db)):
    # Check if coupon exists
    result = await db.execute(select(Coupon).filter(Coupon.id == coupon_id))
    coupon = result.scalars().first()
    
    if not coupon:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Coupon not found"
        )
    
    # Delete the coupon
    await db.delete(coupon)
    await db.commit()
    
    return None

# Public: Verify a coupon code
@coupons_router.post("/coupons/verify", response_model=CouponVerifyResponse)
async def verify_coupon(verify_request: CouponVerifyRequest, db: AsyncSession = Depends(get_db)):
    # Check if coupon exists and is active
    result = await db.execute(
        select(Coupon).filter(
            Coupon.code == verify_request.code,
            Coupon.active == 1
        )
    )
    coupon = result.scalars().first()
    
    if not coupon:
        return {
            "valid": False,
            "message": "Invalid or inactive coupon code"
        }
    
    # Check if coupon has expired
    if coupon.expires_at and coupon.expires_at < datetime.now():
        return {
            "valid": False,
            "message": "Coupon has expired"
        }
    
    # Check if applicable to the provided category_id
    if verify_request.category_id and coupon.applicable_categories:
        if verify_request.category_id not in coupon.applicable_categories:
            # If category doesn't match, check if product_id is applicable
            if not verify_request.product_id or not coupon.applicable_products or verify_request.product_id not in coupon.applicable_products:
                return {
                    "valid": False,
                    "message": "Coupon not applicable to this category or product"
                }
    
    # Check if applicable to the provided product_id
    elif verify_request.product_id and coupon.applicable_products:
        if verify_request.product_id not in coupon.applicable_products:
            return {
                "valid": False,
                "message": "Coupon not applicable to this product"
            }
    
    # If no specific category or product filters are set on the coupon,
    # or if they match the request, the coupon is valid
    return {
        "valid": True,
        "discount_percentage": coupon.discount_percentage,
        "message": "Valid coupon"
    }