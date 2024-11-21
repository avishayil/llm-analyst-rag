from fastapi import APIRouter, Depends, HTTPException, Request, status
from slowapi import Limiter
from slowapi.util import get_remote_address
from starlette.responses import RedirectResponse

from src.auth_utils.aws_utils import signin
from src.auth_utils.oauth_utils import auth, get_user, login
from src.models.api_models import Authentication, HealthCheck

limiter = Limiter(key_func=get_remote_address)

# Define the API router with a prefix for API routes
api_router = APIRouter(prefix="/api/v1")

# Define a router for non-API routes
main_router = APIRouter()


@main_router.get(path="/")
async def public(user: dict = Depends(get_user)):  # noqa: B008
    if user:
        return RedirectResponse(url="/vulnerability-analyst")
    return RedirectResponse(url="/login-page")


@main_router.get(path="/logout")
async def logout(request: Request):
    request.session.pop("user", None)
    return RedirectResponse(url="/")


@main_router.get(path="/login")
async def login_route(request: Request):
    return await login(request)


@main_router.get(path="/auth", name="auth")  # Ensure the name "auth" is specified here
async def auth_route(request: Request):
    return await auth(request)


@main_router.get(
    path="/health",
    tags=["healthcheck"],
    summary="Perform a Health Check",
    response_description="Return HTTP Status Code 200 (OK)",
    status_code=status.HTTP_200_OK,
    response_model=HealthCheck,
)
def get_health() -> HealthCheck:
    """
    ## Perform a Health Check
    Endpoint to perform a healthcheck on. This endpoint can primarily be used Docker
    to ensure a robust container orchestration and management is in place. Other
    services which rely on proper functioning of the API service will not deploy if this
    endpoint returns any other HTTP status code except 200 (OK).
    Returns:
        HealthCheck: Returns a JSON response with the health status
    """
    return HealthCheck(status="OK")


@api_router.post(path="/signin")
@limiter.limit(limit_value="3/minute")
async def signin_route(request: Request, authentication: Authentication):
    username = authentication.username
    password = authentication.password

    if not username or not password:
        raise HTTPException(status_code=400, detail="Username and password required")

    result = signin(username=username, password=password)

    return result["AuthenticationResult"]["IdToken"]
