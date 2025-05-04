from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from routers.auth.auth import auth_router
from routers.user.user import users_router
from routers.products.products import products_router
from routers.products.categories import categories_router
from routers.products.reviews import reviews_router
from routers.products.coupons import coupons_router
from routers.orders.orders import orders_router
from routers.featured.featured import featured_router
from mangum import Mangum
from fastapi.responses import HTMLResponse
from fastapi import Request, HTTPException
import os

app = FastAPI(
    root_path="/Prod",
    docs_url="/apidocs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",  
    servers=[
        {"url": "https://oj5k6unyp3.execute-api.ap-south-1.amazonaws.com/Prod", "description": "Production Server"},
        {"url": "http://localhost:8000", "description": "Local Development Server"},
    ],
)
 
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/docs", include_in_schema=False)
async def api_documentation(request: Request):
    if os.getenv("ENVIRONMENT", "dev") == "dev":
        return HTMLResponse(
            """
<!doctype html>
<html lang="en">
  <head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1, shrink-to-fit=no">
    <title>PRINTDOOT DOCS</title>

    <script src="https://unpkg.com/@stoplight/elements/web-components.min.js"></script>
    <link rel="stylesheet" href="https://unpkg.com/@stoplight/elements/styles.min.css">
  </head>
  <body>

    <elements-api
      apiDescriptionUrl="Prod/openapi.json"
      router="hash"
      theme="dark"
    />

  </body>
</html>"""
        )
    else:
        raise HTTPException(status_code=404, detail="API Documentation not found")

@app.get("/printdoot", response_class=HTMLResponse)
def home():
  """This is the first and default route for the Print Doot Backend"""
  return """
  <html>
    <head>
      <title>Print Doot API</title>
      <style>
        body { font-family: Arial, sans-serif; margin: 40px; background-color: #B3D9FF; }
        h1 { color: #333; }
        ul { list-style-type: none; padding: 0; }
        li { margin: 10px 0; }
        a { color: #0066cc; text-decoration: none; }
        a:hover { text-decoration: underline; }
        hr { margin: 20px 0; }
        h2 { color: #555; }
      </style>
    </head>
    <body>
      <h1>Welcome to Print Doot API</h1>
      <hr>
      <ul>
        <li><a href="/docs">Spotlight API Documentation</a></li>
        <li><a href="/redoc">Redoc API Documentation</a></li>
        <li><a href="/apidocs">Swagger API Documentation</a></li>
        <li><a href="/openapi.json">OpenAPI Specification</a></li>
        <hr>
        <li><a href="https://pridoot.vercel.app">Print Doot Website</a></li>
        <li><a href="https://printdoot.vercel.app/admin">Print Doot Admin Panel</a></li>
        <hr>
        <h2>Website made and maintained by: <a href="https://heshmedia.in">Hesh Media</a></h2>
      </ul>
    </body>
  </html>
  """

app.include_router(auth_router, prefix="/auth", tags=["Authentication"])
app.include_router(users_router, prefix="/users", tags=["Users"])
app.include_router(products_router, tags=["Products"])
app.include_router(categories_router, tags=["Categories"])
app.include_router(reviews_router, tags=["Reviews"])
app.include_router(coupons_router, tags=["Coupons"])
app.include_router(featured_router, tags=["Featured"])
app.include_router(orders_router, tags=["Orders"])
    
handler = Mangum(app)
