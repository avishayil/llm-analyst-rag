import argparse
import logging
import random
import string
import sys
import uuid
from pathlib import Path

import boto3
from botocore.exceptions import ClientError

# Set up logging configuration
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)],
)
logger = logging.getLogger(__name__)


def generate_secure_password(length=16) -> str:
    lowercase = random.choice(string.ascii_lowercase)
    uppercase = random.choice(string.ascii_uppercase)
    digit = random.choice(string.digits)
    special_char = random.choice("!@#$")
    characters = string.ascii_letters + string.digits
    remaining_password = "".join(random.choice(characters) for _ in range(length - 4))
    password = lowercase + uppercase + digit + special_char + remaining_password
    return "".join(random.sample(password, len(password)))


def generate_random_email():
    domains = ["example.com", "test.com", "sample.com"]
    username = "".join(
        random.choice(string.ascii_lowercase + string.digits) for _ in range(8)
    )
    return f"{username}@{random.choice(domains)}"


def generate_secure_key(length=16):
    first_char = random.choice(string.ascii_letters)
    rest_chars = "".join(
        random.choice(string.ascii_letters + string.digits) for _ in range(length - 1)
    )
    return first_char + rest_chars


def setup_clients(is_moto, region):
    endpoint_url = "http://localhost:3000" if is_moto else None
    dynamodb = boto3.resource(
        "dynamodb",
        endpoint_url=endpoint_url,
        region_name=region,
        aws_access_key_id="dummy" if is_moto else None,
        aws_secret_access_key="dummy" if is_moto else None,
    )
    cognito_idp = boto3.client(
        "cognito-idp",
        endpoint_url=endpoint_url,
        region_name=region,
        aws_access_key_id="dummy" if is_moto else None,
        aws_secret_access_key="dummy" if is_moto else None,
    )
    return dynamodb, cognito_idp


def check_existing_table(dynamodb, table_name):
    try:
        existing_tables = [table.name for table in dynamodb.tables.all()]
        if table_name in existing_tables:
            logger.info(f"Table '{table_name}' already exists and will be used.")
            return dynamodb.Table(table_name)
        else:
            logger.info(f"Table '{table_name}' does not exist and will be created.")
            return None
    except ClientError as e:
        logger.error(f"Error checking for existing DynamoDB table: {e}")
        return None


def create_table(dynamodb, table_name):
    table = check_existing_table(dynamodb, table_name)
    if table:
        return table

    try:
        table = dynamodb.create_table(
            TableName=table_name,
            KeySchema=[{"AttributeName": "user_id", "KeyType": "HASH"}],
            AttributeDefinitions=[{"AttributeName": "user_id", "AttributeType": "S"}],
            ProvisionedThroughput={"ReadCapacityUnits": 5, "WriteCapacityUnits": 5},
        )
        table.meta.client.get_waiter("table_exists").wait(TableName=table_name)
        logger.info(f"Table '{table_name}' created successfully.")
        return table
    except ClientError as e:
        logger.error(f"Failed to create table: {e}")
        return None


def check_existing_user_pool(cognito_idp, pool_name):
    try:
        response = cognito_idp.list_user_pools(MaxResults=50)
        for pool in response["UserPools"]:
            if pool["Name"] == pool_name:
                logger.info(
                    f"User Pool '{pool_name}' already exists with ID: {pool['Id']} and will be used."
                )
                return pool["Id"]
        logger.info(f"User Pool '{pool_name}' does not exist and will be created.")
        return None
    except ClientError as e:
        logger.error(f"Error checking for existing Cognito user pool: {e}")
        return None


def create_user_pool(cognito_idp, pool_name="LLMAPIScaffoldUserPool"):
    user_pool_id = check_existing_user_pool(cognito_idp, pool_name)
    if user_pool_id:
        return user_pool_id

    try:
        response = cognito_idp.create_user_pool(PoolName=pool_name)
        user_pool_id = response["UserPool"]["Id"]
        logger.info(f"User Pool '{pool_name}' created with ID: {user_pool_id}")
        return user_pool_id
    except ClientError as e:
        logger.error(f"Failed to create user pool: {e}")
        return None


def create_cognito_user(cognito_idp, user_pool_id, user_id, email, password):
    try:
        cognito_user = cognito_idp.admin_create_user(
            UserPoolId=user_pool_id,
            Username=user_id,
            UserAttributes=[
                {"Name": "email", "Value": email},
                {"Name": "email_verified", "Value": "true"},
            ],
            TemporaryPassword=password,
            MessageAction="SUPPRESS",
        )
        cognito_idp.admin_set_user_password(
            UserPoolId=user_pool_id,
            Username=user_id,
            Password=password,
            Permanent=True,
        )
        sub_value = next(
            attr["Value"]
            for attr in cognito_user["User"]["Attributes"]
            if attr["Name"] == "sub"
        )
        logger.info(
            f"User '{user_id}' created in Cognito with email '{email}' and password set permanently."
        )
        return cognito_user["User"]["Username"], sub_value
    except ClientError as e:
        logger.error(f"Failed to create or set password for user in Cognito: {e}")
        return None, None


