"""
Tests for event CRUD operations.
Based on: flows/03_flow.py and flows/04_flow.py
"""

import pytest
import requests


class TestEventAuthentication:
    """Test that event endpoints require authentication."""

    def test_create_event_without_auth(self, base_url):
        """Test that creating an event without auth fails (flow 03)."""
        payload = {
            "title": "Unauthorized Event",
            "start_time": "2026-03-05T10:00:00",
        }
        
        response = requests.post(f"{base_url}/events", json=payload)
        
        assert response.status_code == 401
        assert response.json()["detail"] == "Not authenticated"

    def test_list_events_without_auth(self, base_url):
        """Test that listing events without auth fails."""
        response = requests.get(f"{base_url}/events")
        
        assert response.status_code == 401

    def test_get_event_without_auth(self, base_url):
        """Test that getting an event without auth fails."""
        response = requests.get(f"{base_url}/events/1")
        
        assert response.status_code == 401

    def test_update_event_without_auth(self, base_url):
        """Test that updating an event without auth fails."""
        response = requests.put(
            f"{base_url}/events/1",
            json={"title": "Updated"},
        )
        
        assert response.status_code == 401

    def test_delete_event_without_auth(self, base_url):
        """Test that deleting an event without auth fails."""
        response = requests.delete(f"{base_url}/events/1")
        
        assert response.status_code == 401


class TestEventCRUD:
    """Test event CRUD operations with authentication."""

    def test_create_event_success(self, base_url, auth_headers):
        """Test creating an event with auth succeeds (flow 04)."""
        payload = {
            "title": "Test Meeting",
            "start_time": "2026-03-10T14:00:00",
            "end_time": "2026-03-10T15:00:00",
            "description": "A test meeting",
            "location": "Test Room",
        }
        
        response = requests.post(
            f"{base_url}/events",
            json=payload,
            headers=auth_headers,
        )
        
        assert response.status_code == 201
        event = response.json()
        assert event["title"] == payload["title"]
        assert event["start_time"] == payload["start_time"]
        assert event["end_time"] == payload["end_time"]
        assert event["description"] == payload["description"]
        assert event["location"] == payload["location"]
        assert "id" in event
        assert "user_id" in event
        
        # Cleanup
        requests.delete(f"{base_url}/events/{event['id']}", headers=auth_headers)

    def test_create_event_minimal(self, base_url, auth_headers):
        """Test creating an event with only required fields."""
        payload = {
            "title": "Minimal Event",
            "start_time": "2026-03-11T09:00:00",
        }
        
        response = requests.post(
            f"{base_url}/events",
            json=payload,
            headers=auth_headers,
        )
        
        assert response.status_code == 201
        event = response.json()
        assert event["title"] == payload["title"]
        assert event["start_time"] == payload["start_time"]
        assert event["end_time"] is None
        assert event["description"] is None
        assert event["location"] is None
        
        # Cleanup
        requests.delete(f"{base_url}/events/{event['id']}", headers=auth_headers)

    def test_list_events(self, base_url, auth_headers, create_test_event):
        """Test listing user's events."""
        # Create some events
        event1 = create_test_event(title="Event 1")
        event2 = create_test_event(title="Event 2")
        
        response = requests.get(f"{base_url}/events", headers=auth_headers)
        
        assert response.status_code == 200
        events = response.json()
        assert isinstance(events, list)
        
        # Our created events should be in the list
        event_ids = [e["id"] for e in events]
        assert event1["id"] in event_ids
        assert event2["id"] in event_ids

    def test_get_event_success(self, base_url, auth_headers, create_test_event):
        """Test getting a specific event."""
        event = create_test_event(title="Get This Event")
        
        response = requests.get(
            f"{base_url}/events/{event['id']}",
            headers=auth_headers,
        )
        
        assert response.status_code == 200
        fetched_event = response.json()
        assert fetched_event["id"] == event["id"]
        assert fetched_event["title"] == "Get This Event"

    def test_get_event_not_found(self, base_url, auth_headers):
        """Test getting a non-existent event."""
        response = requests.get(
            f"{base_url}/events/99999",
            headers=auth_headers,
        )
        
        assert response.status_code == 404

    def test_update_event_success(self, base_url, auth_headers, create_test_event):
        """Test updating an event."""
        event = create_test_event(title="Original Title")
        
        response = requests.put(
            f"{base_url}/events/{event['id']}",
            json={
                "title": "Updated Title",
                "location": "New Location",
            },
            headers=auth_headers,
        )
        
        assert response.status_code == 200
        updated_event = response.json()
        assert updated_event["title"] == "Updated Title"
        assert updated_event["location"] == "New Location"
        # Other fields should remain unchanged
        assert updated_event["start_time"] == event["start_time"]

    def test_update_event_not_found(self, base_url, auth_headers):
        """Test updating a non-existent event."""
        response = requests.put(
            f"{base_url}/events/99999",
            json={"title": "Doesn't Matter"},
            headers=auth_headers,
        )
        
        assert response.status_code == 404

    def test_delete_event_success(self, base_url, auth_headers):
        """Test deleting an event."""
        # Create an event specifically for deletion
        create_response = requests.post(
            f"{base_url}/events",
            json={"title": "Delete Me", "start_time": "2026-03-12T10:00:00"},
            headers=auth_headers,
        )
        event = create_response.json()
        
        # Delete it
        response = requests.delete(
            f"{base_url}/events/{event['id']}",
            headers=auth_headers,
        )
        
        assert response.status_code == 204
        
        # Verify it's gone
        get_response = requests.get(
            f"{base_url}/events/{event['id']}",
            headers=auth_headers,
        )
        assert get_response.status_code == 404

    def test_delete_event_not_found(self, base_url, auth_headers):
        """Test deleting a non-existent event."""
        response = requests.delete(
            f"{base_url}/events/99999",
            headers=auth_headers,
        )
        
        assert response.status_code == 404
