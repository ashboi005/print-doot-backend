from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from config import get_db
from routers.user.schemas import UserDetailsCreate, UserUpdate
from models import User, UserDetails

users_router = APIRouter()

@users_router.post("/add-details")
async def add_user_details(details: UserDetailsCreate, db: AsyncSession = Depends(get_db)):
    """Add user details if they don't already exist."""

    user_result = await db.execute(select(User).filter(User.clerkId == details.clerkId))
    user = user_result.scalars().first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    details_result = await db.execute(select(UserDetails).filter(UserDetails.clerkId == details.clerkId))
    existing_details = details_result.scalars().first()
    if existing_details:
        raise HTTPException(status_code=400, detail="User details already exist")

    new_details = UserDetails(**details.dict())
    db.add(new_details)
    await db.commit()
    await db.refresh(new_details)

    return {"message": "User details added successfully", "data": new_details}

@users_router.put("/update-details/{clerkId}")
async def update_user_details(clerkId: str, details: UserUpdate, db: AsyncSession = Depends(get_db)):
    """Update both User and UserDetails fields for a given Clerk ID."""

    user_result = await db.execute(select(User).filter(User.clerkId == clerkId))
    user = user_result.scalars().first()

    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    details_result = await db.execute(select(UserDetails).filter(UserDetails.clerkId == clerkId))
    user_details = details_result.scalars().first()

    user_update_data = details.dict(exclude_unset=True, include={"first_name", "last_name", "email", "phone_number"})
    for key, value in user_update_data.items():
        setattr(user, key, value)

    if user_details:
        details_update_data = details.dict(exclude_unset=True, exclude={"first_name", "last_name", "email", "phone_number"})
        for key, value in details_update_data.items():
            setattr(user_details, key, value)

    await db.commit()
    
    await db.refresh(user)
    if user_details:
        await db.refresh(user_details)

    return {"message": "User details updated successfully", "user": user, "user_details": user_details}