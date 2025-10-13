# AI Grocery Shopping Assistant API

A conversational AI assistant for grocery shopping with meal planning, product recommendations, and dietary filtering.

## 🚀 Features

- **Multi-Query Support**: Handles meal planning, product recommendations, dietary filters, and general queries
- **Conversational Flow**: Step-by-step interactive conversations with user confirmations
- **Session Management**: Maintains conversation state across multiple interactions
- **Interactive Onboarding**: Comprehensive 5-step onboarding for new users
- **Recipe-Based Recommendations**: Suggests recipes based on dietary preferences
- **Shopping Cart Building**: Creates complete shopping lists from recipes
- **Stock & Promotions**: Checks availability and applies discounts
- **Feedback Learning**: Collects user feedback for continuous improvement

## 🏗️ Architecture

### Core Components

1. **Intent Agent**: Classifies user queries and extracts relevant information
2. **Preference Agent**: Manages user profiles and dietary preferences with interactive onboarding
3. **Meal Planner Agent**: Suggests recipes based on preferences and budget
4. **Basket Builder Agent**: Creates shopping carts from recipe ingredients
5. **Stock Checker Agent**: Checks availability and applies promotions
6. **Feedback Agent**: Learns from user interactions

### Query Types

- **meal_planning**: "plan 4 meals under 20 dollars"
- **product_recommendation**: "suggest low carb recipes"
- **dietary_filter**: "show me gluten free recipes"
- **general_query**: "how do I get delivery?"

## 🛠️ Setup

### Prerequisites

- Python 3.8+
- AWS credentials configured
- DynamoDB tables set up

### Installation

1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. Set up environment variables in `.env`:
```env
AWS_ACCESS_KEY_ID=your_access_key
AWS_SECRET_ACCESS_KEY=your_secret_key
AWS_REGION=your_region
USER_TABLE=mock-users
PRODUCT_TABLE=mock-products
RECIPE_TABLE=mock-recipes
PROMO_TABLE=promo_stock_feed
```

3. Start the server:
```bash
python main.py
```

The API will be available at `http://localhost:8000`

## 📚 API Documentation

### Base URL
```
http://localhost:8000/api/v1
```

### Endpoints

#### 1. Chat Endpoint
**POST** `/chat`

Start or continue a conversation with the AI assistant.

**Request Body:**
```json
{
  "user_id": "user_123",
  "message": "plan 3 meals under 30 dollars",
  "session_id": null
}
```

**Response:**
```json
{
  "session_id": "user_123_20241201_143022",
  "message": "✅ Extracted intent:\n   • Query type: meal_planning\n   • Number of meals: 3\n   • Budget: $30\n   • Dietary preference: N/A",
  "step": "intent_extraction",
  "step_number": 1,
  "requires_confirmation": true,
  "confirmation_prompt": "Does this look correct? Should I proceed?",
  "data": {
    "intent": {...},
    "query_type": "meal_planning"
  },
  "is_complete": false,
  "next_step": "profile_loading"
}
```

#### 2. Onboarding Endpoint (New Users)
**POST** `/onboarding`

Handle interactive onboarding for new users.

**Request Body:**
```json
{
  "session_id": "user_123_20241201_143022",
  "user_id": "user_123",
  "step": "dietary_preferences",
  "input_value": "3"
}
```

**Response:**
```json
{
  "session_id": "user_123_20241201_143022",
  "message": "✅ Dietary preference set to: keto\n\n🍽️ STEP 2: Cuisine Preferences\n------------------------------\nWhat types of cuisine do you enjoy? (Select multiple)",
  "step": "onboarding_cuisine",
  "step_number": 2,
  "requires_input": true,
  "input_prompt": "Select your preferred cuisines (comma-separated numbers):",
  "input_options": [
    "1. Italian (pasta, pizza, risotto, lasagna)",
    "2. Asian (stir-fry, curry, sushi, noodles)",
    "3. Mexican (tacos, enchiladas, burritos, quesadillas)",
    "4. Mediterranean (salads, grilled fish, hummus, falafel)",
    "5. American (burgers, steak, chicken, barbecue)",
    "6. Indian (curry, biryani, dal, naan)",
    "7. Quick Easy (sandwiches, wraps, one-pot, 30-minute)",
    "8. Healthy (salads, smoothies, bowls, lean protein)"
  ],
  "input_type": "multiple_choice",
  "data": {"onboarding_step": "cuisine_preferences"},
  "is_complete": false,
  "next_step": "onboarding_budget"
}
```

#### 3. Confirm Endpoint
**POST** `/confirm`

Confirm or reject the current step and proceed to the next.

**Request Body:**
```json
{
  "session_id": "user_123_20241201_143022",
  "user_id": "user_123",
  "confirmed": true,
  "feedback_data": null
}
```

#### 4. Feedback Endpoint
**POST** `/feedback`

Submit user feedback for learning.

**Request Body:**
```json
{
  "session_id": "user_123_20241201_143022",
  "user_id": "user_123",
  "confirmed": true,
  "feedback_data": {
    "overall_satisfaction": "4",
    "liked_items": ["Chicken Breast", "Greek Yogurt"],
    "disliked_items": [],
    "suggestions": "More vegetarian options please",
    "will_purchase": true
  }
}
```

#### 5. Session Info
**GET** `/sessions/{session_id}`

Get information about a specific session.

#### 6. Delete Session
**DELETE** `/sessions/{session_id}`

Delete a session and clear its data.

## 🔄 Conversation Flow

### Step-by-Step Process

