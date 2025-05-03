from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from typing import List
from models import Category
from routers.products.schemas import CategoryCreate, CategoryResponse, CategoryUpdate, CategoryListResponse
from sqlalchemy import func
from config import get_db 
from utils.aws import upload_base64_image_to_s3

categories_router = APIRouter()

# Admin-only: Create a new category.
@categories_router.post("/admin/categories", response_model=CategoryResponse, status_code=status.HTTP_201_CREATED)
async def create_category(category: CategoryCreate, db: AsyncSession = Depends(get_db)):
    # Handle image upload if provided
    image_url = None
    if category.image:
        image_url = await upload_base64_image_to_s3(
            category.image,
            file_extension=category.image_extension,
            folder="categories"
        )

    new_category = Category(
        name=category.name,
        allowed_customizations=category.allowed_customizations,
        image_url=image_url
    )
    db.add(new_category)
    await db.commit()
    await db.refresh(new_category)
    return new_category

@categories_router.get("/categories", response_model=CategoryListResponse)
async def get_categories(db: AsyncSession = Depends(get_db)):
    # Get total count
    total_result = await db.execute(select(func.count(Category.id)))
    total = total_result.scalar()
    
    # Get all categories
    result = await db.execute(select(Category))
    categories = result.scalars().all()
    
    return {"total": total, "categories": categories}

# Admin-only: Update an existing category.
@categories_router.put("/admin/categories/{category_id}", response_model=CategoryResponse)
async def update_category(category_id: int, category_update: CategoryUpdate, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Category).filter(Category.id == category_id))
    category = result.scalars().first()
    if not category:
        raise HTTPException(status_code=404, detail="Category not found")
    
    # Handle image update if provided
    if category_update.image:
        image_url = await upload_base64_image_to_s3(
            category_update.image,
            file_extension=category_update.image_extension,
            folder="categories"
        )
        # Don't include the base64 image data in the update data
        category_update_data = category_update.dict(exclude_unset=True, exclude={"image", "image_extension"})
        # Set the image URL directly
        category.image_url = image_url
    else:
        category_update_data = category_update.dict(exclude_unset=True)
    
    # Update other fields
    for key, value in category_update_data.items():
        setattr(category, key, value)
    
    await db.commit()
    await db.refresh(category)
    return category

