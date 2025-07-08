"""Main entry point for the interactive storytelling application."""

from __future__ import annotations

import asyncio
import os
import sys
from pathlib import Path

import logfire
from dotenv import load_dotenv

from .cli.interface import StorytellingCLI
from .utils.helpers import validate_environment


def setup_environment() -> bool:
    """
    Set up the environment and validate configuration.
    
    Returns:
        True if setup successful, False otherwise
    """
    # Load environment variables
    load_dotenv()

    # Configure logfire
    logfire.configure(send_to_logfire='if-token-present')

    # Validate environment
    validation = validate_environment()

    # Check critical requirements
    if not validation.get('api_key_present', False):
        print("❌ Missing API key configuration!")
        print("Please set either OPENAI_API_KEY or OPEN_ROUTER_API_KEY in your environment.")
        print("You can copy .env.example to .env and add your API keys.")
        return False

    # Create stories directory if it doesn't exist
    stories_dir = Path("stories")
    stories_dir.mkdir(exist_ok=True)

    return True


def display_startup_info() -> None:
    """Display startup information and configuration status."""
    print("🎭 Interactive Storytelling Application")
    print("=" * 50)
    print("🤖 Powered by PydanticAI multi-agent architecture")

    # Show configuration
    model = os.getenv('LLM_MODEL', 'gpt-4o-mini')
    print(f"🧠 Using model: {model}")

    if os.getenv('OPEN_ROUTER_API_KEY'):
        print("🔑 API: OpenRouter")
    elif os.getenv('OPENAI_API_KEY'):
        print("🔑 API: OpenAI")

    print()


async def main() -> None:
    """
    Main application function.
    
    Sets up the environment, validates configuration, and starts the CLI.
    """
    try:
        # Setup and validate environment
        if not setup_environment():
            sys.exit(1)

        # Display startup information
        display_startup_info()

        # Create and start the CLI
        cli = StorytellingCLI()
        await cli.start()

    except KeyboardInterrupt:
        print("\n\n👋 Goodbye! Thanks for using the storytelling app!")
    except Exception as e:
        print(f"\n❌ Fatal error: {e}")
        print("If this problem persists, please check your configuration and try again.")
        sys.exit(1)


def cli_main() -> None:
    """
    CLI entry point for running the application.
    
    This function is called when the module is run as a script
    or when using the 'storytelling' command from setup.py.
    """
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n\n👋 Goodbye!")
    except Exception as e:
        print(f"❌ Error starting application: {e}")
        sys.exit(1)


if __name__ == "__main__":
    cli_main()
