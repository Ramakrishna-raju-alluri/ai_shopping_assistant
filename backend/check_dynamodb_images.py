import boto3
from botocore.exceptions import ClientError

def check_dynamodb_images():
    """Check if image URLs are present in DynamoDB products table"""
    
    # Initialize DynamoDB client
    dynamodb = boto3.resource('dynamodb', region_name='us-east-1')
    table = dynamodb.Table('mock-products2')
    
    try:
        # Scan the table to get some products
        print("🔄 Scanning DynamoDB table for products...")
        response = table.scan(Limit=5)
        products = response.get('Items', [])
        
        print(f"✅ Found {len(products)} products in DynamoDB")
        
        # Check each product for image URLs
        for i, product in enumerate(products):
            print(f"\n📦 Product {i+1}: {product.get('name', 'Unknown')}")
            print(f"   Image URL: {product.get('image_url', '❌ NO IMAGE URL')}")
            print(f"   Category: {product.get('category', 'No category')}")
            print(f"   Price: ${product.get('price', 'N/A')}")
            
            # Check if image URL exists and is not empty
            image_url = product.get('image_url')
            if image_url and image_url.strip():
                print(f"   ✅ Has image URL")
            else:
                print(f"   ❌ Missing image URL")
                
    except ClientError as e:
        print(f"❌ DynamoDB error: {e}")
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    check_dynamodb_images() 