1. **Intent Extraction** (Step 1)
   - User sends message
   - System extracts intent and query type
   - User confirms or rejects

2. **Profile Loading** (Step 2)
   - **Existing Users**: Load profile from DynamoDB
   - **New Users**: Start interactive onboarding process
   - Display profile information
   - User confirms to proceed

3. **Interactive Onboarding** (New Users Only)
   - **Dietary Preferences**: 10 options (vegetarian, vegan, keto, etc.)
   - **Cuisine Preferences**: 8 cuisine types (Italian, Asian, Mexican, etc.)
   - **Budget Confirmation**: Adjust budget if needed
   - **Cooking Skill Level**: Beginner, Intermediate, Advanced
   - **Allergies & Restrictions**: Collect food allergies

4. **Recipe Planning/Recommendation** (Step 3)
   - Find recipes based on preferences
   - Display recipe suggestions
   - User confirms to build cart

5. **Basket Building** (Step 4)
   - Convert recipes to shopping list
   - Find matching products
   - User confirms to check stock

6. **Stock & Promotions** (Step 5)
   - Check product availability
   - Apply discounts and promotions
   - User confirms for feedback

7. **Feedback Collection** (Step 6)
   - Collect user satisfaction
   - Learn from preferences
   - Complete conversation

### Example Onboarding Flow

```
User: "plan 3 meals under 30 dollars"

System: 🎉 Welcome! Let's set up your profile for personalized recommendations.
============================================================

🥗 STEP 1: Dietary Preferences
------------------------------
What's your dietary preference? (This helps us suggest suitable recipes)

User: "3" (Keto)

System: ✅ Dietary preference set to: keto

🍽️ STEP 2: Cuisine Preferences
------------------------------
What types of cuisine do you enjoy? (Select multiple)

User: "1,4,5" (Italian, Mediterranean, American)

System: ✅ Selected cuisines: italian, mediterranean, american

💰 STEP 3: Budget Preferences
------------------------------
Current budget: $30

User: "n" (No change)

System: ✅ Budget confirmed: $30

👨‍🍳 STEP 4: Cooking Experience
------------------------------
What's your cooking skill level?

User: "2" (Intermediate)

System: ✅ Cooking skill set to: intermediate

⚠️ STEP 5: Allergies and Restrictions
------------------------------------
Do you have any food allergies or restrictions? (e.g., nuts, shellfish, dairy)

User: "nuts, shellfish"

System: ✅ PROFILE SETUP COMPLETE!
============================================================
Diet: keto
Budget: $30
Preferred cuisines: italian, mediterranean, american
Cooking skill: intermediate
Allergies: nuts, shellfish

🎯 Your profile is now set up! We'll use these preferences to provide personalized recommendations.
You can update these preferences anytime by asking for dietary changes or budget adjustments.

User: [confirms]

System: ✅ Found 3 recipes for you:
   1. Keto Mediterranean Salmon - $12 (Score: 4)
   2. Italian Keto Pasta - $8 (Score: 3)
   3. American Keto Bowl - $6 (Score: 2)
   📊 Total recipe cost: $26
   Do you want to proceed with building your shopping cart?
```

## 🧪 Testing

Run the test script to verify the API:

```bash
python test_api.py
```

This will test:
- Health check endpoint
- New user onboarding flow
- Existing user flow
- Chat endpoint
- Confirm endpoint
- Session management

## 📖 API Documentation

Visit `http://localhost:8000/docs` for interactive API documentation (Swagger UI).

## 🔧 Configuration

### Environment Variables

- `AWS_ACCESS_KEY_ID`: AWS access key
- `AWS_SECRET_ACCESS_KEY`: AWS secret key
- `AWS_REGION`: AWS region
- `USER_TABLE`: DynamoDB user table name
- `PRODUCT_TABLE`: DynamoDB product table name
- `RECIPE_TABLE`: DynamoDB recipe table name
- `PROMO_TABLE`: DynamoDB promo table name

### CORS Configuration

The API includes CORS middleware configured to allow all origins. In production, update the `allow_origins` list in `main.py`.

## 🚀 Production Deployment

For production deployment:

1. Use a production WSGI server like Gunicorn
2. Set up proper CORS origins
3. Use Redis or database for session storage
4. Configure proper logging
5. Set up monitoring and health checks

```bash
# Example with Gunicorn
pip install gunicorn
gunicorn main:app -w 4 -k uvicorn.workers.UvicornWorker --bind 0.0.0.0:8000
```

## 🤝 Frontend Integration

The API is designed to work with conversational chatbot frontends. Key integration points:

1. **Session Management**: Use `session_id` to maintain conversation state
2. **Step-by-Step Flow**: Handle `requires_confirmation` and `confirmation_prompt`
3. **Interactive Onboarding**: Handle `requires_input`, `input_prompt`, `input_options`, and `input_type`
4. **Data Display**: Use `data` field for structured information
5. **Feedback Collection**: Implement feedback forms based on `step`

### Onboarding Integration

For new users, the frontend should:

1. **Detect Onboarding Mode**: Check if `requires_input` is true
2. **Display Input Options**: Show `input_options` as buttons/choices
3. **Handle Input Types**:
   - `choice`: Single selection from options
   - `multiple_choice`: Comma-separated selections
   - `text`: Free text input
   - `number`: Numeric input
4. **Submit Onboarding Data**: Use `/onboarding` endpoint with `step` and `input_value`
5. **Progress Through Steps**: Follow `next_step` until onboarding is complete

## 📝 License

This project is part of the AI Grocery Shopping Assistant system. 