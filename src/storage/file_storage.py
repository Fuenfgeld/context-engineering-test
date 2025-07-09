"""File-based storage implementation for story sessions."""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import List, Optional

import logfire

from models.session import StorySession


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
        with logfire.span(
            'Saving session to file storage',
            session_id=session.id,
            session_name=session.get_display_name()
        ) as span:
            session.last_updated = datetime.now()
            file_path = self.storage_dir / f"{session.id}.json"
            span.set_attribute('file_path', str(file_path))
            span.set_attribute('storage_directory', str(self.storage_dir))

            try:
                with logfire.span('Writing session data to file') as write_span:
                    json_data = session.to_json()
                    write_span.set_attribute('json_size_bytes', len(json_data.encode('utf-8')))
                    
                    with open(file_path, 'w', encoding='utf-8') as f:
                        f.write(json_data)
                    
                    write_span.set_attribute('file_written', True)
                    
                span.set_attribute('save_successful', True)
                span.set_attribute('character_count', len(session.world.characters))
                span.set_attribute('history_length', len(session.world.history))
                logfire.info(
                    'Session saved successfully to file storage',
                    session_name=session.get_display_name(),
                    file_size_bytes=file_path.stat().st_size if file_path.exists() else 0
                )
                
            except OSError as e:
                span.set_attribute('save_successful', False)
                span.set_attribute('error_message', str(e))
                logfire.error(
                    'Failed to save session to file storage',
                    session_id=session.id,
                    error=str(e),
                    file_path=str(file_path)
                )
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
        with logfire.span(
            'Loading session from file storage',
            session_id=session_id
        ) as span:
            file_path = self.storage_dir / f"{session_id}.json"
            span.set_attribute('file_path', str(file_path))

            if not file_path.exists():
                span.set_attribute('file_exists', False)
                logfire.info('Session file not found', session_id=session_id, file_path=str(file_path))
                return None

            span.set_attribute('file_exists', True)
            span.set_attribute('file_size_bytes', file_path.stat().st_size)

            try:
                with logfire.span('Reading and parsing session file') as read_span:
                    with open(file_path, encoding='utf-8') as f:
                        json_str = f.read()
                    read_span.set_attribute('json_size_bytes', len(json_str.encode('utf-8')))
                    
                    session = StorySession.from_json(json_str)
                    read_span.set_attribute('parsing_successful', True)
                    
                span.set_attribute('load_successful', True)
                span.set_attribute('session_name', session.get_display_name())
                span.set_attribute('character_count', len(session.world.characters))
                span.set_attribute('history_length', len(session.world.history))
                
                logfire.info(
                    'Session loaded successfully from file storage',
                    session_id=session_id,
                    session_name=session.get_display_name(),
                    character_count=len(session.world.characters)
                )
                
                return session
                
            except (json.JSONDecodeError, KeyError) as e:
                span.set_attribute('load_successful', False)
                span.set_attribute('error_type', 'corruption')
                span.set_attribute('error_message', str(e))
                logfire.error(
                    'Session file is corrupted',
                    session_id=session_id,
                    error=str(e),
                    file_path=str(file_path)
                )
                raise ValueError(f"Corrupted session file {session_id}: {e}")
            except OSError as e:
                span.set_attribute('load_successful', False)
                span.set_attribute('error_type', 'os_error')
                span.set_attribute('error_message', str(e))
                logfire.error(
                    'OS error loading session file',
                    session_id=session_id,
                    error=str(e),
                    file_path=str(file_path)
                )
                raise OSError(f"Failed to load session {session_id}: {e}")

    def list_sessions(self) -> List[StorySession]:
        """
        List all available story sessions.
        
        Returns:
            List of all sessions, sorted by last_updated (newest first)
        """
        with logfire.span(
            'Listing all sessions from file storage',
            storage_directory=str(self.storage_dir)
        ) as span:
            sessions = []
            file_count = 0
            corrupted_count = 0

            with logfire.span('Scanning storage directory for session files') as scan_span:
                session_files = list(self.storage_dir.glob("*.json"))
                scan_span.set_attribute('total_files_found', len(session_files))
                file_count = len(session_files)

            for file_path in session_files:
                try:
                    session_id = file_path.stem
                    
                    with logfire.span(
                        'Loading individual session for listing',
                        session_id=session_id,
                        file_name=file_path.name
                    ) as load_span:
                        session = self.load_session(session_id)
                        if session:
                            sessions.append(session)
                            load_span.set_attribute('session_loaded', True)
                        else:
                            load_span.set_attribute('session_loaded', False)
                            
                except (ValueError, OSError) as e:
                    corrupted_count += 1
                    logfire.warning(
                        'Skipping corrupted session file during listing',
                        file_path=str(file_path),
                        error=str(e)
                    )
                    continue

            # Sort by last_updated, newest first
            with logfire.span('Sorting sessions by last updated') as sort_span:
                sessions.sort(key=lambda s: s.last_updated, reverse=True)
                sort_span.set_attribute('sessions_sorted', True)

            span.set_attribute('total_files_scanned', file_count)
            span.set_attribute('sessions_loaded', len(sessions))
            span.set_attribute('corrupted_files_skipped', corrupted_count)
            span.set_attribute('listing_successful', True)
            
            logfire.info(
                'Session listing completed',
                total_sessions=len(sessions),
                corrupted_files=corrupted_count,
                storage_directory=str(self.storage_dir)
            )
            
            return sessions

    def delete_session(self, session_id: str) -> bool:
        """
        Delete a story session.
        
        Args:
            session_id: ID of the session to delete
            
        Returns:
            True if session was deleted, False if not found
        """
        with logfire.span(
            'Deleting session from file storage',
            session_id=session_id
        ) as span:
            file_path = self.storage_dir / f"{session_id}.json"
            span.set_attribute('file_path', str(file_path))

            if not file_path.exists():
                span.set_attribute('file_exists', False)
                span.set_attribute('deletion_successful', False)
                logfire.info('Session file not found for deletion', session_id=session_id)
                return False

            span.set_attribute('file_exists', True)
            file_size = file_path.stat().st_size
            span.set_attribute('file_size_bytes', file_size)

            try:
                with logfire.span('Unlinking session file') as unlink_span:
                    file_path.unlink()
                    unlink_span.set_attribute('file_unlinked', True)
                    
                span.set_attribute('deletion_successful', True)
                logfire.info(
                    'Session deleted successfully from file storage',
                    session_id=session_id,
                    file_size_bytes=file_size
                )
                return True
                
            except OSError as e:
                span.set_attribute('deletion_successful', False)
                span.set_attribute('error_message', str(e))
                logfire.error(
                    'Failed to delete session file',
                    session_id=session_id,
                    error=str(e),
                    file_path=str(file_path)
                )
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
