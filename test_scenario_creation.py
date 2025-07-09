#!/usr/bin/env python3
"""Test script to directly test scenario creation with the new agent architecture."""

import asyncio
import httpx
import logfire
from dotenv import load_dotenv

from src.agents.storyteller import StorytellerAgent

load_dotenv()

async def test_scenario_creation():
    """Test the scenario creation functionality."""
    print("🎭 Testing Scenario Creation with New Agent Architecture")
    print("=" * 60)
    
    # Configure logfire for testing
    logfire.configure(send_to_logfire='if-token-present')
    
    async with httpx.AsyncClient() as client:
        storyteller = StorytellerAgent(client)
        
        # Test concept
        concept = "A space adventure where explorers discover an ancient alien civilization"
        
        print(f"📖 Creating scenario from concept: {concept}")
        print()
        
        try:
            story_world = await storyteller.create_scenario(concept)
            
            print("✅ Scenario Created Successfully!")
            print("=" * 40)
            print(f"📖 Premise: {story_world.premise}")
            print()
            print(f"🌍 Setting: {story_world.setting}")
            print()
            print(f"⚔️ Conflicts: {', '.join(story_world.conflicts)}")
            print()
            print(f"👥 Characters Created: {len(story_world.characters)}")
            for name, character in story_world.characters.items():
                print(f"   • {name}: {character.description[:80]}{'...' if len(character.description) > 80 else ''}")
            print()
            print(f"🎬 Opening Scene: {story_world.current_scene.location}")
            print(f"   {story_world.current_scene.description}")
            print(f"   Atmosphere: {story_world.current_scene.atmosphere}")
            print(f"   Active Characters: {', '.join(story_world.current_scene.active_characters)}")
            print()
            print(f"📜 History Entries: {len(story_world.history)}")
            for entry in story_world.history:
                print(f"   • {entry}")
            
            return True
        
        except Exception as e:
            print(f"❌ Error creating scenario: {e}")
            import traceback
            traceback.print_exc()
            return False

if __name__ == "__main__":
    success = asyncio.run(test_scenario_creation())
    if success:
        print("\n🎉 Scenario creation test completed successfully!")
    else:
        print("\n💥 Scenario creation test failed!")