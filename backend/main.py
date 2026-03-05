"""
FastAPI backend with user CRUD and authentication endpoints.
"""

from datetime import timedelta
from typing import Optional

from fastapi import FastAPI, HTTPException, Depends, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm

from backend.database import Database
from backend.models import UserCreate, UserUpdate, UserResponse, Token, EventCreate, EventUpdate, EventResponse
from backend.auth import (
    hash_password,
    verify_password,
    create_access_token,
    decode_token,
    invalidate_token,
    ACCESS_TOKEN_EXPIRE_MINUTES,
)

app = FastAPI(title="MeChat API", version="1.0.0")
db = Database()
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="login")

# Ensure tables exist
db.create_table("users")
db.create_table("events")


def get_next_user_id() -> int:
    """Generate the next user ID."""
    users = db.get_all("users")
    if not users:
        return 1
    return max(user.get("id", 0) for user in users) + 1


def get_next_event_id() -> int:
    """Generate the next event ID."""
    events = db.get_all("events")
    if not events:
        return 1
    return max(event.get("id", 0) for event in events) + 1


async def get_current_user(token: str = Depends(oauth2_scheme)) -> dict:
    """Dependency to get the current authenticated user."""
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    payload = decode_token(token)
    if payload is None:
        raise credentials_exception
    username: str = payload.get("sub")
    if username is None:
        raise credentials_exception
    user = db.get("users", "username", username)
    if user is None:
        raise credentials_exception
    return user


# ==================== Authentication Endpoints ====================


@app.post("/login", response_model=Token, tags=["Authentication"])
async def login(form_data: OAuth2PasswordRequestForm = Depends()):
    """
    Authenticate user and return access token.
    """
    user = db.get("users", "username", form_data.username)
    if not user or not verify_password(form_data.password, user.get("password", "")):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user["username"]}, expires_delta=access_token_expires
    )
    return {"access_token": access_token, "token_type": "bearer"}


@app.post("/logout", tags=["Authentication"])
async def logout(token: str = Depends(oauth2_scheme)):
    """
    Logout user by invalidating the current token.
    """
    invalidate_token(token)
    return {"message": "Successfully logged out"}


@app.get("/me", response_model=UserResponse, tags=["Authentication"])
async def get_current_user_info(current_user: dict = Depends(get_current_user)):
    """
    Get current authenticated user info.
    """
    return UserResponse(
        id=current_user["id"],
        username=current_user["username"],
        email=current_user.get("email"),
    )


# ==================== User CRUD Endpoints ====================


@app.post("/users", response_model=UserResponse, status_code=status.HTTP_201_CREATED, tags=["Users"])
async def create_user(user: UserCreate):
    """
    Create a new user.
    """
    # Check if username already exists
    if db.get("users", "username", user.username):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username already registered",
        )
    
    new_user = {
        "id": get_next_user_id(),
        "username": user.username,
        "email": user.email,
        "password": hash_password(user.password),
    }
    db.add("users", new_user)
    return UserResponse(id=new_user["id"], username=new_user["username"], email=new_user["email"])


@app.get("/users", response_model=list[UserResponse], tags=["Users"])
async def list_users(current_user: dict = Depends(get_current_user)):
    """
    Get all users (requires authentication).
    """
    users = db.get_all("users")
    return [
        UserResponse(id=u["id"], username=u["username"], email=u.get("email"))
        for u in users
    ]


@app.get("/users/{user_id}", response_model=UserResponse, tags=["Users"])
async def get_user(user_id: int, current_user: dict = Depends(get_current_user)):
    """
    Get a specific user by ID (requires authentication).
    """
    user = db.get("users", "id", user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )
    return UserResponse(id=user["id"], username=user["username"], email=user.get("email"))


