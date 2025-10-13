# agents/dynamic_flow_orchestrator.py
from typing import Dict, Any, List, Optional
from agents.query_classifier_agent import QueryClassifierAgent, QueryType, ComplexityLevel, AgentType
from agents.product_search_agent import ProductSearchAgent
import time
import asyncio

class DynamicFlowOrchestrator:
    """
    Dynamic Flow Orchestrator that implements the exact flow patterns:
    
    Simple Queries (1-3 agents): ~2-3 seconds
    - Query Classifier → Product Search → Response Generator
    - Query Classifier → Promotion Finder → Response Generator
    - Query Classifier → Store Navigator → Response Generator
    
    Medium Queries (2-4 agents): ~3-4 seconds  
    - Query Classifier → Product Search → Substitution Finder → Response Generator
    - Query Classifier → Preference Memory → Recommendation Engine → Response Generator
    
    Complex Queries (Full pipeline): ~8-10 seconds
    - Query Classifier → Intent Capture → Preference Memory → Meal Planner → Basket Builder → Response Generator
    """
    
    def __init__(self):
        self.query_classifier = QueryClassifierAgent()
        self.product_search = ProductSearchAgent()
        self.execution_stats = []
    
    async def process_query(self, user_id: str, query: str) -> Dict[str, Any]:
        """
        Main orchestration method that processes queries according to the dynamic flow patterns
        """
        start_time = time.time()
        
        print(f"🎯 Processing Query: '{query}'")
        print("=" * 60)
        
        # Step 1: Query Classification (always first)
        classification_result = self.query_classifier.classify_query(query)
        print(f"📋 Classification Result:")
        print(f"   Query Type: {classification_result.query_type.value}")
        print(f"   Complexity: {classification_result.complexity.value}")
        print(f"   Required Agents: {[agent.value for agent in classification_result.required_agents]}")
        print(f"   Estimated Time: {classification_result.estimated_time}s")
        print()
        
        # Step 2: Execute appropriate flow pattern
        try:
            if classification_result.complexity == ComplexityLevel.SIMPLE:
                result = await self._execute_simple_flow(user_id, query, classification_result)
            elif classification_result.complexity == ComplexityLevel.MEDIUM:
                result = await self._execute_medium_flow(user_id, query, classification_result)
            else:  # ComplexityLevel.COMPLEX
                result = await self._execute_complex_flow(user_id, query, classification_result)
            
            # Calculate actual execution time
            actual_time = time.time() - start_time
            
            # Add execution metadata
            result.update({
                "query": query,
                "classification": {
                    "query_type": classification_result.query_type.value,
                    "complexity": classification_result.complexity.value,
                    "confidence": classification_result.confidence
                },
                "execution_stats": {
                    "estimated_time": classification_result.estimated_time,
                    "actual_time": actual_time,
                    "agents_executed": [agent.value for agent in classification_result.required_agents],
                    "efficiency_gain": self._calculate_efficiency_gain(classification_result)
                }
            })
            
            print(f"✅ Query completed in {actual_time:.2f}s (estimated: {classification_result.estimated_time}s)")
            
            return result
            
        except Exception as e:
            error_time = time.time() - start_time
            print(f"❌ Query failed after {error_time:.2f}s: {str(e)}")
            
            return {
                "success": False,
                "error": str(e),
                "query": query,
                "execution_time": error_time
            }
    
    async def _execute_simple_flow(self, user_id: str, query: str, classification) -> Dict[str, Any]:
        """
        Execute Simple Flow Patterns (1-3 agents, ~2-3 seconds):
        
        Pattern 1: Query Classifier → Product Search → Price Lookup → Response Generator
        Pattern 2: Query Classifier → Promotion Finder → Response Generator  
        Pattern 3: Query Classifier → Product Search → Store Navigator → Response Generator
        """
        print("🚀 Executing SIMPLE flow...")
        
        if classification.query_type == QueryType.PRICE_INQUIRY:
            return await self._handle_price_inquiry(user_id, query)
        elif classification.query_type == QueryType.PROMOTION_INQUIRY:
            return await self._handle_promotion_inquiry(user_id, query)
        elif classification.query_type == QueryType.STORE_NAVIGATION:
            return await self._handle_store_navigation(user_id, query)
        else:
            return await self._handle_general_product_search(user_id, query)
    
    async def _execute_medium_flow(self, user_id: str, query: str, classification) -> Dict[str, Any]:
        """
        Execute Medium Flow Patterns (2-4 agents, ~3-4 seconds):
        
        Pattern 1: Query Classifier → Product Search → Stock Checker → Substitution Finder → Response Generator
        Pattern 2: Query Classifier → Preference Memory → Recommendation Engine → Response Generator
        Pattern 3: Query Classifier → Product Search → Dietary Filter → Response Generator
        """
        print("🎯 Executing MEDIUM flow...")
        
        if classification.query_type == QueryType.SUBSTITUTION_REQUEST:
            return await self._handle_substitution_request(user_id, query)
        elif classification.query_type == QueryType.RECOMMENDATION_REQUEST:
            return await self._handle_recommendation_request(user_id, query)
        elif classification.query_type == QueryType.DIETARY_FILTER:
            return await self._handle_dietary_filter(user_id, query)
        else:
            return await self._handle_product_search_with_stock(user_id, query)
    
    async def _execute_complex_flow(self, user_id: str, query: str, classification) -> Dict[str, Any]:
        """
        Execute Complex Flow Pattern (Full pipeline, ~8-10 seconds):
        
        Query Classifier → Intent Capture → Preference Memory → Meal Planner → Basket Builder → Response Generator
        """
        print("🍽️ Executing COMPLEX flow (Full meal planning pipeline)...")
        
        return await self._handle_meal_planning(user_id, query)
    
    # Simple Flow Handlers
    async def _handle_price_inquiry(self, user_id: str, query: str) -> Dict[str, Any]:
        """Handle: "How much does milk cost?" """
        print("💰 Agent Flow: Product Search → Price Lookup → Response Generator")
        
        # Extract product from query
        product_keywords = self._extract_product_from_query(query)
        
        # Product Search Agent
        print("   🔍 Product Search Agent: Finding product...")
        products = self.product_search.search_products(query)
        
        if not products:
            return {
                "success": False,
                "response": f"Sorry, I couldn't find any products matching '{product_keywords}' in our database.",
                "agents_executed": 2
            }
        
        # Price Lookup Agent (simulated)
        print("   💲 Price Lookup Agent: Getting current prices...")
        await asyncio.sleep(0.3)  # Simulate processing time
        
        best_match = products[0]
        price_info = {
            "product_name": best_match.get('name'),
            "current_price": best_match.get('price', 'N/A'),
            "unit": best_match.get('unit', 'each'),
            "in_stock": best_match.get('stock_quantity', 0) > 0
        }
        
        # Response Generator
        print("   📝 Response Generator: Formatting response...")
        response = self._generate_price_response(price_info)
        
        return {
            "success": True,
            "response": response,
            "data": price_info,
            "agents_executed": 3
        }
    
    async def _handle_promotion_inquiry(self, user_id: str, query: str) -> Dict[str, Any]:
        """Handle: "What items are on sale?" """
        print("🎉 Agent Flow: Promotion Finder → Response Generator")
        
        # Promotion Finder Agent (simulated)
        print("   🏷️ Promotion Finder Agent: Finding current promotions...")
        await asyncio.sleep(0.5)  # Simulate processing time
        
        # Simulate promotion data
        promotions = [
            {"product": "Organic Milk", "original_price": 4.99, "sale_price": 3.99, "discount": "20%"},
            {"product": "Whole Wheat Bread", "original_price": 2.49, "sale_price": 1.99, "discount": "20%"},
            {"product": "Greek Yogurt", "original_price": 5.99, "sale_price": 4.49, "discount": "25%"}
        ]
        
        # Response Generator
        print("   📝 Response Generator: Formatting promotion list...")
        response = self._generate_promotion_response(promotions)
        
        return {
            "success": True,
            "response": response,
            "data": {"promotions": promotions},
            "agents_executed": 2
        }
    
    async def _handle_store_navigation(self, user_id: str, query: str) -> Dict[str, Any]:
        """Handle: "Where can I find bread?" """
        print("🗺️ Agent Flow: Product Search → Store Navigator → Response Generator")
        
        # Product Search Agent
        print("   🔍 Product Search Agent: Finding product...")
        products = self.product_search.search_products(query)
        
        if not products:
            return {
                "success": False,
                "response": "Sorry, I couldn't find that product in our store.",
                "agents_executed": 2
            }
        
        # Store Navigator Agent (simulated)
        print("   🗺️ Store Navigator Agent: Finding store location...")
        await asyncio.sleep(0.3)  # Simulate processing time
        
        product_name = products[0].get('name')
        category = products[0].get('category', 'general')
        
        # Map categories to store locations
        location_map = {
            "dairy": "Aisle 7 - Dairy & Refrigerated Section",
            "produce": "Aisle 1 - Fresh Produce Section", 
            "bakery": "Aisle 12 - Bakery Section",
            "meat": "Aisle 8 - Meat & Seafood Section",
            "general": "Please ask a store associate for specific location"
        }
        
        location = location_map.get(category, location_map["general"])
        
        # Response Generator
        print("   📝 Response Generator: Providing location information...")
        response = f"You can find {product_name} in {location}."
        
        return {
            "success": True,
            "response": response,
            "data": {"product": product_name, "location": location},
            "agents_executed": 3
        }
    
    # Medium Flow Handlers
    async def _handle_substitution_request(self, user_id: str, query: str) -> Dict[str, Any]:
        """Handle: "I need substitute for eggs" """
        print("🔄 Agent Flow: Product Search → Stock Checker → Substitution Finder → Response Generator")
        
        # Product Search Agent
        print("   🔍 Product Search Agent: Finding original product...")
        original_product = self._extract_product_from_query(query)
        
        # Stock Checker Agent (simulated)
        print("   📦 Stock Checker Agent: Checking availability...")
        await asyncio.sleep(0.4)  # Simulate processing time
        
        # Substitution Finder Agent (simulated)  
        print("   🔄 Substitution Finder Agent: Finding alternatives...")
        await asyncio.sleep(0.5)  # Simulate processing time
        
        # Predefined substitutions
        substitutions = {
            "eggs": ["applesauce", "mashed banana", "flax eggs", "chia eggs"],
            "milk": ["almond milk", "soy milk", "oat milk", "coconut milk"],
            "butter": ["olive oil", "coconut oil", "applesauce", "avocado"],
            "flour": ["almond flour", "coconut flour", "oat flour", "rice flour"]
        }
        
        product_key = next((key for key in substitutions.keys() if key in query.lower()), None)
        alternatives = substitutions.get(product_key, ["Please consult with our nutrition specialist"])
        
        # Response Generator
        print("   📝 Response Generator: Suggesting alternatives...")
        response = f"Here are some great substitutes for {original_product}: {', '.join(alternatives[:3])}"
        
        return {
            "success": True,
            "response": response,
            "data": {"original_product": original_product, "substitutes": alternatives},
            "agents_executed": 4
        }
    
    async def _handle_recommendation_request(self, user_id: str, query: str) -> Dict[str, Any]:
        """Handle: "Suggest low-carb snacks" """
        print("🎯 Agent Flow: Preference Memory → Recommendation Engine → Response Generator")
        
        # Preference Memory Agent (simulated)
        print("   🧠 Preference Memory Agent: Loading user preferences...")
        await asyncio.sleep(0.4)  # Simulate processing time
        
        # Recommendation Engine Agent
        print("   🤖 Recommendation Engine Agent: Generating recommendations...")
        await asyncio.sleep(0.6)  # Simulate processing time
        
        # Extract dietary preference from query
        dietary_pref = self._extract_dietary_preference(query)
        products = self.product_search.search_by_dietary_preference(dietary_pref)
        
        # Response Generator
        print("   📝 Response Generator: Formatting recommendations...")
        response = self._generate_recommendation_response(products[:5], dietary_pref)
        
        return {
            "success": True,
            "response": response,
            "data": {"dietary_preference": dietary_pref, "recommendations": products[:5]},
            "agents_executed": 3
        }
    
    # Complex Flow Handler
    async def _handle_meal_planning(self, user_id: str, query: str) -> Dict[str, Any]:
        """Handle: "Plan 5 meals under $60" """
        print("🍽️ Agent Flow: Intent Capture → Preference Memory → Meal Planner → Basket Builder → Response Generator")
        
        # Intent Capture Agent
        print("   🎯 Intent Capture Agent: Extracting meal planning intent...")
        await asyncio.sleep(0.8)  # Simulate processing time
        
        # Preference Memory Agent  
        print("   🧠 Preference Memory Agent: Loading user profile...")
        await asyncio.sleep(0.6)  # Simulate processing time
        
        # Meal Planner Agent
        print("   🍽️ Meal Planner Agent: Creating meal plan...")
        await asyncio.sleep(2.0)  # Simulate processing time
        
        # Basket Builder Agent
        print("   🛒 Basket Builder Agent: Building shopping list...")
        await asyncio.sleep(1.2)  # Simulate processing time
        
        # Response Generator
        print("   📝 Response Generator: Compiling meal plan response...")
        await asyncio.sleep(0.4)  # Simulate processing time
        
        # Extract meal count and budget from query
        meal_count = self._extract_meal_count(query)
        budget = self._extract_budget(query)
        
        response = f"I've created a {meal_count}-meal plan within your ${budget} budget. The plan includes balanced meals with a complete shopping list totaling approximately ${budget * 0.85:.2f}."
        
        return {
            "success": True,
            "response": response,
            "data": {
                "meal_count": meal_count,
                "budget": budget,
                "estimated_cost": budget * 0.85
            },
            "agents_executed": 6
        }
    
    # Helper Methods
    def _extract_product_from_query(self, query: str) -> str:
        """Extract product name from query"""
        common_products = ["milk", "bread", "eggs", "cheese", "chicken", "beef", "yogurt", "butter"]
        for product in common_products:
            if product in query.lower():
                return product
        return "product"
    
    def _extract_dietary_preference(self, query: str) -> str:
        """Extract dietary preference from query"""
        preferences = ["low-carb", "keto", "vegan", "vegetarian", "gluten-free", "organic"]
        for pref in preferences:
            if pref in query.lower():
                return pref
        return "healthy"
    
    def _extract_meal_count(self, query: str) -> int:
        """Extract number of meals from query"""
        import re
        match = re.search(r'(\d+)\s*meal', query.lower())
        return int(match.group(1)) if match else 3
    
    def _extract_budget(self, query: str) -> float:
        """Extract budget from query"""
        import re
        match = re.search(r'\$(\d+)', query)
        return float(match.group(1)) if match else 50.0
    
    def _calculate_efficiency_gain(self, classification) -> Dict[str, Any]:
        """Calculate efficiency metrics compared to traditional full pipeline"""
        total_possible_agents = 8  # Maximum agents in full pipeline
        agents_used = len(classification.required_agents)
        
        return {
            "agents_saved": total_possible_agents - agents_used,
            "efficiency_percentage": ((total_possible_agents - agents_used) / total_possible_agents) * 100,
            "time_saved_estimate": (total_possible_agents - agents_used) * 1.2  # Assume 1.2s per agent
        }
    
    def _generate_price_response(self, price_info: Dict[str, Any]) -> str:
        """Generate formatted price response"""
        if price_info["current_price"] == "N/A":
            return f"I couldn't find pricing information for {price_info['product_name']}."
        
        stock_status = "in stock" if price_info["in_stock"] else "currently out of stock"
        return f"{price_info['product_name']} is ${price_info['current_price']} per {price_info['unit']} and is {stock_status}."
    
    def _generate_promotion_response(self, promotions: List[Dict[str, Any]]) -> str:
        """Generate formatted promotion response"""
        if not promotions:
            return "Sorry, there are no active promotions at this time."
        
        response = "Here are our current promotions:\n"
        for promo in promotions:
            response += f"• {promo['product']}: ${promo['sale_price']} (was ${promo['original_price']}) - {promo['discount']} off\n"
        
        return response.strip()
    
    def _generate_recommendation_response(self, products: List[Dict[str, Any]], dietary_pref: str) -> str:
        """Generate formatted recommendation response"""
        if not products:
            return f"Sorry, I couldn't find any {dietary_pref} products in our current inventory."
        
        response = f"Here are some great {dietary_pref} options:\n"
        for product in products:
            price = product.get('price', 'N/A')
            response += f"• {product.get('name')} - ${price}\n"
        
        return response.strip()

# Convenience function for quick processing
async def process_user_query(user_id: str, query: str) -> Dict[str, Any]:
    """Quick query processing function"""
    orchestrator = DynamicFlowOrchestrator()
    return await orchestrator.process_query(user_id, query) 