"""Tests for the AI agents."""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch
import pytest

from src.agents.character import CharacterManager, embody_character, StoryDeps
from src.agents.storyteller import StorytellerAgent
from src.models.story import Character, Scene, StoryWorld


class TestCharacterAgent:
    """Test cases for the character agent and related functionality."""
    
    @pytest.mark.asyncio
    async def test_embody_character_expected_use(self, story_deps: StoryDeps, sample_character: Character):
        """Test character embodiment with valid character."""
        # Add character to story world
        story_deps.story_world.characters["Alice"] = sample_character
        
        # Mock the agent response
        with patch('src.agents.character.character_agent.run') as mock_run:
            mock_response = MagicMock()
            mock_response.data = "Hello there! I'm excited to meet you!"
            mock_run.return_value = mock_response
            
            # Create a mock context
            mock_ctx = MagicMock()
            mock_ctx.deps = story_deps
            
            result = await embody_character(mock_ctx, "Alice", "meeting a new person")
            
            assert "Hello there!" in result
            # Check that memory was added
            assert len(sample_character.memories) > 2  # Original 2 + 1 new
            assert any("meeting a new person" in memory for memory in sample_character.memories)
    
    @pytest.mark.asyncio
    async def test_embody_character_not_found(self, story_deps: StoryDeps):
        """Test character embodiment with non-existent character."""
        mock_ctx = MagicMock()
        mock_ctx.deps = story_deps
        
        with pytest.raises(ValueError) as exc_info:
            await embody_character(mock_ctx, "NonExistent", "test situation")
        
        assert "not found" in str(exc_info.value)
    
    @pytest.mark.asyncio
    async def test_embody_character_memory_management(self, story_deps: StoryDeps):
        """Test that character memories are properly managed."""
        # Create character with many memories
        character = Character(
            name="TestChar",
            description="Test",
            personality="Test", 
            speech_patterns="Test",
            memories=[f"Memory {i}" for i in range(25)]  # More than limit
        )
        story_deps.story_world.characters["TestChar"] = character
        
        with patch('src.agents.character.character_agent.run') as mock_run:
            mock_response = MagicMock()
            mock_response.data = "Test response"
            mock_run.return_value = mock_response
            
            mock_ctx = MagicMock()
            mock_ctx.deps = story_deps
            
            await embody_character(mock_ctx, "TestChar", "test")
            
            # Should limit memories to 20
            assert len(character.memories) == 20
    
    @pytest.mark.asyncio 
    async def test_character_manager_expected_use(self, sample_story_world: StoryWorld, mock_http_client):
        """Test CharacterManager basic functionality."""
        manager = CharacterManager(sample_story_world, mock_http_client)
        
        # Test character listing
        characters = manager.list_characters()
        assert "Alice" in characters
        
        # Test character summary
        summary = manager.get_character_summary("Alice")
        assert summary is not None
        assert "Alice" in summary
        
        # Test non-existent character
        summary = manager.get_character_summary("NonExistent")
        assert summary is None
    
    @pytest.mark.asyncio
    async def test_character_manager_add_memory(self, sample_story_world: StoryWorld, mock_http_client):
        """Test adding memory to character through manager."""
        manager = CharacterManager(sample_story_world, mock_http_client)
        
        # Add memory to existing character
        result = manager.add_character_memory("Alice", "Met a strange wizard")
        assert result is True
        
        character = sample_story_world.characters["Alice"]
        assert "Met a strange wizard" in character.memories
        
        # Try to add memory to non-existent character
        result = manager.add_character_memory("NonExistent", "Test memory")
        assert result is False


