from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from routers.auth.auth import auth_router
from routers.user.user import users_router
from routers.products.products import products_router
from routers.products.categories import categories_router
from routers.products.reviews import reviews_router
from routers.orders.orders import orders_router
from mangum import Mangum  

app = FastAPI(
    root_path="/Prod",
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",  
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth_router, prefix="/auth", tags=["Authentication"])
app.include_router(users_router, prefix="/users", tags=["Users"])
app.include_router(products_router, tags=["Products"])
app.include_router(categories_router, tags=["Categories"])
app.include_router(reviews_router, tags=["Reviews"])
app.include_router(orders_router, tags=["Orders"])

@app.get("/")
def home():
    """This is the first and default route for the Print Doot Backend"""
    return {"message": "Hello World!"}

handler = Mangum(app)  
