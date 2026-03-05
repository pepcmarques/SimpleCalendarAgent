"""
Database module for managing JSON-based database operations.
Supports CRUD operations on tables stored in database.json.
"""

import json
import os
from pathlib import Path
from typing import Any, Optional


class Database:
    def __init__(self, filepath: str = None):
        if filepath is None:
            # Default to database.json in project root
            root_dir = Path(__file__).parent.parent
            filepath = str(root_dir / "database.json")
        self.filepath = filepath
        self._ensure_file_exists()

    def _ensure_file_exists(self) -> None:
        """Create the database file if it doesn't exist."""
        if not os.path.exists(self.filepath):
            self._save({})

    def _load(self) -> dict:
        """Load the database from the JSON file."""
        with open(self.filepath, "r", encoding="utf-8") as f:
            return json.load(f)

    def _save(self, data: dict) -> None:
        """Save the database to the JSON file."""
        with open(self.filepath, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=4, ensure_ascii=False)

    def create_table(self, table_name: str) -> bool:
        """Create a new table if it doesn't exist."""
        data = self._load()
        if table_name in data:
            return False
        data[table_name] = []
        self._save(data)
        return True

    def drop_table(self, table_name: str) -> bool:
        """Delete a table and all its contents."""
        data = self._load()
        if table_name not in data:
            return False
        del data[table_name]
        self._save(data)
        return True

    def get_tables(self) -> list[str]:
        """Return a list of all table names."""
        data = self._load()
        return list(data.keys())

    def add(self, table_name: str, item: dict) -> dict:
        """Add an item to a table. Returns the added item."""
        data = self._load()
        if table_name not in data:
            data[table_name] = []
        data[table_name].append(item)
        self._save(data)
        return item

    def get_all(self, table_name: str) -> list[dict]:
        """Get all items from a table."""
        data = self._load()
        return data.get(table_name, [])

    def get(self, table_name: str, key: str, value: Any) -> Optional[dict]:
        """Get the first item matching the key-value pair."""
        data = self._load()
        items = data.get(table_name, [])
        for item in items:
            if item.get(key) == value:
                return item
        return None

    def find(self, table_name: str, **criteria) -> list[dict]:
        """Find all items matching the given criteria."""
        data = self._load()
        items = data.get(table_name, [])
        results = []
        for item in items:
            if all(item.get(k) == v for k, v in criteria.items()):
                results.append(item)
        return results

    def update(self, table_name: str, key: str, value: Any, updates: dict) -> bool:
        """Update the first item matching the key-value pair with the given updates."""
        data = self._load()
        if table_name not in data:
            return False
        for item in data[table_name]:
            if item.get(key) == value:
                item.update(updates)
                self._save(data)
                return True
        return False

    def update_all(self, table_name: str, criteria: dict, updates: dict) -> int:
        """Update all items matching the criteria. Returns the count of updated items."""
        data = self._load()
        if table_name not in data:
            return 0
        count = 0
        for item in data[table_name]:
            if all(item.get(k) == v for k, v in criteria.items()):
                item.update(updates)
                count += 1
        if count > 0:
            self._save(data)
        return count

    def delete(self, table_name: str, key: str, value: Any) -> bool:
        """Delete the first item matching the key-value pair."""
        data = self._load()
        if table_name not in data:
            return False
        for i, item in enumerate(data[table_name]):
            if item.get(key) == value:
                data[table_name].pop(i)
                self._save(data)
                return True
        return False

    def delete_all(self, table_name: str, **criteria) -> int:
        """Delete all items matching the criteria. Returns the count of deleted items."""
        data = self._load()
        if table_name not in data:
            return 0
        original_length = len(data[table_name])
        data[table_name] = [
            item for item in data[table_name]
            if not all(item.get(k) == v for k, v in criteria.items())
        ]
        count = original_length - len(data[table_name])
        if count > 0:
            self._save(data)
        return count

    def remove(self, table_name: str, key: str, value: Any) -> bool:
        """Alias for delete. Remove the first item matching the key-value pair."""
        return self.delete(table_name, key, value)

    def clear_table(self, table_name: str) -> bool:
        """Remove all items from a table but keep the table."""
        data = self._load()
        if table_name not in data:
            return False
        data[table_name] = []
        self._save(data)
        return True

    def count(self, table_name: str) -> int:
        """Return the number of items in a table."""
        data = self._load()
        return len(data.get(table_name, []))


# Convenience instance for direct usage
db = Database()


if __name__ == "__main__":
    # Example usage
    db = Database()

    # Create a table
    db.create_table("users")

    # Add items
    db.add("users", {"id": 1, "name": "Alice", "email": "alice@example.com"})
    db.add("users", {"id": 2, "name": "Bob", "email": "bob@example.com"})

    # Get all items
    print("All users:", db.get_all("users"))

    # Get single item
    print("User with id 1:", db.get("users", "id", 1))

    # Update item
    db.update("users", "id", 1, {"name": "Alice Updated"})
    print("After update:", db.get("users", "id", 1))

    # Delete item
    db.delete("users", "id", 2)
    print("After delete:", db.get_all("users"))

    # Count items
    print("User count:", db.count("users"))
