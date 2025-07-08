"""Pytest configuration and fixtures for the storytelling application tests."""

from __future__ import annotations

import asyncio
import tempfile
import os
from pathlib import Path
from typing import AsyncGenerator, Generator
from unittest.mock import AsyncMock, MagicMock

import pytest
import httpx

from src.models.story import Character, Scene, StoryWorld
from src.models.session import StorySession
from src.storage.file_storage import FileStorage
from src.agents.character import StoryDeps


@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


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
async def mock_http_client() -> AsyncGenerator[httpx.AsyncClient, None]:
    """Create a mock HTTP client for testing."""
    async with httpx.AsyncClient() as client:
        yield client


@pytest.fixture
def story_deps(sample_story_world: StoryWorld, mock_http_client: httpx.AsyncClient) -> StoryDeps:
    """Create StoryDeps for agent testing."""
    return StoryDeps(story_world=sample_story_world, client=mock_http_client)


@pytest.fixture
def mock_agent_response():
    """Create a mock agent response."""
    mock_response = MagicMock()
    mock_response.data = "This is a test response from the agent"
    mock_response.new_messages.return_value = []
    return mock_response


# Environment variable fixtures
@pytest.fixture
def test_env_vars(monkeypatch):
    """Set test environment variables."""
    monkeypatch.setenv("LLM_MODEL", "gpt-4o-mini")
    monkeypatch.setenv("OPENAI_API_KEY", "test-key-123")


@pytest.fixture
def no_api_key_env(monkeypatch):
    """Environment with no API key set."""
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    monkeypatch.delenv("OPEN_ROUTER_API_KEY", raising=False)


# Storage fixtures with actual file operations
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


# Async test helpers
@pytest.fixture
def async_mock():
    """Create an async mock for testing async functions."""
    return AsyncMock()


# Test data fixtures
@pytest.fixture
def test_story_concept() -> str:
    """Sample story concept for testing."""
    return "A mysterious detective investigates strange disappearances in Victorian London"


@pytest.fixture
def test_user_input() -> str:
    """Sample user input for testing story continuation."""
    return "I examine the mysterious letter on the desk"


@pytest.fixture
def test_meta_command() -> str:
    """Sample meta-command for testing."""
    return "*suddenly it starts raining heavily*"


# Validation fixtures
@pytest.fixture
def invalid_character_data() -> dict:
    """Invalid character data for testing validation."""
    return {
        "name": "",  # Empty name should be invalid
        "description": "Test description",
        "personality": "Test personality",
        "speech_patterns": "Test speech"
    }


@pytest.fixture
def corrupted_session_data() -> str:
    """Corrupted session JSON for testing error handling."""
    return '{"id": "test", "world": {"invalid": "missing required fields"}}'