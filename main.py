from fastapi import FastAPI
from routers.auth.auth import auth_router
from routers.user.user import users_router

app = FastAPI()

app.include_router(auth_router, prefix="/auth", tags=["Authentication"])
app.include_router(users_router, prefix="/users", tags=["Users"])

@app.get("/")
def home():
    '''This is the first and default route for the Print Doot Backend'''
    return {"message": "Hello World!"}

