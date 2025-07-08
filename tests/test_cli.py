"""Tests for the CLI interface."""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch
import pytest

from src.cli.interface import StorytellingCLI
from src.cli.commands import CommandHandler
from src.models.session import StorySession
from src.models.story import StoryWorld, Scene


class TestStorytellingCLI:
    """Test cases for the main CLI interface."""
    
    @pytest.mark.asyncio
    async def test_cli_initialization(self):
        """Test CLI initialization."""
        cli = StorytellingCLI()
        
        assert cli.client is not None
        assert cli.storyteller is not None
        assert cli.storage is not None
        assert cli.current_session is None
        assert cli.messages == []
    
    @pytest.mark.asyncio
    async def test_display_scenario_expected_use(self, sample_story_world: StoryWorld):
        """Test displaying a created scenario."""
        cli = StorytellingCLI()
        
        # This should not raise an exception
        await cli._display_scenario(sample_story_world)
        # Test passes if no exception is raised
        assert True
    
    @pytest.mark.asyncio
    async def test_display_current_state_with_session(self, sample_session: StorySession):
        """Test displaying current state with active session."""
        cli = StorytellingCLI()
        cli.current_session = sample_session
        
        # This should not raise an exception
        await cli._display_current_state()
        assert True
    
    @pytest.mark.asyncio
    async def test_display_current_state_no_session(self):
        """Test displaying current state without active session."""
        cli = StorytellingCLI()
        
        # Should handle gracefully when no session
        await cli._display_current_state()
        assert True
    
    @pytest.mark.asyncio
    async def test_get_user_approval_simulation(self):
        """Test user approval simulation."""
        cli = StorytellingCLI()
        
        # Test approval with mock input
        with patch('builtins.input', return_value='y'):
            result = await cli._get_user_approval()
            assert result is True
        
        # Test rejection with mock input
        with patch('builtins.input', return_value='n'):
            result = await cli._get_user_approval()
            assert result is False
        
        # Test refine option with mock input
        with patch('builtins.input', return_value='r'):
            result = await cli._get_user_approval()
            assert result is False
    
    @pytest.mark.asyncio
    async def test_save_current_session_with_session(self, sample_session: StorySession):
        """Test saving current session when session exists."""
        cli = StorytellingCLI()
        cli.current_session = sample_session
        
        with patch.object(cli.storage, 'save_session') as mock_save:
            await cli._save_current_session()
            mock_save.assert_called_once_with(sample_session)
    
    @pytest.mark.asyncio
    async def test_save_current_session_no_session(self):
        """Test saving when no current session."""
        cli = StorytellingCLI()
        
        # Should handle gracefully when no session
        await cli._save_current_session()
        assert True
    
    @pytest.mark.asyncio
    async def test_save_current_session_error_handling(self, sample_session: StorySession):
        """Test error handling during session save."""
        cli = StorytellingCLI()
        cli.current_session = sample_session
        
        with patch.object(cli.storage, 'save_session', side_effect=Exception("Save failed")):
            # Should handle save errors gracefully
            await cli._save_current_session()
            assert True
    
    @pytest.mark.asyncio
    async def test_list_sessions_empty(self):
        """Test listing sessions when none exist."""
        cli = StorytellingCLI()
        
        with patch.object(cli.storage, 'list_sessions', return_value=[]):
            await cli._list_sessions()
            assert True
    
    @pytest.mark.asyncio
    async def test_list_sessions_with_data(self, sample_session: StorySession):
        """Test listing sessions with existing data."""
        cli = StorytellingCLI()
        
        with patch.object(cli.storage, 'list_sessions', return_value=[sample_session]):
            await cli._list_sessions()
            assert True


