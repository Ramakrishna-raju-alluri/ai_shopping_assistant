from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel
from typing import List, Dict, Any, Optional
from boto3.dynamodb.conditions import Attr
from backend_bedrock.dynamo.client import dynamodb, PRODUCT_TABLE


router = APIRouter()


class Product(BaseModel):
    item_id: str
    name: str
    price: float
    tags: List[str]
    in_stock: bool
    promo: bool
    calories: Optional[int] = None
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
    category: Optional[str] = Query(None),
    search: Optional[str] = Query(None),
    diet: Optional[str] = Query(None),
    min_price: Optional[float] = Query(None),
    max_price: Optional[float] = Query(None),
    in_stock: Optional[bool] = Query(None),
    limit: int = Query(50),
    offset: int = Query(0),
):
    try:
        table = dynamodb.Table(PRODUCT_TABLE)
        filter_expression = None
        if category:
            filter_expression = Attr("category").eq(category.lower())
        if search:
            expr = Attr("name").contains(search.lower())
            filter_expression = expr if filter_expression is None else filter_expression & expr
        if diet:
            expr = Attr("tags").contains(diet.lower())
            filter_expression = expr if filter_expression is None else filter_expression & expr
        if min_price is not None:
            expr = Attr("price").gte(min_price)
            filter_expression = expr if filter_expression is None else filter_expression & expr
        if max_price is not None:
            expr = Attr("price").lte(max_price)
            filter_expression = expr if filter_expression is None else filter_expression & expr
        if in_stock is not None:
            expr = Attr("in_stock").eq(in_stock)
            filter_expression = expr if filter_expression is None else filter_expression & expr

        scan_kwargs = {}
        if filter_expression:
            scan_kwargs["FilterExpression"] = filter_expression
        response = table.scan(**scan_kwargs)
        products = response.get("Items", [])
        while "LastEvaluatedKey" in response:
            scan_kwargs["ExclusiveStartKey"] = response["LastEvaluatedKey"]
            response = table.scan(**scan_kwargs)
            products.extend(response.get("Items", []))

        products = products[offset : offset + limit]

        product_list: List[Product] = []
        for product in products:
            product_list.append(
                Product(
                    item_id=product.get("item_id"),
                    name=product.get("name"),
                    price=float(product.get("price", 0)),
                    tags=product.get("tags", []),
                    in_stock=product.get("in_stock", True),
                    promo=product.get("promo", False),
                    calories=int(product.get("calories", 0)),
                    category=product.get("category"),
                    description=product.get("description"),
                    image_url=product.get("image_url"),
                )
            )

        # categories and count
        all_scan = table.scan()
        all_items = all_scan.get("Items", [])
        all_categories = sorted(list({p.get("category") for p in all_items if p.get("category")}))
        total_count = len(all_items)
        while "LastEvaluatedKey" in all_scan:
            all_scan = table.scan(ExclusiveStartKey=all_scan["LastEvaluatedKey"])
            items = all_scan.get("Items", [])
            total_count += len(items)
            for p in items:
                if p.get("category"):
                    all_categories.append(p.get("category"))
        all_categories = sorted(list(set(all_categories)))

        return ProductResponse(
            success=True,
            message=f"Found {len(product_list)} products",
            products=product_list,
            total_count=total_count,
            categories=all_categories,
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error retrieving products: {str(e)}")


@router.get("/products/categories", response_model=CategoryResponse)
async def get_product_categories():
    try:
        table = dynamodb.Table(PRODUCT_TABLE)
        response = table.scan()
        products = response.get("Items", [])
        category_counts: Dict[str, int] = {}
        for product in products:
            category = product.get("category", "Uncategorized")
            category_counts[category] = category_counts.get(category, 0) + 1
        categories: List[Dict[str, Any]] = []
        for category, count in category_counts.items():
            categories.append({"name": category, "product_count": count, "display_name": category.title()})
        categories.sort(key=lambda x: x["product_count"], reverse=True)
        return CategoryResponse(success=True, message=f"Found {len(categories)} categories", categories=categories)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error retrieving categories: {str(e)}")


@router.get("/products/{item_id}", response_model=Product)
async def get_product(item_id: str):
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
            calories=int(product.get("calories", 0)),
            category=product.get("category"),
            description=product.get("description"),
            image_url=product.get("image_url"),
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error retrieving product: {str(e)}")


@router.get("/products/search/suggestions")
async def get_search_suggestions(query: str = Query(...)):
    try:
        table = dynamodb.Table(PRODUCT_TABLE)
        response = table.scan(FilterExpression=Attr("name").contains(query.lower()), Limit=10)
        products = response.get("Items", [])
        suggestions = []
        for product in products:
            suggestions.append({
                "item_id": product.get("item_id"),
                "name": product.get("name"),
                "category": product.get("category"),
                "price": float(product.get("price", 0)),
                "calories": int(product.get("calories", 0)),
            })
        return {"success": True, "query": query, "suggestions": suggestions, "count": len(suggestions)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting suggestions: {str(e)}")


@router.get("/products/featured")
async def get_featured_products(limit: int = Query(10)):
    try:
        table = dynamodb.Table(PRODUCT_TABLE)
        response = table.scan(FilterExpression=Attr("promo").eq(True), Limit=limit)
        products = response.get("Items", [])
        items = []
        for product in products:
            items.append({
                "item_id": product.get("item_id"),
                "name": product.get("name"),
                "price": float(product.get("price", 0)),
                "tags": product.get("tags", []),
                "in_stock": product.get("in_stock", True),
                "promo": product.get("promo", False),
                "calories": int(product.get("calories", 0)),
                "category": product.get("category"),
                "description": product.get("description"),
                "image_url": product.get("image_url"),
            })
        return {"success": True, "message": f"Found {len(items)} featured products", "products": items, "count": len(items)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error retrieving featured products: {str(e)}")


@router.get("/products/dietary/{diet}")
async def get_products_by_diet(diet: str, limit: int = Query(20)):
    try:
        table = dynamodb.Table(PRODUCT_TABLE)
        response = table.scan(FilterExpression=Attr("tags").contains(diet.lower()), Limit=limit)
        products = response.get("Items", [])
        items = []
        for product in products:
            items.append({
                "item_id": product.get("item_id"),
                "name": product.get("name"),
                "price": float(product.get("price", 0)),
                "tags": product.get("tags", []),
                "in_stock": product.get("in_stock", True),
                "promo": product.get("promo", False),
                "calories": int(product.get("calories", 0)),
                "category": product.get("category"),
                "description": product.get("description"),
                "image_url": product.get("image_url"),
            })
        return {"success": True, "message": f"Found {len(items)} {diet} products", "diet": diet, "products": items, "count": len(items)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error retrieving {diet} products: {str(e)}")


