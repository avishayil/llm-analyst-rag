# oauth_utils.py

from authlib.integrations.starlette_client import OAuth
from fastapi import Depends, HTTPException, Request, status
from fastapi.security import HTTPBearer
from jose import JWTError, jwt
from starlette.responses import RedirectResponse

from src.auth_utils.config import (
    COGNITO_CLIENT_ID,
    COGNITO_ISSUER,
    COGNITO_OPENID_CONFIGURATION_URL,
    JWKS,
    MOTO,
    starlette_config,
)

oauth = OAuth(starlette_config)
oauth.register(
    name="cognito",
    server_metadata_url=COGNITO_OPENID_CONFIGURATION_URL,
    client_kwargs={"scope": "openid email profile"},
)


async def login(request: Request):
    # Determine the correct scheme based on the host
    scheme = (
        "http"
        if "localhost" in request.url.hostname or "motoserver" in request.url.hostname
        else "https"
    )
    port = request.url.port
    host = request.url.hostname
    host_port = f"{host}:{port}" if port else host

    # Manually construct the redirect URI
    redirect_uri = f"{scheme}://{host_port}/auth"
    return await oauth.cognito.authorize_redirect(request, redirect_uri)


async def auth(request: Request):
    access_token = await oauth.cognito.authorize_access_token(request)
    request.session["user"] = dict(access_token)["userinfo"]
    return RedirectResponse(url="/vulnerability-analyst")


def get_user(request: Request):
    return request.session.get("user", None)


# A FastAPI dependency to enforce authentication
oauth2_scheme = HTTPBearer()


def get_cognito_user(token: str = Depends(oauth2_scheme)):  # noqa: B008
    token = token.credentials  # Extract the JWT from the Bearer token
    try:
        # Decode the JWT and verify its signature using Cognito public keys
        unverified_header = jwt.get_unverified_header(token)
        rsa_key = {}
        for key in JWKS["keys"]:
            if key["kid"] == unverified_header["kid"]:
                rsa_key = {
                    "kty": key["kty"],
                    "kid": key["kid"],
                    "use": key["use"],
                    "n": key["n"],
                    "e": key["e"],
                }
        if rsa_key:
            payload = jwt.decode(
                token,
                rsa_key,
                algorithms=["RS256"],
                audience=COGNITO_CLIENT_ID,
                issuer=None if MOTO else COGNITO_ISSUER,
            )
            return payload  # User info is in payload
        else:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Could not verify credentials",
                headers={"WWW-Authenticate": "Bearer"},
            )
    except JWTError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        ) from e