class TestStorytellerAgent:
    """Test cases for the main storyteller agent."""
    
    @pytest.mark.asyncio
    async def test_create_scenario_expected_use(self, mock_http_client):
        """Test scenario creation with valid concept."""
        storyteller = StorytellerAgent(mock_http_client)
        
        with patch.object(storyteller.agent, 'run') as mock_run:
            mock_response = MagicMock()
            mock_response.data = """
            Premise: A mysterious detective investigates strange disappearances in Victorian London.
            Setting: The foggy streets of Victorian London with gaslight and cobblestones.
            """
            mock_run.return_value = mock_response
            
            concept = "A detective story in Victorian London"
            story_world = await storyteller.create_scenario(concept)
            
            assert story_world.premise != ""
            assert story_world.setting != ""
            assert isinstance(story_world.characters, dict)
            assert isinstance(story_world.conflicts, list)
    
    @pytest.mark.asyncio
    async def test_continue_story_normal_input(self, mock_http_client, sample_story_world: StoryWorld):
        """Test continuing story with normal user input."""
        storyteller = StorytellerAgent(mock_http_client)
        
        with patch.object(storyteller.agent, 'run') as mock_run:
            mock_response = MagicMock()
            mock_response.data = "You examine the letter carefully. The handwriting is elegant but rushed."
            mock_run.return_value = mock_response
            
            user_input = "I examine the letter on the desk"
            response, updated_world = await storyteller.continue_story(user_input, sample_story_world)
            
            assert "examine the letter" in response
            assert f"User: {user_input}" in updated_world.history
            assert f"Narrator: {response}" in updated_world.history
    
    @pytest.mark.asyncio
    async def test_continue_story_meta_command(self, mock_http_client, sample_story_world: StoryWorld):
        """Test handling meta-commands with asterisks."""
        storyteller = StorytellerAgent(mock_http_client)
        
        with patch.object(storyteller.agent, 'run') as mock_run:
            mock_response = MagicMock()
            mock_response.data = "Dark clouds gather overhead and rain begins to fall heavily."
            mock_run.return_value = mock_response
            
            meta_command = "*suddenly it starts raining*"
            response, updated_world = await storyteller.continue_story(meta_command, sample_story_world)
            
            assert "rain" in response.lower()
            # Meta-commands should be added as story development, not user input
            assert any("Story development:" in entry for entry in updated_world.history)
    
    @pytest.mark.asyncio
    async def test_refine_scenario_expected_use(self, mock_http_client, sample_story_world: StoryWorld):
        """Test scenario refinement based on feedback."""
        storyteller = StorytellerAgent(mock_http_client)
        
        with patch.object(storyteller.agent, 'run') as mock_run:
            mock_response = MagicMock()
            mock_response.data = "Refined premise: The detective now has a mysterious past connection to the disappearances."
            mock_run.return_value = mock_response
            
            feedback = "Make the detective have a personal connection to the case"
            refined_world = await storyteller.refine_scenario(feedback, sample_story_world)
            
            # Should have added refinement to history
            assert any("refined" in entry.lower() for entry in refined_world.history)
    
    def test_is_meta_command_detection(self, mock_http_client):
        """Test detection of meta-commands."""
        storyteller = StorytellerAgent(mock_http_client)
        
        # Test valid meta-commands
        assert storyteller._is_meta_command("*suddenly it rains*") is True
        assert storyteller._is_meta_command("  *the door opens*  ") is True
        
        # Test invalid meta-commands
        assert storyteller._is_meta_command("*incomplete") is False
        assert storyteller._is_meta_command("incomplete*") is False
        assert storyteller._is_meta_command("normal text") is False
        assert storyteller._is_meta_command("") is False
    
    def test_build_story_context(self, mock_http_client, sample_story_world: StoryWorld):
        """Test building story context for agent."""
        storyteller = StorytellerAgent(mock_http_client)
        
        user_input = "I look around the room"
        context = storyteller._build_story_context(user_input, sample_story_world)
        
        assert "Current Scene:" in context
        assert sample_story_world.current_scene.location in context
        assert user_input in context
        assert "Recent Story Events:" in context
    
    def test_parse_scenario_response_edge_case(self, mock_http_client):
        """Test parsing scenario response with minimal content."""
        storyteller = StorytellerAgent(mock_http_client)
        
        # Test with empty/minimal response
        minimal_response = "Not much information here"
        parsed = storyteller._parse_scenario_response(minimal_response)
        
        assert isinstance(parsed, dict)
        assert "premise" in parsed
        assert "setting" in parsed
        # Should handle gracefully even with no structured content
    
    def test_build_story_world_fallbacks(self, mock_http_client):
        """Test story world building with missing data."""
        storyteller = StorytellerAgent(mock_http_client)
        
        # Test with empty scenario data
        empty_data = {"premise": "", "setting": "", "characters": [], "conflicts": []}
        initial_concept = "Test concept"
        
        world = storyteller._build_story_world(empty_data, initial_concept)
        
        # Should create valid world with fallbacks
        assert world.premise == initial_concept  # Should use initial concept as fallback
        assert world.setting != ""  # Should have fallback setting
        assert len(world.characters) > 0  # Should create default character
        assert len(world.conflicts) > 0  # Should have default conflict