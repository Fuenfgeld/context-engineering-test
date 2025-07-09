"""Tests for the AI agents."""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch
import pytest

from src.agents.character import CharacterManager, embody_character, StoryDeps
from src.agents.character_creator import CharacterCreationManager
from src.agents.scenario_generator import ScenarioGenerationManager
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
            mock_response.output = "Hello there! I'm excited to meet you!"
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
            mock_response.output = "Test response"
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
        """Test scenario creation with valid concept using new agent architecture."""
        storyteller = StorytellerAgent(mock_http_client)
        
        # Mock the scenario manager
        with patch.object(storyteller.scenario_manager, 'create_scenario_from_concept') as mock_scenario:
            # Mock the character creation manager
            with patch('src.agents.storyteller.CharacterCreationManager') as mock_char_manager_class:
                mock_char_manager = AsyncMock()
                mock_char_manager_class.return_value = mock_char_manager
                
                # Mock character creation
                mock_character = Character(
                    name="Detective Holmes",
                    description="A brilliant detective",
                    personality="Observant and logical",
                    speech_patterns="Speaks with precise diction"
                )
                mock_char_manager.create_character_from_concept = AsyncMock(return_value=mock_character)
                
                # Mock scenario creation
                mock_story_world = StoryWorld(
                    premise="A mysterious detective investigates strange disappearances in Victorian London.",
                    setting="The foggy streets of Victorian London with gaslight and cobblestones.",
                    conflicts=["Missing persons case", "Hidden conspiracy"],
                    characters={},
                    current_scene=Scene("Baker Street", "A cozy study", "Mysterious")
                )
                character_concepts = ["A brilliant detective", "A helpful assistant"]
                mock_scenario.return_value = (mock_story_world, character_concepts)
                
                concept = "A detective story in Victorian London"
                story_world = await storyteller.create_scenario(concept)
                
                assert story_world.premise != ""
                assert story_world.setting != ""
                assert isinstance(story_world.characters, dict)
                assert isinstance(story_world.conflicts, list)
                assert len(story_world.characters) > 0  # Should have created characters
    
    @pytest.mark.asyncio
    async def test_continue_story_normal_input(self, mock_http_client, sample_story_world: StoryWorld):
        """Test continuing story with normal user input."""
        storyteller = StorytellerAgent(mock_http_client)
        
        with patch.object(storyteller.agent, 'run') as mock_run:
            mock_response = MagicMock()
            mock_response.output = "You examine the letter carefully. The handwriting is elegant but rushed."
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
            mock_response.output = "Dark clouds gather overhead and rain begins to fall heavily."
            mock_run.return_value = mock_response
            
            meta_command = "*suddenly it starts raining*"
            response, updated_world = await storyteller.continue_story(meta_command, sample_story_world)
            
            assert "rain" in response.lower()
            # Meta-commands should be added as story development, not user input
            assert any("Story development:" in entry for entry in updated_world.history)
    
    @pytest.mark.asyncio
    async def test_refine_scenario_expected_use(self, mock_http_client, sample_story_world: StoryWorld):
        """Test scenario refinement based on feedback using new agent architecture."""
        storyteller = StorytellerAgent(mock_http_client)
        
        # Mock the scenario manager refinement
        with patch.object(storyteller.scenario_manager, 'refine_scenario_from_feedback') as mock_refine:
            refined_world = sample_story_world.copy() if hasattr(sample_story_world, 'copy') else sample_story_world
            refined_world.premise = "Refined premise: The detective now has a mysterious past connection to the disappearances."
            refined_world.add_history_entry("Scenario refined based on user feedback")
            mock_refine.return_value = refined_world
            
            feedback = "Make the detective have a personal connection to the case"
            result_world = await storyteller.refine_scenario(feedback, sample_story_world)
            
            # Should have called the scenario manager
            mock_refine.assert_called_once_with(sample_story_world, feedback)
            # Should have added refinement to history
            assert any("refined" in entry.lower() for entry in result_world.history)
    
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
    

