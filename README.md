# Simple Calendar Management with AI

A calendar management application with FastAPI backend, CLI frontend, and AI-powered chat using LangGraph + Ollama.

## Features

- **User Management**: Register, login, logout with JWT authentication
- **Event CRUD**: Create, read, update, delete calendar events
- **AI Chat**: Natural language interface to manage events using LangGraph + Ollama
- **CLI Interface**: Interactive menu-driven terminal application

## Project Structure

```
SimpleCalendarAgent/
├── backend/
│   ├── main.py          # FastAPI app with user and event endpoints
│   ├── auth.py          # JWT authentication and password hashing
│   ├── database.py      # JSON-based database operations
│   └── models.py        # Pydantic schemas
├── frontend/
│   ├── cli.py           # Interactive CLI menu
│   ├── agent.py         # LangGraph ReAct agent
│   ├── chat.py          # Chat interface
│   └── tools.py         # LangChain tools for event operations
├── tests/               # Pytest test suite
├── database.json        # JSON database file
└── requirements.txt
```

## Setup

```bash
# Create virtual environment
python -m venv .venv
source .venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Set up environment variables
cp .env.example .env  # or create .env with OLLAMA_MODEL=llama3.2

# Create the database
echo {} > database.json

# Ollama
ollama pull llama3.2:3b
```

**Note:** This system uses a JSON file as "database" to make it as simple as possible

## Running

### Start LLM
```bash
ollama serve
```

### Start the backend server

```bash
python -m uvicorn backend.main:app --reload
```

### Start the CLI frontend (in another terminal)

```bash
python -m frontend.cli
```

### Run tests

```bash
pytest tests/ -v
```

## Environment Variables

| Variable       | Default       | Description              |
| -------------- | ------------- | ------------------------ |
| `OLLAMA_MODEL` | `llama3.2:3b` | Ollama model for AI chat |

## Requirements

- Python 3.11+
- Ollama running locally (for AI chat feature)
