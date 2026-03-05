"""
LangChain tools for CRUD operations on calendar events.
These tools interact with the backend API.
"""

import os
from pathlib import Path
from typing import Optional
import requests
from langchain_core.tools import tool
from dotenv import load_dotenv

# Load .env from project root
root_dir = Path(__file__).parent.parent
load_dotenv(root_dir / ".env")

BASE_URL = os.getenv("BASE_URL", "http://localhost:8000")

# Token storage (set by the chat session)
_auth_token: Optional[str] = None


def set_auth_token(token: str) -> None:
    """Set the authentication token for API requests."""
    global _auth_token
    _auth_token = token


def get_auth_token() -> Optional[str]:
    """Get the current authentication token."""
    return _auth_token


def _api_request(method: str, endpoint: str, **kwargs) -> requests.Response:
    """Make an authenticated API request."""
    url = f"{BASE_URL}{endpoint}"
    headers = kwargs.pop("headers", {})
    if _auth_token:
        headers["Authorization"] = f"Bearer {_auth_token}"
    kwargs["headers"] = headers
    return getattr(requests, method)(url, **kwargs)


@tool
def list_events() -> str:
    """
    List all calendar events for the current user.
    Returns a formatted list of all events with their details.
    """
    try:
        response = _api_request("get", "/events")
        if response.status_code == 200:
            events = response.json()
            if not events:
                return "You have no events scheduled."
            
            result = "Your events:\n"
            for event in events:
                result += f"\n- ID {event['id']}: {event['title']}\n"
                result += f"  Start: {event['start_time']}\n"
                if event.get("end_time"):
                    result += f"  End: {event['end_time']}\n"
                if event.get("description"):
                    result += f"  Description: {event['description']}\n"
                if event.get("location"):
                    result += f"  Location: {event['location']}\n"
            return result
        else:
            return f"Error fetching events: {response.json().get('detail', 'Unknown error')}"
    except requests.RequestException as e:
        return f"Connection error: {e}"


@tool
def get_event(event_id: int) -> str:
    """
    Get details of a specific calendar event by its ID.
    
    Args:
        event_id: The ID of the event to retrieve.
    """
    try:
        response = _api_request("get", f"/events/{event_id}")
        if response.status_code == 200:
            event = response.json()
            result = f"Event Details:\n"
            result += f"- ID: {event['id']}\n"
            result += f"- Title: {event['title']}\n"
            result += f"- Start: {event['start_time']}\n"
            if event.get("end_time"):
                result += f"- End: {event['end_time']}\n"
            if event.get("description"):
                result += f"- Description: {event['description']}\n"
            if event.get("location"):
                result += f"- Location: {event['location']}\n"
            return result
        elif response.status_code == 404:
            return f"Event with ID {event_id} not found."
        else:
            return f"Error: {response.json().get('detail', 'Unknown error')}"
    except requests.RequestException as e:
        return f"Connection error: {e}"


@tool
def create_event(
    title: str,
    start_time: str,
    end_time: Optional[str] = None,
    description: Optional[str] = None,
    location: Optional[str] = None,
) -> str:
    """
    Create a new calendar event.
    
    Args:
        title: The title of the event.
        start_time: The start time in ISO format (e.g., '2026-03-05T10:00:00').
        end_time: Optional end time in ISO format.
        description: Optional description of the event.
        location: Optional location of the event.
    """
    try:
        payload = {"title": title, "start_time": start_time}
        if end_time:
            payload["end_time"] = end_time
        if description:
            payload["description"] = description
        if location:
            payload["location"] = location
        
        response = _api_request("post", "/events", json=payload)
        if response.status_code == 201:
            event = response.json()
            return f"Event '{event['title']}' created successfully with ID {event['id']}."
        else:
            return f"Error creating event: {response.json().get('detail', 'Unknown error')}"
    except requests.RequestException as e:
        return f"Connection error: {e}"


@tool
def update_event(
    event_id: int,
    title: Optional[str] = None,
    start_time: Optional[str] = None,
    end_time: Optional[str] = None,
    description: Optional[str] = None,
    location: Optional[str] = None,
) -> str:
    """
    Update an existing calendar event.
    
    Args:
        event_id: The ID of the event to update.
        title: New title for the event (optional).
        start_time: New start time in ISO format (optional).
        end_time: New end time in ISO format (optional).
        description: New description (optional).
        location: New location (optional).
    """
    try:
        payload = {}
        if title is not None:
            payload["title"] = title
        if start_time is not None:
            payload["start_time"] = start_time
        if end_time is not None:
            payload["end_time"] = end_time
        if description is not None:
            payload["description"] = description
        if location is not None:
            payload["location"] = location
        
        if not payload:
            return "No updates provided. Please specify at least one field to update."
        
        response = _api_request("put", f"/events/{event_id}", json=payload)
        if response.status_code == 200:
            event = response.json()
            return f"Event {event_id} updated successfully. New title: '{event['title']}'."
        elif response.status_code == 404:
            return f"Event with ID {event_id} not found."
        else:
            return f"Error updating event: {response.json().get('detail', 'Unknown error')}"
    except requests.RequestException as e:
        return f"Connection error: {e}"


@tool
def delete_event(event_id: int) -> str:
    """
    Delete a calendar event.
    
    Args:
        event_id: The ID of the event to delete.
    """
    try:
        response = _api_request("delete", f"/events/{event_id}")
        if response.status_code == 204:
            return f"Event {event_id} deleted successfully."
        elif response.status_code == 404:
            return f"Event with ID {event_id} not found."
        else:
            return f"Error deleting event: {response.json().get('detail', 'Unknown error')}"
    except requests.RequestException as e:
        return f"Connection error: {e}"


# Export all tools
all_tools = [list_events, get_event, create_event, update_event, delete_event]
