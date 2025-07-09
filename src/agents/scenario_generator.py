"""Scenario generation agent that creates story scenarios and settings."""

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

from models.story import Scene, StoryWorld

load_dotenv()


class ScenarioGenerationRequest(BaseModel):
    """
    Request model for scenario generation.
    
    Attributes:
        premise: The core story premise
        setting: Detailed world setting description
        conflicts: List of main conflicts or plot threads
        opening_scene_location: Location of the opening scene
        opening_scene_description: Description of the opening scene
        opening_scene_atmosphere: Atmosphere/mood of the opening scene
        suggested_characters: List of suggested character concepts
    """
    premise: str = Field(description="The core story premise (2-3 sentences)")
    setting: str = Field(description="Detailed world setting description")
    conflicts: List[str] = Field(description="List of main conflicts or plot threads")
    opening_scene_location: str = Field(description="Location where the story begins")
    opening_scene_description: str = Field(description="Detailed description of the opening scene")
    opening_scene_atmosphere: str = Field(description="Atmosphere and mood of the opening scene")
    character_concepts: List[str] = Field(description="List of character concepts that should be created for this story")


@dataclass
class ScenarioGenerationDeps:
    """
    Dependencies for scenario generation agent.
    
    Attributes:
        client: HTTP client for external requests
    """
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


SCENARIO_GENERATION_PROMPT = """
You are an expert scenario generator for interactive storytelling. Your role is to create compelling, 
immersive story scenarios that provide rich environments for interactive storytelling experiences.

When creating scenarios, consider:
1. A clear, engaging premise that hooks players
2. Rich, detailed world-building that feels authentic
3. Multiple compelling conflicts that can drive the narrative
4. An opening scene that immediately draws players in
5. Suggested character concepts that would fit the world
6. Opportunities for player agency and meaningful choices

Your scenarios should provide structure while leaving room for emergent storytelling and player creativity.
Create scenarios that feel like they could support hours of engaging interactive narrative.
"""

# Create the scenario generation agent
scenario_generator_agent = Agent(
    get_model(),
    system_prompt=SCENARIO_GENERATION_PROMPT,
    deps_type=ScenarioGenerationDeps,
    output_type=ScenarioGenerationRequest,
    retries=2
)


async def generate_scenario(
    ctx: RunContext[ScenarioGenerationDeps],
    initial_concept: str,
    additional_requirements: str = ""
) -> ScenarioGenerationRequest:
    """
    Generate a complete scenario from an initial concept.
    
    Args:
        ctx: The runtime context containing dependencies
        initial_concept: The initial story concept from the user
        additional_requirements: Any additional requirements or constraints
    
    Returns:
        ScenarioGenerationRequest with all scenario details
    """
    with logfire.span(
        'Generating scenario from concept',
        initial_concept=initial_concept[:100] + '...' if len(initial_concept) > 100 else initial_concept,
        additional_requirements_length=len(additional_requirements)
    ) as span:
        
        # Build context for scenario generation
        context_info = f"""
Initial Concept: {initial_concept}

Additional Requirements: {additional_requirements}

Please create a complete scenario that includes:
1. A compelling premise that builds on the initial concept
2. Rich world-building and setting details
3. 2-3 main conflicts or plot threads that can drive the story
4. An engaging opening scene that immediately draws players in
5. 3-5 character concepts that should be created for this world

Make sure the scenario provides structure while leaving room for player creativity and emergent storytelling.
"""
        
        span.set_attribute('context_length', len(context_info))
        
        # Generate scenario using the agent
        with logfire.span('Running scenario generation LLM') as llm_span:
            result = await scenario_generator_agent.run(
                context_info,
                deps=ctx.deps
            )
            
            llm_span.set_attribute('scenario_generated', True)
            llm_span.set_attribute('premise_length', len(result.data.premise))
            llm_span.set_attribute('setting_length', len(result.data.setting))
            llm_span.set_attribute('conflicts_count', len(result.data.conflicts))
            llm_span.set_attribute('character_concepts_count', len(result.data.character_concepts))
            
            logfire.info(
                'Scenario generated successfully',
                premise_preview=result.data.premise[:100] + '...' if len(result.data.premise) > 100 else result.data.premise,
                setting_preview=result.data.setting[:100] + '...' if len(result.data.setting) > 100 else result.data.setting,
                conflicts_count=len(result.data.conflicts),
                character_concepts_count=len(result.data.character_concepts)
            )
            
            span.set_attribute('scenario_generation_successful', True)
            span.set_attribute('final_premise_length', len(result.data.premise))
            
            return result.data


