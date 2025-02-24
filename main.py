from fastapi import FastAPI, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from config import get_db
from routers.auth.auth import auth_router

app = FastAPI()

app.include_router(auth_router, prefix="/auth", tags=["Authentication"])

@app.get("/")
def home():
    '''This is the first and default route for the Print Doot Backend'''
    return {"message": "Hello World!"}

