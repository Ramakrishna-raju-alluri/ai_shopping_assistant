# agents/query_classifier_agent.py
from typing import List, Dict, Any, Tuple
from enum import Enum
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
    GENERAL_INQUIRY = "general_inquiry"

class ComplexityLevel(Enum):
    SIMPLE = "simple"      # 1-3 agents, ~2-3 seconds
    MEDIUM = "medium"      # 2-4 agents, ~3-4 seconds  
    COMPLEX = "complex"    # Full pipeline, ~8-10 seconds

class AgentType(Enum):
    QUERY_CLASSIFIER = "query_classifier"
    PRODUCT_SEARCH = "product_search"
    PRICE_LOOKUP = "price_lookup"
    PROMOTION_FINDER = "promotion_finder"
    STORE_NAVIGATOR = "store_navigator"
    SUBSTITUTION_FINDER = "substitution_finder"
    DIETARY_FILTER = "dietary_filter"
    RECOMMENDATION_ENGINE = "recommendation_engine"
    PREFERENCE_MEMORY = "preference_memory"
    INTENT_CAPTURE = "intent_capture"
    MEAL_PLANNER = "meal_planner"
    BASKET_BUILDER = "basket_builder"
    STOCK_CHECKER = "stock_checker"
    RESPONSE_GENERATOR = "response_generator"

class QueryClassificationResult:
    def __init__(self, query_type: QueryType, complexity: ComplexityLevel, 
                 required_agents: List[AgentType], estimated_time: float,
                 confidence: float = 1.0):
        self.query_type = query_type
        self.complexity = complexity
        self.required_agents = required_agents
        self.estimated_time = estimated_time
        self.confidence = confidence

