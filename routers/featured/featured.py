from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import selectinload
from sqlalchemy import func, distinct
from typing import List, Optional
from models import (
    Product, BestSelling, OnSale, Trending, NewArrivals, ShopByNeed, Banner
)
from routers.featured.schemas import (
    ProductIdList, ShopByNeedCreate, ShopByNeedUpdate, ShopByNeedResponse,
    ShopByNeedBulkCreate, FeaturedProductResponse, BestSellingListResponse,
    OnSaleListResponse, TrendingListResponse, NewArrivalsListResponse,
    ShopByNeedListResponse, NeedsListResponse, NeedResponse,
    BannerCreate, BannerResponse, BannerListResponse, BannerUpdate
)
from config import get_db
from sqlalchemy.exc import IntegrityError
from sqlalchemy import and_
from utils.aws import upload_base64_image_to_s3

featured_router = APIRouter()

# Utility functions for product verification and response building, to be used in every featured route
async def verify_products_exist(db: AsyncSession, product_ids: List[str]):
    """Verify that all product IDs exist and return list of missing IDs."""
    if not product_ids:
        return []
        
    result = await db.execute(
        select(Product.product_id)
        .where(Product.product_id.in_(product_ids))
    )
    existing_ids = {p[0] for p in result.all()}
    missing_ids = set(product_ids) - existing_ids
    return list(missing_ids)

async def build_product_responses(db: AsyncSession, featured_products, include_category=False):
    """Build full product response objects with product details."""
    if not featured_products:
        return []
        
    product_ids = [fp.product_id for fp in featured_products]
    query = select(Product).where(Product.product_id.in_(product_ids))
    
    if include_category:
        query = query.options(selectinload(Product.category))
        
    products_result = await db.execute(query)
    products = {p.product_id: p for p in products_result.scalars().all()}
    
    responses = []
    for fp in featured_products:
        product = products.get(fp.product_id)
        if product:
            response = FeaturedProductResponse(
                id=fp.id,
                product_id=fp.product_id,
                created_at=fp.created_at,
                name=product.name,
                price=product.price,
                description=product.description,
                main_image_url=product.main_image_url,
                average_rating=product.average_rating,
                category_name=product.category.name if include_category and product.category else None
            )
            responses.append(response)
            
    return responses

# ---------------------- BestSelling Routes ----------------------

@featured_router.post("/admin/bestselling", status_code=status.HTTP_201_CREATED)
async def add_bestselling(product_ids: ProductIdList, db: AsyncSession = Depends(get_db)):
    """Add products to bestselling section."""
    # Verify all products exist
    missing_ids = await verify_products_exist(db, product_ids.product_ids)
    if missing_ids:
        raise HTTPException(
            status_code=400,
            detail=f"Products with IDs {missing_ids} do not exist"
        )
    
    # Create bestselling entries
    added_count = 0
    for product_id in product_ids.product_ids:
        try:
            bestselling = BestSelling(product_id=product_id)
            db.add(bestselling)
            await db.flush()
            added_count += 1
        except IntegrityError:
            await db.rollback()  # Product already in bestselling
            continue
    
    await db.commit()
    return {"message": f"Added {added_count} products to bestselling successfully"}

@featured_router.get("/bestselling", response_model=BestSellingListResponse)
async def get_bestselling(db: AsyncSession = Depends(get_db)):
    """Get all bestselling products with details."""
    # Get total count
    total_result = await db.execute(select(func.count(BestSelling.id)))
    total = total_result.scalar()
    
    # Get bestselling products
    result = await db.execute(select(BestSelling).order_by(BestSelling.created_at.desc()))
    bestselling = result.scalars().all()
    
    # Build response with product details
    products = await build_product_responses(db, bestselling, include_category=True)
    
    return {"total": total, "products": products}

