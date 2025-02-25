from sqlalchemy import Column, Integer, String, Enum, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
import enum

Base = declarative_base()

class UserRole(enum.Enum):
    USER = "USER"
    ADMIN = "ADMIN"

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    clerkId = Column(String, unique=True, nullable=False) 
    first_name = Column(String, nullable=False)
    last_name = Column(String, nullable=False)
    email = Column(String, unique=True, nullable=False)
    phone_number = Column(String, unique=True, nullable=False)
    role = Column(Enum(UserRole), default=UserRole.USER, nullable=False)

    details = relationship("UserDetails", back_populates="user", uselist=False, cascade="all, delete-orphan")


class UserDetails(Base):
    __tablename__ = "user_details"

    id = Column(Integer, primary_key=True, index=True)
    clerkId = Column(String, ForeignKey("users.clerkId"), unique=True) 
    user = relationship("User", back_populates="details")
    
    address = Column(String, nullable=True)
    city = Column(String, nullable=True)
    state = Column(String, nullable=True)
    country = Column(String, nullable=True)
    pin_code = Column(String, nullable=True)
