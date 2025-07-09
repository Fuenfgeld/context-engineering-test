"""Character embodiment agent that serves as a tool for the main storyteller."""

from __future__ import annotations

import os
from dataclasses import dataclass
from typing import Optional

import httpx
import logfire
from dotenv import load_dotenv
from pydantic_ai import Agent, RunContext
from pydantic_ai.models.openai import OpenAIModel
from pydantic_ai.providers.openai import OpenAIProvider

from models.story import StoryWorld
from agents.prompts import CHARACTER_SYSTEM_PROMPT

load_dotenv()


@dataclass
class StoryDeps:
    """
    Dependencies for storytelling agents.
    
    Attributes:
        story_world: The current story world state
        client: HTTP client for external requests
    """
    story_world: StoryWorld
    client: httpx.AsyncClient


def get_model() -> OpenAIModel:
    """
    Get the configured LLM model.
    
    Returns:
        Configured OpenAI model instance
    """
    llm = os.getenv('LLM_MODEL', 'gpt-4o-mini')

    # Use OpenRouter if key is available, otherwise use OpenAI
    if os.getenv('OPEN_ROUTER_API_KEY'):
        
            provider = OpenAIProvider(
                base_url='https://openrouter.ai/api/v1',
                api_key=os.getenv('OPEN_ROUTER_API_KEY'))

            return OpenAIModel(
                model_name='gpt-4o-mini',
                provider=provider
                )


    else:
        return OpenAIModel(llm, api_key=os.getenv('OPENAI_API_KEY'))


# Configure logfire with comprehensive instrumentation
logfire_token = os.getenv('LOGFIRE_TOKEN')
if logfire_token:
    logfire.configure(token=logfire_token, inspect_arguments=False)
else:
    logfire.configure(send_to_logfire='if-token-present', inspect_arguments=False)

# Enable instrumentation if available
try:
    logfire.instrument_pydantic_ai()  # Instrument PydanticAI for comprehensive LLM call logging
except Exception as e:
    pass  # Gracefully handle missing dependencies

try:
    logfire.instrument_openai()  # Instrument OpenAI provider
except Exception as e:
    pass  # Gracefully handle missing dependencies

try:
    logfire.instrument_httpx()  # Instrument HTTP calls
except Exception as e:
    pass  # Gracefully handle missing dependencies


# Create the character agent (no tools - just responds as character)
character_agent = Agent(
    get_model(),
    system_prompt=CHARACTER_SYSTEM_PROMPT,
    deps_type=StoryDeps,
    retries=2
)


# This function is used as a tool by the storyteller agent
async def embody_character(
    ctx: RunContext[StoryDeps],
    character_name: str,
    situation: str
) -> str:
    """
    Embody a character and respond to a given situation.
    
    This tool allows the character agent to portray NPCs with their
    distinct personalities, speech patterns, and motivations.
    
    Args:
        ctx: The runtime context containing story dependencies
        character_name: Name of the character to embody
        situation: The situation the character should respond to
    
    Returns:
        The character's response to the situation
    
    Raises:
        ValueError: If the character is not found in the story world
    """
    with logfire.span(
        'Character embodiment: {character_name}',
        character_name=character_name,
        situation=situation[:100] + '...' if len(situation) > 100 else situation
    ) as span:
        # Get the character from the story world
        character = ctx.deps.story_world.characters.get(character_name)

        if not character:
            span.set_attribute('character_found', False)
            logfire.error(
                'Character not found in story world',
                character_name=character_name,
                available_characters=list(ctx.deps.story_world.characters.keys())
            )
            raise ValueError(f"Character '{character_name}' not found in the story world")

        span.set_attribute('character_found', True)
        span.set_attribute('character_description', character.description[:100] + '...' if len(character.description) > 100 else character.description)
        span.set_attribute('character_memory_count', len(character.memories))
        span.set_attribute('character_relationship_count', len(character.relationships))

        # Build context about the character for the AI
        with logfire.span('Building character context') as context_span:
            character_context = f"""
Character: {character.name}
Description: {character.description}
Personality: {character.personality}
Speech Patterns: {character.speech_patterns}
Recent Memories: {', '.join(character.memories[-5:]) if character.memories else 'None'}
Relationships: {', '.join([f'{name}: {rel}' for name, rel in character.relationships.items()]) if character.relationships else 'None'}

Current Scene: {ctx.deps.story_world.current_scene.location}
Scene Description: {ctx.deps.story_world.current_scene.description}
Scene Atmosphere: {ctx.deps.story_world.current_scene.atmosphere}

Situation to respond to: {situation}
"""
            context_span.set_attribute('context_length', len(character_context))
            context_span.set_attribute('scene_location', ctx.deps.story_world.current_scene.location)

        # Run the character agent to get the response
        with logfire.span(
            'Running LLM character response',
            character_name=character_name,
            context_length=len(character_context)
        ) as llm_span:
            result = await character_agent.run(
                character_context,
                deps=ctx.deps
            )
            llm_span.set_attribute('response_length', len(str(result.output)))
            llm_span.set_attribute('model_used', str(get_model()))
            logfire.info(
                'Character LLM response completed',
                character_name=character_name,
                response_preview=str(result.output)[:150] + '...' if len(str(result.output)) > 150 else str(result.output)
            )

        # Update character memories with this interaction
        with logfire.span('Updating character memories') as memory_span:
            memory_entry = f"Responded to: {situation[:100]}{'...' if len(situation) > 100 else ''}"
            character.memories.append(memory_entry)
            
            # Keep memories manageable (last 20 entries)
            if len(character.memories) > 20:
                character.memories = character.memories[-20:]
                memory_span.set_attribute('memories_trimmed', True)
            
            memory_span.set_attribute('total_memories', len(character.memories))
            memory_span.set_attribute('memory_added', memory_entry)
            span.set_attribute('character_response_generated', True)
            span.set_attribute('final_memory_count', len(character.memories))

        return str(result.output)


