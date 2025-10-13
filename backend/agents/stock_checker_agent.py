# agents/stock_checker_agent.py
from dynamo.queries import get_promo_info
from typing import List
from decimal import Decimal

def check_stock_and_promos(cart_items: List[dict]) -> List[dict]:
    item_ids = [item["item_id"] for item in cart_items if "item_id" in item]
    promo_data = get_promo_info(item_ids)

    updated_cart = []
    for item in cart_items:
        item_id = item.get("item_id")
        promo_entry = next((p for p in promo_data if p["item_id"] == item_id), None)

        if promo_entry:
            if not promo_entry.get("in_stock", True):
                item["replacement"] = promo_entry.get("replacement_suggestion")
            if promo_entry.get("discount_percent"):
                discount = promo_entry["discount_percent"]
                # Convert to Decimal to avoid DynamoDB float issues
                price_decimal = Decimal(str(item["price"]))
                discount_decimal = Decimal(str(discount))
                discounted_price = price_decimal * (Decimal('1') - discount_decimal / Decimal('100'))
                item["discounted_price"] = discounted_price.quantize(Decimal('0.01'))

        updated_cart.append(item)

    return updated_cart
