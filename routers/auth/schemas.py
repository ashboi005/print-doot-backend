from pydantic import BaseModel, EmailStr
from typing import Optional

class UserCreate(BaseModel):
    clerkId: str
    first_name: str
    last_name: str
    email: EmailStr
    phone_number: str
    role: Optional[str] = "USER"
