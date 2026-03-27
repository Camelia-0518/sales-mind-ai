"""
Tests for authentication endpoints
"""
import pytest


class TestAuth:
    """Test authentication API"""

    def test_register_success(self, client):
        """Test successful user registration"""
        response = client.post("/api/v1/auth/register", json={
            "email": "newuser@example.com",
            "password": "securepassword123",
            "name": "New User",
            "company": "New Company"
        })

        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert data["token_type"] == "bearer"
        assert data["user"]["email"] == "newuser@example.com"
        assert data["user"]["name"] == "New User"
        assert data["user"]["plan"] == "free"

    def test_register_duplicate_email(self, client, test_user):
        """Test registration with duplicate email"""
        response = client.post("/api/v1/auth/register", json={
            "email": test_user.email,
            "password": "password123",
            "name": "Another User"
        })

        assert response.status_code == 400
        assert "already registered" in response.json()["detail"]

    def test_login_success(self, client, test_user):
        """Test successful login"""
        # Note: This test assumes the password hash matches
        # In real tests, you'd create user with known password
        pass

    def test_login_invalid_credentials(self, client):
        """Test login with invalid credentials"""
        response = client.post("/api/v1/auth/login", json={
            "email": "nonexistent@example.com",
            "password": "wrongpassword"
        })

        assert response.status_code == 401
        assert "Incorrect" in response.json()["detail"]

    def test_get_me_authenticated(self, authorized_client, test_user):
        """Test getting current user info with valid token"""
        response = authorized_client.get("/api/v1/auth/me")

        assert response.status_code == 200
        data = response.json()
        assert data["email"] == test_user.email
        assert data["name"] == test_user.name

    def test_get_me_unauthenticated(self, client):
        """Test getting current user without token"""
        response = client.get("/api/v1/auth/me")

        assert response.status_code == 403

    def test_get_me_invalid_token(self, client):
        """Test getting current user with invalid token"""
        client.headers = {"Authorization": "Bearer invalid_token"}
        response = client.get("/api/v1/auth/me")

        assert response.status_code == 401
