import os
import sys
from pathlib import Path
from typing import Any, Dict, List
from strands import tool

# Support running both as a module and as a script (flexible imports)
current_dir = Path(__file__).resolve().parent
parent_dir = current_dir.parent
project_root = parent_dir.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

try:
    from backend_bedrock.dynamo.client import dynamodb, PRODUCT_TABLE
except ImportError:
    try:
        sys.path.insert(0, str(parent_dir))
        from dynamo.client import dynamodb, PRODUCT_TABLE
    except ImportError:
        import boto3
        dynamodb = boto3.resource("dynamodb")
        PRODUCT_TABLE = os.getenv("PRODUCT_TABLE", "mock-products2")


def _product_table():
    return dynamodb.Table(PRODUCT_TABLE)


def _match_by_name(products: List[Dict[str, Any]], name_query: str) -> List[Dict[str, Any]]:
    q = (name_query or "").strip().lower()
    if not q:
        return []
    exact = [p for p in products if p.get("name", "").lower() == q]
    if exact:
        return exact
    contains = [p for p in products if q in p.get("name", "").lower()]
    if contains:
        return contains
    # word-based loose match
    words = [w for w in q.split() if len(w) > 2]
    loose = []
    for p in products:
        n = p.get("name", "").lower()
        if any(w in n for w in words):
            loose.append(p)
    return loose


@tool
def find_product_stock(product_name: str) -> str:
    """
    Check if a product by name is in stock using the PRODUCT_TABLE.
    Returns a short answer like "Yes, Bananas are in stock" or "No".
    """
    table = _product_table()
    # Scan then fuzzy match by name (schema-agnostic)
    resp = table.scan()
    items = resp.get("Items", [])
    matches = _match_by_name(items, product_name)
    if not matches:
        return f"I couldn't find '{product_name}' in the catalog."
    # Prefer first match; check 'in_stock' boolean or truthy
    m = matches[0]
    in_stock = bool(m.get("in_stock", False))
    name = m.get("name", product_name)
    return (f"Yes, {name} are in stock." if in_stock else f"No, {name} are out of stock.")


