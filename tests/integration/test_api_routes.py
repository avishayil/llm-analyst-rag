import pytest
from jose import jwt

from src.auth_utils.config import TEST_COGNITO_USER_NAME, TEST_COGNITO_USER_PASSWORD


@pytest.fixture
def token(client):
    """Fixture to log in and retrieve a token using extracted Cognito credentials."""

    response = client.post(
        "/api/v1/signin",
        json={
            "username": TEST_COGNITO_USER_NAME,
            "password": TEST_COGNITO_USER_PASSWORD,
        },
    )

    assert response.status_code == 200

    token = response.json()

    decoded_token = jwt.decode(
        token, None, options={"verify_signature": False, "verify_aud": False}
    )
    assert decoded_token.get("cognito:username") == TEST_COGNITO_USER_NAME

    return token


def test_health_route(client):
    """Test the health check endpoint."""
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "OK"}


def test_signin_route(client, token):
    """Test to ensure login works and token is correctly decoded."""
    assert token is not None  # Token is already verified in the fixture


def test_generate_route(client, token):
    """Test the generate route for vulnerability analyst using a valid token."""
    headers = {"Authorization": f"Bearer {token}"}

    json = {"criteria": "Apache"}

    response = client.post(
        "/api/v1/vulnerability-analyst/generate", headers=headers, json=json
    )

    assert response.status_code == 200
    response_json = response.json()
    assert isinstance(
        response_json, dict
    )  # Expecting the top-level response to be a dictionary

    # Ensure the "Suggestion" key exists at the top level
    assert "Summary" in response_json

    # Validate "Suggestion" is itself a dictionary (as shown in the example response)
    assert isinstance(response_json["Summary"], dict)


def test_protected_route_no_auth(client):
    """Test access to protected route without authentication."""
    response = client.post(
        "/api/v1/vulnerability-analyst/generate",
        json={
            "criteria": "Apache",
        },
    )
    assert response.status_code == 403  # Unauthorized without token
