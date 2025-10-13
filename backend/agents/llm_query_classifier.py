#!/usr/bin/env python3
"""
LLM-Based Query Classifier Agent
Replaces rigid keyword matching with intelligent intent understanding
"""

from typing import Dict, Any, List, Tuple, Optional
from enum import Enum
from langchain_core.prompts import ChatPromptTemplate
from bedrock.bedrock_llm import get_bedrock_llm
import json
import re

class QueryType(Enum):
    PRICE_INQUIRY = "price_inquiry"
    PRODUCT_SEARCH = "product_search"
    SUBSTITUTION_REQUEST = "substitution_request"
    STORE_NAVIGATION = "store_navigation"
    PROMOTION_INQUIRY = "promotion_inquiry"
    DIETARY_FILTER = "dietary_filter"
    RECOMMENDATION_REQUEST = "recommendation_request"
    MEAL_PLANNING = "meal_planning"
    AVAILABILITY_CHECK = "availability_check"
    GENERAL_INQUIRY = "general_inquiry"

class ComplexityLevel(Enum):
    SIMPLE = "simple"     # 1-3 agents, ~2-3 seconds
    MEDIUM = "medium"     # 2-4 agents, ~3-4 seconds  
    COMPLEX = "complex"   # 4+ agents, ~8-10 seconds

class QueryClassificationResult:
    """Enhanced query classification result with LLM insights"""
    
    def __init__(self, query_type: str, complexity: str, confidence: float, 
                 reasoning: str = "", extracted_product: str = None, 
                 extracted_budget: int = None, classification_method: str = "llm"):
        self.query_type = query_type
        self.complexity = complexity
        self.confidence = confidence
        self.reasoning = reasoning
        self.extracted_product = extracted_product
        self.extracted_budget = extracted_budget
        self.classification_method = classification_method

