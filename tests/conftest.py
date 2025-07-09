"""Minimal pytest configuration for core functionality tests."""

from __future__ import annotations

import tempfile
from pathlib import Path
from typing import Generator
from unittest.mock import AsyncMock

import pytest
import httpx

from src.models.story import Character, Scene, StoryWorld
from src.models.session import StorySession
from src.storage.file_storage import FileStorage
from src.agents.character import StoryDeps


@pytest.fixture
def temp_storage_dir() -> Generator[str, None, None]:
    """Create a temporary directory for storage tests."""
    with tempfile.TemporaryDirectory() as temp_dir:
        yield temp_dir


@pytest.fixture
def file_storage(temp_storage_dir: str) -> FileStorage:
    """Create a FileStorage instance with temporary directory."""
    return FileStorage(temp_storage_dir)


@pytest.fixture
def sample_character() -> Character:
    """Create a sample character for testing."""
    return Character(
        name="Alice",
        description="A brave adventurer with bright blue eyes and long golden hair",
        personality="Courageous, curious, and kind-hearted",
        speech_patterns="Speaks with confidence and optimism",
        memories=["Met the group at the tavern", "Learned about the ancient map"],
        relationships={"Bob": "trusted friend", "Eve": "mysterious acquaintance"}
    )


@pytest.fixture
def sample_scene() -> Scene:
    """Create a sample scene for testing."""
    return Scene(
        location="The Rusty Dragon Tavern",
        description="A cozy tavern with warm lighting and the smell of fresh bread",
        atmosphere="Welcoming and bustling with activity",
        active_characters=["Alice", "Bob"],
        props=["ancient map", "mysterious key"]
    )


@pytest.fixture
def sample_story_world(sample_character: Character, sample_scene: Scene) -> StoryWorld:
    """Create a sample story world for testing."""
    world = StoryWorld(
        premise="A group of adventurers seeks the lost treasure of the ancients",
        setting="A fantasy realm filled with magic and mystery",
        conflicts=["The evil sorcerer seeks the same treasure", "Time is running out"],
        characters={"Alice": sample_character},
        current_scene=sample_scene,
        history=["The adventure begins at the tavern", "A mysterious stranger appears"]
    )
    return world


@pytest.fixture
def sample_session(sample_story_world: StoryWorld) -> StorySession:
    """Create a sample story session for testing."""
    return StorySession.create_new(sample_story_world, "test-session-001")


@pytest.fixture
def populated_storage(file_storage: FileStorage, sample_session: StorySession) -> FileStorage:
    """Create a file storage with some test sessions."""
    # Save the sample session
    file_storage.save_session(sample_session)
    
    # Create and save additional test sessions
    for i in range(2, 4):
        session = StorySession.create_new(
            StoryWorld(
                premise=f"Test story {i}",
                setting=f"Test setting {i}",
                conflicts=[f"Test conflict {i}"],
                characters={},
                current_scene=Scene("Test location", "Test description", "Test atmosphere"),
                history=[f"Test history entry {i}"]
            ),
            f"test-session-{i:03d}"
        )
        file_storage.save_session(session)
    
    return file_storage


@pytest.fixture
def corrupted_session_data() -> str:
    """Corrupted session JSON for testing error handling."""
    return '{"id": "test", "world": {"invalid": "missing required fields"}}'


@pytest.fixture
def mock_http_client():
    """Create a mock HTTP client for testing."""
    return AsyncMock(spec=httpx.AsyncClient)


@pytest.fixture
def story_deps(sample_story_world: StoryWorld, mock_http_client) -> StoryDeps:
    """Create StoryDeps for testing character agent."""
    return StoryDeps(story_world=sample_story_world, client=mock_http_client)