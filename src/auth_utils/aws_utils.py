import base64
import hashlib
import hmac

import requests

from src.auth_utils.config import (
    COGNITO_CLIENT_ID,
    COGNITO_CLIENT_SECRET,
    COGNITO_REGION,
    MOTO,
)


def calculate_secret_hash(username, client_id, client_secret):
    message = username + client_id
    dig = hmac.new(
        client_secret.encode("utf-8"),
        msg=message.encode("utf-8"),
        digestmod=hashlib.sha256,
    ).digest()
    secret_hash = base64.b64encode(dig).decode()
    return secret_hash


def signin(username: str, password: str):

    url = (
        "http://localhost:3000"
        if MOTO
        else f"https://cognito-idp.{COGNITO_REGION}.amazonaws.com"
    )

    payload = {
        "AuthParameters": {
            "USERNAME": username,
            "PASSWORD": password,
            "SECRET_HASH": calculate_secret_hash(
                username=username,
                client_id=COGNITO_CLIENT_ID,
                client_secret=COGNITO_CLIENT_SECRET,
            ),
        },
        "AuthFlow": "USER_PASSWORD_AUTH",
        "ClientId": COGNITO_CLIENT_ID,
    }

    headers = {
        "X-Amz-Target": "AWSCognitoIdentityProviderService.InitiateAuth",
        "Content-Type": "application/x-amz-json-1.1",
    }

    if MOTO:
        headers["Authorization"] = (
            "AWS4-HMAC-SHA256 Credential=mock_access_key/20220524/us-east-1/cognito-idp/aws4_request, SignedHeaders=content-length;content-type;host;x-amz-date, Signature=asdf"
        )

    response = requests.request("POST", url, headers=headers, json=payload)

    return response.json()
