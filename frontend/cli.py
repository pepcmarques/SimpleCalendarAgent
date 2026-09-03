"""
Text-based frontend interface for Simple Calendar Agent
Provides an interactive CLI for user authentication and event management.
"""

import os
import sys
import getpass
from pathlib import Path
import requests
from dotenv import load_dotenv

# Load .env from project root
root_dir = Path(__file__).parent.parent
load_dotenv(root_dir / ".env")

BASE_URL = os.getenv("BASE_URL", "http://localhost:8000")
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "llama3.2:3b")


class SCACLI:
    def __init__(self):
        self.token = None
        self.username = None

    def clear_screen(self):
        """Clear the terminal screen."""
        os.system("clear" if os.name != "nt" else "cls")

    def print_header(self, title: str):
        """Print a styled header."""
        self.clear_screen()
        print("=" * 50)
        print(f"  Simple Calendar Agent - {title}")
        print("=" * 50)
        print()

    def print_menu(self, options: list[str]):
        """Print menu options."""
        for i, option in enumerate(options, 1):
            print(f"  [{i}] {option}")
        print()

    def get_choice(self, max_choice: int) -> int:
        """Get user's menu choice."""
        while True:
            try:
                choice = input("Enter your choice: ").strip()
                if choice.lower() == "q":
                    return 0
                choice_int = int(choice)
                if 1 <= choice_int <= max_choice:
                    return choice_int
                print(f"Please enter a number between 1 and {max_choice}")
            except ValueError:
                print("Invalid input. Please enter a number.")

    def api_request(self, method: str, endpoint: str, **kwargs) -> requests.Response:
        """Make an API request."""
        url = f"{BASE_URL}{endpoint}"
        if self.token:
            headers = kwargs.pop("headers", {})
            headers["Authorization"] = f"Bearer {self.token}"
            kwargs["headers"] = headers
        return getattr(requests, method)(url, **kwargs)

    # ==================== Authentication ====================

    def login(self):
        """Handle user login."""
        self.print_header("Login")
        
        username = input("Username: ").strip()
        password = getpass.getpass("Password: ")
        
        if not username or not password:
            print("\nUsername and password are required.")
            input("\nPress Enter to continue...")
            return False
        
        try:
            response = requests.post(
                f"{BASE_URL}/login",
                data={"username": username, "password": password},
            )
            if response.status_code == 200:
                data = response.json()
                self.token = data["access_token"]
                self.username = username
                print(f"\nWelcome back, {username}!")
                input("\nPress Enter to continue...")
                return True
            else:
                print(f"\nLogin failed: {response.json().get('detail', 'Unknown error')}")
                input("\nPress Enter to continue...")
                return False
        except requests.RequestException as e:
            print(f"\nConnection error: {e}")
            input("\nPress Enter to continue...")
            return False

    def register(self):
        """Handle user registration."""
        self.print_header("Register")
        
        username = input("Username: ").strip()
        email = input("Email (optional): ").strip() or None
        password = getpass.getpass("Password: ")
        confirm_password = getpass.getpass("Confirm Password: ")
        
        if not username or not password:
            print("\nUsername and password are required.")
            input("\nPress Enter to continue...")
            return False
        
        if password != confirm_password:
            print("\nPasswords do not match.")
            input("\nPress Enter to continue...")
            return False
        
        try:
            response = requests.post(
                f"{BASE_URL}/users",
                json={"username": username, "email": email, "password": password},
            )
            if response.status_code == 201:
                print(f"\nAccount created successfully! You can now login as {username}.")
                input("\nPress Enter to continue...")
                return True
            else:
                print(f"\nRegistration failed: {response.json().get('detail', 'Unknown error')}")
                input("\nPress Enter to continue...")
                return False
        except requests.RequestException as e:
            print(f"\nConnection error: {e}")
            input("\nPress Enter to continue...")
            return False

    def logout(self):
        """Handle user logout."""
        if self.token:
            try:
                self.api_request("post", "/logout")
            except requests.RequestException:
                pass
        self.token = None
        self.username = None
        print("\nYou have been logged out.")
        input("\nPress Enter to continue...")

    # ==================== Events ====================

    def list_events(self):
        """List all events for the current user."""
        self.print_header("My Events")
        
        try:
            response = self.api_request("get", "/events")
            if response.status_code == 200:
                events = response.json()
                if not events:
                    print("No events found.")
                else:
                    for event in events:
                        print(f"  [{event['id']}] {event['title']}")
                        print(f"      Start: {event['start_time']}")
                        if event.get("end_time"):
                            print(f"      End: {event['end_time']}")
                        if event.get("location"):
                            print(f"      Location: {event['location']}")
                        print()
            else:
                print(f"Error: {response.json().get('detail', 'Unknown error')}")
        except requests.RequestException as e:
            print(f"Connection error: {e}")
        
        input("\nPress Enter to continue...")

    def create_event(self):
        """Create a new event."""
        self.print_header("Create Event")
        
        title = input("Title: ").strip()
        if not title:
            print("\nTitle is required.")
            input("\nPress Enter to continue...")
            return
        
        start_time = input("Start time (YYYY-MM-DDTHH:MM:SS): ").strip()
        if not start_time:
            print("\nStart time is required.")
            input("\nPress Enter to continue...")
            return
        
        end_time = input("End time (optional): ").strip() or None
        description = input("Description (optional): ").strip() or None
        location = input("Location (optional): ").strip() or None
        
        payload = {"title": title, "start_time": start_time}
        if end_time:
            payload["end_time"] = end_time
        if description:
            payload["description"] = description
        if location:
            payload["location"] = location
        
        try:
            response = self.api_request("post", "/events", json=payload)
            if response.status_code == 201:
                event = response.json()
                print(f"\nEvent '{event['title']}' created with ID {event['id']}!")
            else:
                print(f"\nError: {response.json().get('detail', 'Unknown error')}")
        except requests.RequestException as e:
            print(f"\nConnection error: {e}")
        
        input("\nPress Enter to continue...")

    def delete_event(self):
        """Delete an event."""
        self.print_header("Delete Event")
        
        event_id = input("Enter event ID to delete: ").strip()
        if not event_id:
            return
        
        try:
            event_id = int(event_id)
            response = self.api_request("delete", f"/events/{event_id}")
            if response.status_code == 204:
                print("\nEvent deleted successfully!")
            else:
                print(f"\nError: {response.json().get('detail', 'Unknown error')}")
        except ValueError:
            print("\nInvalid event ID.")
        except requests.RequestException as e:
            print(f"\nConnection error: {e}")
        
        input("\nPress Enter to continue...")

    # ==================== AI Chat ====================

    def chat_with_ai(self):
        """Start an AI chat session for managing events."""
        from frontend.tools import set_auth_token
        from frontend.agent import CalendarAgent
        
        # Set the auth token for API calls
        set_auth_token(self.token)
        
        self.print_header(f"AI Chat ({self.username})")
        print(f"Loading AI assistant (model: {OLLAMA_MODEL})...")
        
        try:
            agent = CalendarAgent(model_name=OLLAMA_MODEL)
        except Exception as e:
            print(f"\nError loading AI model: {e}")
            print("\nMake sure Ollama is running and the model is available.")
            print(f"You can pull the model with: ollama pull {OLLAMA_MODEL}")
            input("\nPress Enter to go back...")
            return
        
        self.print_header(f"AI Chat ({self.username})")
        print("I'm your calendar assistant! I can help you manage your events.")
        print("You can ask me to:")
        print("  - List your events")
        print("  - Create new events")
        print("  - Update existing events")
        print("  - Delete events")
        print()
        print("Type 'back' to return to the menu.")
        print("Type 'clear' to clear the conversation history.")
        print("-" * 50)
        print()
        
        while True:
            try:
                user_input = input("You: ").strip()
                
                if not user_input:
                    continue
                
                if user_input.lower() in ["back", "exit", "quit"]:
                    break
                
                if user_input.lower() == "clear":
                    agent.reset()
                    self.print_header(f"AI Chat ({self.username})")
                    print("Conversation cleared. How can I help you?")
                    print("-" * 50)
                    print()
                    continue
                
                # Get response from agent
                print()
                response = agent.chat(user_input)
                print(f"Assistant: {response}")
                print()
                
            except KeyboardInterrupt:
                print("\n")
                break
            except Exception as e:
                print(f"\nError: {e}")
                print("Please try again.\n")

    # ==================== Menus ====================

    def main_menu_logged_out(self):
        """Show main menu for logged out users."""
        while True:
            self.print_header("Welcome")
            print("Please login or register to continue.\n")
            self.print_menu(["Login", "Register", "Exit"])
            
            choice = self.get_choice(3)
            
            if choice == 1:
                if self.login():
                    return True  # Logged in successfully
            elif choice == 2:
                self.register()
            elif choice == 3 or choice == 0:
                return False  # Exit app

    def main_menu_logged_in(self):
        """Show main menu for logged in users."""
        while True:
            self.print_header(f"Dashboard ({self.username})")
            self.print_menu([
                "View My Events",
                "Create Event",
                "Delete Event",
                "Chat with AI Assistant",
                "Logout",
            ])
            
            choice = self.get_choice(5)
            
            if choice == 1:
                self.list_events()
            elif choice == 2:
                self.create_event()
            elif choice == 3:
                self.delete_event()
            elif choice == 4:
                self.chat_with_ai()
            elif choice == 5 or choice == 0:
                self.logout()
                return

    def run(self):
        """Main application loop."""
        try:
            while True:
                if self.token:
                    self.main_menu_logged_in()
                else:
                    if not self.main_menu_logged_out():
                        break
        except KeyboardInterrupt:
            print("\n\nGoodbye!")
            sys.exit(0)


if __name__ == "__main__":
    cli = SCACLI()
    cli.run()
