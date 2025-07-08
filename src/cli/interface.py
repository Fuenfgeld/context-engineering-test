"""Main CLI interface for the storytelling application."""

from __future__ import annotations

from typing import List, Optional

import httpx
from pydantic_ai.messages import (
    ModelMessage,
    ModelRequest,
    ModelResponse,
    TextPart,
    UserPromptPart,
)

from ..agents.storyteller import StorytellerAgent
from ..models.session import StorySession
from ..models.story import StoryWorld
from ..storage.file_storage import FileStorage
from ..utils.helpers import (
    format_character_list,
    format_story_history,
    get_display_timestamp,
)


class StorytellingCLI:
    """
    Command-line interface for the interactive storytelling application.
    
    Manages user interactions, session state, and coordinates between
    the storyteller agent and storage system.
    """

    def __init__(self) -> None:
        """Initialize the CLI with necessary components."""
        self.client = httpx.AsyncClient()
        self.storyteller = StorytellerAgent(self.client)
        self.storage = FileStorage()

        self.current_session: Optional[StorySession] = None
        self.messages: List[ModelMessage] = []

    async def start(self) -> None:
        """Start the interactive storytelling CLI."""
        print("🎭 Welcome to the Interactive Storytelling Experience!")
        print("=" * 50)

        try:
            await self._main_menu()
        except KeyboardInterrupt:
            print("\n\nGoodbye! Thanks for storytelling with us! 👋")
        except Exception as e:
            print(f"\n❌ An unexpected error occurred: {e}")
        finally:
            await self.client.aclose()

    async def _main_menu(self) -> None:
        """Display and handle the main menu."""
        while True:
            print("\n" + "=" * 50)
            print("📖 STORYTELLING MENU")
            print("=" * 50)
            print("1. 🆕 Create new story scenario")
            print("2. 📚 Load existing story session")
            print("3. 📋 List all saved sessions")
            print("4. 🗑️  Delete a story session")
            print("5. ❌ Exit")
            print()

            choice = input("Choose an option (1-5): ").strip()

            if choice == "1":
                await self._create_new_scenario()
            elif choice == "2":
                await self._load_existing_session()
            elif choice == "3":
                await self._list_sessions()
            elif choice == "4":
                await self._delete_session()
            elif choice == "5":
                if self.current_session:
                    await self._save_current_session()
                break
            else:
                print("❌ Invalid choice. Please select 1-5.")

    async def _create_new_scenario(self) -> None:
        """Guide user through creating a new story scenario."""
        print("\n🎨 CREATE NEW STORY SCENARIO")
        print("-" * 30)

        initial_concept = input("💡 Enter your story concept: ").strip()
        if not initial_concept:
            print("❌ Story concept cannot be empty.")
            return

        print("\n🤖 Creating your story world... This may take a moment.")

        try:
            # Create the story world using the storyteller agent
            story_world = await self.storyteller.create_scenario(initial_concept)

            # Create a new session
            self.current_session = StorySession.create_new(story_world)
            self.messages = []

            # Display the created scenario
            await self._display_scenario(story_world)

            # Ask for approval
            if await self._get_user_approval():
                print("✅ Scenario approved! Starting story session...")
                await self._story_session()
            else:
                # Offer refinement
                await self._refine_scenario()

        except Exception as e:
            print(f"❌ Error creating scenario: {e}")

    async def _load_existing_session(self) -> None:
        """Load and continue an existing story session."""
        sessions = self.storage.list_sessions()

        if not sessions:
            print("\n📭 No saved sessions found. Create a new scenario first!")
            return

        print("\n📚 SAVED STORY SESSIONS")
        print("-" * 30)

        for i, session in enumerate(sessions, 1):
            timestamp = get_display_timestamp(session.last_updated)
            print(f"{i}. {session.get_display_name()} (Last updated: {timestamp})")

        print(f"{len(sessions) + 1}. ← Back to main menu")

        try:
            choice = int(input(f"\nSelect session (1-{len(sessions) + 1}): "))

            if choice == len(sessions) + 1:
                return
            elif 1 <= choice <= len(sessions):
                selected_session = sessions[choice - 1]
                self.current_session = selected_session
                self.messages = []  # Reset message history for session

                print(f"✅ Loaded: {selected_session.get_display_name()}")
                await self._story_session()
            else:
                print("❌ Invalid choice.")
        except ValueError:
            print("❌ Please enter a valid number.")

    async def _list_sessions(self) -> None:
        """List all saved story sessions with details."""
        sessions = self.storage.list_sessions()

        if not sessions:
            print("\n📭 No saved sessions found.")
            return

        print(f"\n📚 ALL STORY SESSIONS ({len(sessions)} total)")
        print("-" * 50)

        for i, session in enumerate(sessions, 1):
            timestamp = get_display_timestamp(session.last_updated)
            character_count = len(session.world.characters)
            history_length = len(session.world.history)

            print(f"{i}. {session.get_display_name()}")
            print(f"   📅 Last updated: {timestamp}")
            print(f"   👥 Characters: {character_count}")
            print(f"   📜 History entries: {history_length}")
            print(f"   🆔 ID: {session.id[:8]}...")
            print()

    async def _delete_session(self) -> None:
        """Delete a story session."""
        sessions = self.storage.list_sessions()

        if not sessions:
            print("\n📭 No saved sessions found.")
            return

        print("\n🗑️  DELETE STORY SESSION")
        print("-" * 30)

        for i, session in enumerate(sessions, 1):
            print(f"{i}. {session.get_display_name()}")

        print(f"{len(sessions) + 1}. ← Cancel")

        try:
            choice = int(input(f"\nSelect session to delete (1-{len(sessions) + 1}): "))

            if choice == len(sessions) + 1:
                return
            elif 1 <= choice <= len(sessions):
                selected_session = sessions[choice - 1]

                # Confirm deletion
                confirm = input(f"⚠️  Really delete '{selected_session.get_display_name()}'? (y/N): ")
                if confirm.lower() == 'y':
                    if self.storage.delete_session(selected_session.id):
                        print("✅ Session deleted successfully.")
                    else:
                        print("❌ Failed to delete session.")
                else:
                    print("❌ Deletion cancelled.")
            else:
                print("❌ Invalid choice.")
        except ValueError:
            print("❌ Please enter a valid number.")

    async def _story_session(self) -> None:
        """Run the main storytelling session loop."""
        if not self.current_session:
            print("❌ No active session. This shouldn't happen!")
            return

        print("\n🎭 STORY SESSION ACTIVE")
        print("-" * 30)
        print("📝 Type your character's actions or dialogue")
        print("🎯 Use *asterisks* for meta-commands to change story direction")
        print("💾 Type 'save' to save and continue, 'quit' to save and exit")
        print("=" * 50)

        # Display current story state
        await self._display_current_state()

        try:
            while True:
                user_input = input("\n> ").strip()

                if not user_input:
                    continue

                if user_input.lower() in ['quit', 'exit']:
                    await self._save_current_session()
                    break
                elif user_input.lower() == 'save':
                    await self._save_current_session()
                    print("💾 Session saved!")
                    continue
                elif user_input.lower() in ['help', '?']:
                    await self._display_help()
                    continue
                elif user_input.lower() == 'status':
                    await self._display_current_state()
                    continue

                # Process the story input
                try:
                    response, updated_world = await self.storyteller.continue_story(
                        user_input, self.current_session.world
                    )

                    # Update session
                    self.current_session.update_world(updated_world)

                    # Display the narrative response
                    print(f"\n📖 {response}")

                    # Update message history
                    self.messages.append(ModelRequest(parts=[UserPromptPart(content=user_input)]))
                    self.messages.append(ModelResponse(parts=[TextPart(content=response)]))

                except Exception as e:
                    print(f"❌ Error continuing story: {e}")

        except KeyboardInterrupt:
            print("\n\n💾 Saving session before exit...")
            await self._save_current_session()

    async def _display_scenario(self, story_world: StoryWorld) -> None:
        """Display the created scenario details."""
        print("\n🎨 CREATED SCENARIO")
        print("=" * 40)
        print(f"📖 Premise: {story_world.premise}")
        print(f"🌍 Setting: {story_world.setting}")
        print(f"⚔️  Conflicts: {', '.join(story_world.conflicts)}")
        print(f"👥 Characters: {format_character_list(story_world.characters)}")
        print(f"🎬 Opening Scene: {story_world.current_scene.location}")
        print(f"   {story_world.current_scene.description}")

    async def _display_current_state(self) -> None:
        """Display the current story state."""
        if not self.current_session:
            return

        world = self.current_session.world
        print("\n📊 CURRENT STORY STATE")
        print("-" * 30)
        print(f"📍 Location: {world.current_scene.location}")
        print(f"🌟 Atmosphere: {world.current_scene.atmosphere}")
        print(f"👥 Present: {', '.join(world.current_scene.active_characters) if world.current_scene.active_characters else 'You are alone'}")
        print(f"📜 Recent Events:\n{format_story_history(world.history, 3)}")

    async def _display_help(self) -> None:
        """Display help information."""
        print("\n📚 HELP")
        print("-" * 20)
        print("💬 Regular input: Describe your character's actions or speech")
        print("🎯 *meta-command*: Change story direction (e.g., *it starts raining*)")
        print("💾 save: Save the session and continue")
        print("❌ quit/exit: Save and return to main menu")
        print("📊 status: Show current story state")
        print("❓ help/?): Show this help")

    async def _get_user_approval(self) -> bool:
        """Get user approval for the created scenario."""
        while True:
            choice = input("\n✅ Approve this scenario? (y/n/r for refine): ").lower().strip()
            if choice in ['y', 'yes']:
                return True
            elif choice in ['n', 'no']:
                return False
            elif choice in ['r', 'refine']:
                return False
            else:
                print("❌ Please enter 'y' for yes, 'n' for no, or 'r' to refine.")

    async def _refine_scenario(self) -> None:
        """Allow user to refine the scenario."""
        feedback = input("\n🔧 What would you like to change about the scenario? ").strip()
        if not feedback:
            return

        print("🤖 Refining scenario based on your feedback...")

        try:
            if self.current_session is None:
                print("❌ No active session.")
                return
            refined_world = await self.storyteller.refine_scenario(feedback, self.current_session.world)
            self.current_session.update_world(refined_world)

            await self._display_scenario(refined_world)

            if await self._get_user_approval():
                print("✅ Refined scenario approved! Starting story session...")
                await self._story_session()
            else:
                print("📝 Returning to main menu. Scenario not saved.")
        except Exception as e:
            print(f"❌ Error refining scenario: {e}")

    async def _save_current_session(self) -> None:
        """Save the current session to storage."""
        if self.current_session:
            try:
                # Add message history to session
                self.current_session.message_history = [
                    {"type": "message", "content": str(msg)} for msg in self.messages
                ]

                self.storage.save_session(self.current_session)
                print("💾 Session saved successfully!")
            except Exception as e:
                print(f"❌ Error saving session: {e}")
