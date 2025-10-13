# routes/products.py
from fastapi import APIRouter, HTTPException, Query, Depends
from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional
from decimal import Decimal
from dynamo.client import dynamodb, PRODUCT_TABLE
from boto3.dynamodb.conditions import Attr, Key
from routes.auth import get_current_user

router = APIRouter()

# Pydantic models
class Product(BaseModel):
    item_id: str
    name: str
    price: float
    tags: List[str]
    in_stock: bool
    promo: bool
    category: Optional[str] = None
    description: Optional[str] = None
    image_url: Optional[str] = None

class ProductResponse(BaseModel):
    success: bool
    message: str
    products: List[Product]
    total_count: int
    categories: List[str]

class CategoryResponse(BaseModel):
    success: bool
    message: str
    categories: List[Dict[str, Any]]

@router.get("/products", response_model=ProductResponse)
async def get_products(
    category: Optional[str] = Query(None, description="Filter by category"),
    search: Optional[str] = Query(None, description="Search by product name"),
    diet: Optional[str] = Query(None, description="Filter by dietary preference"),
    min_price: Optional[float] = Query(None, description="Minimum price"),
    max_price: Optional[float] = Query(None, description="Maximum price"),
    in_stock: Optional[bool] = Query(None, description="Filter by stock availability"),
    limit: int = Query(50, description="Number of products to return"),
    offset: int = Query(0, description="Number of products to skip")
):
    """Get products with filtering and pagination"""
    try:
        table = dynamodb.Table(PRODUCT_TABLE)
        
        # Build filter expression
        filter_expression = None
        
        if category:
            filter_expression = Attr("category").eq(category.lower())
        
        if search:
            search_filter = Attr("name").contains(search.lower())
            filter_expression = search_filter if filter_expression is None else filter_expression & search_filter
        
        if diet:
            diet_filter = Attr("tags").contains(diet.lower())
            filter_expression = diet_filter if filter_expression is None else filter_expression & diet_filter
        
        if min_price is not None:
            price_filter = Attr("price").gte(min_price)
            filter_expression = price_filter if filter_expression is None else filter_expression & price_filter
        
        if max_price is not None:
            price_filter = Attr("price").lte(max_price)
            filter_expression = price_filter if filter_expression is None else filter_expression & price_filter
        
        if in_stock is not None:
            stock_filter = Attr("in_stock").eq(in_stock)
            filter_expression = stock_filter if filter_expression is None else filter_expression & stock_filter
        
        # Scan with filters - get all products first
        scan_kwargs = {}
        if filter_expression:
            scan_kwargs["FilterExpression"] = filter_expression
        
        response = table.scan(**scan_kwargs)
        products = response.get("Items", [])
        
        # Handle pagination for DynamoDB scan
        while 'LastEvaluatedKey' in response:
            scan_kwargs["ExclusiveStartKey"] = response['LastEvaluatedKey']
            response = table.scan(**scan_kwargs)
            products.extend(response.get("Items", []))
        
        # Apply offset and limit
        products = products[offset:offset + limit]
        
        # Convert to Product objects
        product_list = []
        for product in products:
            product_obj = Product(
                item_id=product.get("item_id"),
                name=product.get("name"),
                price=float(product.get("price", 0)),
                tags=product.get("tags", []),
                in_stock=product.get("in_stock", True),
                promo=product.get("promo", False),
                category=product.get("category"),
                description=product.get("description"),
                image_url=product.get("image_url")
            )
            product_list.append(product_obj)
        
        # Get all categories for UI
        all_products = table.scan()
        all_categories = set()
        for product in all_products.get("Items", []):
            if product.get("category"):
                all_categories.add(product.get("category"))
        
        # Get total count of all products (before pagination)
        total_products = table.scan()
        total_count = len(total_products.get("Items", []))
        
        # Handle pagination for total count
        while 'LastEvaluatedKey' in total_products:
            total_products = table.scan(ExclusiveStartKey=total_products['LastEvaluatedKey'])
            total_count += len(total_products.get("Items", []))
        
        return ProductResponse(
            success=True,
            message=f"Found {len(product_list)} products",
            products=product_list,
            total_count=total_count,
            categories=list(all_categories)
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error retrieving products: {str(e)}")

@router.get("/products/categories", response_model=CategoryResponse)
async def get_product_categories():
    """Get all available product categories"""
    try:
        table = dynamodb.Table(PRODUCT_TABLE)
        
        # Get all products to extract categories
        response = table.scan()
        products = response.get("Items", [])
        
        # Extract categories and count products
        category_counts = {}
        for product in products:
            category = product.get("category", "Uncategorized")
            if category not in category_counts:
                category_counts[category] = 0
            category_counts[category] += 1
        
        # Convert to list format
        categories = []
        for category, count in category_counts.items():
            categories.append({
                "name": category,
                "product_count": count,
                "display_name": category.title()
            })
        
        # Sort by product count
        categories.sort(key=lambda x: x["product_count"], reverse=True)
        
        return CategoryResponse(
            success=True,
            message=f"Found {len(categories)} categories",
            categories=categories
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error retrieving categories: {str(e)}")

@router.get("/products/{item_id}", response_model=Product)
async def get_product(item_id: str):
    """Get specific product by ID"""
    try:
        table = dynamodb.Table(PRODUCT_TABLE)
        
        response = table.get_item(Key={"item_id": item_id})
        product = response.get("Item")
        
        if not product:
            raise HTTPException(status_code=404, detail="Product not found")
        
        return Product(
            item_id=product.get("item_id"),
            name=product.get("name"),
            price=float(product.get("price", 0)),
            tags=product.get("tags", []),
            in_stock=product.get("in_stock", True),
            promo=product.get("promo", False),
            category=product.get("category"),
            description=product.get("description"),
            image_url=product.get("image_url")
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error retrieving product: {str(e)}")

@router.get("/products/search/suggestions")
async def get_search_suggestions(query: str = Query(..., description="Search query")):
    """Get search suggestions based on query"""
    try:
        table = dynamodb.Table(PRODUCT_TABLE)
        
        # Search for products containing the query
        response = table.scan(
            FilterExpression=Attr("name").contains(query.lower()),
            Limit=10
        )
        
        products = response.get("Items", [])
        
        # Extract suggestions
        suggestions = []
        for product in products:
            suggestions.append({
                "item_id": product.get("item_id"),
                "name": product.get("name"),
                "category": product.get("category"),
                "price": float(product.get("price", 0))
            })
        
        return {
            "success": True,
            "query": query,
            "suggestions": suggestions,
            "count": len(suggestions)
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting suggestions: {str(e)}")

@router.get("/products/featured")
async def get_featured_products(limit: int = Query(10, description="Number of featured products")):
    """Get featured products (promotional or popular items)"""
    try:
        table = dynamodb.Table(PRODUCT_TABLE)
        
        # Get products with promotions
        response = table.scan(
            FilterExpression=Attr("promo").eq(True),
            Limit=limit
        )
        
        products = response.get("Items", [])
        
        # Convert to Product objects
        product_list = []
        for product in products:
            product_obj = Product(
                item_id=product.get("item_id"),
                name=product.get("name"),
                price=float(product.get("price", 0)),
                tags=product.get("tags", []),
                in_stock=product.get("in_stock", True),
                promo=product.get("promo", False),
                category=product.get("category"),
                description=product.get("description"),
                image_url=product.get("image_url")
            )
            product_list.append(product_obj)
        
        return {
            "success": True,
            "message": f"Found {len(product_list)} featured products",
            "products": [p.dict() for p in product_list],
            "count": len(product_list)
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error retrieving featured products: {str(e)}")

@router.get("/products/dietary/{diet}")
async def get_products_by_diet(diet: str, limit: int = Query(20, description="Number of products")):
    """Get products filtered by dietary preference"""
    try:
        table = dynamodb.Table(PRODUCT_TABLE)
        
        # Get products matching dietary preference
        response = table.scan(
            FilterExpression=Attr("tags").contains(diet.lower()),
            Limit=limit
        )
        
        products = response.get("Items", [])
        
        # Convert to Product objects
        product_list = []
        for product in products:
            product_obj = Product(
                item_id=product.get("item_id"),
                name=product.get("name"),
                price=float(product.get("price", 0)),
                tags=product.get("tags", []),
                in_stock=product.get("in_stock", True),
                promo=product.get("promo", False),
                category=product.get("category"),
                description=product.get("description"),
                image_url=product.get("image_url")
            )
            product_list.append(product_obj)
        
        return {
            "success": True,
            "message": f"Found {len(product_list)} {diet} products",
            "diet": diet,
            "products": [p.dict() for p in product_list],
            "count": len(product_list)
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error retrieving {diet} products: {str(e)}") 