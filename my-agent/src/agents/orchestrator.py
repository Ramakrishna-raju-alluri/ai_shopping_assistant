import os
import sys
from pathlib import Path
from dotenv import load_dotenv
from datetime import datetime
import logging

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s", datefmt="%Y-%m-%d %H:%M:%S")
logger = logging.getLogger("agentcore-memory")

# Add parent directory to path for imports when running directly
current_dir = Path(__file__).resolve().parent
parent_dir = current_dir.parent
project_root = parent_dir.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

load_dotenv()

from strands import Agent, tool
from strands.models import BedrockModel
from strands.agent.conversation_manager import SummarizingConversationManager
from strands.hooks import AgentInitializedEvent, HookProvider, HookRegistry, MessageAddedEvent

# Import AgentCore Memory for shared memory
try:
    from bedrock_agentcore.memory import MemoryClient
    # Temporarily disable shared memory for frontend testing
    MEMORY_AVAILABLE = False  # Set to True when ready to use shared memory
    print("🔧 Shared memory temporarily disabled for frontend testing")
except ImportError:
    print("AgentCore Memory not available, using conversation manager only")
    MEMORY_AVAILABLE = False

# Initialize shared memory if available
if MEMORY_AVAILABLE:
    memory_client = MemoryClient(region_name=os.getenv('AWS_DEFAULT_REGION', 'us-east-1'))
    memory_name = f"GroceryAssistant_STM_{datetime.now().strftime('%Y%m%d%H%M%S')}"
    memory_id = None
    try:
        memory = memory_client.create_memory_and_wait(
            name=memory_name,
            description="Grocery Assistant Shared Memory",
            strategies=[],
            event_expiry_days=7,  # Minimum allowed value is 7 days
            max_wait=300,
            poll_interval=10
        )
        memory_id = memory['id']
        print(f"✅ Shared memory created: {memory_id}")
    except Exception as e:
        print(f"⚠️ Memory creation failed: {e}")
        MEMORY_AVAILABLE = False

# Create unique actor IDs for each specialized agent but share the session ID
meal_planner_actor_id = f"meal-planner-user-{datetime.now().strftime('%Y%m%d%H%M%S')}"
grocery_list_actor_id = f"grocery-list-user-{datetime.now().strftime('%Y%m%d%H%M%S')}"
health_planner_actor_id = f"health-planner-user-{datetime.now().strftime('%Y%m%d%H%M%S')}"
simple_query_actor_id = f"simple-query-user-{datetime.now().strftime('%Y%m%d%H%M%S')}"
session_id = f"grocery-session-{datetime.now().strftime('%Y%m%d%H%M%S')}"
# Use Nova Pro model
MODEL_ID = "amazon.nova-pro-v1:0"

print(f"🔧 Session ID: {session_id}")
print(f"🔧 Meal Planner Actor ID: {meal_planner_actor_id}")
print(f"🔧 Grocery List Actor ID: {grocery_list_actor_id}")
print(f"🔧 Health Planner Actor ID: {health_planner_actor_id}")
print(f"🔧 Simple Query Actor ID: {simple_query_actor_id}")

# Import with flexible import system
try:
    from backend_bedrock.agents import meal_planner_agent, simple_query_agent, health_planner_agent, grocery_list_agent
except ImportError:
    try:
        from agents import meal_planner_agent, simple_query_agent, health_planner_agent, grocery_list_agent
    except ImportError:
        import meal_planner_agent
        import simple_query_agent
        import health_planner_agent
        import grocery_list_agent

# Import shared memory hook
try:
    from backend_bedrock.agents.shared_memory_hook import ShortTermMemoryHook
except ImportError:
    try:
        from agents.shared_memory_hook import ShortTermMemoryHook
    except ImportError:
        from shared_memory_hook import ShortTermMemoryHook

ORCHESTRATOR_PROMPT = """
You are an orchestrator agent that routes user requests to specialized agents based on the request type while maintaining shared context across all interactions.

ROUTING GUIDELINES:
- For meal planning, recipe creation, and food-related requests → use `meal_planner_wrapper`
- For nutrition tracking, calorie counting, daily meal logging, and health goals → use `health_planner_wrapper`  
- For product availability, stock checks, store information, and simple catalog queries → use `simple_query_wrapper`
- For grocery cart operations (add/remove items), shopping cart management, and grocery list building → use `grocery_list_wrapper`
- For general questions not requiring specialized tools, handle directly with your knowledge

SHARED CONTEXT AWARENESS:
- All agents share the same session memory, so they can reference previous interactions
- When routing to agents, include relevant context from the conversation
- Help users understand connections between different agent capabilities

If user's query requires multiple 'agents', use any combination of the above to answer.
Always pass the user_id and the complete user query to the selected agent.
"""

