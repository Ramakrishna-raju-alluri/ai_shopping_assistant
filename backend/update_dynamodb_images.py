import json
import boto3
from decimal import Decimal
from botocore.exceptions import ClientError

def update_dynamodb_with_images():
    """Update DynamoDB products table with image URLs"""
    
    # Initialize DynamoDB client
    dynamodb = boto3.resource('dynamodb', region_name='us-east-1')
    table = dynamodb.Table('mock-products2')
    
    # Load the updated product data
    with open('mock_products_data.json', 'r') as f:
        products = json.load(f)
    
    updated_count = 0
    error_count = 0
    
    print(f"🔄 Updating {len(products)} products in DynamoDB...")
    
    for product in products:
        try:
            # Prepare item for DynamoDB (convert price to Decimal)
            item = {
                'item_id': product['item_id'],
                'name': product['name'],
                'price': Decimal(str(product['price'])),
                'tags': product['tags'],
                'in_stock': product['in_stock'],
                'promo': product['promo'],
                'category': product.get('category', ''),
                'image_url': product.get('image_url', '')
            }
            
            # Update the item in DynamoDB
            table.put_item(Item=item)
            updated_count += 1
            
            if updated_count % 10 == 0:
                print(f"  ✅ Updated {updated_count} products...")
                
        except ClientError as e:
            print(f"❌ Error updating {product['name']}: {e}")
            error_count += 1
        except Exception as e:
            print(f"❌ Unexpected error updating {product['name']}: {e}")
            error_count += 1
    
    print(f"\n✅ Successfully updated {updated_count} products")
    if error_count > 0:
        print(f"❌ Failed to update {error_count} products")
    
    # Show some examples
    print("\n📸 Example updated products:")
    for i, product in enumerate(products[:3]):
        print(f"  {product['name']}: {product.get('image_url', 'No image')}")

if __name__ == "__main__":
    update_dynamodb_with_images() 