@featured_router.delete("/admin/bestselling/{product_id}", status_code=status.HTTP_204_NO_CONTENT)
async def remove_bestselling(product_id: str, db: AsyncSession = Depends(get_db)):
    """Remove a product from bestselling section."""
    result = await db.execute(
        select(BestSelling).filter(BestSelling.product_id == product_id)
    )
    bestselling = result.scalars().first()
    
    if not bestselling:
        raise HTTPException(status_code=404, detail="Product not found in bestselling")
    
    await db.delete(bestselling)
    await db.commit()
    return

# ---------------------- OnSale Routes ----------------------

@featured_router.post("/admin/onsale", status_code=status.HTTP_201_CREATED)
async def add_onsale(product_ids: ProductIdList, db: AsyncSession = Depends(get_db)):
    """Add products to on-sale section."""
    # Verify all products exist
    missing_ids = await verify_products_exist(db, product_ids.product_ids)
    if missing_ids:
        raise HTTPException(
            status_code=400,
            detail=f"Products with IDs {missing_ids} do not exist"
        )
    
    # Create on-sale entries
    added_count = 0
    for product_id in product_ids.product_ids:
        try:
            onsale = OnSale(product_id=product_id)
            db.add(onsale)
            await db.flush()
            added_count += 1
        except IntegrityError:
            await db.rollback()  # Product already in on-sale
            continue
    
    await db.commit()
    return {"message": f"Added {added_count} products to on-sale successfully"}

@featured_router.get("/onsale", response_model=OnSaleListResponse)
async def get_onsale(db: AsyncSession = Depends(get_db)):
    """Get all on-sale products with details."""
    # Get total count
    total_result = await db.execute(select(func.count(OnSale.id)))
    total = total_result.scalar()
    
    # Get on-sale products
    result = await db.execute(select(OnSale).order_by(OnSale.created_at.desc()))
    onsale = result.scalars().all()
    
    # Build response with product details
    products = await build_product_responses(db, onsale, include_category=True)
    
    return {"total": total, "products": products}

@featured_router.delete("/admin/onsale/{product_id}", status_code=status.HTTP_204_NO_CONTENT)
async def remove_onsale(product_id: str, db: AsyncSession = Depends(get_db)):
    """Remove a product from on-sale section."""
    result = await db.execute(
        select(OnSale).filter(OnSale.product_id == product_id)
    )
    onsale = result.scalars().first()
    
    if not onsale:
        raise HTTPException(status_code=404, detail="Product not found in on-sale")
    
    await db.delete(onsale)
    await db.commit()
    return

# ---------------------- Trending Routes ----------------------

@featured_router.post("/admin/trending", status_code=status.HTTP_201_CREATED)
async def add_trending(product_ids: ProductIdList, db: AsyncSession = Depends(get_db)):
    """Add products to trending section."""
    # Verify all products exist
    missing_ids = await verify_products_exist(db, product_ids.product_ids)
    if missing_ids:
        raise HTTPException(
            status_code=400,
            detail=f"Products with IDs {missing_ids} do not exist"
        )
    
    # Create trending entries
    added_count = 0
    for product_id in product_ids.product_ids:
        try:
            trending = Trending(product_id=product_id)
            db.add(trending)
            await db.flush()
            added_count += 1
        except IntegrityError:
            await db.rollback()  # Product already in trending
            continue
    
    await db.commit()
    return {"message": f"Added {added_count} products to trending successfully"}

@featured_router.get("/trending", response_model=TrendingListResponse)
async def get_trending(db: AsyncSession = Depends(get_db)):
    """Get all trending products with details."""
    # Get total count
    total_result = await db.execute(select(func.count(Trending.id)))
    total = total_result.scalar()
    
    # Get trending products
    result = await db.execute(select(Trending).order_by(Trending.created_at.desc()))
    trending = result.scalars().all()
    
    # Build response with product details
    products = await build_product_responses(db, trending, include_category=True)
    
    return {"total": total, "products": products}

@featured_router.delete("/admin/trending/{product_id}", status_code=status.HTTP_204_NO_CONTENT)
async def remove_trending(product_id: str, db: AsyncSession = Depends(get_db)):
    """Remove a product from trending section."""
    result = await db.execute(
        select(Trending).filter(Trending.product_id == product_id)
    )
    trending = result.scalars().first()
    
    if not trending:
        raise HTTPException(status_code=404, detail="Product not found in trending")
    
    await db.delete(trending)
    await db.commit()
    return