# Configure conversation manager for orchestrator
conversation_manager = SummarizingConversationManager(
    summary_ratio=0.3,
    preserve_recent_messages=5,
)

# Create wrapper functions that pass memory parameters to each agent
@tool
def meal_planner_wrapper(user_id: str, query: str) -> str:
    """Wrapper for meal planner agent with memory parameters"""
    if MEMORY_AVAILABLE:
        return meal_planner_agent.meal_planner_agent(
            user_id=user_id, 
            query=query,
            model_id=MODEL_ID,
            actor_id=meal_planner_actor_id,
            session_id=session_id,
            memory_client=memory_client,
            memory_id=memory_id
        )
    else:
        return meal_planner_agent.meal_planner_agent(user_id=user_id, query=query, model_id=MODEL_ID)

@tool
def grocery_list_wrapper(user_id: str, query: str) -> str:
    """Wrapper for grocery list agent with memory parameters"""
    print(f"🔍 GROCERY_LIST_WRAPPER called with user_id: {user_id}, query: {query[:50]}...")
    if MEMORY_AVAILABLE:
        return grocery_list_agent.grocery_list_agent(
            user_id=user_id, 
            query=query,
            model_id=MODEL_ID,
            actor_id=grocery_list_actor_id,
            session_id=session_id,
            memory_client=memory_client,
            memory_id=memory_id
        )
    else:
        return grocery_list_agent.grocery_list_agent(user_id=user_id, query=query, model_id=MODEL_ID)

@tool
def health_planner_wrapper(user_id: str, query: str) -> str:
    """Wrapper for health planner agent with memory parameters"""
    if MEMORY_AVAILABLE:
        return health_planner_agent.health_planner_agent(
            user_id=user_id, 
            query=query,
            model_id=MODEL_ID,
            actor_id=health_planner_actor_id,
            session_id=session_id,
            memory_client=memory_client,
            memory_id=memory_id
        )
    else:
        return health_planner_agent.health_planner_agent(user_id=user_id, query=query, model_id=MODEL_ID)

@tool
def simple_query_wrapper(user_id: str, query: str) -> str:
    """Wrapper for simple query agent with memory parameters"""
    if MEMORY_AVAILABLE:
        return simple_query_agent.simple_query_agent(
            user_id=user_id, 
            query=query,
            model_id=MODEL_ID,
            actor_id=simple_query_actor_id,
            session_id=session_id,
            memory_client=memory_client,
            memory_id=memory_id
        )
    else:
        return simple_query_agent.simple_query_agent(user_id=user_id, query=query, model_id=MODEL_ID)

# Create orchestrator with shared memory if available
if MEMORY_AVAILABLE:
    shared_memory_hooks = ShortTermMemoryHook(memory_client, memory_id)
    orchestrator_agent = Agent(
        system_prompt=ORCHESTRATOR_PROMPT,
        model=MODEL_ID,
        tools=[
            meal_planner_wrapper,
            health_planner_wrapper,
            simple_query_wrapper,
            grocery_list_wrapper
        ],
        conversation_manager=conversation_manager,
        hooks=[shared_memory_hooks],
        state={"actor_id": "orchestrator", "session_id": session_id}
    )
else:
    # Fallback without shared memory
    orchestrator_agent = Agent(
        system_prompt=ORCHESTRATOR_PROMPT,
        model=MODEL_ID,
        tools=[
            meal_planner_wrapper,
            health_planner_wrapper,
            simple_query_wrapper,
            grocery_list_wrapper
        ],
        conversation_manager=conversation_manager,
    )

print("🚀 Multi-Agent System with Shared Memory is ready!")
print(f"📝 Memory Available: {MEMORY_AVAILABLE}")
if MEMORY_AVAILABLE:
    print(f"🧠 Memory ID: {memory_id}")
print("🔧 All agents configured with unique actor IDs and shared session ID")