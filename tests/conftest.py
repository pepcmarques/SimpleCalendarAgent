"""
Pytest configuration and shared fixtures for MeChat tests.
"""

import os
import sys
from pathlib import Path

import pytest
import requests
from dotenv import load_dotenv

# Add project root to path
root_dir = Path(__file__).parent.parent
sys.path.insert(0, str(root_dir))

# Load environment
load_dotenv(root_dir / ".env")

BASE_URL = os.getenv("BASE_URL", "http://localhost:8000")
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "llama3.2:3b")

# Test user credentials
TEST_USER = {
    "username": "pytest_user",
    "password": "pytest_password123",
    "email": "pytest@example.com",
}


@pytest.fixture(scope="session")
def base_url():
    """Return the API base URL."""
    return BASE_URL


@pytest.fixture(scope="session")
def test_user_data():
    """Return test user data."""
    return TEST_USER.copy()


@pytest.fixture(scope="session")
def registered_user(base_url, test_user_data):
    """
    Register a test user for the session.
    Cleans up by deleting the user after all tests.
    """
    # Try to create the user (may already exist)
    response = requests.post(
        f"{base_url}/users",
        json=test_user_data,
    )
    
    if response.status_code == 201:
        user = response.json()
    elif response.status_code == 400 and "already registered" in response.json().get("detail", ""):
        # User exists, login to get their info
        login_response = requests.post(
            f"{base_url}/login",
            data={"username": test_user_data["username"], "password": test_user_data["password"]},
        )
        login_response.raise_for_status()
        token = login_response.json()["access_token"]
        me_response = requests.get(
            f"{base_url}/me",
            headers={"Authorization": f"Bearer {token}"},
        )
        me_response.raise_for_status()
        user = me_response.json()
    else:
        response.raise_for_status()
        user = response.json()
    
    yield user
    
    # Cleanup: delete the test user
    try:
        login_response = requests.post(
            f"{base_url}/login",
            data={"username": test_user_data["username"], "password": test_user_data["password"]},
        )
        if login_response.status_code == 200:
            token = login_response.json()["access_token"]
            requests.delete(
                f"{base_url}/users/{user['id']}",
                headers={"Authorization": f"Bearer {token}"},
            )
    except Exception:
        pass  # Ignore cleanup errors


@pytest.fixture(scope="function")
def auth_token(base_url, test_user_data, registered_user):
    """Get a fresh authentication token for the test user."""
    response = requests.post(
        f"{base_url}/login",
        data={"username": test_user_data["username"], "password": test_user_data["password"]},
    )
    response.raise_for_status()
    return response.json()["access_token"]


@pytest.fixture(scope="function")
def auth_headers(auth_token):
    """Return authorization headers."""
    return {"Authorization": f"Bearer {auth_token}"}


@pytest.fixture
def create_test_event(base_url, auth_headers):
    """
    Factory fixture to create test events.
    Returns a function that creates events and tracks them for cleanup.
    """
    created_event_ids = []
    
    def _create_event(title="Test Event", start_time="2026-03-10T10:00:00", **kwargs):
        payload = {"title": title, "start_time": start_time, **kwargs}
        response = requests.post(
            f"{base_url}/events",
            json=payload,
            headers=auth_headers,
        )
        response.raise_for_status()
        event = response.json()
        created_event_ids.append(event["id"])
        return event
    
    yield _create_event
    
    # Cleanup: delete created events
    for event_id in created_event_ids:
        try:
            requests.delete(f"{base_url}/events/{event_id}", headers=auth_headers)
        except Exception:
            pass
