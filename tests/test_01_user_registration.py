"""
Tests for user registration and management.
Based on: flows/01_flow.py
"""

import pytest
import requests


class TestUserRegistration:
    """Test user registration functionality."""

    def test_create_user_success(self, base_url):
        """Test successful user creation."""
        # Use unique username to avoid conflicts
        import uuid
        unique_username = f"test_user_{uuid.uuid4().hex[:8]}"
        
        payload = {
            "username": unique_username,
            "password": "testpassword123",
            "email": f"{unique_username}@example.com",
        }
        
        response = requests.post(f"{base_url}/users", json=payload)
        
        assert response.status_code == 201
        user = response.json()
        assert user["username"] == unique_username
        assert user["email"] == payload["email"]
        assert "id" in user
        assert "password" not in user  # Password should not be returned
        
        # Cleanup: delete the created user
        login_response = requests.post(
            f"{base_url}/login",
            data={"username": unique_username, "password": "testpassword123"},
        )
        if login_response.status_code == 200:
            token = login_response.json()["access_token"]
            requests.delete(
                f"{base_url}/users/{user['id']}",
                headers={"Authorization": f"Bearer {token}"},
            )

    def test_create_user_duplicate_username(self, base_url, registered_user, test_user_data):
        """Test that duplicate usernames are rejected."""
        payload = {
            "username": test_user_data["username"],
            "password": "differentpassword",
            "email": "different@example.com",
        }
        
        response = requests.post(f"{base_url}/users", json=payload)
        
        assert response.status_code == 400
        assert "already registered" in response.json()["detail"].lower()

    def test_create_user_missing_password(self, base_url):
        """Test that password is required."""
        payload = {
            "username": "incomplete_user",
        }
        
        response = requests.post(f"{base_url}/users", json=payload)
        
        assert response.status_code == 422  # Validation error
