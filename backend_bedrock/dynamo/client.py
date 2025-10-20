import os
import boto3
from boto3.session import Session

AWS_REGION = os.getenv("AWS_REGION", "us-east-1")

# Initialize DynamoDB resource
session = Session()
dynamodb = session.resource("dynamodb", region_name=AWS_REGION)

# Table names from environment
USER_TABLE = os.getenv("USER_TABLE", "mock-users2")
PRODUCT_TABLE = os.getenv("PRODUCT_TABLE", "mock-products2_with_calories")
RECIPE_TABLE = os.getenv("RECIPE_TABLE", "mock-recipes2")
PROMO_TABLE = os.getenv("PROMO_TABLE", "promo_stock_feed2")

