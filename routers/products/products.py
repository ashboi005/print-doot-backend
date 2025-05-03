from fastapi import APIRouter, Depends, HTTPException, status, File, UploadFile
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from typing import List, Optional
from models import Product, Category, ProductStatus
from routers.products.schemas import ProductCreateForm, ProductResponse, ProductStatusEnum, ProductUpdate, ProductCreateJSON, ProductListResponse, ProductImageBase64
from sqlalchemy import func
from config import get_db
from utils.aws import upload_image_to_s3, upload_base64_image_to_s3
from sqlalchemy.orm import selectinload

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

    # ✅ Validate bulk_prices if provided - using Pydantic validation
    # No need for explicit validation as Pydantic handles it now through the BulkPriceItem model
    if product.bulk_prices:
        for bulk_price in product.bulk_prices:
            if bulk_price.quantity <= 0:
                raise HTTPException(
                    status_code=400,
                    detail=f"Quantity must be positive (got {bulk_price.quantity})"
                )
            if bulk_price.price < 0:
                raise HTTPException(
                    status_code=400,
                    detail=f"Price must be non-negative (got {bulk_price.price})"
                )

    # ✅ Use provided product_id or generate a unique one if not provided
    new_product_id = None
    if product.product_id:
        # Use admin-provided product_id
        new_product_id = product.product_id
        
        # Check if product_id already exists
        result = await db.execute(select(Product).filter(Product.product_id == new_product_id))
        existing_product = result.scalars().first()
        if existing_product:
            raise HTTPException(
                status_code=400,
                detail=f"Product ID '{new_product_id}' already exists. Please use a unique ID."
            )
    else:
        # Generate unique product ID if not provided
        abbreviation = category.name.upper()[:3]
        result = await db.execute(select(Product).filter(Product.category_id == product.category_id))
        count = len(result.scalars().all())
        new_product_id = f"PRNTDT{abbreviation}{count + 1:03d}"

    # ✅ Process dimensions if provided
    dimensions_dict = None
    if product.dimensions:
        dimensions_dict = product.dimensions.dict()

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
        bulk_prices=[bp.dict() for bp in product.bulk_prices] if product.bulk_prices else None,
        dimensions=dimensions_dict,
        weight=product.weight,
        material=product.material,
        status=ProductStatus(product.status.value)
    )

    db.add(new_product)
    await db.commit()
    await db.refresh(new_product)
    return new_product

# Admin-only: Upload product images using base64 encoded images
# Supports multiple image formats: jpg, jpeg, png, gif, webp, etc.
@products_router.post("/admin/products/{product_id}/images", response_model=ProductResponse)
async def upload_product_images(
    product_id: str,
    images: ProductImageBase64,
    db: AsyncSession = Depends(get_db)
):
    # ✅ Fetch the product by its product_id
    result = await db.execute(select(Product).filter(Product.product_id == product_id))
    product = result.scalars().first()
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")

    # ✅ Upload main image if provided
    if images.main_image:
        main_image_url = await upload_base64_image_to_s3(
            images.main_image, 
            file_extension=images.main_image_extension
        )
        product.main_image_url = main_image_url

    # ✅ Upload side images if provided
    if images.side_images:
        # Make sure we have extensions for each side image
        extensions = images.side_images_extensions or ['jpg'] * len(images.side_images)
        
        # Make sure we have enough extensions
        if len(extensions) < len(images.side_images):
            extensions.extend(['jpg'] * (len(images.side_images) - len(extensions)))
            
        # Upload each side image
        side_images_urls = []
        for i, img in enumerate(images.side_images):
            url = await upload_base64_image_to_s3(img, file_extension=extensions[i])
            side_images_urls.append(url)
            
        product.side_images_url = side_images_urls

    await db.commit()
    await db.refresh(product)
    return product


# Public: Retrieve all products.
@products_router.get("/products", response_model=ProductListResponse)
async def get_products(skip: int = 0, limit: int = 10, db: AsyncSession = Depends(get_db)):
    # Get total count
    total_result = await db.execute(select(func.count(Product.id)))
    total = total_result.scalar()
    
    # Get paginated products
    query = select(Product).options(selectinload(Product.category)).offset(skip).limit(limit)
    result = await db.execute(query)
    products = result.scalars().all()
    
    return {"total": total, "products": products}

@products_router.get("/products/filter", response_model=ProductListResponse)
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
    # Build base query
    query = select(Product).options(selectinload(Product.category))
    
    # Apply filters
    if category_id is not None:
        query = query.filter(Product.category_id == category_id)
    if min_price is not None:
        query = query.filter(Product.price >= min_price)
    if max_price is not None:
        query = query.filter(Product.price <= max_price)
    if min_rating is not None:
        query = query.filter(Product.average_rating >= min_rating)
    
    # Get total count with filters applied
    total_result = await db.execute(select(func.count()).select_from(query.subquery()))
    total = total_result.scalar()
    
    # Apply sorting
    if sort_by:
        if sort_by == "price_asc":
            query = query.order_by(Product.price.asc())
        elif sort_by == "price_desc":
            query = query.order_by(Product.price.desc())
        elif sort_by == "rating_asc":
            query = query.order_by(Product.average_rating.asc())
        elif sort_by == "rating_desc":
            query = query.order_by(Product.average_rating.desc())
    
    # Apply pagination
    query = query.offset(skip).limit(limit)
    
    # Execute final query
    result = await db.execute(query)
    products = result.scalars().all()
    
    return {"total": total, "products": products}


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
        
    # ✅ Handle bulk_prices conversion if provided
    if "bulk_prices" in update_data and update_data["bulk_prices"] is not None:
        update_data["bulk_prices"] = [bp.dict() for bp in update_data["bulk_prices"]]
        
    # ✅ Handle dimensions conversion if provided
    if "dimensions" in update_data and update_data["dimensions"] is not None:
        update_data["dimensions"] = update_data["dimensions"].dict()

    # ✅ Update fields dynamically
    for key, value in update_data.items():
        setattr(db_product, key, value)

    # ✅ Commit changes to DB
    await db.commit()
    await db.refresh(db_product)
    return db_product

# Admin-only: Update a product image.
@products_router.put("/admin/products/{product_id}/images", response_model=ProductResponse)
async def update_product_image(
    product_id: str,
    image: ProductImageBase64,
    db: AsyncSession = Depends(get_db)
):
    # ✅ Check if product exists
    result = await db.execute(select(Product).filter(Product.product_id == product_id))
    product = result.scalars().first()
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    
    # ✅ Update main image if provided
    if image.main_image:
        main_image_url = await upload_base64_image_to_s3(
            image.main_image,
            file_extension=image.main_image_extension
        )   
        product.main_image_url = main_image_url

    # ✅ Update side images if provided
    if image.side_images:
        # Make sure we have extensions for each side image
        extensions = image.side_images_extensions or ['jpg'] * len(image.side_images)   
        
        # Make sure we have enough extensions
        if len(extensions) < len(image.side_images):
            extensions.extend(['jpg'] * (len(image.side_images) - len(extensions)))
            
        # Upload each side image
        side_images_urls = []
        for i, img in enumerate(image.side_images):
            url = await upload_base64_image_to_s3(img, file_extension=extensions[i])
            side_images_urls.append(url)
            
        product.side_images_url = side_images_urls
        
    await db.commit()
    await db.refresh(product)
    return product


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
