# Coles Shopping Assistant Agent

An AI-powered agent built with AWS Bedrock Agent Core that helps users with grocery shopping, nutrition tracking, and meal planning.

## Features

- **Product Information**: Check product availability and stock status
- **Nutrition Tracking**: Log meals, track calories, set daily targets
- **Meal Planning**: Generate meal suggestions based on preferences and budget
- **User Profile Management**: Access and manage user dietary preferences

## Architecture

```
my-agent/
├── src/
│   ├── main.py              # Entry point (Lambda-style handler)
│   ├── agent_logic.py       # Core orchestration logic
│   ├── tools/               # Agent tools
│   │   ├── __init__.py
│   │   ├── db_tool.py       # DynamoDB operations
│   │   ├── model_tool.py    # Bedrock model calls
│   │   └── custom_tool.py   # Custom utility functions
│   └── utils/
│       ├── logger.py        # Logging utilities
│       └── helper.py        # Helper functions
├── requirements.txt
├── Dockerfile
├── bedrock-config.yaml      # Agent configuration
└── README.md
```

## Tools

### Database Tools (`db_tool.py`)
- `find_product_stock`: Check product availability
- `get_nutrition_plan`: Fetch daily nutrition data
- `set_nutrition_target`: Set daily calorie targets
- `append_meal`: Log meals to nutrition tracker
- `get_calories_remaining`: Calculate remaining calories
- `get_user_profile`: Access user preferences

### Model Tools (`model_tool.py`)
- `calculate_calories`: Estimate calories from ingredients
- `calculate_cost`: Calculate meal costs
- `generate_meal_suggestions`: AI-powered meal recommendations

### Utility Tools (`custom_tool.py`)
- `get_current_date`: Get current date
- `format_nutrition_summary`: Format nutrition data
- `validate_date_format`: Validate date strings
- `parse_meal_input`: Parse natural language meal descriptions

## Setup

### Prerequisites
- Python 3.12+
- AWS CLI configured
- DynamoDB tables created
- Bedrock access

### Installation

1. Clone the repository:
```bash
git clone <repository-url>
cd my-agent
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Set environment variables:
```bash
# PowerShell
$env:AWS_REGION="us-east-1"
$env:USER_TABLE="mock-users2"
$env:PRODUCT_TABLE="mock-products2"
$env:NUTRITION_TABLE="nutrition_calendar"

# Bash
export AWS_REGION=us-east-1
export USER_TABLE=mock-users2
export PRODUCT_TABLE=mock-products2
export NUTRITION_TABLE=nutrition_calendar
```

### Local Development

Run the agent locally:
```bash
python -m src.main --prompt "Are bananas in stock?" --user-id test-user-123
```

Run the comprehensive test suite:
```bash
python test_agent.py
```

### Docker

Build and run with Docker:
```bash
docker build -t coles-agent .
docker run -e AWS_REGION=us-east-1 coles-agent
```

## Usage Examples

### Product Queries
```
"Are bananas in stock?"
"Do you have organic milk available?"
"What's the price of whole wheat bread?"
```

### Nutrition Tracking
```
"Set my daily calorie target to 1800 for 2025-01-18"
"Log breakfast with 400 calories for today"
"How many calories do I have left for 2025-01-18?"
"Show my nutrition summary for today"
```

### Meal Planning
```
"Suggest healthy meals under $20"
"Generate meal ideas for a vegetarian diet"
"What can I cook with chicken, rice, and vegetables?"
```

## Configuration

The agent behavior is configured in `bedrock-config.yaml`:

- **Model settings**: Claude 3.7 Sonnet with temperature 0.1
- **Tool definitions**: All available tools and their parameters
- **Environment variables**: DynamoDB table names and AWS region
- **Deployment settings**: Runtime, timeout, memory, and IAM permissions

## Database Schema

### Nutrition Table (`nutrition_calendar`)
```json
{
  "user_id": "string",
  "date": "string (YYYY-MM-DD)",
  "target": "number",
  "consumed": "number", 
  "meals": [
    {
      "name": "string",
      "calories": "number",
      "protein": "number",
      "carbs": "number",
      "fat": "number"
    }
  ]
}
```

### Product Table (`mock-products2`)
```json
{
  "item_id": "string",
  "name": "string",
  "price": "number",
  "in_stock": "boolean",
  "category": "string",
  "tags": ["string"]
}
```

## Deployment

### AWS Lambda
The agent is designed to run as a Lambda function with the Bedrock Agent Core runtime.

### Environment Variables
Set these in your deployment environment:
- `AWS_REGION`: AWS region for DynamoDB and Bedrock
- `USER_TABLE`: DynamoDB table for user profiles
- `PRODUCT_TABLE`: DynamoDB table for products
- `NUTRITION_TABLE`: DynamoDB table for nutrition data

## Testing

Run tests:
```bash
pytest tests/
```

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests
5. Submit a pull request

## License

This project is licensed under the MIT License.
