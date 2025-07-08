"""Session management models for story persistence."""

from __future__ import annotations

import json
import uuid
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, List

from .story import StoryWorld


@dataclass
class StorySession:
    """
    Represents a complete storytelling session.
    
    Attributes:
        id: Unique session identifier
        world: The story world state
        message_history: List of conversation messages (serialized)
        created_at: When the session was created
        last_updated: When the session was last modified
        metadata: Additional session metadata
    """
    id: str
    world: StoryWorld
    message_history: List[Dict[str, Any]] = field(default_factory=list)
    created_at: datetime = field(default_factory=datetime.now)
    last_updated: datetime = field(default_factory=datetime.now)
    metadata: Dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        """Initialize session with current timestamp."""
        if not self.id:
            self.id = str(uuid.uuid4())
        self.last_updated = datetime.now()

    def add_message(self, message: Dict[str, Any]) -> None:
        """Add a message to the session history."""
        self.message_history.append(message)
        self.last_updated = datetime.now()

    def update_world(self, world: StoryWorld) -> None:
        """Update the story world and timestamp."""
        self.world = world
        self.last_updated = datetime.now()

    def to_dict(self) -> Dict[str, Any]:
        """Convert session to dictionary for JSON serialization."""
        return {
            "id": self.id,
            "world": self.world.to_dict(),
            "message_history": self.message_history,
            "created_at": self.created_at.isoformat(),
            "last_updated": self.last_updated.isoformat(),
            "metadata": self.metadata
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> StorySession:
        """Create session from dictionary."""
        world = StoryWorld.from_dict(data["world"])

        return cls(
            id=data["id"],
            world=world,
            message_history=data.get("message_history", []),
            created_at=datetime.fromisoformat(data["created_at"]),
            last_updated=datetime.fromisoformat(data["last_updated"]),
            metadata=data.get("metadata", {})
        )

    def to_json(self) -> str:
        """Convert session to JSON string."""
        return json.dumps(self.to_dict(), indent=2)

    @classmethod
    def from_json(cls, json_str: str) -> StorySession:
        """Create session from JSON string."""
        data = json.loads(json_str)
        return cls.from_dict(data)

    @classmethod
    def create_new(cls, world: StoryWorld, session_id: str | None = None) -> StorySession:
        """Create a new session with a story world."""
        return cls(
            id=session_id or str(uuid.uuid4()),
            world=world
        )

    def get_summary(self) -> str:
        """Get a brief summary of the session."""
        return f"Session {self.id[:8]}... - {self.world.premise[:50]}..."

    def get_display_name(self) -> str:
        """Get a human-readable display name for the session."""
        if self.world.premise:
            return f"{self.world.premise[:30]}{'...' if len(self.world.premise) > 30 else ''}"
        return f"Session {self.id[:8]}..."
