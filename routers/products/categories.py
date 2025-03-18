from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from typing import List
from models import Category
from routers.products.schemas import CategoryCreate, CategoryResponse, CategoryUpdate
from config import get_db 

categories_router = APIRouter()

# Admin-only: Create a new category.
@categories_router.post("/admin/categories", response_model=CategoryResponse, status_code=status.HTTP_201_CREATED)
async def create_category(category: CategoryCreate, db: AsyncSession = Depends(get_db)):
    new_category = Category(
        name=category.name,
        allowed_customizations=category.allowed_customizations,
        user_customization_options=category.user_customization_options
    )
    db.add(new_category)
    await db.commit()
    await db.refresh(new_category)
    return new_category

# Public: Retrieve all categories.
@categories_router.get("/categories", response_model=List[CategoryResponse])
async def get_categories(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Category))
    categories = result.scalars().all()
    return categories

# Admin-only: Update an existing category.
@categories_router.put("/admin/categories/{category_id}", response_model=CategoryResponse)
async def update_category(category_id: int, category_update: CategoryUpdate, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Category).filter(Category.id == category_id))
    category = result.scalars().first()
    if not category:
        raise HTTPException(status_code=404, detail="Category not found")
    
    update_data = category_update.dict(exclude_unset=True)
    for key, value in update_data.items():
        setattr(category, key, value)
    
    await db.commit()
    await db.refresh(category)
    return category