async def refine_scenario(
    ctx: RunContext[ScenarioGenerationDeps],
    current_scenario: Dict,
    refinement_feedback: str
) -> ScenarioGenerationRequest:
    """
    Refine an existing scenario based on feedback.
    
    Args:
        ctx: The runtime context containing dependencies
        current_scenario: The current scenario data
        refinement_feedback: User feedback for refinement
    
    Returns:
        ScenarioGenerationRequest with refined scenario details
    """
    with logfire.span(
        'Refining scenario based on feedback',
        refinement_feedback=refinement_feedback[:100] + '...' if len(refinement_feedback) > 100 else refinement_feedback,
        current_premise_length=len(current_scenario.get('premise', ''))
    ) as span:
        
        # Build context for scenario refinement
        context_info = f"""
Current Scenario:
Premise: {current_scenario.get('premise', '')}
Setting: {current_scenario.get('setting', '')}
Conflicts: {current_scenario.get('conflicts', [])}
Opening Scene: {current_scenario.get('opening_scene_location', '')} - {current_scenario.get('opening_scene_description', '')}

User Feedback: {refinement_feedback}

Please refine the scenario based on this feedback while maintaining the core elements that work well.
Keep the improvements focused and coherent with the existing narrative structure.
"""
        
        span.set_attribute('context_length', len(context_info))
        span.set_attribute('current_conflicts_count', len(current_scenario.get('conflicts', [])))
        
        # Generate refined scenario using the agent
        with logfire.span('Running scenario refinement LLM') as llm_span:
            result = await scenario_generator_agent.run(
                context_info,
                deps=ctx.deps
            )
            
            llm_span.set_attribute('scenario_refined', True)
            llm_span.set_attribute('new_premise_length', len(result.data.premise))
            llm_span.set_attribute('new_setting_length', len(result.data.setting))
            llm_span.set_attribute('new_conflicts_count', len(result.data.conflicts))
            
            logfire.info(
                'Scenario refined successfully',
                refinement_feedback=refinement_feedback[:50] + '...' if len(refinement_feedback) > 50 else refinement_feedback,
                new_premise_preview=result.data.premise[:100] + '...' if len(result.data.premise) > 100 else result.data.premise
            )
            
            span.set_attribute('scenario_refinement_successful', True)
            span.set_attribute('final_refined_premise_length', len(result.data.premise))
            
            return result.data