class QueryClassifierAgent:
    """
    Central Query Classifier Agent that determines:
    - Query Type: What the user is asking for
    - Complexity Level: Simple, medium, or complex
    - Required Agents: Only the agents needed for this specific query
    """
    
    def __init__(self):
        self.classification_patterns = self._initialize_patterns()
        self.flow_mappings = self._initialize_flow_mappings()
    
    def _initialize_patterns(self) -> Dict[QueryType, Dict[str, List[str]]]:
        """Initialize pattern matching for query classification"""
        return {
            QueryType.PRICE_INQUIRY: {
                "keywords": ["price", "cost", "how much", "price of", "cost of", "$", "expensive", "cheap"],
                "patterns": [
                    r"(?:what.?s|how much).{0,20}(?:price|cost)",
                    r"(?:price|cost).{0,10}(?:of|for)",
                    r"\$\d+",
                    r"(?:expensive|cheap|affordable)"
                ]
            },
            QueryType.PRODUCT_SEARCH: {
                "keywords": ["find", "search", "look for", "where", "have", "carry", "stock", "available"],
                "patterns": [
                    r"(?:do you|can you).{0,20}(?:have|carry|find)",
                    r"(?:where).{0,20}(?:find|get|buy)",
                    r"(?:in stock|available|carry)"
                ]
            },
            QueryType.SUBSTITUTION_REQUEST: {
                "keywords": ["substitute", "alternative", "replacement", "instead of", "replace", "swap"],
                "patterns": [
                    r"(?:substitute|alternative|replacement).{0,20}(?:for|to)",
                    r"(?:instead of|replace|swap)",
                    r"(?:can.t find|out of|don.t have).{0,20}(?:alternative|substitute)"
                ]
            },
            QueryType.STORE_NAVIGATION: {
                "keywords": ["where", "aisle", "section", "department", "location", "find"],
                "patterns": [
                    r"(?:where).{0,20}(?:aisle|section|find)",
                    r"(?:which aisle|what section)",
                    r"(?:where is|where can i find)"
                ]
            },
            QueryType.PROMOTION_INQUIRY: {
                "keywords": ["sale", "discount", "promotion", "deal", "offer", "coupon", "special"],
                "patterns": [
                    r"(?:on sale|sale items|discounts?)",
                    r"(?:promotion|deal|offer|special)",
                    r"(?:coupon|savings|reduced price)"
                ]
            },
            QueryType.DIETARY_FILTER: {
                "keywords": ["low-carb", "gluten-free", "vegan", "vegetarian", "keto", "organic", "sugar-free"],
                "patterns": [
                    r"(?:low.?carb|keto|ketogenic)",
                    r"(?:gluten.?free|celiac)",
                    r"(?:vegan|plant.?based)",
                    r"(?:vegetarian|veggie)",
                    r"(?:organic|natural|sugar.?free)"
                ]
            },
            QueryType.RECOMMENDATION_REQUEST: {
                "keywords": ["recommend", "suggest", "what should", "best", "good", "popular"],
                "patterns": [
                    r"(?:recommend|suggest|what should)",
                    r"(?:what.?s.{0,10}(?:best|good|popular))",
                    r"(?:any suggestions|ideas for)"
                ]
            },
            QueryType.MEAL_PLANNING: {
                "keywords": ["meal", "plan", "recipe", "dinner", "lunch", "breakfast", "cook", "prepare"],
                "patterns": [
                    r"(?:plan|create).{0,20}(?:meal|menu)",
                    r"(?:\d+).{0,10}(?:meal|recipe|dinner)",
                    r"(?:meal plan|weekly plan|menu)",
                    r"(?:under \$\d+|budget.{0,10}\$\d+)"
                ]
            }
        }
    
    def _initialize_flow_mappings(self) -> Dict[QueryType, Tuple[ComplexityLevel, List[AgentType], float]]:
        """Initialize flow mappings for each query type"""
        return {
            # Simple Queries (1-3 agents, ~2-3 seconds)
            QueryType.PRICE_INQUIRY: (
                ComplexityLevel.SIMPLE,
                [AgentType.PRODUCT_SEARCH, AgentType.PRICE_LOOKUP, AgentType.RESPONSE_GENERATOR],
                2.0
            ),
            QueryType.STORE_NAVIGATION: (
                ComplexityLevel.SIMPLE,
                [AgentType.PRODUCT_SEARCH, AgentType.STORE_NAVIGATOR, AgentType.RESPONSE_GENERATOR],
                2.0
            ),
            QueryType.PROMOTION_INQUIRY: (
                ComplexityLevel.SIMPLE,
                [AgentType.PROMOTION_FINDER, AgentType.RESPONSE_GENERATOR],
                2.0
            ),
            
            # Medium Queries (2-4 agents, ~3-4 seconds)
            QueryType.PRODUCT_SEARCH: (
                ComplexityLevel.MEDIUM,
                [AgentType.PRODUCT_SEARCH, AgentType.STOCK_CHECKER, AgentType.RESPONSE_GENERATOR],
                3.0
            ),
            QueryType.SUBSTITUTION_REQUEST: (
                ComplexityLevel.MEDIUM,
                [AgentType.PRODUCT_SEARCH, AgentType.STOCK_CHECKER, AgentType.SUBSTITUTION_FINDER, AgentType.RESPONSE_GENERATOR],
                4.0
            ),
            QueryType.DIETARY_FILTER: (
                ComplexityLevel.MEDIUM,
                [AgentType.PRODUCT_SEARCH, AgentType.DIETARY_FILTER, AgentType.RESPONSE_GENERATOR],
                3.0
            ),
            QueryType.RECOMMENDATION_REQUEST: (
                ComplexityLevel.MEDIUM,
                [AgentType.PREFERENCE_MEMORY, AgentType.RECOMMENDATION_ENGINE, AgentType.RESPONSE_GENERATOR],
                3.5
            ),
            
            # Complex Queries (Full pipeline, ~8-10 seconds)
            QueryType.MEAL_PLANNING: (
                ComplexityLevel.COMPLEX,
                [AgentType.INTENT_CAPTURE, AgentType.PREFERENCE_MEMORY, AgentType.MEAL_PLANNER, 
                 AgentType.BASKET_BUILDER, AgentType.STOCK_CHECKER, AgentType.RESPONSE_GENERATOR],
                9.0
            ),
            
            # Fallback
            QueryType.GENERAL_INQUIRY: (
                ComplexityLevel.SIMPLE,
                [AgentType.RESPONSE_GENERATOR],
                1.5
            )
        }
    
    def classify_query(self, query: str) -> QueryClassificationResult:
        """
        Main classification method that analyzes the query and returns
        the query type, complexity, and required agents
        """
        query_lower = query.lower()
        
        # Score each query type based on pattern matching
        scores = {}
        for query_type, patterns in self.classification_patterns.items():
            score = self._calculate_pattern_score(query_lower, patterns)
            if score > 0:
                scores[query_type] = score
        
        # Determine the best match
        if not scores:
            query_type = QueryType.GENERAL_INQUIRY
            confidence = 0.5
        else:
            query_type = max(scores, key=scores.get)
            max_score = scores[query_type]
            confidence = min(max_score / 10.0, 1.0)  # Normalize confidence
        
        # Get flow mapping
        complexity, required_agents, estimated_time = self.flow_mappings[query_type]
        
        # Apply special rules for complex queries
        if self._is_meal_planning_query(query_lower):
            query_type = QueryType.MEAL_PLANNING
            complexity, required_agents, estimated_time = self.flow_mappings[QueryType.MEAL_PLANNING]
        elif self._has_dietary_constraint(query_lower) and query_type == QueryType.RECOMMENDATION_REQUEST:
            # Upgrade to dietary filter if dietary constraints are mentioned
            query_type = QueryType.DIETARY_FILTER
            complexity, required_agents, estimated_time = self.flow_mappings[QueryType.DIETARY_FILTER]
        
        return QueryClassificationResult(
            query_type=query_type,
            complexity=complexity,
            required_agents=required_agents,
            estimated_time=estimated_time,
            confidence=confidence
        )
    
    def _calculate_pattern_score(self, query: str, patterns: Dict[str, List[str]]) -> float:
        """Calculate pattern matching score for a query type"""
        score = 0.0
        
        # Keyword matching
        for keyword in patterns["keywords"]:
            if keyword in query:
                score += 1.0
        
        # Regex pattern matching
        for pattern in patterns["patterns"]:
            if re.search(pattern, query, re.IGNORECASE):
                score += 2.0
        
        return score
    
    def _is_meal_planning_query(self, query: str) -> bool:
        """Check if query is specifically about meal planning"""
        meal_indicators = [
            r"plan.{0,20}(?:meal|menu|dinner|lunch)",
            r"(?:\d+).{0,10}(?:meal|recipe)",
            r"(?:weekly|daily).{0,10}(?:plan|menu)",
            r"(?:under|budget).{0,10}\$\d+"
        ]
        return any(re.search(pattern, query, re.IGNORECASE) for pattern in meal_indicators)
    
    def _has_dietary_constraint(self, query: str) -> bool:
        """Check if query mentions dietary constraints"""
        dietary_terms = ["low-carb", "keto", "vegan", "vegetarian", "gluten-free", "dairy-free", "sugar-free"]
        return any(term in query for term in dietary_terms)
    
    def get_flow_description(self, result: QueryClassificationResult) -> str:
        """Get human-readable flow description"""
        agent_names = [agent.value.replace('_', ' ').title() for agent in result.required_agents]
        flow_str = " → ".join(agent_names)
        
        return f"""
Query Type: {result.query_type.value.replace('_', ' ').title()}
Complexity: {result.complexity.value.title()}
Flow: {flow_str}
Agents: {len(result.required_agents)} total
Estimated Time: ~{result.estimated_time:.1f} seconds
Confidence: {result.confidence:.2f}
        """.strip()

# Convenience function for quick classification
def classify_user_query(query: str) -> QueryClassificationResult:
    """Quick classification function"""
    classifier = QueryClassifierAgent()
    return classifier.classify_query(query) 