import boto3
import json
bedrock_runtime = boto3.client("bedrock-runtime", region_name="us-east-1")

    # Use the inference profile ARN
inference_profile_arn = "amazon.nova-lite-v1:0"
messages = [
        {
            "role": "user",
            "content": [{"text": "Write a short poem about AI agents."}]
        }
    ]


try:
    response = bedrock_runtime.invoke_model(
        modelId=inference_profile_arn,
        body=json.dumps({"messages": messages}),
        contentType="application/json",
        accept="application/json"
    )

        # Parse and print the model output
    result = json.loads(response["body"].read().decode("utf-8"))
    print(json.dumps(result, indent=2))

except Exception as e:
        print("Error:", e)