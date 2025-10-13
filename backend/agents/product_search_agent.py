# agents/product_search_agent.py
from typing import List, Dict, Any, Optional
from dynamo.client import dynamodb, PRODUCT_TABLE
from boto3.dynamodb.conditions import Attr, Key
import re

class ProductSearchAgent:
    """
    Product Search Agent handles finding products based on user queries.
    Core component for most query flows.
    """
    
    def __init__(self):
        self.product_table = dynamodb.Table(PRODUCT_TABLE)
    
    def search_products(self, query: str, filters: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        """
        Main search method that finds products based on query text and optional filters
        """
        try:
            # Extract product keywords from query
            keywords = self._extract_product_keywords(query)
            
            # Perform search
            if keywords:
                products = self._search_by_keywords(keywords, filters)
            else:
                products = self._search_all_products(filters)
            
            # Rank and filter results
            ranked_products = self._rank_search_results(products, query)
            
            return ranked_products[:20]  # Limit to top 20 results
            
        except Exception as e:
            print(f"❌ Product search error: {str(e)}")
            return []
    
    def find_product_by_name(self, product_name: str) -> Optional[Dict[str, Any]]:
        """Find a specific product by exact or fuzzy name match"""
        try:
            # Try exact match first
            response = self.product_table.scan(
                FilterExpression=Attr('name').contains(product_name.lower())
            )
            
            products = response.get('Items', [])
            
            if products:
                # Return best match
                return self._find_best_name_match(products, product_name)
            
            return None
            
        except Exception as e:
            print(f"❌ Product lookup error: {str(e)}")
            return None
    
    def search_by_category(self, category: str, limit: int = 20) -> List[Dict[str, Any]]:
        """Search products by category"""
        try:
            response = self.product_table.scan(
                FilterExpression=Attr('category').eq(category.lower()),
                Limit=limit
            )
            
            return response.get('Items', [])
            
        except Exception as e:
            print(f"❌ Category search error: {str(e)}")
            return []
    
    def search_by_dietary_preference(self, dietary_preference: str) -> List[Dict[str, Any]]:
        """Search products matching dietary preferences"""
        try:
            # Map dietary preferences to search terms
            dietary_mappings = {
                'low-carb': ['low carb', 'keto', 'protein'],
                'keto': ['keto', 'low carb', 'high fat'],
                'vegan': ['vegan', 'plant-based'],
                'vegetarian': ['vegetarian', 'veggie'],
                'gluten-free': ['gluten-free', 'gluten free'],
                'dairy-free': ['dairy-free', 'lactose-free', 'almond', 'soy'],
                'organic': ['organic', 'natural'],
                'sugar-free': ['sugar-free', 'no sugar', 'diabetic']
            }
            
            search_terms = dietary_mappings.get(dietary_preference.lower(), [dietary_preference])
            
            # Search for products matching dietary terms
            all_products = []
            for term in search_terms:
                response = self.product_table.scan(
                    FilterExpression=Attr('name').contains(term) | 
                                   Attr('description').contains(term) |
                                   Attr('tags').contains(term)
                )
                all_products.extend(response.get('Items', []))
            
            # Remove duplicates and return
            seen_ids = set()
            unique_products = []
            for product in all_products:
                if product['product_id'] not in seen_ids:
                    seen_ids.add(product['product_id'])
                    unique_products.append(product)
            
            return unique_products[:20]
            
        except Exception as e:
            print(f"❌ Dietary search error: {str(e)}")
            return []
    
    def _extract_product_keywords(self, query: str) -> List[str]:
        """Extract potential product keywords from query"""
        # Remove common question words
        stop_words = {
            'what', 'where', 'how', 'much', 'does', 'is', 'are', 'can', 'do', 'you', 'have',
            'price', 'cost', 'find', 'search', 'look', 'for', 'the', 'a', 'an', 'and', 'or',
            'in', 'on', 'at', 'to', 'from', 'with', 'without', 'of'
        }
        
        # Extract meaningful words
        words = re.findall(r'\b[a-zA-Z]+\b', query.lower())
        keywords = [word for word in words if word not in stop_words and len(word) > 2]
        
        # Look for product-specific terms
        product_indicators = ['milk', 'bread', 'cheese', 'yogurt', 'chicken', 'beef', 'fish', 
                            'vegetables', 'fruits', 'snacks', 'cereal', 'pasta', 'rice']
        
        # Prioritize product indicators
        priority_keywords = [kw for kw in keywords if kw in product_indicators]
        other_keywords = [kw for kw in keywords if kw not in product_indicators]
        
        return priority_keywords + other_keywords[:5]  # Limit to avoid over-broad searches
    
    def _search_by_keywords(self, keywords: List[str], filters: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        """Search products using keywords"""
        try:
            all_products = []
            
            for keyword in keywords:
                # Search in name, description, and category
                filter_expression = (
                    Attr('name').contains(keyword) |
                    Attr('description').contains(keyword) |
                    Attr('category').contains(keyword)
                )
                
                # Apply additional filters if provided
                if filters:
                    for key, value in filters.items():
                        if key == 'max_price':
                            filter_expression = filter_expression & Attr('price').lte(value)
                        elif key == 'category':
                            filter_expression = filter_expression & Attr('category').eq(value)
                        elif key == 'in_stock':
                            filter_expression = filter_expression & Attr('stock_quantity').gt(0)
                
                response = self.product_table.scan(
                    FilterExpression=filter_expression,
                    Limit=50
                )
                
                all_products.extend(response.get('Items', []))
            
            return all_products
            
        except Exception as e:
            print(f"❌ Keyword search error: {str(e)}")
            return []
    
    def _search_all_products(self, filters: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        """Get all products with optional filters"""
        try:
            scan_kwargs = {'Limit': 50}
            
            if filters:
                filter_expressions = []
                for key, value in filters.items():
                    if key == 'max_price':
                        filter_expressions.append(Attr('price').lte(value))
                    elif key == 'category':
                        filter_expressions.append(Attr('category').eq(value))
                    elif key == 'in_stock':
                        filter_expressions.append(Attr('stock_quantity').gt(0))
                
                if filter_expressions:
                    combined_filter = filter_expressions[0]
                    for expr in filter_expressions[1:]:
                        combined_filter = combined_filter & expr
                    scan_kwargs['FilterExpression'] = combined_filter
            
            response = self.product_table.scan(**scan_kwargs)
            return response.get('Items', [])
            
        except Exception as e:
            print(f"❌ General search error: {str(e)}")
            return []
    
    def _rank_search_results(self, products: List[Dict[str, Any]], query: str) -> List[Dict[str, Any]]:
        """Rank search results by relevance to query"""
        query_lower = query.lower()
        
        def calculate_relevance_score(product):
            score = 0
            name = product.get('name', '').lower()
            description = product.get('description', '').lower()
            
            # Exact name match gets highest score
            if query_lower in name:
                score += 10
            
            # Partial name match
            query_words = query_lower.split()
            for word in query_words:
                if word in name:
                    score += 5
                if word in description:
                    score += 2
            
            # Boost popular/common items
            if any(common in name for common in ['milk', 'bread', 'eggs', 'cheese']):
                score += 1
            
            return score
        
        # Sort by relevance score
        scored_products = [(product, calculate_relevance_score(product)) for product in products]
        scored_products.sort(key=lambda x: x[1], reverse=True)
        
        # Remove duplicates while preserving order
        seen_ids = set()
        unique_products = []
        for product, score in scored_products:
            if product['product_id'] not in seen_ids:
                seen_ids.add(product['product_id'])
                product['relevance_score'] = score
                unique_products.append(product)
        
        return unique_products
    
    def _find_best_name_match(self, products: List[Dict[str, Any]], target_name: str) -> Dict[str, Any]:
        """Find the best matching product by name similarity"""
        target_lower = target_name.lower()
        
        best_match = products[0]
        best_score = 0
        
        for product in products:
            name = product.get('name', '').lower()
            
            # Calculate similarity score
            if target_lower == name:
                return product  # Exact match
            elif target_lower in name:
                score = len(target_lower) / len(name)
                if score > best_score:
                    best_score = score
                    best_match = product
        
        return best_match

# Convenience functions
def search_products(query: str, filters: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
    """Quick product search function"""
    agent = ProductSearchAgent()
    return agent.search_products(query, filters)

def find_product(product_name: str) -> Optional[Dict[str, Any]]:
    """Quick product lookup function"""
    agent = ProductSearchAgent()
    return agent.find_product_by_name(product_name) 