class LLMQueryClassifier:
    """
    Smart LLM-based Query Classifier that understands intent contextually
    instead of relying on rigid keyword matching
    """
    
    def __init__(self):
        self.llm = get_bedrock_llm()
        self.classification_prompt = ChatPromptTemplate.from_template(self._get_classification_prompt())
        
    def _get_classification_prompt(self) -> str:
        return """
You are an intelligent grocery shopping assistant classifier. Analyze the user's message and determine their INTENT, not just keywords.

CLASSIFICATION CATEGORIES:

1. SUBSTITUTION_REQUEST - User wants alternatives/replacements for a product:
   Examples: "I'm out of eggs, what can I use?", "Can't find milk, what else works?", "Something similar to butter?", "What replaces flour?", "I need substitute for eggs", "Butter alternative for baking", "Out of bread, what else?"

2. PRICE_INQUIRY - User wants to know cost/price of products:
   Examples: "How much does milk cost?", "What's the price of bread?", "Is chicken expensive?", "Price check on apples", "Cost of organic vegetables"

3. PRODUCT_SEARCH - User looking for specific products or checking availability:
   Examples: "Do you have Greek yogurt?", "Where can I find quinoa?", "Is almond milk available?", "Looking for organic vegetables", "Any fresh salmon?"

4. MEAL_PLANNING - User wants to plan meals with budget/quantity constraints:
   Examples: "Plan 3 meals under $50", "Weekly meal planning for $40", "Create meal plan for family of 4", "Budget-friendly dinner ideas", "5 meals under $60"

5. RECOMMENDATION_REQUEST - User wants product suggestions/recommendations:
   Examples: "Suggest healthy snacks", "Recommend low-carb products", "What's good for breakfast?", "Best pasta brands", "Show me protein options"

6. DIETARY_FILTER - User filtering products by dietary needs:
   Examples: "Show me gluten-free options", "Vegan products only", "Keto-friendly items", "Low-sodium foods", "Gluten-free products"

7. PROMOTION_INQUIRY - User asking about sales/discounts/deals:
   Examples: "What's on sale?", "Any discounts today?", "Current promotions?", "Deals this week", "Items with coupons"

8. STORE_NAVIGATION - User needs help finding location of products:
   Examples: "Where is the bread section?", "How do I find frozen foods?", "Aisle for cleaning supplies", "Location of dairy products"

9. AVAILABILITY_CHECK - User checking if specific items are in stock:
   Examples: "Is salmon available today?", "Do you have fresh strawberries?", "Any organic apples left?", "Stock check on pasta"

10. GENERAL_INQUIRY - Everything else (greetings, store hours, policies, etc.):
    Examples: "Hello", "Store hours?", "Return policy?", "How are you?", "Help with delivery"

IMPORTANT CONTEXT CLUES:
- "out of", "can't find", "ran out", "what else" often indicate SUBSTITUTION_REQUEST
- Budget amounts ($XX) with meal/planning words indicate MEAL_PLANNING  
- "How much", "price", "cost" indicate PRICE_INQUIRY
- "Do you have", "available", "in stock" indicate AVAILABILITY_CHECK
- "Suggest", "recommend", "best" indicate RECOMMENDATION_REQUEST
- Dietary words (gluten-free, vegan, keto) indicate DIETARY_FILTER

COMPLEXITY LEVELS:
- SIMPLE: Quick answer, no complex processing (price checks, availability, store info)
- MEDIUM: Some processing needed (product search, recommendations, substitutions)
- COMPLEX: Full planning/analysis needed (meal planning)

ANALYZE THIS MESSAGE: "{message}"

Return ONLY a JSON object:
{{
    "query_type": "one_of_the_categories_above",
    "complexity": "simple|medium|complex", 
    "confidence": 0.95,
    "reasoning": "Brief explanation of why you classified it this way",
    "extracted_product": "product_name_if_any_or_null",
    "extracted_budget": "budget_amount_if_any_or_null"
}}
"""

    def classify_query(self, user_message: str) -> QueryClassificationResult:
        """
        Classify query using LLM intelligence instead of rigid keywords
        """
        try:
            # Use LLM for intelligent classification
            prompt = self.classification_prompt.format(message=user_message)
            response = self.llm.invoke(prompt)
            
            # Extract JSON from response
            response_text = response.content if hasattr(response, 'content') else str(response)
            
            # Try to find JSON in the response
            json_match = re.search(r'\{.*\}', response_text, re.DOTALL)
            if json_match:
                classification = json.loads(json_match.group())
                
                # Validate required fields
                if not all(key in classification for key in ['query_type', 'complexity', 'confidence']):
                    raise ValueError("Missing required classification fields")
                
                # Ensure valid enum values
                query_type = classification['query_type']
                complexity = classification['complexity']
                
                if query_type not in [e.value for e in QueryType]:
                    query_type = QueryType.GENERAL_INQUIRY.value
                
                if complexity not in [e.value for e in ComplexityLevel]:
                    complexity = ComplexityLevel.SIMPLE.value
                
                return QueryClassificationResult(
                    query_type=query_type,
                    complexity=complexity,
                    confidence=min(float(classification.get('confidence', 0.8)), 1.0),
                    reasoning=classification.get('reasoning', 'LLM classification'),
                    extracted_product=classification.get('extracted_product'),
                    extracted_budget=self._extract_budget_safely(classification.get('extracted_budget')),
                    classification_method='llm'
                )
            else:
                raise ValueError("No JSON found in LLM response")
                
        except Exception as e:
            print(f"   LLM classification failed: {e}")
            return self._fallback_keyword_classification(user_message)
    
    def _extract_budget_safely(self, budget_value) -> Optional[int]:
        """Safely extract budget as integer"""
        if budget_value is None:
            return None
        try:
            if isinstance(budget_value, str):
                # Extract number from string like "$50" or "50"
                match = re.search(r'\d+', budget_value)
                return int(match.group()) if match else None
            return int(budget_value)
        except (ValueError, TypeError):
            return None
    
    def _fallback_keyword_classification(self, user_message: str) -> QueryClassificationResult:
        """
        Enhanced fallback classification if LLM fails
        """
        message_lower = user_message.lower()
        
        # Enhanced substitution detection with better patterns
        substitution_patterns = [
            r"out of.*what.*use", r"can't find.*what.*else", r"can't find.*what.*works",
            r"similar to", r"substitute", r"alternative", r"replacement", r"instead of", 
            r"replace", r"swap", r"what.*use.*for", r"what.*can.*use", r"what.*else.*works",
            r"ran out.*what", r"something like", r"other.*option"
        ]
        if any(re.search(pattern, message_lower) for pattern in substitution_patterns):
            # Don't classify as substitution if it's about non-food items
            if not any(word in message_lower for word in ["list", "order", "delivery", "appointment", "subscription"]):
                return QueryClassificationResult(
                    query_type=QueryType.SUBSTITUTION_REQUEST.value,
                    complexity=ComplexityLevel.MEDIUM.value,
                    confidence=0.75,
                    reasoning="Keyword fallback: detected substitution patterns",
                    classification_method="keyword_fallback"
                )
        
        # Meal planning detection - enhanced with budget detection
        meal_patterns = [r"\d+.*meals?", r"meal.*plan", r"plan.*meals?"]
        budget_match = re.search(r"under.*\$(\d+)", message_lower)
        if any(re.search(pattern, message_lower) for pattern in meal_patterns) or budget_match:
            budget = int(budget_match.group(1)) if budget_match else None
            return QueryClassificationResult(
                query_type=QueryType.MEAL_PLANNING.value,
                complexity=ComplexityLevel.COMPLEX.value,
                confidence=0.85,
                reasoning="Keyword fallback: detected meal planning patterns",
                extracted_budget=budget,
                classification_method="keyword_fallback"
            )
        
        # Price inquiry detection
        price_patterns = [r"price", r"cost", r"how much", r"\$", r"expensive", r"cheap"]
        if any(pattern in message_lower for pattern in price_patterns):
            return QueryClassificationResult(
                query_type=QueryType.PRICE_INQUIRY.value,
                complexity=ComplexityLevel.SIMPLE.value,
                confidence=0.8,
                reasoning="Keyword fallback: detected price inquiry",
                classification_method="keyword_fallback"
            )
        
        # Product search/availability
        search_patterns = [r"do you have", r"available", r"in stock", r"carry", r"find", r"where"]
        if any(pattern in message_lower for pattern in search_patterns):
            return QueryClassificationResult(
                query_type=QueryType.AVAILABILITY_CHECK.value,
                complexity=ComplexityLevel.SIMPLE.value,
                confidence=0.7,
                reasoning="Keyword fallback: detected availability check",
                classification_method="keyword_fallback"
            )
        
        # Recommendations
        recommendation_patterns = [r"suggest", r"recommend", r"best", r"good", r"what.*should"]
        if any(pattern in message_lower for pattern in recommendation_patterns):
            return QueryClassificationResult(
                query_type=QueryType.RECOMMENDATION_REQUEST.value,
                complexity=ComplexityLevel.MEDIUM.value,
                confidence=0.7,
                reasoning="Keyword fallback: detected recommendation request",
                classification_method="keyword_fallback"
            )
        
        # Dietary filters
        dietary_patterns = [r"gluten.?free", r"vegan", r"vegetarian", r"keto", r"low.?carb", r"organic"]
        if any(re.search(pattern, message_lower) for pattern in dietary_patterns):
            return QueryClassificationResult(
                query_type=QueryType.DIETARY_FILTER.value,
                complexity=ComplexityLevel.MEDIUM.value,
                confidence=0.8,
                reasoning="Keyword fallback: detected dietary filter",
                classification_method="keyword_fallback"
            )
        
        # Default to general inquiry
        return QueryClassificationResult(
            query_type=QueryType.GENERAL_INQUIRY.value,
            complexity=ComplexityLevel.SIMPLE.value,
            confidence=0.5,
            reasoning="Keyword fallback: default classification",
            classification_method="keyword_fallback"
        )

