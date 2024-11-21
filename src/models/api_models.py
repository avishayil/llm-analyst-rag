from pydantic import BaseModel, constr


class AnalysisRequest(BaseModel):
    """Model for requesting vulnerability analyst."""

    criteria: constr(
        max_length=100, strict=True
    )  # Product, vendor, category, or severity


class Authentication(BaseModel):
    """Model for authentication requests."""

    username: constr(max_length=50, strict=True)  # Limit username to 50 characters
    password: constr(max_length=30, strict=True)  # Limit password to 30 characters


class HealthCheck(BaseModel):
    """Response model to validate and return when performing a health check."""

    status: str = "OK"