@app.put("/users/{user_id}", response_model=UserResponse, tags=["Users"])
async def update_user(
    user_id: int,
    user_update: UserUpdate,
    current_user: dict = Depends(get_current_user),
):
    """
    Update a user (requires authentication, can only update own profile).
    """
    if current_user["id"] != user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Can only update your own profile",
        )
    
    user = db.get("users", "id", user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )
    
    updates = {}
    if user_update.username is not None:
        # Check if new username is taken
        existing = db.get("users", "username", user_update.username)
        if existing and existing["id"] != user_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Username already taken",
            )
        updates["username"] = user_update.username
    if user_update.email is not None:
        updates["email"] = user_update.email
    if user_update.password is not None:
        updates["password"] = hash_password(user_update.password)
    
    if updates:
        db.update("users", "id", user_id, updates)
    
    updated_user = db.get("users", "id", user_id)
    return UserResponse(
        id=updated_user["id"],
        username=updated_user["username"],
        email=updated_user.get("email"),
    )


@app.delete("/users/{user_id}", status_code=status.HTTP_204_NO_CONTENT, tags=["Users"])
async def delete_user(user_id: int, current_user: dict = Depends(get_current_user)):
    """
    Delete a user (requires authentication, can only delete own account).
    """
    if current_user["id"] != user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Can only delete your own account",
        )
    
    if not db.delete("users", "id", user_id):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )
    return None


# ==================== Calendar Event CRUD Endpoints ====================


@app.post("/events", response_model=EventResponse, status_code=status.HTTP_201_CREATED, tags=["Events"])
async def create_event(event: EventCreate, current_user: dict = Depends(get_current_user)):
    """
    Create a new calendar event for the current user.
    """
    new_event = {
        "id": get_next_event_id(),
        "user_id": current_user["id"],
        "title": event.title,
        "description": event.description,
        "start_time": event.start_time,
        "end_time": event.end_time,
        "location": event.location,
    }
    db.add("events", new_event)
    return EventResponse(**new_event)


@app.get("/events", response_model=list[EventResponse], tags=["Events"])
async def list_events(current_user: dict = Depends(get_current_user)):
    """
    Get all events for the current user.
    """
    events = db.find("events", user_id=current_user["id"])
    return [EventResponse(**e) for e in events]


@app.get("/events/{event_id}", response_model=EventResponse, tags=["Events"])
async def get_event(event_id: int, current_user: dict = Depends(get_current_user)):
    """
    Get a specific event by ID (must belong to current user).
    """
    event = db.get("events", "id", event_id)
    if not event:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Event not found",
        )
    if event["user_id"] != current_user["id"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied",
        )
    return EventResponse(**event)


@app.put("/events/{event_id}", response_model=EventResponse, tags=["Events"])
async def update_event(
    event_id: int,
    event_update: EventUpdate,
    current_user: dict = Depends(get_current_user),
):
    """
    Update an event (must belong to current user).
    """
    event = db.get("events", "id", event_id)
    if not event:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Event not found",
        )
    if event["user_id"] != current_user["id"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied",
        )
    
    updates = {}
    if event_update.title is not None:
        updates["title"] = event_update.title
    if event_update.description is not None:
        updates["description"] = event_update.description
    if event_update.start_time is not None:
        updates["start_time"] = event_update.start_time
    if event_update.end_time is not None:
        updates["end_time"] = event_update.end_time
    if event_update.location is not None:
        updates["location"] = event_update.location
    
    if updates:
        db.update("events", "id", event_id, updates)
    
    updated_event = db.get("events", "id", event_id)
    return EventResponse(**updated_event)


@app.delete("/events/{event_id}", status_code=status.HTTP_204_NO_CONTENT, tags=["Events"])
async def delete_event(event_id: int, current_user: dict = Depends(get_current_user)):
    """
    Delete an event (must belong to current user).
    """
    event = db.get("events", "id", event_id)
    if not event:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Event not found",
        )
    if event["user_id"] != current_user["id"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied",
        )
    db.delete("events", "id", event_id)
    return None


# ==================== Health Check ====================


@app.get("/health", tags=["Health"])
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
