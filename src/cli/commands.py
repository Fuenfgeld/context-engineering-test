
"""Command handlers for the storytelling CLI application."""

from __future__ import annotations

from typing import Optional

from models.session import StorySession
from storage.file_storage import FileStorage
from utils.helpers import (
    get_display_timestamp,
    truncate_text,
    validate_environment,
)


class CommandHandler:
    """
    Handles various CLI commands and utilities.
    
    Provides functionality for session management, diagnostics,
    and utility operations.
    """

    def __init__(self, storage: FileStorage):
        """
        Initialize command handler.
        
        Args:
            storage: Storage instance for session management
        """
        self.storage = storage

    async def handle_info_command(self, session: Optional[StorySession] = None) -> str:
        """
        Handle info command to display session or system information.
        
        Args:
            session: Optional current session
            
        Returns:
            Formatted information string
        """
        if session:
            return self._format_session_info(session)
        else:
            return self._format_system_info()

    async def handle_characters_command(self, session: Optional[StorySession] = None) -> str:
        """
        Handle characters command to list characters in current session.
        
        Args:
            session: Optional current session
            
        Returns:
            Formatted character list
        """
        if not session:
            return "❌ No active session. Load or create a story first."

        if not session.world.characters:
            return "👥 No characters in this story yet."

        output = ["👥 CHARACTERS IN CURRENT STORY", "-" * 30]

        for i, (name, character) in enumerate(session.world.characters.items(), 1):
            output.append(f"{i}. **{character.name}**")
            output.append(f"   Description: {truncate_text(character.description, 80)}")
            output.append(f"   Personality: {truncate_text(character.personality, 80)}")

            if character.relationships:
                relationships = ", ".join([f"{name}: {rel}" for name, rel in character.relationships.items()])
                output.append(f"   Relationships: {truncate_text(relationships, 80)}")

            if character.memories:
                recent_memories = character.memories[-3:]  # Last 3 memories
                output.append(f"   Recent memories: {len(character.memories)} total")
                for memory in recent_memories:
                    output.append(f"     • {truncate_text(memory, 60)}")

            output.append("")  # Empty line between characters

        return "\n".join(output)

    async def handle_history_command(self, session: Optional[StorySession] = None, count: int = 10) -> str:
        """
        Handle history command to display story history.
        
        Args:
            session: Optional current session
            count: Number of history entries to show
            
        Returns:
            Formatted history string
        """
        if not session:
            return "❌ No active session. Load or create a story first."

        if not session.world.history:
            return "📜 No story history yet."

        output = [f"📜 STORY HISTORY (Last {count} entries)", "-" * 40]

        recent_history = session.world.history[-count:] if len(session.world.history) > count else session.world.history

        for i, entry in enumerate(recent_history, 1):
            output.append(f"{i}. {entry}")

        if len(session.world.history) > count:
            remaining = len(session.world.history) - count
            output.append(f"\n... and {remaining} earlier entries")

        return "\n".join(output)

    async def handle_scene_command(self, session: Optional[StorySession] = None) -> str:
        """
        Handle scene command to display current scene details.
        
        Args:
            session: Optional current session
            
        Returns:
            Formatted scene information
        """
        if not session:
            return "❌ No active session. Load or create a story first."

        scene = session.world.current_scene
        output = ["🎬 CURRENT SCENE", "-" * 20]

        output.extend([
            f"📍 Location: {scene.location}",
            f"📝 Description: {scene.description}",
            f"🌟 Atmosphere: {scene.atmosphere}",
        ])

        if scene.active_characters:
            output.append(f"👥 Present: {', '.join(scene.active_characters)}")
        else:
            output.append("👥 Present: You are alone")

        if scene.props:
            output.append(f"🎭 Props: {', '.join(scene.props)}")

        return "\n".join(output)

    async def handle_export_command(self, session: Optional[StorySession] = None, format: str = "txt") -> str:
        """
        Handle export command to export session data.
        
        Args:
            session: Optional current session
            format: Export format (txt, json)
            
        Returns:
            Status message about export
        """
        if not session:
            return "❌ No active session. Load or create a story first."

        try:
            filename = f"story_export_{session.id[:8]}.{format}"

            if format == "txt":
                content = self._export_as_text(session)
            elif format == "json":
                content = session.to_json()
            else:
                return "❌ Unsupported format. Use 'txt' or 'json'."

            with open(filename, 'w', encoding='utf-8') as f:
                f.write(content)

            return f"✅ Story exported to {filename}"

        except Exception as e:
            return f"❌ Export failed: {e}"

    async def handle_stats_command(self, session: Optional[StorySession] = None) -> str:
        """
        Handle stats command to display session statistics.
        
        Args:
            session: Optional current session
            
        Returns:
            Formatted statistics
        """
        if not session:
            return "❌ No active session. Load or create a story first."

        output = ["📊 SESSION STATISTICS", "-" * 25]

        # Basic stats
        character_count = len(session.world.characters)
        history_length = len(session.world.history)
        conflict_count = len(session.world.conflicts)

        output.extend([
            f"🆔 Session ID: {session.id}",
            f"📅 Created: {session.created_at.strftime('%Y-%m-%d %H:%M')}",
            f"🔄 Last updated: {get_display_timestamp(session.last_updated)}",
            f"👥 Characters: {character_count}",
            f"📜 History entries: {history_length}",
            f"⚔️  Conflicts: {conflict_count}",
        ])

        # Character memory stats
        if session.world.characters:
            total_memories = sum(len(char.memories) for char in session.world.characters.values())
            avg_memories = total_memories / character_count if character_count > 0 else 0
            output.append(f"🧠 Total character memories: {total_memories} (avg: {avg_memories:.1f} per character)")

        # Session file size (if available)
        try:
            import os
            session_file = f"stories/{session.id}.json"
            if os.path.exists(session_file):
                file_size = os.path.getsize(session_file)
                output.append(f"💾 File size: {file_size:,} bytes")
        except:
            pass

        return "\n".join(output)

    async def handle_diagnostics_command(self) -> str:
        """
        Handle diagnostics command to check system status.
        
        Returns:
            Diagnostic information
        """
        output = ["🔧 SYSTEM DIAGNOSTICS", "-" * 25]

        # Environment validation
        env_status = validate_environment()
        output.append("🌍 Environment Variables:")

        for var, status in env_status.items():
            status_icon = "✅" if status else "❌"
            output.append(f"   {status_icon} {var}")

        # Storage diagnostics
        try:
            sessions = self.storage.list_sessions()
            output.append(f"\n💾 Storage: ✅ Working ({len(sessions)} sessions)")
        except Exception as e:
            output.append(f"\n💾 Storage: ❌ Error - {e}")

        # Check for common issues
        issues = []
        if not env_status.get('api_key_present', False):
            issues.append("No API key configured (OPENAI_API_KEY or OPEN_ROUTER_API_KEY)")

        if issues:
            output.append("\n⚠️  Issues Found:")
            for issue in issues:
                output.append(f"   • {issue}")
        else:
            output.append("\n✅ No issues detected")

        return "\n".join(output)

    def _format_session_info(self, session: StorySession) -> str:
        """Format detailed session information."""
        output = ["ℹ️  SESSION INFORMATION", "-" * 25]

        output.extend([
            f"🆔 ID: {session.id}",
            f"📖 Story: {session.get_display_name()}",
            f"📅 Created: {session.created_at.strftime('%Y-%m-%d %H:%M')}",
            f"🔄 Updated: {get_display_timestamp(session.last_updated)}",
            "",
            f"📝 Premise: {session.world.premise}",
            f"🌍 Setting: {session.world.setting}",
            "",
            f"👥 Characters: {len(session.world.characters)}",
            f"📜 History: {len(session.world.history)} entries",
            f"⚔️  Conflicts: {len(session.world.conflicts)}",
        ])

        return "\n".join(output)

    def _format_system_info(self) -> str:
        """Format system information."""
        output = ["ℹ️  SYSTEM INFORMATION", "-" * 25]

        try:
            sessions = self.storage.list_sessions()
            output.extend([
                f"💾 Total sessions: {len(sessions)}",
                f"📁 Storage directory: {self.storage.storage_dir}",
            ])

            if sessions:
                most_recent = max(sessions, key=lambda s: s.last_updated)
                output.append(f"🔄 Most recent: {most_recent.get_display_name()}")
        except Exception as e:
            output.append(f"❌ Storage error: {e}")

        return "\n".join(output)

    def _export_as_text(self, session: StorySession) -> str:
        """Export session as formatted text."""
        output = [
            f"STORY EXPORT: {session.get_display_name()}",
            "=" * 50,
            f"Session ID: {session.id}",
            f"Created: {session.created_at}",
            f"Last Updated: {session.last_updated}",
            "",
            "PREMISE:",
            session.world.premise,
            "",
            "SETTING:",
            session.world.setting,
            "",
        ]

        if session.world.conflicts:
            output.extend(["CONFLICTS:", *[f"• {conflict}" for conflict in session.world.conflicts], ""])

        if session.world.characters:
            output.append("CHARACTERS:")
            for name, character in session.world.characters.items():
                output.extend([
                    f"• {character.name}",
                    f"  Description: {character.description}",
                    f"  Personality: {character.personality}",
                    f"  Speech: {character.speech_patterns}",
                    ""
                ])

        if session.world.history:
            output.extend(["STORY HISTORY:", "-" * 20])
            output.extend(session.world.history)

        return "\n".join(output)