# Convenience function for backward compatibility
def classify_query_with_llm(user_message: str) -> Dict[str, Any]:
    """
    Main classification function for use throughout the system
    Returns dict for backward compatibility
    """
    classifier = LLMQueryClassifier()
    result = classifier.classify_query(user_message)
    
    return {
        'query_type': result.query_type,
        'complexity': result.complexity,
        'confidence': result.confidence,
        'reasoning': result.reasoning,
        'extracted_product': result.extracted_product,
        'extracted_budget': result.extracted_budget,
        'classification_method': result.classification_method
    }

# Test function
def test_llm_classification():
    """Test the LLM classification with real examples"""
    
    test_cases = [
        "I'm out of eggs, what can I use?",
        "Can't find milk, what else works for cereal?",
        "Something similar to butter for baking?",
        "I need substitute for eggs",
        "Plan 3 meals under $50",
        "How much does milk cost?",
        "Do you have Greek yogurt?",
        "Suggest healthy snacks",
        "Show me gluten-free options",
        "I need to replace my shopping list",  # Should NOT be substitution
    ]
    
    classifier = LLMQueryClassifier()
    
    print("🧪 LLM QUERY CLASSIFICATION TEST")
    print("=" * 40)
    
    for query in test_cases:
        result = classifier.classify_query(query)
        print(f"\nQuery: '{query}'")
        print(f"   Type: {result.query_type}")
        print(f"   Complexity: {result.complexity}")
        print(f"   Confidence: {result.confidence:.2f}")
        print(f"   Method: {result.classification_method}")
        if result.reasoning:
            print(f"   Reasoning: {result.reasoning}")
        if result.extracted_product:
            print(f"   Product: {result.extracted_product}")
        if result.extracted_budget:
            print(f"   Budget: ${result.extracted_budget}")

if __name__ == "__main__":
    test_llm_classification() 