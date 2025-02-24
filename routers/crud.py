from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from models import User

async def get_user_by_email(db: AsyncSession, email: str):
    result = await db.execute(select(User).filter(User.email == email))
    return result.scalars().first()

async def get_user_by_clerkId(db: AsyncSession, clerkId: str):
    result = await db.execute(select(User).filter(User.clerkId == clerkId))
    return result.scalars().first()
