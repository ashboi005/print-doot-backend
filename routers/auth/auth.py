from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from config import get_db
from routers.auth.schemas import UserCreate
from models import User
from sqlalchemy.future import select
from ..crud import get_user_by_email,get_user_by_clerkId

auth_router = APIRouter()

async def get_user_by_email(db: AsyncSession, email: str):
    result = await db.execute(select(User).filter(User.email == email))
    return result.scalars().first()

@auth_router.post("/create-user")
async def create_user(user: UserCreate, db: AsyncSession = Depends(get_db)):
    existing_user = await get_user_by_clerkId(db, user.clerkId)
    if existing_user:
        raise HTTPException(status_code=400, detail="User already exists")

    new_user = User(**user.dict())
    db.add(new_user)
    await db.commit()
    await db.refresh(new_user)
    
    return new_user

@auth_router.delete("/delete-user/{clerkId}")
async def delete_user(clerkId: str, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(User).filter(User.clerkId == clerkId))
    user = result.scalars().first()

    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    await db.delete(user)
    await db.commit()
    return {"message": "User deleted successfully"}
