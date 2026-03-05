"""
Tests for AI agent tools.
Based on: flows/05_debug_agent.py
"""

import os
import pytest
import requests
from pathlib import Path


# Skip all tests in this module if Ollama is not available
pytestmark = pytest.mark.skipif(
    os.getenv("SKIP_AI_TESTS", "false").lower() == "true",
    reason="AI tests skipped (set SKIP_AI_TESTS=false to run)"
)


class TestEventTools:
    """Test the LangChain tools directly (without the LLM)."""

    def test_list_events_tool(self, base_url, auth_token, create_test_event):
        """Test the list_events tool."""
        from frontend.tools import list_events, set_auth_token
        
        # Create a test event
        event = create_test_event(title="Tool Test Event")
        
        # Set auth and call tool
        set_auth_token(auth_token)
        result = list_events.invoke({})
        
        assert "Tool Test Event" in result
        assert "Your events:" in result

    def test_create_event_tool(self, base_url, auth_token, auth_headers):
        """Test the create_event tool."""
        from frontend.tools import create_event, set_auth_token
        
        set_auth_token(auth_token)
        result = create_event.invoke({
            "title": "Created by Tool",
            "start_time": "2026-03-15T10:00:00",
            "description": "Tool test",
        })
        
        assert "created successfully" in result.lower()
        assert "Created by Tool" in result
        
        # Cleanup: find and delete the event
        events_response = requests.get(f"{base_url}/events", headers=auth_headers)
        for event in events_response.json():
            if event["title"] == "Created by Tool":
                requests.delete(f"{base_url}/events/{event['id']}", headers=auth_headers)

    def test_update_event_tool(self, base_url, auth_token, create_test_event):
        """Test the update_event tool."""
        from frontend.tools import update_event, set_auth_token
        
        event = create_test_event(title="Before Update")
        
        set_auth_token(auth_token)
        result = update_event.invoke({
            "event_id": event["id"],
            "title": "After Update",
        })
        
        assert "updated successfully" in result.lower()

    def test_delete_event_tool(self, base_url, auth_token, auth_headers):
        """Test the delete_event tool."""
        from frontend.tools import delete_event, set_auth_token
        
        # Create an event to delete
        create_response = requests.post(
            f"{base_url}/events",
            json={"title": "Delete via Tool", "start_time": "2026-03-16T10:00:00"},
            headers=auth_headers,
        )
        event = create_response.json()
        
        set_auth_token(auth_token)
        result = delete_event.invoke({"event_id": event["id"]})
        
        assert "deleted successfully" in result.lower()

    def test_get_event_tool(self, base_url, auth_token, create_test_event):
        """Test the get_event tool."""
        from frontend.tools import get_event, set_auth_token
        
        event = create_test_event(title="Get This Event", description="Detailed description")
        
        set_auth_token(auth_token)
        result = get_event.invoke({"event_id": event["id"]})
        
        assert "Get This Event" in result
        assert "Detailed description" in result

    def test_list_events_no_events(self, base_url, auth_headers):
        """Test list_events when user has no events."""
        from frontend.tools import list_events, set_auth_token
        
        # Create a new user with no events
        import uuid
        unique_user = f"empty_user_{uuid.uuid4().hex[:8]}"
        
        # Register
        requests.post(
            f"{base_url}/users",
            json={"username": unique_user, "password": "password123"},
        )
        
        # Login
        login_response = requests.post(
            f"{base_url}/login",
            data={"username": unique_user, "password": "password123"},
        )
        token = login_response.json()["access_token"]
        
        set_auth_token(token)
        result = list_events.invoke({})
        
        assert "no events" in result.lower()
        
        # Cleanup
        me_response = requests.get(
            f"{base_url}/me",
            headers={"Authorization": f"Bearer {token}"},
        )
        user_id = me_response.json()["id"]
        requests.delete(
            f"{base_url}/users/{user_id}",
            headers={"Authorization": f"Bearer {token}"},
        )


@pytest.mark.slow
class TestCalendarAgent:
    """Test the full AI agent (requires Ollama)."""

    @pytest.fixture
    def agent(self, auth_token):
        """Create a CalendarAgent for testing."""
        from frontend.tools import set_auth_token
        from frontend.agent import CalendarAgent
        
        set_auth_token(auth_token)
        
        model = os.getenv("OLLAMA_MODEL", "llama3.2")
        return CalendarAgent(model_name=model)

    def test_agent_list_events(self, agent, create_test_event):
        """Test that the agent can list events."""
        event = create_test_event(title="Agent Test Event")
        
        response = agent.chat("List my events")
        
        # The response should contain event info
        assert "Agent Test Event" in response or "event" in response.lower()

    def test_agent_conversation_memory(self, agent):
        """Test that the agent maintains conversation history."""
        # First message
        response1 = agent.chat("Hello, what can you help me with?")
        assert len(response1) > 0
        
        # Second message - agent should remember context
        response2 = agent.chat("What did I just ask you?")
        assert len(response2) > 0
        
        # History should have multiple messages
        assert len(agent.messages) > 2

    def test_agent_reset(self, agent):
        """Test that agent reset clears history."""
        agent.chat("Hello")
        initial_count = len(agent.messages)
        
        agent.reset()
        
        # Should only have system message
        assert len(agent.messages) == 1
        assert len(agent.messages) < initial_count
