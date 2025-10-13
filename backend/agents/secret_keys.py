import boto3

client = boto3.client("secretsmanager", region_name="us-east-1")

# List all secrets
response = client.list_secrets()
for secret in response["SecretList"]:
    print(secret["Name"])  # this is the name you use
