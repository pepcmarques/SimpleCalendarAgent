"""
Tests for user authentication (login/logout).
Based on: flows/02_flow.py
"""

import pytest
import requests


class TestUserLogin:
    """Test user login functionality."""

    def test_login_success(self, base_url, registered_user, test_user_data):
        """Test successful login returns access token."""
        response = requests.post(
            f"{base_url}/login",
            data={
                "username": test_user_data["username"],
                "password": test_user_data["password"],
            },
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert data["token_type"] == "bearer"
        assert len(data["access_token"]) > 0

    def test_login_wrong_password(self, base_url, registered_user, test_user_data):
        """Test login with wrong password fails."""
        response = requests.post(
            f"{base_url}/login",
            data={
                "username": test_user_data["username"],
                "password": "wrong_password",
            },
        )
        
        assert response.status_code == 401
        assert "incorrect" in response.json()["detail"].lower()

    def test_login_nonexistent_user(self, base_url):
        """Test login with non-existent user fails."""
        response = requests.post(
            f"{base_url}/login",
            data={
                "username": "nonexistent_user_xyz",
                "password": "somepassword",
            },
        )
        
        assert response.status_code == 401

    def test_get_current_user(self, base_url, auth_token):
        """Test getting current user info with valid token."""
        response = requests.get(
            f"{base_url}/me",
            headers={"Authorization": f"Bearer {auth_token}"},
        )
        
        assert response.status_code == 200
        user = response.json()
        assert "id" in user
        assert "username" in user

    def test_get_current_user_no_token(self, base_url):
        """Test accessing /me without token fails."""
        response = requests.get(f"{base_url}/me")
        
        assert response.status_code == 401

    def test_get_current_user_invalid_token(self, base_url):
        """Test accessing /me with invalid token fails."""
        response = requests.get(
            f"{base_url}/me",
            headers={"Authorization": "Bearer invalid_token_here"},
        )
        
        assert response.status_code == 401


class TestUserLogout:
    """Test user logout functionality."""

    def test_logout_success(self, base_url, registered_user, test_user_data):
        """Test successful logout invalidates token."""
        # First login to get a fresh token
        login_response = requests.post(
            f"{base_url}/login",
            data={
                "username": test_user_data["username"],
                "password": test_user_data["password"],
            },
        )
        token = login_response.json()["access_token"]
        
        # Logout
        logout_response = requests.post(
            f"{base_url}/logout",
            headers={"Authorization": f"Bearer {token}"},
        )
        
        assert logout_response.status_code == 200
        assert "logged out" in logout_response.json()["message"].lower()
        
        # Try to use the token again - should fail
        me_response = requests.get(
            f"{base_url}/me",
            headers={"Authorization": f"Bearer {token}"},
        )
        
        assert me_response.status_code == 401