class TestCharacterCreationAgent:
    """Test cases for the character creation agent."""
    
    @pytest.mark.asyncio
    async def test_character_creation_manager_expected_use(self, sample_story_world: StoryWorld, mock_http_client):
        """Test character creation manager with valid concept."""
        manager = CharacterCreationManager(sample_story_world, mock_http_client)
        
        # Mock the character creation agent
        with patch('src.agents.character_creator.create_character') as mock_create:
            mock_character_request = MagicMock()
            mock_character_request.name = "Detective Watson"
            mock_character_request.description = "A loyal friend and assistant to the detective"
            mock_character_request.personality = "Loyal, brave, and observant"
            mock_character_request.speech_patterns = "Speaks with warmth and enthusiasm"
            mock_create.return_value = mock_character_request
            
            concept = "A helpful assistant to the detective"
            character = await manager.create_character_from_concept(concept)
            
            assert character.name == "Detective Watson"
            assert character.description != ""
            assert character.personality != ""
            assert character.speech_patterns != ""
            assert character.name in sample_story_world.characters
    
    @pytest.mark.asyncio
    async def test_character_creation_multiple_characters(self, sample_story_world: StoryWorld, mock_http_client):
        """Test creating multiple characters from concepts."""
        manager = CharacterCreationManager(sample_story_world, mock_http_client)
        
        with patch('src.agents.character_creator.create_character') as mock_create:
            # Mock multiple character responses
            mock_chars = [
                MagicMock(name="Character1", description="Desc1", personality="Pers1", speech_patterns="Speech1"),
                MagicMock(name="Character2", description="Desc2", personality="Pers2", speech_patterns="Speech2")
            ]
            mock_create.side_effect = mock_chars
            
            concepts = ["First character concept", "Second character concept"]
            characters = await manager.create_multiple_characters(concepts)
            
            assert len(characters) == 2
            assert all(char.name in sample_story_world.characters for char in characters)


class TestScenarioGenerationAgent:
    """Test cases for the scenario generation agent."""
    
    @pytest.mark.asyncio
    async def test_scenario_generation_manager_expected_use(self, mock_http_client):
        """Test scenario generation manager with valid concept."""
        manager = ScenarioGenerationManager(mock_http_client)
        
        # Mock the scenario generation agent
        with patch('src.agents.scenario_generator.generate_scenario') as mock_generate:
            mock_scenario_request = MagicMock()
            mock_scenario_request.premise = "A thrilling adventure in space"
            mock_scenario_request.setting = "A distant galaxy filled with alien worlds"
            mock_scenario_request.conflicts = ["Alien invasion", "Resource shortage"]
            mock_scenario_request.opening_scene_location = "Spaceship Bridge"
            mock_scenario_request.opening_scene_description = "The bridge hums with activity"
            mock_scenario_request.opening_scene_atmosphere = "Tense anticipation"
            mock_scenario_request.character_concepts = ["Space captain", "Alien diplomat"]
            mock_generate.return_value = mock_scenario_request
            
            concept = "A space adventure story"
            story_world, character_concepts = await manager.create_scenario_from_concept(concept)
            
            assert story_world.premise == "A thrilling adventure in space"
            assert story_world.setting != ""
            assert len(story_world.conflicts) == 2
            assert len(character_concepts) == 2
            assert "Space captain" in character_concepts
    
    @pytest.mark.asyncio
    async def test_scenario_refinement_expected_use(self, mock_http_client, sample_story_world: StoryWorld):
        """Test scenario refinement based on feedback."""
        manager = ScenarioGenerationManager(mock_http_client)
        
        with patch('src.agents.scenario_generator.refine_scenario') as mock_refine:
            mock_refined_request = MagicMock()
            mock_refined_request.premise = "Refined premise with personal stakes"
            mock_refined_request.setting = sample_story_world.setting
            mock_refined_request.conflicts = sample_story_world.conflicts + ["Personal vendetta"]
            mock_refined_request.opening_scene_location = "Updated location"
            mock_refined_request.opening_scene_description = "Updated description"
            mock_refined_request.opening_scene_atmosphere = "Updated atmosphere"
            mock_refined_request.character_concepts = ["Updated character"]
            mock_refine.return_value = mock_refined_request
            
            feedback = "Add more personal stakes for the protagonist"
            refined_world = await manager.refine_scenario_from_feedback(sample_story_world, feedback)
            
            assert refined_world.premise == "Refined premise with personal stakes"
            assert "Personal vendetta" in refined_world.conflicts
            assert any("refined" in entry.lower() for entry in refined_world.history)