# ---------------------- NewArrivals Routes ----------------------

@featured_router.post("/admin/newarrivals", status_code=status.HTTP_201_CREATED)
async def add_newarrivals(product_ids: ProductIdList, db: AsyncSession = Depends(get_db)):
    """Add products to new arrivals section."""
    # Verify all products exist
    missing_ids = await verify_products_exist(db, product_ids.product_ids)
    if missing_ids:
        raise HTTPException(
            status_code=400,
            detail=f"Products with IDs {missing_ids} do not exist"
        )
    
    # Create new arrivals entries
    added_count = 0
    for product_id in product_ids.product_ids:
        try:
            newarrival = NewArrivals(product_id=product_id)
            db.add(newarrival)
            await db.flush()
            added_count += 1
        except IntegrityError:
            await db.rollback()  # Product already in new arrivals
            continue
    
    await db.commit()
    return {"message": f"Added {added_count} products to new arrivals successfully"}

@featured_router.get("/newarrivals", response_model=NewArrivalsListResponse)
async def get_newarrivals(db: AsyncSession = Depends(get_db)):
    """Get all new arrivals products with details."""
    # Get total count
    total_result = await db.execute(select(func.count(NewArrivals.id)))
    total = total_result.scalar()
    
    # Get new arrivals products
    result = await db.execute(select(NewArrivals).order_by(NewArrivals.created_at.desc()))
    newarrivals = result.scalars().all()
    
    # Build response with product details
    products = await build_product_responses(db, newarrivals, include_category=True)
    
    return {"total": total, "products": products}

@featured_router.delete("/admin/newarrivals/{product_id}", status_code=status.HTTP_204_NO_CONTENT)
async def remove_newarrivals(product_id: str, db: AsyncSession = Depends(get_db)):
    """Remove a product from new arrivals section."""
    result = await db.execute(
        select(NewArrivals).filter(NewArrivals.product_id == product_id)
    )
    newarrival = result.scalars().first()
    
    if not newarrival:
        raise HTTPException(status_code=404, detail="Product not found in new arrivals")
    
    await db.delete(newarrival)
    await db.commit()
    return

# ---------------------- ShopByNeed Routes ----------------------

@featured_router.post("/admin/shopbyneed", status_code=status.HTTP_201_CREATED)
async def add_shopbyneed(items: ShopByNeedBulkCreate, db: AsyncSession = Depends(get_db)):
    """Add multiple products to shop by need section with the same need."""
    # Verify all products exist
    missing_ids = await verify_products_exist(db, items.product_ids)
    if missing_ids:
        raise HTTPException(
            status_code=400,
            detail=f"Products with IDs {missing_ids} do not exist"
        )
    
    # Create shop by need entries
    added_count = 0
    for product_id in items.product_ids:
        try:
            shopbyneed = ShopByNeed(product_id=product_id, need=items.need)
            db.add(shopbyneed)
            await db.flush()
            added_count += 1
        except IntegrityError:
            await db.rollback()  # Product already exists for this need
            continue
    
    await db.commit()
    return {"message": f"Added {added_count} products to shop by need '{items.need}' successfully"}

@featured_router.get("/shopbyneed", response_model=NeedsListResponse)
async def get_needs(db: AsyncSession = Depends(get_db)):
    """Get list of all available needs with counts."""
    result = await db.execute(
        select(ShopByNeed.need, func.count(ShopByNeed.id).label("count"))
        .group_by(ShopByNeed.need)
        .order_by(func.count(ShopByNeed.id).desc())
    )
    needs = result.all()
    
    need_responses = [
        NeedResponse(need=need, count=count) for need, count in needs
    ]
    
    return {"total": len(need_responses), "needs": need_responses}

