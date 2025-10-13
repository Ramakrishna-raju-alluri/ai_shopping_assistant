from fastapi import APIRouter, HTTPException, BackgroundTasks, Depends
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime
import asyncio
from decimal import Decimal
import json

# Import our agent components
from agents.intent_agent import extract_intent
from agents.preference_agent import get_or_create_user_profile, get_user_profile, create_user_profile
from agents.meal_planner_agent import plan_meals, get_product_recommendations
from agents.basket_builder_agent import build_basket
from agents.stock_checker_agent import check_stock_and_promos
from agents.feedback_agent import learn_from_feedback
from agents.general_query_agent import process_conversation, handle_general_query

# Import authentication
from routes.auth import get_current_user

# Import chat history service
from services.chat_history_service import chat_history_service
from services.cart_service import cart_service

router = APIRouter()

# In-memory session storage (in production, use Redis or database)
user_sessions = {}

# Pydantic models for request/response
class ChatMessage(BaseModel):
    message: str = Field(..., description="User's message/query")
    session_id: Optional[str] = Field(None, description="Session identifier for multi-turn conversations")

class ChatResponse(BaseModel):
    session_id: str
    message: str
    step: str
    step_number: int
    requires_confirmation: bool
    confirmation_prompt: Optional[str] = None
    data: Optional[Dict[str, Any]] = None
    is_complete: bool = False
    next_step: Optional[str] = None
    requires_input: bool = False
    input_prompt: Optional[str] = None
    input_options: Optional[List[str]] = None
    input_type: Optional[str] = None
    query_type: Optional[str] = None
    classification: Optional[str] = None
    assistant_message: str = ""
    feedback_step: Optional[str] = None

class ConfirmationRequest(BaseModel):
    session_id: str
    confirmed: bool
    feedback_data: Optional[Dict[str, Any]] = None

class FeedbackRequest(BaseModel):
    session_id: str
    overall_satisfaction: Optional[int] = Field(None, ge=1, le=5)
    liked_items: Optional[List[str]] = None
    disliked_items: Optional[List[str]] = None
    suggestions: Optional[str] = None
    will_purchase: Optional[bool] = None

class SessionState(BaseModel):
    user_id: str
    current_step: str
    step_number: int
    message: Optional[str] = None  # Add message field
    intent: Optional[Dict[str, Any]] = None
    user_profile: Optional[Dict[str, Any]] = None
    recipes: Optional[List[Dict[str, Any]]] = None
    cart: Optional[List[Dict[str, Any]]] = None
    final_cart: Optional[List[Dict[str, Any]]] = None
    product_recommendations: Optional[Dict[str, Any]] = None
    general_response: Optional[Dict[str, Any]] = None
    query_type: Optional[str] = None
    classification: Optional[str] = None
    feedback: Dict[str, Any] = {}
    created_at: datetime
    last_updated: datetime
    # Onboarding fields
    onboarding_step: Optional[str] = None
    onboarding_data: Dict[str, Any] = {}
    is_new_user: bool = False

def create_session_id(user_id: str) -> str:
    """Create a unique session ID"""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    return f"{user_id}_{timestamp}"

def get_session(session_id: str) -> Optional[SessionState]:
    """Get session by ID"""
    return user_sessions.get(session_id)

def save_session(session_id: str, session: SessionState):
    """Save session to memory"""
    user_sessions[session_id] = session

def update_session(session_id: str, **kwargs):
    """Update session with new data"""
    if session_id in user_sessions:
        session = user_sessions[session_id]
        old_step = session.current_step
        for key, value in kwargs.items():
            if hasattr(session, key) and key not in ['created_at', 'last_updated']:
                setattr(session, key, value)
        session.last_updated = datetime.now()
        user_sessions[session_id] = session
        
        # Debug logging for step changes
        if 'current_step' in kwargs and kwargs['current_step'] != old_step:
            print(f"🔄 Session step updated: {old_step} → {kwargs['current_step']} (Session: {session_id})")

