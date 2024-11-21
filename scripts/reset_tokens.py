import os

import boto3
from dotenv import load_dotenv

# Load environment variables from the .env file
load_dotenv()

MOTO = os.getenv("MOTO", "False").lower() == "true"
DYNAMODB_TABLE_NAME = os.getenv("DYNAMODB_TABLE_NAME")
COGNITO_REGION = os.getenv("COGNITO_REGION", "us-west-2")

# Set up the DynamoDB client
if MOTO:
    dynamodb = boto3.resource(
        "dynamodb", region_name=COGNITO_REGION, endpoint_url="http://localhost:3000"
    )
else:
    dynamodb = boto3.resource("dynamodb", region_name=COGNITO_REGION)

table = dynamodb.Table(DYNAMODB_TABLE_NAME)


def reset_tokens():
    try:
        # Scan the table to get all users
        response = table.scan()
        items = response.get("Items", [])

        for item in items:
            user_id = item["user_id"]

            # Update tokens_used to 0
            table.update_item(
                Key={"user_id": user_id},
                UpdateExpression="set tokens_used = :val",
                ExpressionAttributeValues={":val": 0},
            )
            print(f"Reset tokens_used for user_id: {user_id}")

    except Exception as e:
        print(f"An error occurred: {e}")


if __name__ == "__main__":
    reset_tokens()