class CharacterManager:
    """
    Manager class for character-related operations.
    
    Provides utilities for managing character interactions and state.
    """

    def __init__(self, story_world: StoryWorld, client: httpx.AsyncClient):
        """
        Initialize character manager.
        
        Args:
            story_world: The story world containing characters
            client: HTTP client for external requests
        """
        self.story_world = story_world
        self.client = client
        self.deps = StoryDeps(story_world=story_world, client=client)

    async def character_speaks(self, character_name: str, situation: str) -> str:
        """
        Have a character respond to a situation.
        
        Args:
            character_name: Name of the character
            situation: The situation to respond to
            
        Returns:
            The character's response
        """
        with logfire.span(
            'Character manager: character speaks',
            character_name=character_name,
            situation_length=len(situation)
        ) as span:
            result = await embody_character(
                RunContext(deps=self.deps),
                character_name,
                situation
            )
            span.set_attribute('response_generated', True)
            span.set_attribute('response_length', len(str(result)))
            return str(result)

    def get_character_summary(self, character_name: str) -> Optional[str]:
        """
        Get a brief summary of a character.
        
        Args:
            character_name: Name of the character
            
        Returns:
            Character summary or None if not found
        """
        character = self.story_world.characters.get(character_name)
        if not character:
            return None

        return f"{character.name}: {character.description[:100]}{'...' if len(character.description) > 100 else ''}"

    def list_characters(self) -> list[str]:
        """
        Get a list of all character names.
        
        Returns:
            List of character names
        """
        return list(self.story_world.characters.keys())

    def add_character_memory(self, character_name: str, memory: str) -> bool:
        """
        Add a memory to a character.
        
        Args:
            character_name: Name of the character
            memory: Memory to add
            
        Returns:
            True if memory was added, False if character not found
        """
        with logfire.span(
            'Adding character memory',
            character_name=character_name,
            memory=memory[:100] + '...' if len(memory) > 100 else memory
        ) as span:
            character = self.story_world.characters.get(character_name)
            if not character:
                span.set_attribute('character_found', False)
                logfire.warning(
                    'Attempted to add memory to non-existent character',
                    character_name=character_name,
                    available_characters=list(self.story_world.characters.keys())
                )
                return False

            span.set_attribute('character_found', True)
            span.set_attribute('memory_count_before', len(character.memories))
            
            character.memories.append(memory)

            # Keep memories manageable
            trimmed = False
            if len(character.memories) > 20:
                character.memories = character.memories[-20:]
                trimmed = True

            span.set_attribute('memory_count_after', len(character.memories))
            span.set_attribute('memories_trimmed', trimmed)
            span.set_attribute('memory_added', True)
            
            logfire.info(
                'Character memory added successfully',
                character_name=character_name,
                total_memories=len(character.memories)
            )

            return True