def save_assistant_message_to_history(user_id: str, chat_session_id: str, response: ChatResponse):
    """Helper function to save assistant messages to DynamoDB chat history"""
    try:
        if not chat_session_id:
            print("❌ No chat_session_id provided for assistant message")
            return False
            
        if not user_id:
            print("❌ No user_id provided for assistant message")
            return False
            
        print(f"🔄 Saving assistant message to DynamoDB session: {chat_session_id}")
        
        # Use assistant_message field if available, otherwise fall back to message
        message_content = response.assistant_message if response.assistant_message else response.message
        
        assistant_message_data = {
            "type": "assistant",
            "content": message_content,
            "assistant_message": response.assistant_message,  # Ensure assistant_message is saved
            "timestamp": datetime.now().isoformat(),
            "id": f"msg_assistant_{int(datetime.now().timestamp())}",
            "step": response.step,
            "step_number": response.step_number,
            "requires_confirmation": response.requires_confirmation,
            "confirmation_prompt": response.confirmation_prompt,
            "requires_input": response.requires_input,
            "input_prompt": response.input_prompt,
            "input_type": response.input_type,
            "input_options": response.input_options,
            "data": response.data,
            "is_complete": response.is_complete,
            "query_type": response.query_type,
            "classification": response.classification,
            "feedback_step": response.feedback_step,  # Persist feedback step
        }
        
        print(f"🔍 Debug - Assistant message content: {message_content[:100]}...")
        print(f"🔍 Debug - Assistant message type: {assistant_message_data['type']}")
        
        # Remove None values to keep the data clean
        assistant_message_data = {k: v for k, v in assistant_message_data.items() if v is not None}
        
        success = chat_history_service.add_message_to_session(
            user_id=user_id,
            session_id=chat_session_id,
            message=assistant_message_data
        )
        
        if success:
            print(f"✅ Saved assistant message to chat history: {chat_session_id}")
            return True
        else:
            print(f"❌ Failed to save assistant message (returned False): {chat_session_id}")
            return False
        
    except Exception as e:
        print(f"❌ Error saving assistant message to chat history: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

def save_and_return_response(user_id: str, chat_session_id: str, response: ChatResponse) -> ChatResponse:
    """Helper function to save assistant message and return the response"""
    print(f"🔄 save_and_return_response - Step: {response.step}, Session: {chat_session_id}")
    save_assistant_message_to_history(user_id, chat_session_id, response)
    return response

@router.post("/chat", response_model=ChatResponse)
async def chat_endpoint(chat_message: ChatMessage, current_user: dict = Depends(get_current_user)):
    """
    Main conversation endpoint that handles all types of queries
    Requires authentication
    """
    try:
        # Use authenticated user's ID instead of the one in the message
        user_id = current_user["user_id"]
        message = chat_message.message
        
        # Create or get session - IMPROVED SESSION MANAGEMENT
        chat_session_id = None  # For DynamoDB storage
        
        if chat_message.session_id:
            session = get_session(chat_message.session_id)
            if not session:
                raise HTTPException(status_code=404, detail="Session not found")
            
            print(f"🔍 Chat endpoint - Session step: {session.current_step}, Message: {message[:50]}...")
            
            # Check if the session is in a feedback step and route accordingly
            if session.current_step and session.current_step.startswith('feedback_'):
                print(f"🎯 Feedback Debug - Session in feedback step: {session.current_step}")
                print(f"🎯 Feedback Debug - User input: {message}")
                print(f"🎯 Feedback Debug - Session ID: {chat_message.session_id}")
                print(f"🎯 Feedback Debug - User ID: {user_id}")
                
                # Route to the appropriate feedback endpoint
                if session.current_step == 'feedback_rating':
                    try:
                        rating = int(message)
                        if 1 <= rating <= 5:
                            print(f"🎯 Feedback Debug - Valid rating received: {rating}")
                            return await submit_feedback_rating(FeedbackRequest(session_id=chat_message.session_id, overall_satisfaction=rating), current_user)
                        else:
                            # Invalid rating, send error message but stay in feedback step
                            error_response = ChatResponse(
                                session_id=chat_message.session_id,
                                message="Please provide a rating between 1 and 5.",
                                step=session.current_step,
                                step_number=session.step_number,
                                requires_confirmation=False,
                                requires_input=True,
                                input_type="number",
                                input_prompt="Please rate your satisfaction (1-5):",
                                is_complete=False,
                                assistant_message="Please provide a valid rating between 1 and 5."
                            )
                            return save_and_return_response(user_id, chat_message.session_id, error_response)
                    except ValueError:
                        # Invalid input (not a number), send error message but stay in feedback step
                        error_response = ChatResponse(
                            session_id=chat_message.session_id,
                            message="Please provide a valid number between 1 and 5.",
                            step=session.current_step,
                            step_number=session.step_number,
                            requires_confirmation=False,
                            requires_input=True,
                            input_type="number",
                            input_prompt="Please rate your satisfaction (1-5):",
                            is_complete=False,
                            assistant_message="Please provide a valid number between 1 and 5."
                        )
                        return save_and_return_response(user_id, chat_message.session_id, error_response)
                        
                elif session.current_step == 'feedback_liked_items':
                    try:
                        liked_items = message.split(',') if message.lower() != 'none' else []
                        print(f"🎯 Feedback Debug - Liked items received: {liked_items}")
                        return await submit_liked_items(FeedbackRequest(session_id=chat_message.session_id, liked_items=liked_items), current_user)
                    except Exception as e:
                        # Handle any errors in liked items processing
                        error_response = ChatResponse(
                            session_id=chat_message.session_id,
                            message="Please provide the items you liked, separated by commas, or type 'none'.",
                            step=session.current_step,
                            step_number=session.step_number,
                            requires_confirmation=False,
                            requires_input=True,
                            input_type="text",
                            input_prompt="Which items did you like? (comma-separated, or 'none'):",
                            is_complete=False,
                            assistant_message="Please provide the items you liked, separated by commas, or type 'none'."
                        )
                        return save_and_return_response(user_id, chat_message.session_id, error_response)
                    
                elif session.current_step == 'feedback_disliked_items':
                    try:
                        disliked_items = message.split(',') if message.lower() != 'none' else []
                        print(f"🎯 Feedback Debug - Disliked items received: {disliked_items}")
                        return await submit_disliked_items(FeedbackRequest(session_id=chat_message.session_id, disliked_items=disliked_items), current_user)
                    except Exception as e:
                        # Handle any errors in disliked items processing
                        error_response = ChatResponse(
                            session_id=chat_message.session_id,
                            message="Please provide the items you disliked, separated by commas, or type 'none'.",
                            step=session.current_step,
                            step_number=session.step_number,
                            requires_confirmation=False,
                            requires_input=True,
                            input_type="text",
                            input_prompt="Which items did you dislike? (comma-separated, or 'none'):",
                            is_complete=False,
                            assistant_message="Please provide the items you disliked, separated by commas, or type 'none'."
                        )
                        return save_and_return_response(user_id, chat_message.session_id, error_response)
                    
                elif session.current_step == 'feedback_suggestions':
                    try:
                        return await submit_suggestions(FeedbackRequest(session_id=chat_message.session_id, suggestions=message), current_user)
                    except Exception as e:
                        # Handle any errors in suggestions processing
                        error_response = ChatResponse(
                            session_id=chat_message.session_id,
                            message="Please provide your suggestions or press Enter to skip.",
                            step=session.current_step,
                            step_number=session.step_number,
                            requires_confirmation=False,
                            requires_input=True,
                            input_type="text",
                            input_prompt="Do you have any suggestions for improving our recommendations? (Press Enter to skip):",
                            is_complete=False,
                            assistant_message="Please provide your suggestions or press Enter to skip."
                        )
                        return save_and_return_response(user_id, chat_message.session_id, error_response)
                    
                elif session.current_step == 'feedback_purchase':
                    try:
                        will_purchase = message.lower() in ['yes', 'y', 'true', '1']
                        return await submit_purchase_intent(FeedbackRequest(session_id=chat_message.session_id, will_purchase=will_purchase), current_user)
                    except Exception as e:
                        # Handle any errors in purchase intent processing
                        error_response = ChatResponse(
                            session_id=chat_message.session_id,
                            message="Please answer with 'yes' or 'no'.",
                            step=session.current_step,
                            step_number=session.step_number,
                            requires_confirmation=False,
                            requires_input=True,
                            input_type="text",
                            input_prompt="Will you purchase these items? (yes/no):",
                            is_complete=False,
                            assistant_message="Please answer with 'yes' or 'no'."
                        )
                        return save_and_return_response(user_id, chat_message.session_id, error_response)
                
                # If we reach here, it means we're in a feedback step but the step wasn't handled above
                # This should not happen, but if it does, return an error response
                error_response = ChatResponse(
                    session_id=chat_message.session_id,
                    message="I'm sorry, there was an issue with the feedback collection. Please try again.",
                    step=session.current_step,
                    step_number=session.step_number,
                    requires_confirmation=False,
                    requires_input=True,
                    input_type="text",
                    input_prompt="Please try again:",
                    is_complete=False,
                    assistant_message="I'm sorry, there was an issue with the feedback collection. Please try again."
                )
                return save_and_return_response(user_id, chat_message.session_id, error_response)
            
            # 🔧 CRITICAL FIX: Update session with new message
            session.message = message
            session.last_updated = datetime.now()
            # Clear previous intent/classification for fresh processing
            session.intent = None
            session.query_type = None
            session.classification = None
            save_session(chat_message.session_id, session)
            
            session_id = chat_message.session_id
            # Use the session_id directly as chat_session_id for consistency
            chat_session_id = session_id
        else:
            # Create new session and corresponding DynamoDB session
            session_id = create_session_id(user_id)
            chat_session_id = session_id  # Use same ID for consistency
            
            # Create in-memory session first
            session = SessionState(
                user_id=user_id,
                message=message,
                current_step="conversation_start",
                step_number=1,
                feedback={},
                created_at=datetime.now(),
                last_updated=datetime.now()
            )
            save_session(session_id, session)
            
            # Create DynamoDB chat session with the same session_id
            try:
                # Generate a clean title from the message
                title = message[:50].strip()
                if len(message) > 50:
                    title += "..."
                
                print(f"🔄 Creating DynamoDB session with ID: {session_id}")
                chat_session_data = chat_history_service.create_chat_session(
                    user_id=user_id,
                    title=title,
                    session_id=session_id
                )
                print(f"✅ Created DynamoDB chat session: {session_id}")
            except Exception as e:
                print(f"❌ Failed to create DynamoDB chat session: {str(e)}")
                import traceback
                traceback.print_exc()
                # Continue anyway - don't block the chat
        
        # Save user message to DynamoDB chat history
        try:
            print(f"🔄 Saving user message to DynamoDB session: {chat_session_id}")
            user_message_data = {
                "type": "user",
                "content": message,
                "session_id": session_id,
                "timestamp": datetime.now().isoformat(),
                "id": f"msg_{int(datetime.now().timestamp())}"
            }
            
            success = chat_history_service.add_message_to_session(
                user_id=user_id,
                session_id=chat_session_id,
                message=user_message_data
            )
            
            if success:
                print(f"✅ Saved user message to chat history: {chat_session_id}")
            else:
                print(f"⚠️ Failed to save user message (returned False): {chat_session_id}")
        except Exception as e:
            print(f"❌ Error saving user message to chat history: {str(e)}")
            import traceback
            traceback.print_exc()
        
        # Process the message using conversation agent
        conv_result = process_conversation(message)
        classification = conv_result['classification']
        query_type = conv_result.get('query_type', 'general_query')
        response = conv_result['response']
        
        # Update session with conversation results
        update_session(
            session_id,
            classification=classification,
            query_type=query_type,
            current_step="conversation_processed",
            step_number=2
        )
        
        # Handle different query types
        if classification == "GOAL" and query_type != "general_query":
            # Goal-based queries (meal planning, product recommendations, dietary filtering)
            response_obj = await handle_goal_based_query(session_id, session, message, query_type, response)
        else:
            # Casual queries or general queries
            response_obj = await handle_casual_query(session_id, session, message, query_type, response)
        
        # Save assistant response to chat history
        return save_and_return_response(user_id, chat_session_id, response_obj)
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error processing chat: {str(e)}")

async def handle_goal_based_query(session_id: str, session: SessionState, message: str, query_type: str, response: str) -> ChatResponse:
    """Handle goal-based queries (meal planning, product recommendations, dietary filtering)"""
    
    # Show appropriate confirmation message based on query type
    if query_type == "meal_planning":
        confirmation_prompt = "Should I proceed with detailed meal planning?"
    elif query_type in ["product_recommendation", "dietary_filter"]:
        confirmation_prompt = "Should I build products for your cart?"
    else:
        confirmation_prompt = "Should I proceed with detailed shopping assistance?"
    
    return ChatResponse(
        session_id=session_id,
        message=message,
        step="goal_confirmation",
        step_number=session.step_number,
        requires_confirmation=True,
        confirmation_prompt=confirmation_prompt,
        data={
            "query_type": query_type,
            "classification": session.classification,
            "response": response
        },
        is_complete=False,
        next_step="intent_extraction",
        query_type=query_type,
        classification=session.classification,
        assistant_message="I'll help you with detailed meal planning and shopping!"
    )

async def handle_casual_query(session_id: str, session: SessionState, message: str, query_type: str, response: str) -> ChatResponse:
    """Handle casual queries and general queries"""
    
    # Check if this is a cart operation first
    cart_keywords = ["add", "put", "place", "cart", "basket", "view cart", "show cart"]
    if any(keyword in message.lower() for keyword in cart_keywords):
        print(f"🛒 Cart Operation detected in casual query: {message}")
        return await handle_cart_operation(session_id, session, None)
    
    # Always try the product lookup agent first for any query that might be about products
    # This ensures we don't miss any products in our database
    
    # Check if this query might be about a product (contains product-related terms)
    product_indicators = [
        'price', 'cost', 'how much', 'available', 'have', 'stock', 'carry', 
        'organic', 'cheese', 'milk', 'bread', 'eggs', 'fruit', 'vegetable',
        'meat', 'fish', 'grain', 'pasta', 'sauce', 'oil', 'spice', 'herb'
    ]
    
    might_be_product_query = any(indicator in message.lower() for indicator in product_indicators)
    
    if might_be_product_query:
        # Try the product lookup agent first
        from agents.product_lookup_agent import handle_product_query
        result = handle_product_query(message)
        
        if result["success"]:
            # Product found in database - return accurate information
            return ChatResponse(
                session_id=session_id,
                message=message,
                step="product_lookup_complete",
                step_number=session.step_number + 1,
                requires_confirmation=False,
                data={
                    "product_lookup": True,
                    "product_info": result.get("product_info"),
                    "product_name": result.get("product_name")
                },
                is_complete=True,
                assistant_message=result["message"]
            )
        else:
            # Product not found in database - fall back to LLM for general response
            print(f"🔍 Product lookup failed for: {message} - falling back to LLM")
    
    # For other general queries, offer additional help
    additional_help = False
    if query_type == "general_query" and any(keyword in message.lower() for keyword in ['recipe', 'history', 'promotion', 'delivery']):
        additional_help = True
    
    # Update session with the new step
    update_session(
        session_id,
        current_step="casual_response",
        step_number=session.step_number
    )
    
    return ChatResponse(
        session_id=session_id,
        message=message,
        step="casual_response",
        step_number=session.step_number,
        requires_confirmation=additional_help,
        confirmation_prompt="Should I search our database for more specific information?" if additional_help else None,
        data={
            "query_type": query_type,
            "classification": session.classification,
            "response": response
        },
        is_complete=not additional_help,
        next_step="general_query_search" if additional_help else None,
        query_type=query_type,
        classification=session.classification,
        assistant_message=response
    )

@router.post("/confirm", response_model=ChatResponse)
async def confirm_step(confirmation: ConfirmationRequest, current_user: dict = Depends(get_current_user)):
    """Handle user confirmations and proceed to next step"""
    try:
        print(f"🔍 Backend Debug - confirm_step called for session {confirmation.session_id}")
        
        # Get user_id and chat_session_id for history saving
        user_id = current_user["user_id"]
        chat_session_id = confirmation.session_id
        
        # Verify the user owns this session
        session = get_session(confirmation.session_id)
        if not session:
            raise HTTPException(status_code=404, detail="Session not found")
        if session.user_id != current_user["user_id"]:
            raise HTTPException(status_code=403, detail="Access denied to this session")
        
        print(f"🔍 Backend Debug - Current session step: {session.current_step}")
        print(f"🔍 Backend Debug - User confirmed: {confirmation.confirmed}")
        
        # Save user confirmation to chat history
        try:
            user_confirmation_data = {
                "type": "user",
                "content": "✅ Yes" if confirmation.confirmed else "❌ No",
                "session_id": confirmation.session_id,
                "timestamp": datetime.now().isoformat(),
                "id": f"msg_confirm_{int(datetime.now().timestamp())}"
            }
            
            success = chat_history_service.add_message_to_session(
                user_id=user_id,
                session_id=chat_session_id,
                message=user_confirmation_data
            )
            print(f"✅ Saved user confirmation to chat history: {success}")
        except Exception as e:
            print(f"❌ Failed to save user confirmation: {str(e)}")
        
        if not confirmation.confirmed:
            # User declined - end session
            response_obj = ChatResponse(
                session_id=confirmation.session_id,
                message="User declined",
                step="declined",
                step_number=session.step_number,
                requires_confirmation=False,
                is_complete=True,
                assistant_message="No problem! Feel free to ask me anything else."
            )
            return save_and_return_response(user_id, chat_session_id, response_obj)
        else:
            # User confirmed - process next step and save the response
            next_step_response = await process_next_step(confirmation.session_id, session, confirmation, current_user)
            return save_and_return_response(user_id, chat_session_id, next_step_response)
            
    except Exception as e:
        print(f"🔍 Backend Debug - Error in confirm_step: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error processing confirmation: {str(e)}")

async def process_next_step(session_id: str, session: SessionState, confirmation: ConfirmationRequest, current_user: dict) -> ChatResponse:
    """Process the next step after a user confirmation"""
    print(f"🔍 Backend Debug - Processing next step for session {session_id}, current_step: {session.current_step}")
    
    if session.current_step == "intent_confirmation" or session.current_step == "intent_extracted":
        print(f"🔍 Backend Debug - Processing intent confirmation")
        query_type = session.query_type
        if query_type == "product_lookup":
            return await handle_general_query_search(session_id, session)
        elif query_type == "cart_operation":
            return await handle_cart_operation(session_id, session, current_user)
        elif query_type == "meal_planning":
            return await handle_meal_planning_flow(session_id, session)
        elif query_type == "basket_builder":
            return await handle_direct_basket_builder(session_id, session)
        elif query_type in ["product_recommendation", "dietary_filter"]:
            return await handle_product_recommendation_flow(session_id, session)
        else:
            return await handle_meal_planning_flow(session_id, session)
    elif session.current_step == "goal_confirmation":
        print(f"🔍 Backend Debug - Processing goal confirmation")
        return await handle_intent_extraction(session_id, session)
    elif session.current_step == "recipes_ready":
        print(f"🔍 Backend Debug - Processing recipes ready")
        return await handle_basket_building(session_id, session)
    elif session.current_step == "products_ready":
        print(f"🔍 Backend Debug - Processing products ready")
        return await handle_basket_building(session_id, session)
    elif session.current_step == "cart_ready":
        print(f"🔍 Backend Debug - Processing cart ready")
        return await handle_stock_checking_and_feedback(session_id, session)
    elif session.current_step == "final_cart_ready":
        print(f"🔍 Backend Debug - Processing final cart ready")
        return await handle_cart_action_selection(session_id, session, confirmation)
    elif session.current_step == "casual_response":
        print(f"🔍 Backend Debug - Processing casual_response confirmation for session {session_id}")
        update_session(
            session_id,
            current_step="general_query_search",
            step_number=session.step_number + 1
        )
        return await handle_general_query_search(session_id, session)
    elif session.current_step == "general_query_search":
        print(f"🔍 Backend Debug - Processing general_query_search")
        return await handle_general_query_search(session_id, session)
    else:
        print(f"🔍 Backend Debug - Default case, processing intent extraction")
        return await handle_intent_extraction(session_id, session)

async def handle_general_query_search(session_id: str, session: SessionState) -> ChatResponse:
    """Handle general query search with database lookup"""
    try:
        print(f"🔍 Backend Debug - handle_general_query_search called for session {session_id}")
        print(f"🔍 Backend Debug - Original message: {session.message}")
        
        # Check if this is a product-specific query (price, availability, etc.)
        original_message = session.message.lower()
        print(f"🔍 Backend Debug - Checking for product query keywords in: {original_message}")
        
        # Check for product-specific query patterns
        product_query_keywords = [
            "cost of", "price of", "how much does", "what is the price of",
            "do you have", "is there", "available", "in stock", "carry"
        ]
        
        if any(keyword in original_message for keyword in product_query_keywords):
            print(f"🔍 Backend Debug - Found product query keywords, using product lookup agent")
            
            # Use the new product lookup agent
            from agents.product_lookup_agent import handle_product_query
            result = handle_product_query(session.message)
            
            if result["success"]:
                print(f"🔍 Backend Debug - Product lookup successful")
                return ChatResponse(
                    session_id=session_id,
                    message=session.message,
                    step="product_lookup_complete",
                    step_number=session.step_number + 1,
                    requires_confirmation=False,
                    data={
                        "product_lookup": True,
                        "product_info": result.get("product_info"),
                        "product_name": result.get("product_name")
                    },
                    is_complete=True,
                    assistant_message=result["message"]
                )
            else:
                print(f"🔍 Backend Debug - Product lookup failed: {result['message']}")
                return ChatResponse(
                    session_id=session_id,
                    message=session.message,
                    step="product_lookup_failed",
                    step_number=session.step_number + 1,
                    requires_confirmation=False,
                    data={"product_lookup": False},
                    is_complete=True,
                    assistant_message=result["message"]
                )
        
        # Check if this is a cart operation (add to cart, view cart, etc.)
        cart_keywords = ["add", "put", "place", "cart", "basket", "view cart", "show cart"]
        if any(keyword in original_message for keyword in cart_keywords):
            print(f"🔍 Backend Debug - Found cart keywords, using cart operation agent")
            return await handle_cart_operation(session_id, session, None)  # current_user will be passed from the calling function
        
        # Default to general query processing
        print(f"🔍 Backend Debug - No specific keywords found, using general query agent")
        response = await handle_general_query(session_id, session)
        
        return response
        
    except Exception as e:
        print(f"🔍 Backend Debug - Error in handle_general_query_search: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error processing general query search: {str(e)}")

async def handle_cart_operation(session_id: str, session: SessionState, current_user: dict) -> ChatResponse:
    """Handle cart operations (add to cart, view cart, etc.)"""
    try:
        print(f"🛒 Cart Operation - Processing cart request: {session.message}")
        
        # Import cart operation agent
        from agents.cart_operation_agent import handle_cart_operation as cart_op_handler, handle_view_cart
        
        user_id = session.user_id
        
        # Check if this is a view cart request
        message_lower = session.message.lower()
        if any(keyword in message_lower for keyword in ["view cart", "show cart", "my cart", "see cart"]):
            result = handle_view_cart(user_id)
        else:
            # Handle cart operation request (add/delete/etc.) and pass intent
            result = cart_op_handler(session.message, user_id, session.intent)
        
        if result["success"]:
            return ChatResponse(
                session_id=session_id,
                message=session.message,
                step="cart_operation_complete",
                step_number=session.step_number + 1,
                requires_confirmation=False,
                data={
                    "cart_operation": True,
                    "cart_info": result.get("cart_info"),
                    "product_info": result.get("product_info"),
                    "quantity": result.get("quantity")
                },
                is_complete=True,
                assistant_message=result["message"]
            )
        else:
            return ChatResponse(
                session_id=session_id,
                message=session.message,
                step="cart_operation_failed",
                step_number=session.step_number + 1,
                requires_confirmation=False,
                data={"cart_operation": False},
                is_complete=True,
                assistant_message=result["message"]
            )
            
    except Exception as e:
        print(f"🛒 Cart Operation - Error: {str(e)}")
        return ChatResponse(
            session_id=session_id,
            message=session.message,
            step="cart_operation_error",
            step_number=session.step_number + 1,
            requires_confirmation=False,
            data={"cart_operation": False},
            is_complete=True,
            assistant_message=f"Sorry, I encountered an error while processing your cart request. Please try again."
        )

async def handle_intent_extraction(session_id: str, session: SessionState) -> ChatResponse:
    """Handle intent extraction step"""
    try:
        # Extract intent from the original message
        intent = extract_intent(session.message)
        query_type = intent.get("query_type", "meal_planning")
        
        # Check if this is a product-specific query that should go directly to product lookup
        original_message = session.message.lower()
        product_query_keywords = [
            "cost of", "price of", "how much does", "what is the price of",
            "do you have", "is there", "available", "in stock", "carry"
        ]
        
        if any(keyword in original_message for keyword in product_query_keywords):
            print(f"🔍 Backend Debug - Detected product query, routing to product lookup")
            query_type = "product_lookup"
        
        # Check if this is a product-specific query that should go directly to product lookup
        original_message = session.message.lower()
        product_query_keywords = [
            "cost of", "price of", "how much does", "what is the price of",
            "do you have", "is there", "available", "in stock", "carry"
        ]
        
        if any(keyword in original_message for keyword in product_query_keywords):
            print(f"🔍 Backend Debug - Detected product query, routing to product lookup")
            query_type = "product_lookup"
        
        # Update session
        update_session(
            session_id,
            intent=intent,
            query_type=query_type,
            current_step="intent_extracted",
            step_number=3
        )
        
        # Show intent confirmation
        intent_summary = f"Query type: {query_type}"
        if intent.get("number_of_meals"):
            intent_summary += f", Meals: {intent['number_of_meals']}"
        if intent.get("budget"):
            intent_summary += f", Budget: ${intent['budget']}"
        if intent.get("dietary_preference"):
            intent_summary += f", Diet: {intent['dietary_preference']}"
        
        return ChatResponse(
            session_id=session_id,
            message=session.message,
            step="intent_confirmation",
            step_number=3,
            requires_confirmation=True,
            confirmation_prompt="Does this look correct? Should I proceed?",
            data={
                "intent": intent,
                "intent_summary": intent_summary
            },
            is_complete=False,
            next_step="profile_loading",
            query_type=query_type,
            assistant_message=f"✅ Extracted intent: {intent_summary}"
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error extracting intent: {str(e)}")

async def handle_meal_planning_flow(session_id: str, session: SessionState) -> ChatResponse:
    """Handle meal planning flow"""
    try:
        # Load user profile
        user_profile = get_or_create_user_profile(session.user_id, session.intent)
        
        # Update session
        update_session(
            session_id,
            user_profile=user_profile,
            current_step="profile_loaded",
            step_number=4
        )
        
        # Plan meals
        recipes = plan_meals(user_profile)
        
        # Update session
        update_session(
            session_id,
            recipes=recipes,
            current_step="recipes_ready",
            step_number=5
        )
        
        if not recipes:
            return ChatResponse(
                session_id=session_id,
                message=session.message,
                step="no_recipes",
                step_number=5,
                requires_confirmation=False,
                is_complete=True,
                assistant_message="❌ No recipes found within your budget and dietary preferences. Try increasing your budget or being more flexible with dietary restrictions."
            )
        
        # Show recipes and ask for confirmation
        recipe_summary = f"Found {len(recipes)} recipes:"
        total_cost = sum(Decimal(str(recipe.get('total_cost', 0))) for recipe in recipes)
        for i, recipe in enumerate(recipes, 1):
            cost = recipe.get('total_cost', 0)
            recipe_summary += f"\n{i}. {recipe.get('title')} - ${cost}"
        recipe_summary += f"\nTotal cost: ${total_cost}"
        
        return ChatResponse(
            session_id=session_id,
            message=session.message,
            step="recipes_ready",
            step_number=5,
            requires_confirmation=True,
            confirmation_prompt="Do you want to proceed with building your shopping cart?",
            data={
                "recipes": recipes,
                "recipe_summary": recipe_summary,
                "total_cost": str(total_cost)
            },
            is_complete=False,
            next_step="basket_building",
            query_type="meal_planning",
            assistant_message=recipe_summary
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error in meal planning: {str(e)}")

async def handle_product_recommendation_flow(session_id: str, session: SessionState) -> ChatResponse:
    """Handle product recommendation flow"""
    try:
        # Load user profile
        user_profile = get_or_create_user_profile(session.user_id, session.intent)
        
        # Get product recommendations
        recommendations = get_product_recommendations(session.intent, user_profile)
        
        # Update session
        update_session(
            session_id,
            user_profile=user_profile,
            product_recommendations=recommendations,
            current_step="products_ready",
            step_number=4
        )
        
        # Show products and ask for confirmation
        products = recommendations.get("products", [])
        if not products:
            return ChatResponse(
                session_id=session_id,
                message=session.message,
                step="no_products",
                step_number=4,
                requires_confirmation=False,
                is_complete=True,
                assistant_message="❌ No products found matching your criteria. Try adjusting your preferences."
            )
        
        product_summary = f"Found {len(products)} products:"
        total_cost = sum(Decimal(str(product.get('price', 0))) for product in products)
        for i, product in enumerate(products, 1):
            price = product.get('price', 0)
            tags = product.get('tags', [])
            tag_text = f" [{', '.join(tags[:2])}]" if tags else ""
            product_summary += f"\n{i}. {product.get('name')} - ${price}{tag_text}"
        product_summary += f"\nTotal cost: ${total_cost}"
        
        return ChatResponse(
            session_id=session_id,
            message=session.message,
            step="products_ready",
            step_number=4,
            requires_confirmation=True,
            confirmation_prompt="Do you want to proceed with building your shopping cart from these products?",
            data={
                "products": products,
                "product_summary": product_summary,
                "total_cost": str(total_cost)
            },
            is_complete=False,
            next_step="basket_building",
            query_type=session.query_type,
            assistant_message=product_summary
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error in product recommendation: {str(e)}")

async def handle_basket_building(session_id: str, session: SessionState) -> ChatResponse:
    """Handle basket building step"""
    try:
        # Build cart based on query type
        if session.query_type == "meal_planning":
            # Build cart from recipes
            budget_limit = session.user_profile.get("budget_limit") if session.user_profile else None
            cart = build_basket(session.recipes, budget_limit)
        else:
            # Use products directly for product recommendations
            cart = session.product_recommendations.get("products", [])
        
        # Update session
        update_session(
            session_id,
            cart=cart,
            current_step="cart_ready",
            step_number=6
        )
        
        if not cart:
            return ChatResponse(
                session_id=session_id,
                message=session.message,
                step="no_cart_items",
                step_number=6,
                requires_confirmation=False,
                is_complete=True,
                assistant_message="❌ No products found for your selection."
            )
        
        # Show cart and ask for stock checking
        cart_summary = f"Added {len(cart)} products to your cart:"
        total_cost = sum(Decimal(str(item.get('price', 0))) for item in cart)
        for i, item in enumerate(cart, 1):
            price = item.get('price', 0)
            cart_summary += f"\n{i}. {item.get('name')} - ${price}"
        cart_summary += f"\nTotal cost: ${total_cost}"
        
        return ChatResponse(
            session_id=session_id,
            message=session.message,
            step="cart_ready",
            step_number=6,
            requires_confirmation=True,
            confirmation_prompt="Should I check stock availability and apply promotions?",
            data={
                "cart": cart,
                "cart_summary": cart_summary,
                "total_cost": str(total_cost)
            },
            is_complete=False,
            next_step="stock_checking",
            query_type=session.query_type,
            assistant_message=cart_summary
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error building cart: {str(e)}")

async def handle_stock_checking_and_feedback(session_id: str, session: SessionState) -> ChatResponse:
    """Handle stock checking and start feedback collection"""
    try:
        # Get user_id and chat_session_id for history saving
        user_id = session.user_id
        chat_session_id = session_id
        
        # Get the cart from session
        cart = session.cart or []
        
        # Simulate stock checking and promotions
        # In a real system, this would check actual stock levels and apply promotions
        final_cart = []
        total_savings = Decimal('0')
        
        for item in cart:
            # Simulate some items being out of stock or having promotions
            item_copy = item.copy()
            
            # Simulate 10% discount on some items
            if "bread" in item.get('name', '').lower():
                original_price = Decimal(str(item.get('price', 0)))
                discount = original_price * Decimal('0.1')
                item_copy['price'] = float(original_price - discount)
                item_copy['original_price'] = float(original_price)
                item_copy['discount'] = float(discount)
                total_savings += discount
            
            final_cart.append(item_copy)
        
        # Update session with final cart
        update_session(
            session_id,
            final_cart=final_cart,
            current_step="final_cart_ready",
            step_number=7
        )
        
        # Show final cart with savings
        cart_summary = f"Final cart with stock check and promotions:"
        total_cost = sum(Decimal(str(item.get('price', 0))) for item in final_cart)
        
        for i, item in enumerate(final_cart, 1):
            price = item.get('price', 0)
            original_price = item.get('original_price')
            discount = item.get('discount')
            
            if original_price and discount:
                cart_summary += f"\n{i}. {item.get('name')} - ${price} (was ${original_price}, saved ${discount:.2f})"
            else:
                cart_summary += f"\n{i}. {item.get('name')} - ${price}"
        
        cart_summary += f"\nTotal cost: ${total_cost}"
        if total_savings > 0:
            cart_summary += f"\nTotal savings: ${total_savings:.2f}"
        
        # Add "Add to Cart" functionality
        cart_summary += f"\n\n🛒 **Add to Cart Options:**"
        cart_summary += f"\n• Click 'Add All to Cart' to add all {len(final_cart)} items to your shopping cart"
        cart_summary += f"\n• Click 'View Product Catalog' to browse and add individual items"
        cart_summary += f"\n• Click 'Continue with Feedback' to provide feedback on these recommendations"
        
        # Save assistant response and return
        return save_and_return_response(user_id, chat_session_id, ChatResponse(
            session_id=session_id,
            message=session.message,
            step="final_cart_ready",
            step_number=7,
            requires_confirmation=True,
            confirmation_prompt="What would you like to do? (Add All to Cart / View Catalog / Continue with Feedback)",
            data={
                "cart_summary": cart_summary,
                "final_cart": final_cart,
                "total_cost": float(total_cost),
                "total_savings": float(total_savings),
                "add_to_cart_enabled": True,
                "cart_options": ["Add All to Cart", "View Product Catalog", "Continue with Feedback"]
            },
            is_complete=False,
            next_step="cart_action_selection",
            query_type=session.query_type,
            assistant_message=cart_summary
        ))
        
    except Exception as e:
        print(f"❌ Error in stock checking: {str(e)}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Error in stock checking: {str(e)}")

async def handle_cart_action_selection(session_id: str, session: SessionState, confirmation: ConfirmationRequest) -> ChatResponse:
    """Handle cart action selection (Add to Cart, View Catalog, or Continue with Feedback)"""
    try:
        user_id = session.user_id
        chat_session_id = session_id
        
        # Get user's choice from confirmation
        user_choice = confirmation.feedback_data.get("choice", "").lower() if confirmation.feedback_data else ""
        
        if "add all to cart" in user_choice or "add to cart" in user_choice:
            # Add all items to user's cart
            final_cart = session.final_cart or []
            
            if final_cart:
                # Convert cart items to format expected by cart service
                cart_items = []
                for item in final_cart:
                    cart_item = {
                        "item_id": item.get("item_id"),
                        "name": item.get("name"),
                        "price": item.get("price", item.get("discounted_price", 0)),
                        "quantity": 1
                    }
                    cart_items.append(cart_item)
                
                # Add to user's cart
                result = cart_service.add_items_to_cart(user_id, cart_items)
                
                if result["success"]:
                    success_message = f"✅ Successfully added {len(cart_items)} items to your shopping cart!\n\n"
                    success_message += f"📊 Your cart now contains {result['cart']['total_items']} items"
                    success_message += f"\n💰 Total cart value: ${result['cart']['total_cost']:.2f}"
                    success_message += f"\n\n🛒 You can view your cart anytime by asking 'Show my cart'"
                    success_message += f"\n🛍️ Browse more products by asking 'Show me products'"
                    
                    return save_and_return_response(user_id, chat_session_id, ChatResponse(
                        session_id=session_id,
                        message=session.message,
                        step="cart_added",
                        step_number=8,
                        requires_confirmation=True,
                        confirmation_prompt="Would you like to provide feedback on these recommendations?",
                        data={
                            "cart_added": True,
                            "items_added": len(cart_items),
                            "cart_total": result['cart']['total_cost'],
                            "user_cart": result['cart']
                        },
                        is_complete=False,
                        next_step="feedback_collection",
                        query_type=session.query_type,
                        assistant_message=success_message
                    ))
                else:
                    error_message = f"❌ Error adding items to cart: {result['message']}"
                    return save_and_return_response(user_id, chat_session_id, ChatResponse(
                        session_id=session_id,
                        message=session.message,
                        step="cart_error",
                        step_number=8,
                        requires_confirmation=False,
                        is_complete=True,
                        query_type=session.query_type,
                        assistant_message=error_message
                    ))
            else:
                error_message = "❌ No items to add to cart"
                return save_and_return_response(user_id, chat_session_id, ChatResponse(
                    session_id=session_id,
                    message=session.message,
                    step="cart_error",
                    step_number=8,
                    requires_confirmation=False,
                    is_complete=True,
                    query_type=session.query_type,
                    assistant_message=error_message
                ))
        
        elif "view catalog" in user_choice or "catalog" in user_choice:
            # Redirect to product catalog
            catalog_message = "🛍️ **Product Catalog Access**\n\n"
            catalog_message += "You can now browse our full product catalog!\n\n"
            catalog_message += "**Available Categories:**\n"
            catalog_message += "• 🥩 Protein (Meat, Fish, Eggs)\n"
            catalog_message += "• 🥬 Vegetables (Organic & Fresh)\n"
            catalog_message += "• 🍎 Fruits (Fresh & Dried)\n"
            catalog_message += "• 🥛 Dairy & Alternatives\n"
            catalog_message += "• 🥜 Nuts & Seeds\n"
            catalog_message += "• 🍚 Grains & Legumes\n"
            catalog_message += "• 🫒 Oils & Condiments\n\n"
            catalog_message += "**How to browse:**\n"
            catalog_message += "• Ask: 'Show me vegetables'\n"
            catalog_message += "• Ask: 'Show keto products'\n"
            catalog_message += "• Ask: 'Show products under $10'\n"
            catalog_message += "• Ask: 'Search for organic products'\n\n"
            catalog_message += "**Add to cart:**\n"
            catalog_message += "• Say: 'Add [product name] to cart'\n"
            catalog_message += "• Say: 'Add 2 [product name] to cart'\n"
            
            return save_and_return_response(user_id, chat_session_id, ChatResponse(
                session_id=session_id,
                message=session.message,
                step="catalog_access",
                step_number=8,
                requires_confirmation=True,
                confirmation_prompt="Would you like to provide feedback on the meal recommendations?",
                data={
                    "catalog_access": True,
                    "categories_available": True
                },
                is_complete=False,
                next_step="feedback_collection",
                query_type=session.query_type,
                assistant_message=catalog_message
            ))
        
        else:
            # Continue with feedback collection (default)
            return await collect_detailed_feedback(confirmation, {"user_id": user_id})
            
    except Exception as e:
        print(f"❌ Error in cart action selection: {str(e)}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Error in cart action selection: {str(e)}")

# Feedback collection endpoints
@router.post("/collect-feedback", response_model=ChatResponse)
async def collect_detailed_feedback(confirmation: ConfirmationRequest, current_user: dict = Depends(get_current_user)):
    """Start detailed feedback collection"""
    try:
        # Get user_id and chat_session_id for history saving
        user_id = current_user["user_id"]
        chat_session_id = confirmation.session_id
        
        session = get_session(confirmation.session_id)
        if not session:
            raise HTTPException(status_code=404, detail="Session not found")
        if session.user_id != current_user["user_id"]:
            raise HTTPException(status_code=403, detail="Access denied to this session")
        
        # Save user confirmation to chat history
        try:
            user_confirmation_data = {
                "type": "user",
                "content": "✅ Yes" if confirmation.confirmed else "❌ No",
                "session_id": confirmation.session_id,
                "timestamp": datetime.now().isoformat(),
                "id": f"msg_feedback_{int(datetime.now().timestamp())}"
            }
            
            success = chat_history_service.add_message_to_session(
                user_id=user_id,
                session_id=chat_session_id,
                message=user_confirmation_data
            )
            print(f"✅ Saved user feedback confirmation to chat history: {success}")
        except Exception as e:
            print(f"❌ Failed to save user feedback confirmation: {str(e)}")
        
        if not confirmation.confirmed:
            # User doesn't want to provide feedback
            response_obj = ChatResponse(
                session_id=confirmation.session_id,
                message="Thank you for your time!",
                step="feedback_declined",
                step_number=session.step_number + 1,
                requires_confirmation=False,
                is_complete=True,
                assistant_message="Thank you for your time! Your order is complete."
            )
            return save_and_return_response(user_id, chat_session_id, response_obj)
        
        # User wants to provide feedback - start collection
        # Update session to feedback_rating step
        update_session(
            confirmation.session_id,
            current_step="feedback_rating",
            step_number=session.step_number + 1
        )
        
        response_obj = ChatResponse(
            session_id=confirmation.session_id,
            message="🎯 FEEDBACK COLLECTION\n\nHow satisfied are you with these recommendations? (1-5)",
            step="feedback_rating",
            step_number=session.step_number + 1,
            requires_confirmation=False,  # This is input collection, not confirmation
            requires_input=True,
            input_type="number",
            input_prompt="Please rate your satisfaction (1-5):",
            is_complete=False,
            assistant_message="🎯 FEEDBACK COLLECTION\n\nHow satisfied are you with these recommendations? (1-5)"
        )
        return save_and_return_response(user_id, chat_session_id, response_obj)
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error starting feedback collection: {str(e)}")

@router.post("/feedback-rating", response_model=ChatResponse)
async def submit_feedback_rating(feedback: FeedbackRequest, current_user: dict = Depends(get_current_user)):
    """Submit feedback rating"""
    try:
        # Get user_id and chat_session_id for history saving
        user_id = current_user["user_id"]
        chat_session_id = feedback.session_id
        
        session = get_session(feedback.session_id)
        if not session:
            raise HTTPException(status_code=404, detail="Session not found")
        if session.user_id != current_user["user_id"]:
            raise HTTPException(status_code=403, detail="Access denied to this session")
        
        # Save user rating to chat history
        try:
            user_rating_data = {
                "type": "user",
                "content": str(feedback.overall_satisfaction),
                "session_id": feedback.session_id,
                "timestamp": datetime.now().isoformat(),
                "id": f"msg_rating_{int(datetime.now().timestamp())}"
            }
            
            success = chat_history_service.add_message_to_session(
                user_id=user_id,
                session_id=chat_session_id,
                message=user_rating_data
            )
            print(f"✅ Saved user rating to chat history: {success}")
        except Exception as e:
            print(f"❌ Failed to save user rating: {str(e)}")
        
        # Store rating and continue to next step
        update_session(
            feedback.session_id,
            current_step="feedback_liked_items",
            step_number=session.step_number + 1,
            feedback={"overall_satisfaction": feedback.overall_satisfaction}
        )
        
        response_obj = ChatResponse(
            session_id=feedback.session_id,
            message="Which items did you like? (comma-separated, or 'none')",
            step="feedback_liked_items",
            step_number=session.step_number + 1,
            requires_confirmation=False,  # This is input collection, not confirmation
            requires_input=True,
            input_type="text",
            input_prompt="Which items did you like? (comma-separated, or 'none'):",
            is_complete=False,
            assistant_message="Which items did you like? (comma-separated, or 'none')"
        )
        return save_and_return_response(user_id, chat_session_id, response_obj)
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error submitting rating: {str(e)}")

@router.post("/feedback-liked", response_model=ChatResponse)
async def submit_liked_items(feedback: FeedbackRequest, current_user: dict = Depends(get_current_user)):
    """Submit liked items"""
    try:
        # Get user_id and chat_session_id for history saving
        user_id = current_user["user_id"]
        chat_session_id = feedback.session_id
        
        session = get_session(feedback.session_id)
        if not session:
            raise HTTPException(status_code=404, detail="Session not found")
        if session.user_id != current_user["user_id"]:
            raise HTTPException(status_code=403, detail="Access denied to this session")
        
        # Update session with liked items
        update_session(
            feedback.session_id,
            current_step="feedback_disliked_items",
            step_number=session.step_number + 1,
            feedback={"liked_items": feedback.liked_items}
        )
        
        response_obj = ChatResponse(
            session_id=feedback.session_id,
            message=session.message,
            step="feedback_disliked_items",
            step_number=session.step_number + 1,
            requires_confirmation=False,
            requires_input=True,
            input_prompt="Which items did you dislike? (comma-separated, or 'none')",
            input_type="text",
            data={"cart": session.final_cart or session.cart},
            is_complete=False,
            assistant_message="Which items did you dislike? (comma-separated, or 'none')"
        )
        return save_and_return_response(user_id, chat_session_id, response_obj)
        
    except Exception as e:
        print(f"❌ Error in submit_liked_items: {str(e)}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Error submitting liked items: {str(e)}")

@router.post("/feedback-disliked", response_model=ChatResponse)
async def submit_disliked_items(feedback: FeedbackRequest, current_user: dict = Depends(get_current_user)):
    """Submit disliked items"""
    try:
        # Get user_id and chat_session_id for history saving  
        user_id = current_user["user_id"]
        chat_session_id = feedback.session_id
        
        session = get_session(feedback.session_id)
        if not session:
            raise HTTPException(status_code=404, detail="Session not found")
        if session.user_id != current_user["user_id"]:
            raise HTTPException(status_code=403, detail="Access denied to this session")
        
        # Update session with disliked items
        update_session(
            feedback.session_id,
            current_step="feedback_suggestions",
            step_number=session.step_number + 1,
            feedback={"disliked_items": feedback.disliked_items}
        )
        
        response_obj = ChatResponse(
            session_id=feedback.session_id,
            message=session.message,
            step="feedback_suggestions",
            step_number=session.step_number + 1,
            requires_confirmation=False,
            requires_input=True,
            input_prompt="Any suggestions for improvement?",
            input_type="text",
            data={"cart": session.final_cart or session.cart},
            is_complete=False,
            assistant_message="Any suggestions for improvement?"
        )
        return save_and_return_response(user_id, chat_session_id, response_obj)
        
    except Exception as e:
        print(f"❌ Error in submit_disliked_items: {str(e)}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Error submitting disliked items: {str(e)}")

@router.post("/feedback-suggestions", response_model=ChatResponse)
async def submit_suggestions(feedback: FeedbackRequest, current_user: dict = Depends(get_current_user)):
    """Submit suggestions"""
    try:
        # Get user_id and chat_session_id for history saving
        user_id = current_user["user_id"]
        chat_session_id = feedback.session_id
        
        session = get_session(feedback.session_id)
        if not session:
            raise HTTPException(status_code=404, detail="Session not found")
        if session.user_id != current_user["user_id"]:
            raise HTTPException(status_code=403, detail="Access denied to this session")
        
        # Update session with suggestions
        update_session(
            feedback.session_id,
            current_step="feedback_purchase",
            step_number=session.step_number + 1,
            feedback={"suggestions": feedback.suggestions}
        )
        
        # Create nicely formatted purchase intent question
        final_cart = session.final_cart or session.cart or []
        cart_summary = ""
        
        if final_cart:
            total_cost = sum(Decimal(str(item.get('price', 0))) for item in final_cart)
            total_savings = sum(Decimal(str(item.get('discount', 0))) for item in final_cart if item.get('discount'))
            
            cart_summary = f"\n\n**Your Shopping Cart:**\n"
            for i, item in enumerate(final_cart, 1):
                price = item.get('price', 0)
                original_price = item.get('original_price')
                discount = item.get('discount')
                
                if original_price and discount:
                    cart_summary += f"{i}. **{item.get('name')}** - ${price} (was ${original_price}, saved ${discount:.2f})\n"
                else:
                    cart_summary += f"{i}. **{item.get('name')}** - ${price}\n"
            
            cart_summary += f"\n**Total Cost:** ${total_cost:.2f}"
            
            if total_savings > 0:
                cart_summary += f"\n**Total Savings:** ${total_savings:.2f}"
        
        purchase_message = f"**Ready to Purchase?**\n\nBased on your feedback and preferences, here's what we've prepared for you:{cart_summary}\n\nWould you like to proceed with purchasing these items?"
        
        response_obj = ChatResponse(
            session_id=feedback.session_id,
            message=session.message,
            step="feedback_purchase",
            step_number=session.step_number + 1,
            requires_confirmation=True,
            confirmation_prompt="Will you purchase these items? (yes/no)",
            data={
                "cart": final_cart,
                "total_cost": float(total_cost) if final_cart else 0,
                "total_savings": float(total_savings) if final_cart else 0,
                "purchase_intent": True,
                "purchase_summary": purchase_message
            },
            is_complete=False,
            assistant_message="Ready to purchase your selected items?"
        )
        return save_and_return_response(user_id, chat_session_id, response_obj)
        
    except Exception as e:
        print(f"❌ Error in submit_suggestions: {str(e)}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Error submitting suggestions: {str(e)}")

@router.post("/feedback-purchase", response_model=ChatResponse)
async def submit_purchase_intent(feedback: FeedbackRequest, current_user: dict = Depends(get_current_user)):
    """Submit purchase intent"""
    try:
        # Get user_id and chat_session_id for history saving
        user_id = current_user["user_id"]
        chat_session_id = feedback.session_id
        
        session = get_session(feedback.session_id)
        if not session:
            raise HTTPException(status_code=404, detail="Session not found")
        if session.user_id != current_user["user_id"]:
            raise HTTPException(status_code=403, detail="Access denied to this session")
        
        # Update session with purchase intent
        update_session(
            feedback.session_id,
            current_step="complete",
            step_number=session.step_number + 1,
            feedback={"will_purchase": feedback.will_purchase}
        )
        
        # Create nicely formatted final response
        final_cart = session.final_cart or session.cart or []
        
        if feedback.will_purchase:
            purchase_message = "**Thank you for your purchase!**\n\nYour items have been added to your cart and are ready for checkout."
        else:
            purchase_message = "**No problem at all!**\n\nFeel free to ask for other recommendations or browse our product catalog anytime."
        
        # Create final cart summary with clean formatting
        cart_summary = ""
        if final_cart:
            total_cost = sum(Decimal(str(item.get('price', 0))) for item in final_cart)
            total_savings = sum(Decimal(str(item.get('discount', 0))) for item in final_cart if item.get('discount'))
            
            cart_summary = f"\n\n**Your Shopping Cart Summary:**\n"
            for i, item in enumerate(final_cart, 1):
                price = item.get('price', 0)
                original_price = item.get('original_price')
                discount = item.get('discount')
                
                if original_price and discount:
                    cart_summary += f"{i}. **{item.get('name')}** - ${price} (was ${original_price}, saved ${discount:.2f})\n"
                else:
                    cart_summary += f"{i}. **{item.get('name')}** - ${price}\n"
            
            cart_summary += f"\n**Total Cost:** ${total_cost:.2f}"
            
            if total_savings > 0:
                cart_summary += f"\n**Total Savings:** ${total_savings:.2f}"
        
        # Add next steps
        next_steps = ""
        if feedback.will_purchase:
            next_steps = f"\n\n**Next Steps:**\n• Review your cart in the shopping cart widget\n• Proceed to checkout when ready\n• Check out our product catalog for more items\n• Ask me for more personalized recommendations"
        else:
            next_steps = f"\n\n**What's Next:**\n• Browse our product catalog for different options\n• Ask me for new meal recommendations\n• Tell me about your dietary preferences\n• I'm here to help you find the perfect products"
        
        final_message = f"{purchase_message}{cart_summary}{next_steps}"
        
        response_obj = ChatResponse(
            session_id=feedback.session_id,
            message=session.message,
            step="complete",
            step_number=session.step_number + 1,
            requires_confirmation=False,
            data={
                "cart": final_cart,
                "total_cost": float(total_cost) if final_cart else 0,
                "total_savings": float(total_savings) if final_cart else 0,
                "purchase_intent": feedback.will_purchase,
                "purchase_confirmation": True,
                "purchase_summary": final_message
            },
            is_complete=True,
            assistant_message="Purchase completed successfully!"
        )
        return save_and_return_response(user_id, chat_session_id, response_obj)
        
    except Exception as e:
        print(f"❌ Error in submit_purchase_intent: {str(e)}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Error submitting purchase intent: {str(e)}") 

async def handle_direct_basket_builder(session_id: str, session: SessionState) -> ChatResponse:
    """Build basket directly from a single recipe referenced in the user's message"""
    try:
        from agents.basket_builder_agent import build_basket
        from dynamo.client import dynamodb, RECIPE_TABLE
        from boto3.dynamodb.conditions import Attr
        
        message_lower = session.message.lower()
        # Heuristic to extract recipe title phrase after keywords like contents/components/ingredients of ...
        # Fallback to entire message if we can't parse
        recipe_title = None
        trigger_keywords = ["contents of", "components of", "ingredients of", "ingredients for", "for "]
        for key in trigger_keywords:
            if key in message_lower:
                recipe_title = session.message.lower().split(key, 1)[1].strip()
                # remove trailing 'to cart' or similar
                for tail in [" to cart", " into cart", " in cart", " to basket", " into basket"]:
                    if recipe_title.endswith(tail):
                        recipe_title = recipe_title[: -len(tail)].strip()
                break
        if not recipe_title:
            recipe_title = session.message.strip()
        
        table = dynamodb.Table(RECIPE_TABLE)
        print(table)
        # Scan all recipes and match title in Python (case-insensitive, partial)
        response = table.scan()
        all_recipes = response.get("Items", [])
        print(f"   🗄️ DynamoDB recipe table: {RECIPE_TABLE}")
        print(f"   📚 Total recipes scanned: {len(all_recipes)}")
        preview_titles = [r.get('title', 'Untitled') for r in all_recipes[:10]]
        if preview_titles:
            print("   🔎 Sample recipe titles:")
            for t in preview_titles:
                print(f"      - {t}")
        recipe_title_norm = recipe_title.strip().strip('"\'')
        recipe_title_lower = recipe_title_norm.lower()
        
        # Try exact (case-insensitive), then contains
        matching = [r for r in all_recipes if r.get('title','').lower() == recipe_title_lower]
        if not matching:
            matching = [r for r in all_recipes if recipe_title_lower in r.get('title','').lower()]
        
        if not matching:
            return ChatResponse(
                session_id=session_id,
                message=session.message,
                step="no_matching_recipe",
                step_number=session.step_number + 1,
                requires_confirmation=False,
                is_complete=True,
                assistant_message=f"❌ I couldn't find a recipe matching '{recipe_title_norm}'. Please try with the exact recipe name."
            )
        
        # Build basket from the first matching recipe
        budget_limit = session.user_profile.get("budget_limit") if session.user_profile else None
        cart = build_basket([matching[0]], budget_limit)
        
        # Update session
        update_session(
            session_id,
            cart=cart,
            current_step="cart_ready",
            step_number=session.step_number + 1
        )
        
        if not cart:
            return ChatResponse(
                session_id=session_id,
                message=session.message,
                step="no_cart_items",
                step_number=session.step_number + 1,
                requires_confirmation=False,
                is_complete=True,
                assistant_message="❌ No products found for that recipe."
            )
        
        recipe_title_render = matching[0].get('title', 'the recipe')
        cart_summary = f"Added {len(cart)} products to your cart from '{recipe_title_render}':"
        total_cost = sum(Decimal(str(item.get('price', 0))) for item in cart)
        for i, item in enumerate(cart, 1):
            price = item.get('price', 0)
            cart_summary += f"\n{i}. {item.get('name')} - ${price}"
        cart_summary += f"\nTotal cost: ${total_cost}"
        
        return ChatResponse(
            session_id=session_id,
            message=session.message,
            step="cart_ready",
            step_number=session.step_number + 1,
            requires_confirmation=True,
            data={"cart": cart},
            is_complete=False,
            next_step="stock_checking",
            query_type="basket_builder",
            assistant_message=cart_summary
        )
    except Exception as e:
        return ChatResponse(
            session_id=session_id,
            message=session.message,
            step="basket_builder_error",
            step_number=session.step_number + 1,
            requires_confirmation=False,
            is_complete=True,
            assistant_message=f"Sorry, I couldn't build a basket from that recipe. Error: {str(e)}"
        ) 