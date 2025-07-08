"""Storage-related data models."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Any, Dict


@dataclass
class SessionMetadata:
    """
    Metadata for a story session.
    
    Attributes:
        id: Session identifier
        display_name: Human-readable session name
        created_at: Creation timestamp
        last_updated: Last modification timestamp
        character_count: Number of characters in the session
        history_length: Number of history entries
        file_size: Size of the session file in bytes
    """
    id: str
    display_name: str
    created_at: datetime
    last_updated: datetime
    character_count: int
    history_length: int
    file_size: int

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            "id": self.id,
            "display_name": self.display_name,
            "created_at": self.created_at.isoformat(),
            "last_updated": self.last_updated.isoformat(),
            "character_count": self.character_count,
            "history_length": self.history_length,
            "file_size": self.file_size
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> SessionMetadata:
        """Create from dictionary."""
        return cls(
            id=data["id"],
            display_name=data["display_name"],
            created_at=datetime.fromisoformat(data["created_at"]),
            last_updated=datetime.fromisoformat(data["last_updated"]),
            character_count=data["character_count"],
            history_length=data["history_length"],
            file_size=data["file_size"]
        )


@dataclass
class StorageConfig:
    """
    Configuration for storage system.
    
    Attributes:
        storage_dir: Directory for storing session files
        max_file_size: Maximum file size in bytes
        backup_enabled: Whether to create backups
        backup_dir: Directory for backup files
        compression_enabled: Whether to compress files
    """
    storage_dir: str = "stories"
    max_file_size: int = 50 * 1024 * 1024  # 50MB
    backup_enabled: bool = True
    backup_dir: str = "stories/backups"
    compression_enabled: bool = False
