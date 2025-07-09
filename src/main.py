"""Main entry point for the interactive storytelling application."""

from __future__ import annotations

import asyncio
import os
import sys
from pathlib import Path

import logfire
from dotenv import load_dotenv

from cli.interface import StorytellingCLI
from utils.helpers import validate_environment


def setup_environment() -> bool:
    """
    Set up the environment and validate configuration.
    
    Returns:
        True if setup successful, False otherwise
    """
    with logfire.span('Setting up application environment') as span:
        # Load environment variables
        with logfire.span('Loading environment variables') as env_span:
            load_dotenv()
            env_span.set_attribute('dotenv_loaded', True)

        # Configure logfire
        with logfire.span('Configuring logfire') as logfire_span:
            logfire_token = os.getenv('LOGFIRE_TOKEN')
            if logfire_token:
                logfire.configure(token=logfire_token, inspect_arguments=False)
                logfire_span.set_attribute('logfire_token_present', True)
            else:
                logfire.configure(send_to_logfire='if-token-present', inspect_arguments=False)
                logfire_span.set_attribute('logfire_token_present', False)
            
            # Enable instrumentation if available
            instrumentation_count = 0
            for instrument_name, instrument_func in [
                ('pydantic_ai', logfire.instrument_pydantic_ai),
                ('openai', logfire.instrument_openai),
                ('httpx', logfire.instrument_httpx)
            ]:
                try:
                    instrument_func()
                    instrumentation_count += 1
                    logfire_span.set_attribute(f'{instrument_name}_instrumented', True)
                except Exception:
                    logfire_span.set_attribute(f'{instrument_name}_instrumented', False)
            
            logfire_span.set_attribute('logfire_configured', True)
            logfire_span.set_attribute('instrumentations_enabled', instrumentation_count)
            logfire.info('Logfire configured for interactive storytelling application', 
                        token_configured=bool(logfire_token),
                        instrumentations_enabled=instrumentation_count)

        # Validate environment
        with logfire.span('Validating environment configuration') as validate_span:
            validation = validate_environment()
            validate_span.set_attribute('validation_result', validation)
            validate_span.set_attribute('api_key_present', validation.get('api_key_present', False))

        # Check critical requirements
        if not validation.get('api_key_present', False):
            print("❌ Missing API key configuration!")
            print("Please set either OPENAI_API_KEY or OPEN_ROUTER_API_KEY in your environment.")
            print("You can copy .env.example to .env and add your API keys.")
            span.set_attribute('setup_successful', False)
            span.set_attribute('failure_reason', 'missing_api_key')
            logfire.error('Application setup failed: missing API key configuration')
            return False

        # Create stories directory if it doesn't exist
        with logfire.span('Creating stories directory') as dir_span:
            stories_dir = Path("stories")
            stories_dir.mkdir(exist_ok=True)
            dir_span.set_attribute('stories_directory', str(stories_dir.absolute()))
            dir_span.set_attribute('directory_created', True)

        span.set_attribute('setup_successful', True)
        span.set_attribute('model_configured', os.getenv('LLM_MODEL', 'gpt-4o-mini'))
        span.set_attribute('api_provider', 'openrouter' if os.getenv('OPEN_ROUTER_API_KEY') else 'openai')
        
        logfire.info(
            'Application environment setup completed successfully',
            model=os.getenv('LLM_MODEL', 'gpt-4o-mini'),
            api_provider='openrouter' if os.getenv('OPEN_ROUTER_API_KEY') else 'openai'
        )
        
        return True


def display_startup_info() -> None:
    """Display startup information and configuration status."""
    with logfire.span('Displaying startup information') as span:
        print("🎭 Interactive Storytelling Application")
        print("=" * 50)
        print("🤖 Powered by PydanticAI multi-agent architecture")

        # Show configuration
        model = os.getenv('LLM_MODEL', 'gpt-4o-mini')
        print(f"🧠 Using model: {model}")
        span.set_attribute('model_displayed', model)

        api_provider = None
        if os.getenv('OPEN_ROUTER_API_KEY'):
            print("🔑 API: OpenRouter")
            api_provider = 'openrouter'
        elif os.getenv('OPENAI_API_KEY'):
            print("🔑 API: OpenAI")
            api_provider = 'openai'
            
        span.set_attribute('api_provider_displayed', api_provider)
        span.set_attribute('startup_info_displayed', True)

        print()
        
        logfire.info(
            'Startup information displayed to user',
            model=model,
            api_provider=api_provider
        )


async def main() -> None:
    """
    Main application function.
    
    Sets up the environment, validates configuration, and starts the CLI.
    """
    with logfire.span('Interactive storytelling application main execution') as span:
        try:
            # Setup and validate environment
            with logfire.span('Application setup phase') as setup_span:
                if not setup_environment():
                    setup_span.set_attribute('setup_failed', True)
                    logfire.error('Application setup failed, exiting')
                    sys.exit(1)
                setup_span.set_attribute('setup_successful', True)

            # Display startup information
            display_startup_info()

            # Create and start the CLI
            with logfire.span('Creating and starting CLI interface') as cli_span:
                cli = StorytellingCLI()
                cli_span.set_attribute('cli_created', True)
                
                logfire.info('Starting interactive storytelling CLI')
                await cli.start()
                cli_span.set_attribute('cli_completed', True)

            span.set_attribute('application_completed_normally', True)
            logfire.info('Interactive storytelling application completed normally')

        except KeyboardInterrupt:
            print("\n\n👋 Goodbye! Thanks for using the storytelling app!")
            span.set_attribute('exit_type', 'keyboard_interrupt')
            logfire.info('Application exited via keyboard interrupt')
        except Exception as e:
            print(f"\n❌ Fatal error: {e}")
            print("If this problem persists, please check your configuration and try again.")
            span.set_attribute('exit_type', 'fatal_error')
            span.set_attribute('error_message', str(e))
            logfire.error(
                'Fatal error in main application',
                error=str(e),
                error_type=type(e).__name__
            )
            sys.exit(1)


def cli_main() -> None:
    """
    CLI entry point for running the application.
    
    This function is called when the module is run as a script
    or when using the 'storytelling' command from setup.py.
    """
    with logfire.span('CLI entry point execution') as span:
        try:
            span.set_attribute('entry_point', 'cli_main')
            logfire.info('Starting interactive storytelling application from CLI entry point')
            
            with logfire.span('Running asyncio main loop') as async_span:
                asyncio.run(main())
                async_span.set_attribute('asyncio_completed', True)
                
            span.set_attribute('cli_main_successful', True)
            
        except KeyboardInterrupt:
            print("\n\n👋 Goodbye!")
            span.set_attribute('exit_type', 'keyboard_interrupt')
            logfire.info('CLI exited via keyboard interrupt')
        except Exception as e:
            print(f"❌ Error starting application: {e}")
            span.set_attribute('exit_type', 'startup_error')
            span.set_attribute('error_message', str(e))
            logfire.error(
                'Error starting application from CLI entry point',
                error=str(e),
                error_type=type(e).__name__
            )
            sys.exit(1)


if __name__ == "__main__":
    cli_main()