def create_app_client(
    cognito_idp, user_pool_id, client_name="ExampleAppClient", is_moto=False
):
    try:
        response = cognito_idp.list_user_pool_clients(
            UserPoolId=user_pool_id, MaxResults=10
        )
        for client in response["UserPoolClients"]:
            if client["ClientName"] == client_name:
                logger.info(
                    f"App Client '{client_name}' already exists with Client ID: {client['ClientId']} and will be used."
                )
                return client["ClientId"], client.get("ClientSecret")

        # Create the App Client
        response = cognito_idp.create_user_pool_client(
            UserPoolId=user_pool_id,
            ClientName=client_name,
            GenerateSecret=True,
            ExplicitAuthFlows=[
                "ALLOW_USER_PASSWORD_AUTH",
                "ALLOW_REFRESH_TOKEN_AUTH",
                "ALLOW_USER_SRP_AUTH",
            ],
            CallbackURLs=[
                "http://localhost:8000/auth"
            ],  # Set callback URL for localhost
            LogoutURLs=["http://localhost:8000"],  # Optional: set logout URL
            AllowedOAuthFlows=["code"],  # OAuth code grant flow
            AllowedOAuthScopes=["email", "openid", "profile"],  # Set required scopes
            AllowedOAuthFlowsUserPoolClient=True,  # Enable OAuth flows
            SupportedIdentityProviders=[
                "COGNITO"
            ],  # Set identity provider to user pool
        )
        client_id = response["UserPoolClient"]["ClientId"]
        client_secret = response["UserPoolClient"]["ClientSecret"]
        logger.info(
            f"App Client '{client_name}' created with Client ID: {client_id} and Client Secret."
        )

        # Set up a domain for the Hosted UI if not using Moto
        if not is_moto:
            # Format the domain name correctly
            formatted_user_pool_id = user_pool_id.lower().replace("_", "-")
            domain_prefix = f"task-guard-{formatted_user_pool_id}"
            try:
                cognito_idp.create_user_pool_domain(
                    Domain=domain_prefix, UserPoolId=user_pool_id
                )
                logger.info(
                    f"Domain '{domain_prefix}' created for User Pool ID '{user_pool_id}'."
                )
            except ClientError as e:
                logger.error(f"Failed to create domain '{domain_prefix}': {e}")

        return client_id, client_secret
    except ClientError as e:
        logger.error(f"Failed to create app client: {e}")
        return None, None


def insert_default_user(dynamodb, table_name, user_id, email):
    try:
        table = dynamodb.Table(table_name)
        default_user = {
            "user_id": user_id,
            "email": email,
            "token_limit": 10000,
            "tokens_used": 0,
        }
        table.put_item(Item=default_user)
        logger.info(f"Inserted default user into DynamoDB: {default_user}")
    except ClientError as e:
        logger.error(f"Failed to insert user into DynamoDB: {e}")


def write_to_env_file(env_file, variables):
    env_path = Path(env_file)
    try:
        with env_path.open("w") as f:
            for key, value in variables.items():
                f.write(f"{key}={value}\n")
        logger.info(f".env file created with the following values:\n{variables}")
    except IOError as e:
        logger.error(f"Failed to write to .env file: {e}")


def main():
    parser = argparse.ArgumentParser(
        description="Initialize the backend with DynamoDB and Cognito"
    )
    parser.add_argument(
        "--is-moto", action="store_true", help="Use Moto backend or regular AWS backend"
    )
    parser.add_argument(
        "--region", default="us-east-1", help="AWS region for resources"
    )
    parser.add_argument(
        "--table-name", default="LLMAPIScaffoldUsers", help="DynamoDB table name"
    )
    args = parser.parse_args()

    dynamodb, cognito_idp = setup_clients(args.is_moto, args.region)
    table_name = create_table(dynamodb, args.table_name)
    user_pool_id = create_user_pool(cognito_idp)

    if user_pool_id and table_name:
        user_id = str(uuid.uuid4())
        email = generate_random_email()
        password = generate_secure_password()

        user_name, user_sub = create_cognito_user(
            cognito_idp, user_pool_id, user_id, email, password
        )
        if user_name and user_sub:
            client_id, client_secret = create_app_client(
                cognito_idp, user_pool_id, is_moto=args.is_moto
            )
            insert_default_user(dynamodb, args.table_name, user_sub, email)

            env_variables = {
                "MOTO": str(args.is_moto),
                "SECRET_KEY": generate_secure_key(),
                "DYNAMODB_TABLE_NAME": args.table_name,
                "COGNITO_REGION": args.region,
                "COGNITO_USER_POOL_ID": user_pool_id,
                "COGNITO_CLIENT_ID": client_id,
                "COGNITO_CLIENT_SECRET": client_secret,
                "TEST_COGNITO_USER_NAME": user_name,
                "TEST_COGNITO_USER_PASSWORD": password,
            }
            write_to_env_file(".env", env_variables)


if __name__ == "__main__":
    main()
