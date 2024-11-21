def test_public_route(client):
    """Test access to the public root route."""
    response = client.get("/", follow_redirects=False)
    assert response.status_code == 307  # Redirect to /login-page if not logged in


def test_login_page(client):
    """Test access to the login page."""
    response = client.get("/login-page")
    assert response.status_code == 200


def test_vulnerability_patch_assistant_ui(client):
    """Test access to the vulnerability analyst UI."""
    response = client.get("/vulnerability-analyst", follow_redirects=False)
    assert response.status_code == 307  # Redirect to login if not authenticated


def test_logout_route(client):
    """Test the logout route."""
    response = client.get("/logout", follow_redirects=False)
    assert response.status_code == 307  # Redirect after logout
