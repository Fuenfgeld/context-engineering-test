"""Tests for the storage layer."""

from __future__ import annotations

import json
import os
from pathlib import Path
from datetime import datetime, timedelta

import pytest

from src.storage.file_storage import FileStorage
from src.models.session import StorySession
from src.models.story import StoryWorld, Character, Scene


class TestFileStorage:
    """Test cases for FileStorage class."""
    
    def test_save_session_expected_use(self, file_storage: FileStorage, sample_session: StorySession):
        """Test saving a session successfully."""
        # Save the session
        file_storage.save_session(sample_session)
        
        # Verify file was created
        expected_file = Path(file_storage.storage_dir) / f"{sample_session.id}.json"
        assert expected_file.exists()
        
        # Verify content is valid JSON
        with open(expected_file, 'r') as f:
            data = json.load(f)
            assert data["id"] == sample_session.id
    
    def test_save_session_updates_timestamp(self, file_storage: FileStorage, sample_session: StorySession):
        """Test that saving updates the last_updated timestamp."""
        original_time = sample_session.last_updated
        
        # Save the session
        file_storage.save_session(sample_session)
        
        # Timestamp should be updated
        assert sample_session.last_updated > original_time
    
    def test_save_session_failure_case(self, temp_storage_dir: str):
        """Test handling of save failures."""
        # Create a FileStorage with invalid directory permissions
        invalid_dir = Path(temp_storage_dir) / "readonly"
        invalid_dir.mkdir()
        invalid_dir.chmod(0o444)  # Read-only
        
        storage = FileStorage(str(invalid_dir))
        
        session = StorySession.create_new(
            StoryWorld("Test", "Test", [], {}, Scene("", "", ""), [])
        )
        
        # Should raise OSError on save failure
        with pytest.raises(OSError):
            storage.save_session(session)
    
    def test_load_session_expected_use(self, populated_storage: FileStorage):
        """Test loading an existing session."""
        # Load the test session
        session = populated_storage.load_session("test-session-001")
        
        assert session is not None
        assert session.id == "test-session-001"
        assert session.world.premise == "A group of adventurers seeks the lost treasure of the ancients"
        assert len(session.world.characters) == 1
        assert "Alice" in session.world.characters
    
    def test_load_session_not_found(self, file_storage: FileStorage):
        """Test loading a non-existent session."""
        session = file_storage.load_session("non-existent-session")
        assert session is None
    
    def test_load_session_corrupted_file(self, file_storage: FileStorage, corrupted_session_data: str):
        """Test handling of corrupted session files."""
        # Create a corrupted session file
        corrupted_file = Path(file_storage.storage_dir) / "corrupted.json"
        with open(corrupted_file, 'w') as f:
            f.write(corrupted_session_data)
        
        # Should raise ValueError for corrupted data
        with pytest.raises(ValueError):
            file_storage.load_session("corrupted")
    
    def test_list_sessions_expected_use(self, populated_storage: FileStorage):
        """Test listing all sessions."""
        sessions = populated_storage.list_sessions()
        
        # Should have 3 sessions (one from sample + 2 additional)
        assert len(sessions) == 3
        
        # Should be sorted by last_updated (newest first)
        for i in range(len(sessions) - 1):
            assert sessions[i].last_updated >= sessions[i + 1].last_updated
    
    def test_list_sessions_empty_storage(self, file_storage: FileStorage):
        """Test listing sessions when none exist."""
        sessions = file_storage.list_sessions()
        assert len(sessions) == 0
    
    def test_list_sessions_with_corrupted_file(self, file_storage: FileStorage, sample_session: StorySession):
        """Test that corrupted files are skipped during listing."""
        # Save a valid session
        file_storage.save_session(sample_session)
        
        # Create a corrupted file
        corrupted_file = Path(file_storage.storage_dir) / "corrupted.json"
        with open(corrupted_file, 'w') as f:
            f.write("invalid json")
        
        # Should only return valid sessions
        sessions = file_storage.list_sessions()
        assert len(sessions) == 1
        assert sessions[0].id == sample_session.id
    
    def test_delete_session_expected_use(self, populated_storage: FileStorage):
        """Test deleting an existing session."""
        # Verify session exists
        assert populated_storage.session_exists("test-session-001")
        
        # Delete the session
        result = populated_storage.delete_session("test-session-001")
        assert result is True
        
        # Verify session is gone
        assert not populated_storage.session_exists("test-session-001")
    
    def test_delete_session_not_found(self, file_storage: FileStorage):
        """Test deleting a non-existent session."""
        result = file_storage.delete_session("non-existent")
        assert result is False
    
    def test_session_exists_expected_use(self, populated_storage: FileStorage):
        """Test checking if session exists."""
        assert populated_storage.session_exists("test-session-001") is True
        assert populated_storage.session_exists("non-existent") is False
    
    def test_get_session_summary_expected_use(self, populated_storage: FileStorage):
        """Test getting session summary."""
        summary = populated_storage.get_session_summary("test-session-001")
        assert summary is not None
        assert "test-ses" in summary  # Check for truncated session ID
    
    def test_get_session_summary_not_found(self, file_storage: FileStorage):
        """Test getting summary for non-existent session."""
        summary = file_storage.get_session_summary("non-existent")
        assert summary is None
    
    def test_cleanup_old_sessions_expected_use(self, file_storage: FileStorage, temp_storage_dir: str):
        """Test cleaning up old session files."""
        # Create some test files with different ages
        now = datetime.now()
        
        # Recent file (should not be deleted)
        recent_session = StorySession.create_new(
            StoryWorld("Recent", "Recent", [], {}, Scene("", "", ""), [])
        )
        file_storage.save_session(recent_session)
        
        # Old file (simulate by creating file and modifying timestamp)
        old_file = Path(file_storage.storage_dir) / "old.json"
        with open(old_file, 'w') as f:
            json.dump({"test": "old_file"}, f)
        
        # Set old timestamp (35 days ago)
        old_timestamp = (now - timedelta(days=35)).timestamp()
        os.utime(old_file, (old_timestamp, old_timestamp))
        
        # Cleanup files older than 30 days
        deleted_count = file_storage.cleanup_old_sessions(max_age_days=30)
        
        # Should have deleted 1 file
        assert deleted_count == 1
        assert not old_file.exists()
        assert file_storage.session_exists(recent_session.id)


class TestStorageModels:
    """Test cases for storage-related models."""
    
    def test_session_metadata_serialization(self):
        """Test SessionMetadata serialization."""
        from src.storage.models import SessionMetadata
        
        metadata = SessionMetadata(
            id="test-id",
            display_name="Test Session",
            created_at=datetime.now(),
            last_updated=datetime.now(),
            character_count=3,
            history_length=10,
            file_size=1024
        )
        
        # Test to_dict
        data = metadata.to_dict()
        assert data["id"] == "test-id"
        assert data["character_count"] == 3
        
        # Test from_dict
        restored = SessionMetadata.from_dict(data)
        assert restored.id == metadata.id
        assert restored.character_count == metadata.character_count
    
    def test_storage_config_defaults(self):
        """Test StorageConfig default values."""
        from src.storage.models import StorageConfig
        
        config = StorageConfig()
        assert config.storage_dir == "stories"
        assert config.max_file_size == 50 * 1024 * 1024
        assert config.backup_enabled is True