class ScenarioGenerationManager:
    """
    Manager class for scenario generation operations.
    
    Provides utilities for creating and refining scenarios using the scenario generation agent.
    """

    def __init__(self, client: httpx.AsyncClient):
        """
        Initialize scenario generation manager.
        
        Args:
            client: HTTP client for external requests
        """
        self.client = client
        self.deps = ScenarioGenerationDeps(client=client)

    async def create_scenario_from_concept(self, initial_concept: str, additional_requirements: str = "") -> StoryWorld:
        """
        Create a complete story scenario from an initial concept.
        
        Args:
            initial_concept: The initial story concept from the user
            additional_requirements: Any additional requirements or constraints
            
        Returns:
            StoryWorld object with the generated scenario
        """
        with logfire.span(
            'Scenario generation manager: create scenario',
            initial_concept=initial_concept[:50] + '...' if len(initial_concept) > 50 else initial_concept,
            additional_requirements_length=len(additional_requirements)
        ) as span:
            
            # Use the scenario generation agent
            result = await scenario_generator_agent.run(
                f"Generate scenario: {initial_concept}\nAdditional requirements: {additional_requirements}",
                deps=self.deps
            )
            scenario_request = result.data
            
            # Create opening scene
            opening_scene = Scene(
                location=scenario_request.opening_scene_location,
                description=scenario_request.opening_scene_description,
                atmosphere=scenario_request.opening_scene_atmosphere,
                active_characters=[],  # Will be populated when characters are created
                props=[]
            )
            
            # Create StoryWorld object
            story_world = StoryWorld(
                premise=scenario_request.premise,
                setting=scenario_request.setting,
                conflicts=scenario_request.conflicts,
                characters={},  # Will be populated by character creation
                current_scene=opening_scene,
                history=[f"Story begins: {scenario_request.premise}"]
            )
            
            span.set_attribute('story_world_created', True)
            span.set_attribute('premise_length', len(story_world.premise))
            span.set_attribute('setting_length', len(story_world.setting))
            span.set_attribute('conflicts_count', len(story_world.conflicts))
            span.set_attribute('character_concepts_count', len(scenario_request.character_concepts))
            
            logfire.info(
                'Story world created from scenario',
                premise_preview=story_world.premise[:100] + '...' if len(story_world.premise) > 100 else story_world.premise,
                conflicts_count=len(story_world.conflicts),
                character_concepts_count=len(scenario_request.character_concepts)
            )
            
            return story_world, scenario_request.character_concepts

    async def refine_scenario_from_feedback(self, story_world: StoryWorld, refinement_feedback: str) -> StoryWorld:
        """
        Refine an existing scenario based on user feedback.
        
        Args:
            story_world: The current story world to refine
            refinement_feedback: User feedback for refinement
            
        Returns:
            Updated StoryWorld object with refined scenario
        """
        with logfire.span(
            'Scenario generation manager: refine scenario',
            refinement_feedback=refinement_feedback[:50] + '...' if len(refinement_feedback) > 50 else refinement_feedback,
            current_premise_length=len(story_world.premise)
        ) as span:
            
            # Prepare current scenario data
            current_scenario = {
                'premise': story_world.premise,
                'setting': story_world.setting,
                'conflicts': story_world.conflicts,
                'opening_scene_location': story_world.current_scene.location,
                'opening_scene_description': story_world.current_scene.description,
                'opening_scene_atmosphere': story_world.current_scene.atmosphere
            }
            
            # Use the scenario generation agent for refinement
            refinement_prompt = f"""
Current scenario: {current_scenario}
User feedback: {refinement_feedback}
Please refine the scenario based on this feedback.
"""
            result = await scenario_generator_agent.run(
                refinement_prompt,
                deps=self.deps
            )
            refined_scenario = result.data
            
            # Update the story world with refined data
            story_world.premise = refined_scenario.premise
            story_world.setting = refined_scenario.setting
            story_world.conflicts = refined_scenario.conflicts
            
            # Update opening scene
            story_world.current_scene.location = refined_scenario.opening_scene_location
            story_world.current_scene.description = refined_scenario.opening_scene_description
            story_world.current_scene.atmosphere = refined_scenario.opening_scene_atmosphere
            
            # Note: Character concepts from refinement will be used to create actual characters via character_creator
            
            # Add to history
            story_world.add_history_entry("Scenario refined based on user feedback")
            
            span.set_attribute('scenario_refined', True)
            span.set_attribute('new_premise_length', len(story_world.premise))
            span.set_attribute('new_setting_length', len(story_world.setting))
            span.set_attribute('new_conflicts_count', len(story_world.conflicts))
            
            logfire.info(
                'Scenario refined successfully',
                new_premise_preview=story_world.premise[:100] + '...' if len(story_world.premise) > 100 else story_world.premise,
                new_conflicts_count=len(story_world.conflicts)
            )
            
            return story_world

    def get_scenario_summary(self, story_world: StoryWorld) -> Dict:
        """
        Get a summary of the current scenario.
        
        Args:
            story_world: The story world to summarize
            
        Returns:
            Dictionary with scenario summary
        """
        return {
            'premise': story_world.premise,
            'setting': story_world.setting[:200] + '...' if len(story_world.setting) > 200 else story_world.setting,
            'conflicts_count': len(story_world.conflicts),
            'current_scene': story_world.current_scene.location,
            'characters_count': len(story_world.characters),
            'history_length': len(story_world.history)
        }