class TestCommandHandler:
    """Test cases for CLI command handlers."""
    
    def test_command_handler_initialization(self, file_storage):
        """Test CommandHandler initialization."""
        handler = CommandHandler(file_storage)
        assert handler.storage == file_storage
    
    @pytest.mark.asyncio
    async def test_handle_info_command_with_session(self, file_storage, sample_session: StorySession):
        """Test info command with active session."""
        handler = CommandHandler(file_storage)
        
        result = await handler.handle_info_command(sample_session)
        
        assert "SESSION INFORMATION" in result
        assert sample_session.id in result
        assert sample_session.world.premise in result
    
    @pytest.mark.asyncio
    async def test_handle_info_command_without_session(self, file_storage):
        """Test info command without active session."""
        handler = CommandHandler(file_storage)
        
        with patch.object(file_storage, 'list_sessions', return_value=[]):
            result = await handler.handle_info_command()
            
            assert "SYSTEM INFORMATION" in result
            assert "Total sessions: 0" in result
    
    @pytest.mark.asyncio
    async def test_handle_characters_command_with_session(self, file_storage, sample_session: StorySession):
        """Test characters command with active session."""
        handler = CommandHandler(file_storage)
        
        result = await handler.handle_characters_command(sample_session)
        
        assert "CHARACTERS IN CURRENT STORY" in result
        assert "Alice" in result  # From sample character
    
    @pytest.mark.asyncio
    async def test_handle_characters_command_no_session(self, file_storage):
        """Test characters command without active session."""
        handler = CommandHandler(file_storage)
        
        result = await handler.handle_characters_command()
        
        assert "No active session" in result
    
    @pytest.mark.asyncio
    async def test_handle_characters_command_no_characters(self, file_storage):
        """Test characters command with session but no characters."""
        handler = CommandHandler(file_storage)
        
        # Create session with no characters
        empty_world = StoryWorld("Test", "Test", [], {}, Scene("", "", ""), [])
        empty_session = StorySession.create_new(empty_world)
        
        result = await handler.handle_characters_command(empty_session)
        
        assert "No characters" in result
    
    @pytest.mark.asyncio
    async def test_handle_history_command_with_session(self, file_storage, sample_session: StorySession):
        """Test history command with active session."""
        handler = CommandHandler(file_storage)
        
        result = await handler.handle_history_command(sample_session, count=5)
        
        assert "STORY HISTORY" in result
        # Should contain history from sample session
        assert len(result) > 0
    
    @pytest.mark.asyncio
    async def test_handle_history_command_no_session(self, file_storage):
        """Test history command without active session."""
        handler = CommandHandler(file_storage)
        
        result = await handler.handle_history_command()
        
        assert "No active session" in result
    
    @pytest.mark.asyncio
    async def test_handle_history_command_no_history(self, file_storage):
        """Test history command with session but no history."""
        handler = CommandHandler(file_storage)
        
        # Create session with no history
        empty_world = StoryWorld("Test", "Test", [], {}, Scene("", "", ""), [])
        empty_session = StorySession.create_new(empty_world)
        
        result = await handler.handle_history_command(empty_session)
        
        assert "No story history" in result
    
    @pytest.mark.asyncio
    async def test_handle_scene_command_with_session(self, file_storage, sample_session: StorySession):
        """Test scene command with active session."""
        handler = CommandHandler(file_storage)
        
        result = await handler.handle_scene_command(sample_session)
        
        assert "CURRENT SCENE" in result
        assert sample_session.world.current_scene.location in result
    
    @pytest.mark.asyncio
    async def test_handle_scene_command_no_session(self, file_storage):
        """Test scene command without active session."""
        handler = CommandHandler(file_storage)
        
        result = await handler.handle_scene_command()
        
        assert "No active session" in result
    
    @pytest.mark.asyncio
    async def test_handle_export_command_txt_format(self, file_storage, sample_session: StorySession, tmp_path):
        """Test export command with text format."""
        handler = CommandHandler(file_storage)
        
        # Change to temp directory for test
        import os
        original_cwd = os.getcwd()
        os.chdir(tmp_path)
        
        try:
            result = await handler.handle_export_command(sample_session, "txt")
            
            assert "exported" in result.lower()
            # Check that file was created
            export_file = tmp_path / f"story_export_{sample_session.id[:8]}.txt"
            assert export_file.exists()
            
            # Check file content
            content = export_file.read_text()
            assert sample_session.world.premise in content
        finally:
            os.chdir(original_cwd)
    
    @pytest.mark.asyncio
    async def test_handle_export_command_json_format(self, file_storage, sample_session: StorySession, tmp_path):
        """Test export command with JSON format."""
        handler = CommandHandler(file_storage)
        
        import os
        original_cwd = os.getcwd()
        os.chdir(tmp_path)
        
        try:
            result = await handler.handle_export_command(sample_session, "json")
            
            assert "exported" in result.lower()
            export_file = tmp_path / f"story_export_{sample_session.id[:8]}.json"
            assert export_file.exists()
        finally:
            os.chdir(original_cwd)
    
    @pytest.mark.asyncio
    async def test_handle_export_command_invalid_format(self, file_storage, sample_session: StorySession):
        """Test export command with invalid format."""
        handler = CommandHandler(file_storage)
        
        result = await handler.handle_export_command(sample_session, "invalid")
        
        assert "Unsupported format" in result
    
    @pytest.mark.asyncio
    async def test_handle_export_command_no_session(self, file_storage):
        """Test export command without active session."""
        handler = CommandHandler(file_storage)
        
        result = await handler.handle_export_command(None, "txt")
        
        assert "No active session" in result
    
    @pytest.mark.asyncio
    async def test_handle_stats_command_with_session(self, file_storage, sample_session: StorySession):
        """Test stats command with active session."""
        handler = CommandHandler(file_storage)
        
        result = await handler.handle_stats_command(sample_session)
        
        assert "SESSION STATISTICS" in result
        assert sample_session.id in result
        assert "Characters:" in result
        assert "History entries:" in result
    
    @pytest.mark.asyncio
    async def test_handle_stats_command_no_session(self, file_storage):
        """Test stats command without active session."""
        handler = CommandHandler(file_storage)
        
        result = await handler.handle_stats_command()
        
        assert "No active session" in result
    
    @pytest.mark.asyncio
    async def test_handle_diagnostics_command(self, file_storage):
        """Test diagnostics command."""
        handler = CommandHandler(file_storage)
        
        with patch('src.cli.commands.validate_environment') as mock_validate:
            mock_validate.return_value = {"api_key_present": True, "LLM_MODEL": True}
            
            result = await handler.handle_diagnostics_command()
            
            assert "SYSTEM DIAGNOSTICS" in result
            assert "Environment Variables:" in result