import pytest
from fastapi.testclient import TestClient


@pytest.fixture
def client():
    from app import init_app

    app = init_app()
    with TestClient(app) as test_client:
        yield test_client
