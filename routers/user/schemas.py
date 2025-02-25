from pydantic import BaseModel,EmailStr
from typing import Optional

class UserDetailsBase(BaseModel):
    address: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None
    country: Optional[str] = None
    pin_code: Optional[str] = None

class UserUpdate(UserDetailsBase):
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    email: Optional[EmailStr] = None
    phone_number: Optional[str] = None

class UserDetailsCreate(UserDetailsBase):
    clerkId: str  


