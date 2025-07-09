"""Main CLI interface for the storytelling application."""

from __future__ import annotations

from typing import List, Optional

import httpx
import logfire
from pydantic_ai.messages import (
    ModelMessage,
    ModelRequest,
    ModelResponse,
    TextPart,
    UserPromptPart,
)

from agents.storyteller import StorytellerAgent
from models.session import StorySession
from models.story import StoryWorld
from storage.file_storage import FileStorage
from utils.helpers import (
    format_character_list,
    format_story_history,
    get_display_timestamp,
    format_character_speech,
    format_narrator_text,
    format_system_message,
    format_error_message,
    format_success_message,
    parse_character_speech,
    format_story_with_colored_dialogue,
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
        with logfire.span('Starting interactive storytelling CLI') as span:
            print("🎭 Welcome to the Interactive Storytelling Experience!")
            print("=" * 50)

            try:
                logfire.info('CLI application started successfully')
                await self._main_menu()
                span.set_attribute('clean_exit', True)
            except KeyboardInterrupt:
                print("\n\nGoodbye! Thanks for storytelling with us! 👋")
                span.set_attribute('exit_type', 'keyboard_interrupt')
                logfire.info('CLI exited via keyboard interrupt')
            except Exception as e:
                print(f"\n❌ An unexpected error occurred: {e}")
                span.set_attribute('exit_type', 'error')
                span.set_attribute('error_message', str(e))
                logfire.error('CLI exited due to unexpected error', error=str(e))
                raise
            finally:
                await self.client.aclose()
                span.set_attribute('http_client_closed', True)

    async def _main_menu(self) -> None:
        """Display and handle the main menu."""
        while True:
            try:
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
            except KeyboardInterrupt:
                print("\n\n👋 Exiting...")
                if self.current_session:
                    await self._save_current_session()
                break

    async def _create_new_scenario(self) -> None:
        """Guide user through creating a new story scenario."""
        with logfire.span('Creating new story scenario') as span:
            print("\n🎨 CREATE NEW STORY SCENARIO")
            print("-" * 30)

            try:
                initial_concept = input("💡 Enter your story concept: ").strip()
                if not initial_concept:
                    print("❌ Story concept cannot be empty.")
                    span.set_attribute('empty_concept', True)
                    logfire.warning('User provided empty story concept')
                    return
            except KeyboardInterrupt:
                print("\n\n👋 Scenario creation cancelled by user.")
                span.set_attribute('cancelled_by_user', True)
                return

            span.set_attribute('story_concept', initial_concept[:100] + '...' if len(initial_concept) > 100 else initial_concept)
            span.set_attribute('concept_length', len(initial_concept))
            
            print("\n🤖 Creating your story world... This may take a moment.")

            try:
                # Create the story world using the storyteller agent
                with logfire.span('Creating story world via storyteller') as create_span:
                    story_world = await self.storyteller.create_scenario(initial_concept)
                    create_span.set_attribute('story_world_created', True)
                    create_span.set_attribute('character_count', len(story_world.characters))

                # Create a new session
                with logfire.span('Creating new story session') as session_span:
                    self.current_session = StorySession.create_new(story_world)
                    self.messages = []
                    session_span.set_attribute('session_id', self.current_session.id)
                    session_span.set_attribute('session_created', True)

                # Display the created scenario
                await self._display_scenario(story_world)

                # Ask for approval
                with logfire.span('Getting user approval') as approval_span:
                    approved = await self._get_user_approval()
                    approval_span.set_attribute('scenario_approved', approved)
                    
                    if approved:
                        print("✅ Scenario approved! Starting story session...")
                        span.set_attribute('scenario_approved', True)
                        await self._story_session()
                    else:
                        # Offer refinement
                        span.set_attribute('scenario_approved', False)
                        await self._refine_scenario()

            except Exception as e:
                print(f"❌ Error creating scenario: {e}")
                span.set_attribute('error_occurred', True)
                span.set_attribute('error_message', str(e))
                logfire.error('Error creating new scenario', error=str(e), concept=initial_concept)
                raise

    async def _load_existing_session(self) -> None:
        """Load and continue an existing story session."""
        with logfire.span('Loading existing story session') as span:
            with logfire.span('Listing available sessions') as list_span:
                sessions = self.storage.list_sessions()
                list_span.set_attribute('session_count', len(sessions))

            if not sessions:
                print("\n📭 No saved sessions found. Create a new scenario first!")
                span.set_attribute('no_sessions_found', True)
                logfire.info('No saved sessions found when attempting to load')
                return

            print("\n📚 SAVED STORY SESSIONS")
            print("-" * 30)

            for i, session in enumerate(sessions, 1):
                timestamp = get_display_timestamp(session.last_updated)
                print(f"{i}. {session.get_display_name()} (Last updated: {timestamp})")

            print(f"{len(sessions) + 1}. ← Back to main menu")

            try:
                choice = int(input(f"\nSelect session (1-{len(sessions) + 1}): "))
                span.set_attribute('user_choice', choice)

                if choice == len(sessions) + 1:
                    span.set_attribute('action', 'cancelled')
                    logfire.info('User cancelled session loading')
                    return
                elif 1 <= choice <= len(sessions):
                    selected_session = sessions[choice - 1]
                    span.set_attribute('action', 'session_loaded')
                    span.set_attribute('loaded_session_id', selected_session.id)
                    span.set_attribute('session_name', selected_session.get_display_name())
                    
                    with logfire.span('Setting up loaded session') as setup_span:
                        self.current_session = selected_session
                        self.messages = []  # Reset message history for session
                        setup_span.set_attribute('character_count', len(selected_session.world.characters))
                        setup_span.set_attribute('history_length', len(selected_session.world.history))

                    print(f"✅ Loaded: {selected_session.get_display_name()}")
                    logfire.info('Session loaded successfully', session_name=selected_session.get_display_name())
                    await self._story_session()
                else:
                    print("❌ Invalid choice.")
                    span.set_attribute('action', 'invalid_choice')
                    logfire.warning('User made invalid choice when loading session', choice=choice)
            except ValueError:
                print("❌ Please enter a valid number.")
                span.set_attribute('action', 'invalid_input')
                logfire.warning('User provided invalid input when loading session')

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
        with logfire.span(
            'Running story session',
            session_id=self.current_session.id if self.current_session else None
        ) as span:
            if not self.current_session:
                print("❌ No active session. This shouldn't happen!")
                span.set_attribute('no_active_session', True)
                logfire.error('Story session started without active session')
                return

            span.set_attribute('session_name', self.current_session.get_display_name())
            span.set_attribute('initial_character_count', len(self.current_session.world.characters))
            span.set_attribute('initial_history_length', len(self.current_session.world.history))

            print("\n🎭 STORY SESSION ACTIVE")
            print("-" * 30)
            print("📝 Type your character's actions or dialogue")
            print("🎯 Use *asterisks* for meta-commands to change story direction")
            print("💾 Type 'save' to save and continue, 'quit' to save and exit")
            print("=" * 50)

            # Display current story state
            await self._display_current_state()

            interaction_count = 0
            
            try:
                while True:
                    try:
                        user_input = input("\n> ").strip()

                        if not user_input:
                            continue

                        interaction_count += 1
                    except KeyboardInterrupt:
                        print("\n\n💾 Interrupted by user. Saving session before exit...")
                        await self._save_current_session()
                        break
                    except EOFError:
                        print("\n\n💾 Input stream closed. Saving session before exit...")
                        await self._save_current_session()
                        break
                    
                    with logfire.span(
                        'Processing user input',
                        interaction_number=interaction_count,
                        input_length=len(user_input)
                    ) as input_span:
                        if user_input.lower() in ['quit', 'exit']:
                            input_span.set_attribute('action_type', 'quit')
                            logfire.info('User initiated session quit')
                            await self._save_current_session()
                            break
                        elif user_input.lower() == 'save':
                            input_span.set_attribute('action_type', 'save')
                            logfire.info('User initiated manual save')
                            await self._save_current_session()
                            print("💾 Session saved!")
                            continue
                        elif user_input.lower() in ['help', '?']:
                            input_span.set_attribute('action_type', 'help')
                            await self._display_help()
                            continue
                        elif user_input.lower() == 'status':
                            input_span.set_attribute('action_type', 'status')
                            await self._display_current_state()
                            continue

                        input_span.set_attribute('action_type', 'story_input')
                        input_span.set_attribute('user_input_preview', user_input[:50] + '...' if len(user_input) > 50 else user_input)
                        
                        # Process the story input
                        try:
                            with logfire.span('Processing story continuation') as story_span:
                                response, updated_world = await self.storyteller.continue_story(
                                    user_input, self.current_session.world
                                )
                                story_span.set_attribute('response_length', len(response))
                                story_span.set_attribute('world_updated', True)

                            # Update session
                            with logfire.span('Updating session state') as update_span:
                                self.current_session.update_world(updated_world)
                                update_span.set_attribute('new_history_length', len(updated_world.history))

                            # Display the narrative response with colored character speech
                            print(f"\n{self._format_story_response(response)}")

                            # Update message history
                            with logfire.span('Updating message history') as msg_span:
                                self.messages.append(ModelRequest(parts=[UserPromptPart(content=user_input)]))
                                self.messages.append(ModelResponse(parts=[TextPart(content=response)]))
                                msg_span.set_attribute('total_messages', len(self.messages))
                                
                            input_span.set_attribute('story_processed_successfully', True)
                            logfire.info(
                                'Story interaction completed successfully',
                                interaction_number=interaction_count,
                                response_preview=response[:100] + '...' if len(response) > 100 else response
                            )

                        except Exception as e:
                            print(f"\n{format_error_message(f'Error continuing story: {e}')}")
                            input_span.set_attribute('story_error', True)
                            input_span.set_attribute('error_message', str(e))
                            logfire.error(
                                'Error processing story continuation',
                                error=str(e),
                                user_input=user_input,
                                interaction_number=interaction_count
                            )
                            
                            # Give user option to exit on error
                            retry_choice = input("\n🔄 Would you like to (r)etry, (s)ave and quit, or (c)ontinue? ").lower().strip()
                            if retry_choice in ['s', 'save', 'quit']:
                                await self._save_current_session()
                                break
                            elif retry_choice in ['c', 'continue']:
                                continue
                            # If 'r' or 'retry' or any other input, continue to retry

                span.set_attribute('total_interactions', interaction_count)
                span.set_attribute('session_completed', True)
                
            except KeyboardInterrupt:
                print("\n\n💾 Saving session before exit...")
                span.set_attribute('exit_type', 'keyboard_interrupt')
                span.set_attribute('total_interactions', interaction_count)
                logfire.info('Story session interrupted by user, saving session')
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
            try:
                choice = input("\n✅ Approve this scenario? (y/n/r for refine): ").lower().strip()
                if choice in ['y', 'yes']:
                    return True
                elif choice in ['n', 'no']:
                    return False
                elif choice in ['r', 'refine']:
                    return False
                else:
                    print("❌ Please enter 'y' for yes, 'n' for no, or 'r' to refine.")
            except KeyboardInterrupt:
                print("\n\n👋 User cancelled approval. Returning to main menu.")
                return False

    async def _refine_scenario(self) -> None:
        """Allow user to refine the scenario."""
        try:
            feedback = input("\n🔧 What would you like to change about the scenario? ").strip()
            if not feedback:
                return
        except KeyboardInterrupt:
            print("\n\n👋 Scenario refinement cancelled by user.")
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
        except KeyboardInterrupt:
            print("\n\n👋 Refinement cancelled by user.")
        except Exception as e:
            print(f"❌ Error refining scenario: {e}")

    async def _save_current_session(self) -> None:
        """Save the current session to storage."""
        with logfire.span(
            'Saving current session',
            session_id=self.current_session.id if self.current_session else None
        ) as span:
            if self.current_session:
                try:
                    span.set_attribute('session_name', self.current_session.get_display_name())
                    span.set_attribute('message_count', len(self.messages))
                    span.set_attribute('history_length', len(self.current_session.world.history))
                    span.set_attribute('character_count', len(self.current_session.world.characters))
                    
                    # Add message history to session
                    with logfire.span('Preparing message history') as msg_span:
                        self.current_session.message_history = [
                            {"type": "message", "content": str(msg)} for msg in self.messages
                        ]
                        msg_span.set_attribute('messages_processed', len(self.messages))

                    with logfire.span('Writing session to storage') as storage_span:
                        self.storage.save_session(self.current_session)
                        storage_span.set_attribute('save_successful', True)
                        
                    print(f"\n{format_success_message('Session saved successfully!')}")
                    span.set_attribute('save_successful', True)
                    logfire.info(
                        'Session saved successfully',
                        session_name=self.current_session.get_display_name(),
                        message_count=len(self.messages)
                    )
                    
                except Exception as e:
                    print(f"\n{format_error_message(f'Error saving session: {e}')}")
                    span.set_attribute('save_successful', False)
                    span.set_attribute('error_message', str(e))
                    logfire.error(
                        'Error saving session',
                        error=str(e),
                        session_name=self.current_session.get_display_name() if self.current_session else None
                    )
                    raise
            else:
                span.set_attribute('no_session_to_save', True)
                logfire.warning('Attempted to save session but no current session exists')

    def _format_story_response(self, response: str) -> str:
        """
        Format story response with colored character speech.
        
        Args:
            response: The raw story response from the storyteller
            
        Returns:
            Formatted response with colored character dialogue
        """
        # Use the improved formatting function
        formatted_response = format_story_with_colored_dialogue(response)
        return f"{format_system_message('Story continues...')}\n{formatted_response}"
