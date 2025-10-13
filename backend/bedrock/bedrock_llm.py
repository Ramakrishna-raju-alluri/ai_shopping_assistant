# bedrock/bedrock_llm.py
import boto3
import os
from langchain_aws import ChatBedrock

# Get AWS credentials from environment
AWS_ACCESS_KEY = os.getenv("AWS_ACCESS_KEY_ID")
AWS_SECRET_KEY = os.getenv("AWS_SECRET_ACCESS_KEY")
AWS_REGION = os.getenv("AWS_REGION", "us-east-1")

# Bedrock model config (adjust model_id as needed)
BEDROCK_MODEL_ID = os.getenv("BEDROCK_MODEL_ID", "anthropic.claude-3-sonnet-20240229-v1:0")

# Create boto3 client for Bedrock
bedrock_runtime = boto3.client(
    service_name="bedrock-runtime",
    region_name=AWS_REGION,
    aws_access_key_id=AWS_ACCESS_KEY,
    aws_secret_access_key=AWS_SECRET_KEY
)

def get_bedrock_llm():
    return ChatBedrock(
        client=bedrock_runtime,
        model_id=BEDROCK_MODEL_ID,
        model_kwargs={"temperature": 0.5, "max_tokens": 512}
    )
