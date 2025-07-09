"""Character creation agent that generates characters for stories."""

from __future__ import annotations

import os
from dataclasses import dataclass
from typing import Dict, List

import httpx
import logfire
from dotenv import load_dotenv
from pydantic import BaseModel, Field
from pydantic_ai import Agent, RunContext
from pydantic_ai.models.openai import OpenAIModel
from pydantic_ai.providers.openai import OpenAIProvider

from models.story import Character, StoryWorld

load_dotenv()


class CharacterCreationRequest(BaseModel):
    """
    Request model for character creation.
    
    Attributes:
        name: Character name
        description: Character description
        personality: Character personality traits
        speech_patterns: How the character speaks
        context: Additional context for character creation
    """
    name: str = Field(description="The character's name")
    description: str = Field(description="Physical appearance and background description")
    personality: str = Field(description="Personality traits and characteristics")
    speech_patterns: str = Field(description="How the character speaks and communicates")
    context: str = Field(default="", description="Additional context for character creation")


@dataclass
class CharacterCreationDeps:
    """
    Dependencies for character creation agent.
    
    Attributes:
        story_world: The current story world context
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
    logfire.instrument_pydantic_ai()
except Exception:
    pass

try:
    logfire.instrument_openai()
except Exception:
    pass

try:
    logfire.instrument_httpx()
except Exception:
    pass


CHARACTER_CREATION_PROMPT = """
You are an expert character creator for interactive storytelling. Your role is to create compelling, 
well-developed characters that will enhance the narrative experience.

When creating characters, consider:
1. Physical appearance and distinguishing features
2. Background and personal history
3. Personality traits, motivations, and flaws
4. Speech patterns and mannerisms
5. Relationships with other characters
6. Role in the story

Always create characters that feel authentic and three-dimensional, with clear motivations
and interesting quirks that make them memorable.
"""

# Create the character creation agent
character_creator_agent = Agent(
    get_model(),
    system_prompt=CHARACTER_CREATION_PROMPT,
    deps_type=CharacterCreationDeps,
    output_type=CharacterCreationRequest,
    retries=2
)


async def create_character(
    ctx: RunContext[CharacterCreationDeps],
    character_concept: str,
    story_context: str = ""
) -> CharacterCreationRequest:
    """
    Create a detailed character based on a concept and story context.
    
    Args:
        ctx: The runtime context containing dependencies
        character_concept: Basic concept or description of the character
        story_context: Additional story context for character creation
    
    Returns:
        CharacterCreationRequest with all character details
    """
    with logfire.span(
        'Creating character from concept',
        character_concept=character_concept[:100] + '...' if len(character_concept) > 100 else character_concept,
        story_context_length=len(story_context)
    ) as span:
        
        # Build context for character creation
        context_info = f"""
Story Setting: {ctx.deps.story_world.setting}
Story Premise: {ctx.deps.story_world.premise}
Existing Characters: {list(ctx.deps.story_world.characters.keys())}
Current Scene: {ctx.deps.story_world.current_scene.location}

Character Concept: {character_concept}
Additional Context: {story_context}

Create a detailed character that fits well into this story world and complements the existing characters.
"""
        
        span.set_attribute('context_length', len(context_info))
        span.set_attribute('existing_character_count', len(ctx.deps.story_world.characters))
        
        # Generate character using the agent
        with logfire.span('Running character creation LLM') as llm_span:
            result = await character_creator_agent.run(
                context_info,
                deps=ctx.deps
            )
            
            llm_span.set_attribute('character_created', True)
            llm_span.set_attribute('character_name', result.data.name)
            llm_span.set_attribute('description_length', len(result.data.description))
            llm_span.set_attribute('personality_length', len(result.data.personality))
            
            logfire.info(
                'Character created successfully',
                character_name=result.data.name,
                character_concept=character_concept,
                description_preview=result.data.description[:100] + '...' if len(result.data.description) > 100 else result.data.description
            )
            
            span.set_attribute('character_creation_successful', True)
            span.set_attribute('final_character_name', result.data.name)
            
            return result.data


class CharacterCreationManager:
    """
    Manager class for character creation operations.
    
    Provides utilities for creating and managing characters using the character creation agent.
    """

    def __init__(self, story_world: StoryWorld, client: httpx.AsyncClient):
        """
        Initialize character creation manager.
        
        Args:
            story_world: The story world where characters will be created
            client: HTTP client for external requests
        """
        self.story_world = story_world
        self.client = client
        self.deps = CharacterCreationDeps(story_world=story_world, client=client)

    async def create_character_from_concept(self, character_concept: str, story_context: str = "") -> Character:
        """
        Create a character from a concept and add it to the story world.
        
        Args:
            character_concept: Basic concept or description of the character
            story_context: Additional story context for character creation
            
        Returns:
            Created Character object
        """
        with logfire.span(
            'Character creation manager: create character',
            character_concept=character_concept[:50] + '...' if len(character_concept) > 50 else character_concept,
            story_context_length=len(story_context)
        ) as span:
            
            # Use the character creation agent to generate character
            result = await character_creator_agent.run(
                f"Create a character: {character_concept}\nStory context: {story_context}",
                deps=self.deps
            )
            char_request = result.data
            
            # Create Character object
            character = Character(
                name=char_request.name,
                description=char_request.description,
                personality=char_request.personality,
                speech_patterns=char_request.speech_patterns
            )
            
            # Add to story world
            self.story_world.add_character(character)
            
            span.set_attribute('character_added_to_world', True)
            span.set_attribute('character_name', character.name)
            span.set_attribute('total_characters_in_world', len(self.story_world.characters))
            
            logfire.info(
                'Character created and added to story world',
                character_name=character.name,
                total_characters=len(self.story_world.characters)
            )
            
            return character

    async def create_multiple_characters(self, character_concepts: List[str], story_context: str = "") -> List[Character]:
        """
        Create multiple characters from a list of concepts.
        
        Args:
            character_concepts: List of character concepts
            story_context: Additional story context for character creation
            
        Returns:
            List of created Character objects
        """
        with logfire.span(
            'Creating multiple characters',
            character_count=len(character_concepts),
            story_context_length=len(story_context)
        ) as span:
            
            characters = []
            for i, concept in enumerate(character_concepts):
                with logfire.span(f'Creating character {i+1}/{len(character_concepts)}') as char_span:
                    char_span.set_attribute('character_concept', concept[:50] + '...' if len(concept) > 50 else concept)
                    
                    character = await self.create_character_from_concept(concept, story_context)
                    characters.append(character)
                    
                    char_span.set_attribute('character_created', True)
                    char_span.set_attribute('character_name', character.name)
            
            span.set_attribute('total_characters_created', len(characters))
            span.set_attribute('character_names', [char.name for char in characters])
            
            logfire.info(
                'Multiple characters created successfully',
                character_count=len(characters),
                character_names=[char.name for char in characters]
            )
            
            return characters

    def get_character_summary(self, character_name: str) -> str:
        """
        Get a summary of a character.
        
        Args:
            character_name: Name of the character
            
        Returns:
            Character summary string
        """
        character = self.story_world.characters.get(character_name)
        if not character:
            return f"Character '{character_name}' not found"
        
        return f"{character.name}: {character.description[:100]}{'...' if len(character.description) > 100 else ''}"

    def list_characters(self) -> List[str]:
        """
        Get a list of all character names in the story world.
        
        Returns:
            List of character names
        """
        return list(self.story_world.characters.keys())