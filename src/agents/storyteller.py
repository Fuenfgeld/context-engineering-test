"""Main storyteller agent that orchestrates the interactive storytelling experience."""

from __future__ import annotations

import re
from typing import Dict, Tuple

import httpx
from pydantic_ai import Agent

from ..models.story import Character, Scene, StoryWorld
from .character import StoryDeps, embody_character, get_model
from .prompts import STORYTELLER_SYSTEM_PROMPT


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

    async def create_scenario(self, initial_concept: str) -> StoryWorld:
        """
        Create a complete story scenario through conversational development.
        
        Args:
            initial_concept: The initial story concept from the user
            
        Returns:
            A complete StoryWorld with all necessary elements
        """
        # Create empty story world to start
        story_world = StoryWorld(
            premise="",
            setting="",
            conflicts=[],
            characters={},
            current_scene=Scene("", "", ""),
            history=[]
        )

        deps = StoryDeps(story_world=story_world, client=self.client)

        # Guide the agent to create a complete scenario
        scenario_prompt = f"""
Please help develop this story concept into a complete scenario: "{initial_concept}"

I need you to create:
1. A compelling premise (2-3 sentences)
2. A detailed setting description
3. 2-3 main conflicts or plot threads
4. 2-3 main characters with full profiles (name, description, personality, speech patterns)
5. An opening scene description

Present this as a structured response that I can approve or refine.
"""

        result = await self.agent.run(scenario_prompt, deps=deps)

        # Parse the agent's response to extract structured data
        scenario_data = self._parse_scenario_response(result.output)

        # Create the complete story world
        return self._build_story_world(scenario_data, initial_concept)

    async def continue_story(self, user_input: str, story_world: StoryWorld) -> Tuple[str, StoryWorld]:
        """
        Continue the story based on user input.
        
        Args:
            user_input: The user's input or action
            story_world: Current story world state
            
        Returns:
            Tuple of (narrative response, updated story world)
        """
        # Check for meta-commands
        if self._is_meta_command(user_input):
            return await self._handle_meta_command(user_input, story_world)

        # Create dependencies with current story world
        deps = StoryDeps(story_world=story_world, client=self.client)

        # Build context for the storytelling agent
        story_context = self._build_story_context(user_input, story_world)

        # Get narrative response from the agent
        result = await self.agent.run(story_context, deps=deps)

        # Update story history
        story_world.add_history_entry(f"User: {user_input}")
        story_world.add_history_entry(f"Narrator: {result.output}")

        return str(result.output), story_world

    async def refine_scenario(self, feedback: str, story_world: StoryWorld) -> StoryWorld:
        """
        Refine a scenario based on user feedback.
        
        Args:
            feedback: User feedback for improvements
            story_world: Current story world to refine
            
        Returns:
            Updated story world
        """
        deps = StoryDeps(story_world=story_world, client=self.client)

        refinement_prompt = f"""
Current scenario:
Premise: {story_world.premise}
Setting: {story_world.setting}
Characters: {list(story_world.characters.keys())}

User feedback: {feedback}

Please refine the scenario based on this feedback. Provide the updated elements.
"""

        result = await self.agent.run(refinement_prompt, deps=deps)

        # Parse and apply refinements
        refinement_data = self._parse_scenario_response(result.output)
        return self._update_story_world(story_world, refinement_data)

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
        # Remove asterisks
        meta_instruction = command.strip()[1:-1]

        deps = StoryDeps(story_world=story_world, client=self.client)

        # Create prompt for handling the meta-command
        meta_prompt = f"""
The following change needs to be incorporated naturally into the ongoing narrative: {meta_instruction}

Current scene: {story_world.current_scene.location}
Recent history: {'; '.join(story_world.history[-3:]) if story_world.history else 'None'}

Incorporate this change seamlessly without acknowledging it as a command. Just naturally weave it into the story.
"""

        result = await self.agent.run(meta_prompt, deps=deps)

        # Add to history as a natural story development
        story_world.add_history_entry(f"Story development: {result.output}")

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

    def _parse_scenario_response(self, response: str) -> Dict:
        """
        Parse the agent's scenario creation response.
        
        Args:
            response: The agent's response text
            
        Returns:
            Dictionary with parsed scenario elements
        """
        # This is a simplified parser - in a production system,
        # you might want more sophisticated parsing or structured output

        scenario_data = {
            "premise": "",
            "setting": "",
            "conflicts": [],
            "characters": [],
            "opening_scene": {}
        }

        # Extract premise
        premise_match = re.search(r"premise[:\s]*(.+?)(?=\n.*?setting|\n.*?conflict|\n.*?character|$)", response, re.IGNORECASE | re.DOTALL)
        if premise_match:
            scenario_data["premise"] = premise_match.group(1).strip()

        # Extract setting
        setting_match = re.search(r"setting[:\s]*(.+?)(?=\n.*?conflict|\n.*?character|\n.*?scene|$)", response, re.IGNORECASE | re.DOTALL)
        if setting_match:
            scenario_data["setting"] = setting_match.group(1).strip()

        return scenario_data

    def _build_story_world(self, scenario_data: Dict, initial_concept: str) -> StoryWorld:
        """
        Build a complete StoryWorld from parsed scenario data.
        
        Args:
            scenario_data: Parsed scenario elements
            initial_concept: Original concept for fallback
            
        Returns:
            Complete StoryWorld object
        """
        # Create basic story world with fallbacks
        premise = scenario_data.get("premise", initial_concept)
        setting = scenario_data.get("setting", "A mysterious location")

        # Create some default characters if none were parsed
        characters = {}
        if not scenario_data.get("characters"):
            # Create a simple default character
            default_character = Character(
                name="Guide",
                description="A mysterious figure who seems to know this place well",
                personality="Wise, helpful, but secretive about their past",
                speech_patterns="Speaks in measured tones with occasional cryptic hints"
            )
            characters["Guide"] = default_character

        # Create opening scene
        opening_scene = Scene(
            location="The Beginning",
            description="The story is about to unfold",
            atmosphere="Anticipation and mystery",
            active_characters=list(characters.keys())[:2],  # Limit to 2 active characters
            props=[]
        )

        return StoryWorld(
            premise=premise,
            setting=setting,
            conflicts=scenario_data.get("conflicts", ["An unknown challenge awaits"]),
            characters=characters,
            current_scene=opening_scene,
            history=[f"Story begins: {premise}"]
        )

    def _update_story_world(self, story_world: StoryWorld, refinement_data: Dict) -> StoryWorld:
        """
        Update story world with refinement data.
        
        Args:
            story_world: Current story world
            refinement_data: Parsed refinement elements
            
        Returns:
            Updated story world
        """
        # Update premise if provided
        if refinement_data.get("premise"):
            story_world.premise = refinement_data["premise"]

        # Update setting if provided
        if refinement_data.get("setting"):
            story_world.setting = refinement_data["setting"]

        # Add refinement to history
        story_world.add_history_entry("Scenario refined based on user feedback")

        return story_world
