# AI Shopping Assistant

A comprehensive AI-powered shopping assistant built with AWS Bedrock, FastAPI, and React. The system helps users with meal planning, grocery list generation, and smart shopping recommendations.

## 🏗️ Architecture

```
ai_shopping_assistant/
├── frontend/          # React web application
├── backend/           # FastAPI backend with DynamoDB
└── agentcore/         # AWS Bedrock AgentCore containerized agents
```

## 🚀 Features

- **Intelligent Chat Interface**: Natural language interaction for shopping assistance
- **Meal Planning**: AI-powered meal suggestions based on dietary preferences
- **Smart Grocery Lists**: Automatic grocery list generation from meal plans
- **Shopping Cart Management**: Real-time cart operations with budget tracking
- **User Profiles**: Personalized recommendations based on dietary restrictions and preferences
- **Product Search**: Advanced product catalog with substitution suggestions

## 🛠️ Tech Stack

### Frontend
- **React 18** with TypeScript
- **Material-UI** for component library
- **Axios** for API communication
- **Deployed on**: AWS S3 Static Website

### Backend
- **FastAPI** with Python 3.11+
- **AWS DynamoDB** for data storage
- **JWT Authentication** for user management
- **CORS** enabled for cross-origin requests
- **Deployed on**: AWS Elastic Beanstalk

### AI Agents
- **AWS Bedrock** with Claude models
- **Strands Agent Framework** for orchestration
- **AgentCore Runtime** for containerized deployment
- **Deployed on**: AWS ECR + Bedrock AgentCore

## 📦 Quick Start

### Prerequisites
- Node.js 18+
- Python 3.11+
- AWS CLI configured
- Docker (for AgentCore development)

### 1. Frontend Setup
```bash
cd frontend
npm install
npm start
# Runs on http://localhost:3000
```

### 2. Backend Setup
```bash
cd backend
pip install -r requirements.txt
uvicorn main:app --reload --port 8100
# Runs on http://localhost:8100
```

### 3. AgentCore Development
```bash
cd agentcore
pip install -r requirements.txt
python main.py
# Test locally before deployment
```

## 🌐 Deployment

### Frontend (S3)
```bash
cd frontend
npm run build
aws s3 sync build/ s3://your-s3-bucket-name --delete
```

### Backend (Elastic Beanstalk)
```bash
cd backend
eb init
eb create your-agent-env
eb deploy
```

### AgentCore (Bedrock)
```bash
cd agentcore
agentcore configure --entrypoint 
```

## 🔧 Configuration

### Environment Variables

**Frontend** (`.env.production`):
```
REACT_APP_API_BASE_URL=https://your-backend-url.com/api/v1
```

**Backend** (Elastic Beanstalk environment):
```
AWS_REGION=us-east-1
USER_TABLE=mock-users2
PRODUCT_TABLE=mock-products2_with_calories
CART_TABLE=user_carts_v2
```

## 🤖 AI Agents

The system uses specialized AI agents for different tasks:

- **Orchestrator Agent**: Routes requests to appropriate specialized agents
- **Meal Planner Agent**: Creates personalized meal plans
- **Grocery List Agent**: Generates shopping lists from meal plans
- **Health Planner Agent**: Provides nutritional guidance
- **Simple Query Agent**: Handles basic product questions


## 🚦 Live URLs

- **Frontend**: http://ai-shopping-assistant-frontend.s3-website-us-east-1.amazonaws.com/
- **API Docs**: http://ai-shopping-assistant-env.eba-kdhudhcc.us-west-2.elasticbeanstalk.com/docs

<img width="1919" height="882" alt="image" src="https://github.com/user-attachments/assets/6ac8f04a-842f-49e2-bbdf-1fea6d2bf868" />

