from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from typing import List
from routers.products.models import ProductReview, Product
from routers.products.schemas import ProductReviewCreate, ProductReviewResponse
from ..crud import get_user_by_clerkId  
from config import get_db  

reviews_router = APIRouter()

# Public: Create a review for a product.
@reviews_router.post("/reviews", response_model=ProductReviewResponse, status_code=status.HTTP_201_CREATED)
async def create_review(review: ProductReviewCreate, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(ProductReview).filter(
            ProductReview.clerkId == review.clerkId,
            ProductReview.product_id == review.product_id
        )
    )
    existing_review = result.scalars().first()
    if existing_review:
        raise HTTPException(status_code=400, detail="User has already reviewed this product")
    
    user = await get_user_by_clerkId(db, review.clerkId)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    new_review = ProductReview(
        clerkId=review.clerkId,
        user_name=user.first_name + " " + user.last_name,  
        product_id=review.product_id,
        rating=review.rating,
        review_text=review.review_text
    )
    db.add(new_review)
    await db.commit()
    await db.refresh(new_review)
    
    # Update the product's average rating.
    result = await db.execute(select(ProductReview).filter(ProductReview.product_id == review.product_id))
    reviews = result.scalars().all()
    if reviews:
        avg_rating = sum(r.rating for r in reviews) / len(reviews)
        result = await db.execute(select(Product).filter(Product.product_id == review.product_id))
        product = result.scalars().first()
        if product:
            product.average_rating = avg_rating
            await db.commit()
    
    return new_review

# Public: Retrieve all reviews for a specific product.
@reviews_router.get("/reviews/{product_id}", response_model=List[ProductReviewResponse])
async def get_reviews(product_id: str, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(ProductReview).filter(ProductReview.product_id == product_id))
    reviews = result.scalars().all()
    return reviews