@featured_router.get("/shopbyneed/{need}", response_model=ShopByNeedListResponse)
async def get_shopbyneed_by_need(need: str, db: AsyncSession = Depends(get_db)):
    """Get all products for a specific need."""
    # Get total count
    total_result = await db.execute(
        select(func.count(ShopByNeed.id)).filter(ShopByNeed.need == need)
    )
    total = total_result.scalar()
    
    # Get shop by need products
    result = await db.execute(
        select(ShopByNeed)
        .filter(ShopByNeed.need == need)
        .order_by(ShopByNeed.created_at.desc())
    )
    shopbyneed = result.scalars().all()
    
    # Build response with product details
    products = await build_product_responses(db, shopbyneed, include_category=True)
    
    return {"total": total, "products": products}

@featured_router.delete("/admin/shopbyneed", status_code=status.HTTP_204_NO_CONTENT)
async def remove_shopbyneed(product_id: str, need: str, db: AsyncSession = Depends(get_db)):
    """Remove a product from shop by need for a specific need."""
    result = await db.execute(
        select(ShopByNeed).filter(
            and_(
                ShopByNeed.product_id == product_id,
                ShopByNeed.need == need
            )
        )
    )
    shopbyneed = result.scalars().first()
    
    if not shopbyneed:
        raise HTTPException(
            status_code=404, 
            detail=f"Product not found in shop by need '{need}'"
        )
    
    await db.delete(shopbyneed)
    await db.commit()
    return

# ---------------------- Banner Routes ----------------------

@featured_router.post("/admin/banners", response_model=BannerResponse, status_code=status.HTTP_201_CREATED)
async def add_banner(banner: BannerCreate, db: AsyncSession = Depends(get_db)):
    """Add a new banner to the homepage."""
    try:
        # Upload the banner image to S3
        image_url = await upload_base64_image_to_s3(
            banner.image, 
            file_extension=banner.image_extension,
            folder="banners"  # Store in the banners folder
        )
        
        # Create new banner entry
        new_banner = Banner(
            image_url=image_url,
            display_order=banner.display_order,
            active=banner.active
        )
        
        db.add(new_banner)
        await db.commit()
        await db.refresh(new_banner)
        
        return new_banner
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to create banner: {str(e)}"
        )

@featured_router.get("/banners", response_model=BannerListResponse)
async def get_banners(active_only: Optional[bool] = False, db: AsyncSession = Depends(get_db)):
    """Get all banners or only active banners if active_only is True."""
    try:
        # Build query based on active_only parameter
        query = select(Banner)
        if active_only:
            query = query.filter(Banner.active == 1)
            
        query = query.order_by(Banner.display_order)
            
        # Get total count
        total_result = await db.execute(select(func.count()).select_from(query.subquery()))
        total = total_result.scalar()
        
        # Get banners
        result = await db.execute(query)
        banners = result.scalars().all()
        
        return {"total": total, "banners": banners}
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to retrieve banners: {str(e)}"
        )

@featured_router.put("/admin/banners/{banner_id}", response_model=BannerResponse)
async def update_banner(banner_id: int, banner: BannerUpdate, db: AsyncSession = Depends(get_db)):
    """Update banner display order or active status."""
    try:
        # Check if banner exists
        result = await db.execute(select(Banner).filter(Banner.id == banner_id))
        db_banner = result.scalars().first()
        if not db_banner:
            raise HTTPException(status_code=404, detail="Banner not found")
        
        # Update specified fields
        update_data = banner.dict(exclude_unset=True)
        for key, value in update_data.items():
            setattr(db_banner, key, value)
            
        await db.commit()
        await db.refresh(db_banner)
        
        return db_banner
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to update banner: {str(e)}"
        )

@featured_router.delete("/admin/banners/{banner_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_banner(banner_id: int, db: AsyncSession = Depends(get_db)):
    """Delete a banner."""
    try:
        # Check if banner exists
        result = await db.execute(select(Banner).filter(Banner.id == banner_id))
        db_banner = result.scalars().first()
        if not db_banner:
            raise HTTPException(status_code=404, detail="Banner not found")
        
        # Delete the banner
        await db.delete(db_banner)
        await db.commit()
        
        return
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to delete banner: {str(e)}"
        )

