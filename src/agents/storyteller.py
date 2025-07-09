"""Main storyteller agent that orchestrates the interactive storytelling experience."""

from __future__ import annotations

from typing import Dict, Tuple

import httpx
import logfire
from pydantic_ai import Agent

from models.story import Character, Scene, StoryWorld
from agents.character import StoryDeps, embody_character, get_model
from agents.character_creator import CharacterCreationManager
from agents.scenario_generator import ScenarioGenerationManager
from agents.prompts import STORYTELLER_SYSTEM_PROMPT


class StorytellerAgent:
    """
    Main storytelling agent that orchestrates narrative generation.
    
    This agent manages scenario creation, story progression, and character
    interactions through delegation to the character agent.
    """

    def __init__(self, client: httpx.AsyncClient):
        """
        Initialize the storyteller agent.
        
        Args:
            client: HTTP client for external requests
        """
        self.client = client

        # Create the main agent with character tool
        self.agent = Agent(
            get_model(),
            system_prompt=STORYTELLER_SYSTEM_PROMPT,
            deps_type=StoryDeps,
            tools=[embody_character],
            retries=2
        )
        
        # Initialize specialized managers
        self.scenario_manager = ScenarioGenerationManager(client)
        self.character_creation_manager = None  # Will be initialized when we have a story world

    async def create_scenario(self, initial_concept: str) -> StoryWorld:
        """
        Create a complete story scenario using specialized agents.
        
        Args:
            initial_concept: The initial story concept from the user
            
        Returns:
            A complete StoryWorld with all necessary elements
        """
        with logfire.span(
            'Creating story scenario from concept: {concept}',
            concept=initial_concept
        ) as span:
            
            # Step 1: Create the base scenario using scenario generator
            with logfire.span('Generating base scenario') as scenario_span:
                story_world, character_concepts = await self.scenario_manager.create_scenario_from_concept(initial_concept)
                scenario_span.set_attribute('scenario_generated', True)
                scenario_span.set_attribute('character_concepts_count', len(character_concepts))
                scenario_span.set_attribute('conflicts_count', len(story_world.conflicts))
                
                logfire.info(
                    'Base scenario generated',
                    premise_preview=story_world.premise[:100] + '...' if len(story_world.premise) > 100 else story_world.premise,
                    character_concepts=character_concepts
                )
            
            # Step 2: Initialize character creation manager with the story world
            with logfire.span('Initializing character creation') as char_init_span:
                self.character_creation_manager = CharacterCreationManager(story_world, self.client)
                char_init_span.set_attribute('character_manager_initialized', True)
            
            # Step 3: Create characters from the concepts
            with logfire.span('Creating characters from concepts') as char_creation_span:
                created_characters = []
                for i, concept in enumerate(character_concepts):
                    with logfire.span(f'Creating character {i+1}/{len(character_concepts)}') as single_char_span:
                        single_char_span.set_attribute('character_concept', concept[:50] + '...' if len(concept) > 50 else concept)
                        
                        # Create character using the character creation agent
                        character = await self.character_creation_manager.create_character_from_concept(
                            concept, 
                            f"Setting: {story_world.setting}\nPremise: {story_world.premise}"
                        )
                        created_characters.append(character)
                        
                        single_char_span.set_attribute('character_created', True)
                        single_char_span.set_attribute('character_name', character.name)
                
                char_creation_span.set_attribute('total_characters_created', len(created_characters))
                char_creation_span.set_attribute('character_names', [char.name for char in created_characters])
                
                logfire.info(
                    'Characters created from concepts',
                    character_count=len(created_characters),
                    character_names=[char.name for char in created_characters]
                )
            
            # Step 4: Update the opening scene with active characters
            with logfire.span('Updating opening scene with characters') as scene_span:
                # Add up to 2 characters to the opening scene as active
                active_characters = [char.name for char in created_characters[:2]]
                story_world.current_scene.active_characters = active_characters
                
                scene_span.set_attribute('active_characters_set', True)
                scene_span.set_attribute('active_characters', active_characters)
                scene_span.set_attribute('scene_location', story_world.current_scene.location)
                
                logfire.info(
                    'Opening scene updated with active characters',
                    scene_location=story_world.current_scene.location,
                    active_characters=active_characters
                )
                
                # Enhanced logging for final story world data structure
                logfire.info(
                    'Complete story world created',
                    story_world_structure={
                        'premise_length': len(story_world.premise),
                        'setting_length': len(story_world.setting),
                        'conflicts': story_world.conflicts,
                        'character_names': list(story_world.characters.keys()),
                        'character_details': {
                            name: {
                                'description_length': len(char.description),
                                'personality_length': len(char.personality),
                                'speech_patterns_length': len(char.speech_patterns),
                                'memories_count': len(char.memories),
                                'relationships_count': len(char.relationships)
                            } for name, char in story_world.characters.items()
                        },
                        'current_scene': {
                            'location': story_world.current_scene.location,
                            'description_length': len(story_world.current_scene.description),
                            'atmosphere': story_world.current_scene.atmosphere,
                            'active_characters': story_world.current_scene.active_characters,
                            'props': story_world.current_scene.props
                        },
                        'history_entries': len(story_world.history)
                    }
                )
                
                span.set_attribute('scenario_created', True)
                span.set_attribute('final_character_count', len(story_world.characters))
                span.set_attribute('final_conflicts_count', len(story_world.conflicts))
                span.set_attribute('active_characters_in_scene', len(active_characters))
                
            return story_world

    async def continue_story(self, user_input: str, story_world: StoryWorld) -> Tuple[str, StoryWorld]:
        """
        Continue the story based on user input.
        
        Args:
            user_input: The user's input or action
            story_world: Current story world state
            
        Returns:
            Tuple of (narrative response, updated story world)
        """
        with logfire.span(
            'Continuing story with user input',
            user_input=user_input[:100] + '...' if len(user_input) > 100 else user_input,
            current_scene=story_world.current_scene.location,
            active_characters=story_world.current_scene.active_characters
        ) as span:
            # Check for meta-commands
            is_meta = self._is_meta_command(user_input)
            span.set_attribute('is_meta_command', is_meta)
            
            if is_meta:
                with logfire.span('Handling meta-command') as meta_span:
                    meta_span.set_attribute('meta_command', user_input)
                    result = await self._handle_meta_command(user_input, story_world)
                    span.set_attribute('meta_command_processed', True)
                    return result

            # Create dependencies with current story world
            deps = StoryDeps(story_world=story_world, client=self.client)

            # Build context for the storytelling agent
            with logfire.span('Building story context') as context_span:
                story_context = self._build_story_context(user_input, story_world)
                context_span.set_attribute('context_length', len(story_context))
                context_span.set_attribute('history_entries', len(story_world.history))

            # Get narrative response from the agent
            with logfire.span(
                'Running LLM story continuation',
                input_length=len(user_input),
                context_length=len(story_context)
            ) as llm_span:
                result = await self.agent.run(story_context, deps=deps)
                llm_span.set_attribute('response_length', len(str(result.output)))
                llm_span.set_attribute('model_used', str(get_model()))
                logfire.info(
                    'LLM story continuation completed',
                    response_preview=str(result.output)[:200] + '...' if len(str(result.output)) > 200 else str(result.output)
                )

            # Update story history
            with logfire.span('Updating story history') as history_span:
                story_world.add_history_entry(f"User: {user_input}")
                story_world.add_history_entry(f"Narrator: {result.output}")
                history_span.set_attribute('total_history_entries', len(story_world.history))
                span.set_attribute('story_continued', True)
                span.set_attribute('final_history_length', len(story_world.history))

            return str(result.output), story_world

    async def refine_scenario(self, feedback: str, story_world: StoryWorld) -> StoryWorld:
        """
        Refine a scenario based on user feedback using specialized agents.
        
        Args:
            feedback: User feedback for improvements
            story_world: Current story world to refine
            
        Returns:
            Updated story world
        """
        with logfire.span(
            'Refining scenario based on feedback',
            feedback=feedback[:100] + '...' if len(feedback) > 100 else feedback,
            current_premise=story_world.premise[:50] + '...' if len(story_world.premise) > 50 else story_world.premise
        ) as span:
            
            # Use the scenario manager to refine the scenario
            with logfire.span('Refining scenario via scenario manager') as refine_span:
                refined_world = await self.scenario_manager.refine_scenario_from_feedback(story_world, feedback)
                refine_span.set_attribute('scenario_refined', True)
                refine_span.set_attribute('new_premise_length', len(refined_world.premise))
                refine_span.set_attribute('new_setting_length', len(refined_world.setting))
                
                logfire.info(
                    'Scenario refined via specialized agent',
                    feedback_preview=feedback[:50] + '...' if len(feedback) > 50 else feedback,
                    new_premise_preview=refined_world.premise[:100] + '...' if len(refined_world.premise) > 100 else refined_world.premise
                )
                
                span.set_attribute('scenario_refined', True)
                span.set_attribute('character_count_after', len(refined_world.characters))
                span.set_attribute('final_premise_length', len(refined_world.premise))
                
            return refined_world

    def _is_meta_command(self, user_input: str) -> bool:
        """Check if user input is a meta-command with *asterisks*."""
        return user_input.strip().startswith('*') and user_input.strip().endswith('*')

    async def _handle_meta_command(self, command: str, story_world: StoryWorld) -> Tuple[str, StoryWorld]:
        """
        Handle meta-commands that alter story direction.
        
        Args:
            command: The meta-command (including asterisks)
            story_world: Current story world state
            
        Returns:
            Tuple of (narrative response, updated story world)
        """
        with logfire.span(
            'Processing meta-command',
            meta_command=command,
            current_scene=story_world.current_scene.location
        ) as span:
            # Remove asterisks
            meta_instruction = command.strip()[1:-1]
            span.set_attribute('meta_instruction', meta_instruction)

            deps = StoryDeps(story_world=story_world, client=self.client)

            # Create prompt for handling the meta-command
            meta_prompt = f"""
The following change needs to be incorporated naturally into the ongoing narrative: {meta_instruction}

Current scene: {story_world.current_scene.location}
Recent history: {'; '.join(story_world.history[-3:]) if story_world.history else 'None'}

Incorporate this change seamlessly without acknowledging it as a command. Just naturally weave it into the story.
"""

            with logfire.span(
                'Running LLM meta-command processing',
                prompt_length=len(meta_prompt)
            ) as llm_span:
                result = await self.agent.run(meta_prompt, deps=deps)
                llm_span.set_attribute('response_length', len(str(result.output)))
                llm_span.set_attribute('model_used', str(get_model()))
                logfire.info(
                    'LLM meta-command processing completed',
                    meta_instruction=meta_instruction,
                    response_preview=str(result.output)[:200] + '...' if len(str(result.output)) > 200 else str(result.output)
                )

            # Add to history as a natural story development
            story_world.add_history_entry(f"Story development: {result.output}")
            span.set_attribute('meta_command_processed', True)
            span.set_attribute('history_entries_after', len(story_world.history))

            return str(result.output), story_world

    def _build_story_context(self, user_input: str, story_world: StoryWorld) -> str:
        """
        Build context string for the storytelling agent.
        
        Args:
            user_input: The user's current input
            story_world: Current story world state
            
        Returns:
            Formatted context string
        """
        recent_history = story_world.history[-5:] if story_world.history else []
        active_characters = story_world.current_scene.active_characters

        context = f"""
Current Scene: {story_world.current_scene.location}
Scene Description: {story_world.current_scene.description}
Atmosphere: {story_world.current_scene.atmosphere}
Active Characters: {', '.join(active_characters) if active_characters else 'None'}

Recent Story Events:
{chr(10).join(recent_history) if recent_history else 'This is the beginning of the story.'}

User Action/Input: {user_input}

Continue the narrative naturally, using character tools when NPCs need to speak or act.
"""
        return context
