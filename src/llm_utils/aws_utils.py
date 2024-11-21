import boto3
from boto3.dynamodb.conditions import Key
from fastapi import HTTPException, status

from src.auth_utils.config import DYNAMODB_TABLE_NAME, MOTO

# Configure the DynamoDB client to connect to Moto server, if applicable
dynamodb = (
    boto3.resource(
        "dynamodb",
        endpoint_url="http://localhost:3000",  # Moto server's URL for DynamoDB
        region_name="us-east-1",
        aws_access_key_id="dummy",  # Moto does not require real credentials
        aws_secret_access_key="dummy",
    )
    if MOTO
    else boto3.resource("dynamodb")
)

table = dynamodb.Table(DYNAMODB_TABLE_NAME)


# Function to get user data from DynamoDB
def get_user_data(user_id: str):
    response = table.query(KeyConditionExpression=Key("user_id").eq(user_id))
    if "Items" not in response or not response["Items"]:
        return None
    return response["Items"][0]


# Function to update token usage in DynamoDB
def update_user_tokens(user_id: str, new_tokens_used: int):
    table.update_item(
        Key={"user_id": user_id},
        UpdateExpression="SET tokens_used = tokens_used + :val",
        ExpressionAttributeValues={":val": new_tokens_used},
        ReturnValues="UPDATED_NEW",
    )


# Dependency to check token limits
def check_token_limit(user_id: str):
    user_data = get_user_data(user_id=user_id)
    if not user_data:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="User not found"
        )
    tokens_remaining = user_data["token_limit"] - user_data["tokens_used"]
    if tokens_remaining <= 0:
        raise HTTPException(
            status_code=status.HTTP_402_PAYMENT_REQUIRED,
            detail="Token limit exceeded",
        )
    return user_data
