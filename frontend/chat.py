"""
Chat interface for calendar management using LangGraph and ChatOllama.
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
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "llama3.2")


def clear_screen():
    """Clear the terminal screen."""
    os.system("clear" if os.name != "nt" else "cls")


def print_header(title: str):
    """Print a styled header."""
    clear_screen()
    print("=" * 60)
    print(f"  MeChat - {title}")
    print("=" * 60)
    print()


def login() -> tuple[str, str] | None:
    """Handle user login. Returns (token, username) or None if failed."""
    print_header("Login")
    
    username = input("Username: ").strip()
    password = getpass.getpass("Password: ")
    
    if not username or not password:
        print("\nUsername and password are required.")
        input("\nPress Enter to continue...")
        return None
    
    try:
        response = requests.post(
            f"{BASE_URL}/login",
            data={"username": username, "password": password},
        )
        if response.status_code == 200:
            data = response.json()
            print(f"\nWelcome back, {username}!")
            input("\nPress Enter to start chatting...")
            return (data["access_token"], username)
        else:
            print(f"\nLogin failed: {response.json().get('detail', 'Unknown error')}")
            input("\nPress Enter to continue...")
            return None
    except requests.RequestException as e:
        print(f"\nConnection error: {e}")
        print("Make sure the backend server is running.")
        input("\nPress Enter to continue...")
        return None


def register() -> bool:
    """Handle user registration."""
    print_header("Register")
    
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


def auth_menu() -> tuple[str, str] | None:
    """Show authentication menu. Returns (token, username) or None to exit."""
    while True:
        print_header("Welcome")
        print("Please login or register to continue.\n")
        print("  [1] Login")
        print("  [2] Register")
        print("  [3] Exit")
        print()
        
        choice = input("Enter your choice: ").strip()
        
        if choice == "1":
            result = login()
            if result:
                return result
        elif choice == "2":
            register()
        elif choice == "3":
            return None
        else:
            print("Invalid choice. Please try again.")
            input("\nPress Enter to continue...")


def chat_loop(token: str, username: str):
    """Main chat loop with the calendar agent."""
    # Import here to avoid loading heavy dependencies unnecessarily
    from frontend.tools import set_auth_token
    from frontend.agent import CalendarAgent
    
    # Set the auth token for API calls
    set_auth_token(token)
    
    # Create the agent
    print_header(f"Chat ({username})")
    print(f"Loading AI assistant (model: {OLLAMA_MODEL})...")
    
    try:
        agent = CalendarAgent(model_name=OLLAMA_MODEL)
    except Exception as e:
        print(f"\nError loading AI model: {e}")
        print("\nMake sure Ollama is running and the model is available.")
        print(f"You can pull the model with: ollama pull {OLLAMA_MODEL}")
        input("\nPress Enter to exit...")
        return
    
    print_header(f"Chat ({username})")
    print("I'm your calendar assistant! I can help you manage your events.")
    print("You can ask me to:")
    print("  - List your events")
    print("  - Create new events")
    print("  - Update existing events")
    print("  - Delete events")
    print()
    print("Type 'quit' or 'exit' to logout.")
    print("Type 'clear' to clear the conversation history.")
    print("-" * 60)
    print()
    
    while True:
        try:
            user_input = input("You: ").strip()
            
            if not user_input:
                continue
            
            if user_input.lower() in ["quit", "exit", "logout"]:
                print("\nGoodbye!")
                break
            
            if user_input.lower() == "clear":
                agent.reset()
                print_header(f"Chat ({username})")
                print("Conversation cleared. How can I help you?")
                print("-" * 60)
                print()
                continue
            
            # Get response from agent
            print()
            response = agent.chat(user_input)
            print(f"Assistant: {response}")
            print()
            
        except KeyboardInterrupt:
            print("\n\nGoodbye!")
            break
        except Exception as e:
            print(f"\nError: {e}")
            print("Please try again.\n")


def main():
    """Main entry point."""
    try:
        while True:
            result = auth_menu()
            if result is None:
                print("\nGoodbye!")
                sys.exit(0)
            
            token, username = result
            chat_loop(token, username)
            
    except KeyboardInterrupt:
        print("\n\nGoodbye!")
        sys.exit(0)


if __name__ == "__main__":
    main()
