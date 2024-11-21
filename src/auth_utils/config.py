# config.py
import os

import requests
from dotenv import dotenv_values
from starlette.config import Config

config = {
    **os.environ,
    **dotenv_values(".env", verbose=True),
}

MOTO = True if config.get("MOTO") == "True" else False
SECRET_KEY: str = config.get("SECRET_KEY", "")
DYNAMODB_TABLE_NAME: str = config.get("DYNAMODB_TABLE_NAME", "")
COGNITO_REGION: str = config.get("COGNITO_REGION", "")
COGNITO_USER_POOL_ID: str = config.get("COGNITO_USER_POOL_ID", "")
COGNITO_CLIENT_ID: str = config.get("COGNITO_CLIENT_ID", "")
COGNITO_CLIENT_SECRET: str = config.get("COGNITO_CLIENT_SECRET", "")
TEST_COGNITO_USER_NAME: str = config.get("TEST_COGNITO_USER_NAME", "")
TEST_COGNITO_USER_PASSWORD: str = config.get("TEST_COGNITO_USER_PASSWORD", "")
COGNITO_ISSUER: str = (
    f"http://localhost:3000/{COGNITO_USER_POOL_ID}"
    if MOTO
    else f"https://cognito-idp.{COGNITO_REGION}.amazonaws.com/{COGNITO_USER_POOL_ID}"
)
LOG_LEVEL: str = config.get("LOG_LEVEL", "INFO")
JWKS_URL: str = f"{COGNITO_ISSUER}/.well-known/jwks.json"
COGNITO_OPENID_CONFIGURATION_URL: str = (
    f"{COGNITO_ISSUER}/.well-known/openid-configuration"
)
config_data = {
    "COGNITO_CLIENT_ID": COGNITO_CLIENT_ID,
    "COGNITO_CLIENT_SECRET": COGNITO_CLIENT_SECRET,
}

starlette_config = Config(environ=config_data)

# Cache the public keys
headers = (
    {
        "Authorization": "AWS4-HMAC-SHA256 Credential=mock_access_key/20220524/us-east-1/cognito-idp/aws4_request, SignedHeaders=content-length;content-type;host;x-amz-date, Signature=asdf"
    }
    if MOTO
    else {}
)

response = requests.get(JWKS_URL, headers=headers)
JWKS = response.json()
