from fastapi import APIRouter, Depends, HTTPException, status, File, UploadFile
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from typing import List, Optional
from models import Product, Category, ProductStatus
from routers.products.schemas import ProductCreateForm, ProductResponse, ProductStatusEnum, ProductUpdate, ProductCreateJSON
from config import get_db
from utils.aws import upload_image_to_s3

products_router = APIRouter()

# Admin-only: Create a new product.
@products_router.post("/admin/products", response_model=ProductResponse, status_code=status.HTTP_201_CREATED)
async def create_product_json(
    product: ProductCreateJSON,
    db: AsyncSession = Depends(get_db)
):
    # ✅ Check if category exists
    result = await db.execute(select(Category).filter(Category.id == product.category_id))
    category = result.scalars().first()
    if not category:
        raise HTTPException(status_code=404, detail="Category not found")
    
    # ✅ (Optional) Validate customization options against category.allowed_customizations
    if product.customization_options:
        if category.allowed_customizations:
            allowed_keys = set(category.allowed_customizations.keys())
            provided_keys = set(product.customization_options.keys())
            if not provided_keys.issubset(allowed_keys):
                invalid_keys = provided_keys - allowed_keys
                raise HTTPException(
                    status_code=400,
                    detail=f"Customization option keys {invalid_keys} are not allowed for category {category.name}"
                )
            for key in provided_keys:
                allowed_values = set(category.allowed_customizations.get(key, []))
                provided_values = set(product.customization_options.get(key, []))
                if not provided_values.issubset(allowed_values):
                    invalid_values = provided_values - allowed_values
                    raise HTTPException(
                        status_code=400,
                        detail=f"Values {invalid_values} for customization '{key}' are not allowed for category {category.name}"
                    )
        else:
            raise HTTPException(
                status_code=400,
                detail=f"Category {category.name} does not allow customization options."
            )

    # ✅ Generate unique product ID
    abbreviation = category.name.upper()[:3]
    result = await db.execute(select(Product).filter(Product.category_id == product.category_id))
    count = len(result.scalars().all())
    new_product_id = f"PRNTDT{abbreviation}{count + 1:03d}"

    # ✅ Create new product instance (set image URLs as empty)
    new_product = Product(
        product_id=new_product_id,
        main_image_url="",  # Initially empty; will be updated in the next route.
        side_images_url=[],  # Initially empty.
        name=product.name,
        price=product.price,
        category_id=product.category_id,
        description=product.description,
        customization_options=product.customization_options,
        status=ProductStatus(product.status.value)
    )

    db.add(new_product)
    await db.commit()
    await db.refresh(new_product)
    return new_product

# Admin-only: Upload product images.
@products_router.post("/admin/products/{product_id}/images", response_model=ProductResponse)
async def upload_product_images(
    product_id: str,
    main_image: Optional[UploadFile] = File(None),
    side_images: Optional[List[UploadFile]] = File(None),
    db: AsyncSession = Depends(get_db)
):
    # ✅ Fetch the product by its product_id
    result = await db.execute(select(Product).filter(Product.product_id == product_id))
    product = result.scalars().first()
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")

    # ✅ Upload main image if provided
    if main_image:
        main_image_url = upload_image_to_s3(main_image)
        product.main_image_url = main_image_url

    # ✅ Ensure side_images is a list
    if side_images is None:
        side_images = []
    else:
        # Sometimes an empty value might be passed as an empty string;
        # filter out any non-UploadFile objects.
        side_images = [img for img in side_images if isinstance(img, UploadFile)]

    # ✅ Upload side images if provided
    if side_images:
        side_images_urls = [upload_image_to_s3(img) for img in side_images]
        product.side_images_url = side_images_urls

    await db.commit()
    await db.refresh(product)
    return product



# Public: Retrieve all products.
@products_router.get("/products", response_model=List[ProductResponse])
async def get_products(skip: int = 0, limit: int = 10, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Product).offset(skip).limit(limit))
    products = result.scalars().all()
    return products

# Public: Retrieve products with filtering and sorting options.
@products_router.get("/products/filter", response_model=List[ProductResponse])
async def filter_products(
    category_id: Optional[int] = None,
    min_price: Optional[float] = None,
    max_price: Optional[float] = None,
    min_rating: Optional[float] = None,
    sort_by: Optional[str] = None,
    skip: int = 0,
    limit: int = 10,
    db: AsyncSession = Depends(get_db)
):
    query = select(Product)
    
    if category_id is not None:
        query = query.filter(Product.category_id == category_id)
    if min_price is not None:
        query = query.filter(Product.price >= min_price)
    if max_price is not None:
        query = query.filter(Product.price <= max_price)
    if min_rating is not None:
        query = query.filter(Product.average_rating >= min_rating)
    
    if sort_by:
        if sort_by == "price_asc":
            query = query.order_by(Product.price.asc())
        elif sort_by == "price_desc":
            query = query.order_by(Product.price.desc())
        elif sort_by == "rating_asc":
            query = query.order_by(Product.average_rating.asc())
        elif sort_by == "rating_desc":
            query = query.order_by(Product.average_rating.desc())
    
    query = query.offset(skip).limit(limit)
    result = await db.execute(query)
    products = result.scalars().all()
    return products

# Public: Retrieve a single product by its custom product_id.
@products_router.get("/products/{product_id}", response_model=ProductResponse)
async def get_product(product_id: str, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Product).filter(Product.product_id == product_id))
    product = result.scalars().first()
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    return product


# Admin-only: Update a product.
@products_router.put("/admin/products/{product_id}", response_model=ProductResponse)
async def update_product(
    product_id: str, 
    product: ProductUpdate,  # ✅ Use proper Pydantic model here
    db: AsyncSession = Depends(get_db)
):
    # ✅ Check if product exists
    result = await db.execute(select(Product).filter(Product.product_id == product_id))
    db_product = result.scalars().first()
    if not db_product:
        raise HTTPException(status_code=404, detail="Product not found")

    update_data = product.dict(exclude_unset=True)

    # ✅ Handle status conversion if provided
    if "status" in update_data and update_data["status"]:
        update_data["status"] = ProductStatus(update_data["status"].value)

    # ✅ Update fields dynamically
    for key, value in update_data.items():
        setattr(db_product, key, value)

    # ✅ Commit changes to DB
    await db.commit()
    await db.refresh(db_product)
    return db_product

# Admin-only: Delete a product.
@products_router.delete("/admin/products/{product_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_product(product_id: str, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Product).filter(Product.product_id == product_id))
    db_product = result.scalars().first()
    if not db_product:
        raise HTTPException(status_code=404, detail="Product not found")
    await db.delete(db_product)
    await db.commit()
    return
