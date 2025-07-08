"""File-based storage implementation for story sessions."""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import List, Optional

from ..models.session import StorySession


class FileStorage:
    """
    File-based storage for story sessions.
    
    Manages saving, loading, and listing story sessions using JSON files.
    """

    def __init__(self, storage_dir: str = "stories"):
        """
        Initialize file storage.
        
        Args:
            storage_dir: Directory to store session files
        """
        self.storage_dir = Path(storage_dir)
        self.storage_dir.mkdir(exist_ok=True)

    def save_session(self, session: StorySession) -> None:
        """
        Save a story session to disk.
        
        Args:
            session: The session to save
        
        Raises:
            OSError: If file cannot be written
        """
        session.last_updated = datetime.now()
        file_path = self.storage_dir / f"{session.id}.json"

        try:
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(session.to_json())
        except OSError as e:
            raise OSError(f"Failed to save session {session.id}: {e}")

    def load_session(self, session_id: str) -> Optional[StorySession]:
        """
        Load a story session from disk.
        
        Args:
            session_id: ID of the session to load
            
        Returns:
            The loaded session or None if not found
            
        Raises:
            ValueError: If session file is corrupted
        """
        file_path = self.storage_dir / f"{session_id}.json"

        if not file_path.exists():
            return None

        try:
            with open(file_path, encoding='utf-8') as f:
                json_str = f.read()
            return StorySession.from_json(json_str)
        except (json.JSONDecodeError, KeyError) as e:
            raise ValueError(f"Corrupted session file {session_id}: {e}")
        except OSError as e:
            raise OSError(f"Failed to load session {session_id}: {e}")

    def list_sessions(self) -> List[StorySession]:
        """
        List all available story sessions.
        
        Returns:
            List of all sessions, sorted by last_updated (newest first)
        """
        sessions = []

        for file_path in self.storage_dir.glob("*.json"):
            try:
                session_id = file_path.stem
                session = self.load_session(session_id)
                if session:
                    sessions.append(session)
            except (ValueError, OSError):
                # Skip corrupted files
                continue

        # Sort by last_updated, newest first
        sessions.sort(key=lambda s: s.last_updated, reverse=True)
        return sessions

    def delete_session(self, session_id: str) -> bool:
        """
        Delete a story session.
        
        Args:
            session_id: ID of the session to delete
            
        Returns:
            True if session was deleted, False if not found
        """
        file_path = self.storage_dir / f"{session_id}.json"

        if not file_path.exists():
            return False

        try:
            file_path.unlink()
            return True
        except OSError:
            return False

    def session_exists(self, session_id: str) -> bool:
        """
        Check if a session exists.
        
        Args:
            session_id: ID of the session to check
            
        Returns:
            True if session exists, False otherwise
        """
        file_path = self.storage_dir / f"{session_id}.json"
        return file_path.exists()

    def get_session_summary(self, session_id: str) -> Optional[str]:
        """
        Get a brief summary of a session without loading it fully.
        
        Args:
            session_id: ID of the session
            
        Returns:
            Brief summary or None if session not found
        """
        try:
            session = self.load_session(session_id)
            return session.get_summary() if session else None
        except (ValueError, OSError):
            return None

    def cleanup_old_sessions(self, max_age_days: int = 30) -> int:
        """
        Clean up old session files.
        
        Args:
            max_age_days: Maximum age in days for session files
            
        Returns:
            Number of sessions deleted
        """
        cutoff_time = datetime.now().timestamp() - (max_age_days * 24 * 60 * 60)
        deleted_count = 0

        for file_path in self.storage_dir.glob("*.json"):
            try:
                if file_path.stat().st_mtime < cutoff_time:
                    file_path.unlink()
                    deleted_count += 1
            except OSError:
                continue

        return deleted_count
