#!/usr/bin/env python3
"""Test script to verify the infinite loop fixes work."""

import asyncio
import signal
import sys
import os
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.cli.interface import StorytellingCLI
import httpx

async def test_fixed_app():
    """Test that the application can be properly interrupted."""
    print("🧪 Testing fixed storytelling application...")
    print("📋 This test will run the app and you can verify:")
    print("   1. Ctrl+C can interrupt at any input prompt")
    print("   2. Error handling gives user options to exit")
    print("   3. All while loops can be properly terminated")
    print("=" * 50)
    
    # Create CLI instance
    cli = StorytellingCLI()
    
    try:
        # Start the CLI
        await cli.start()
        print("✅ Application exited normally")
    except KeyboardInterrupt:
        print("\n✅ Application properly handled KeyboardInterrupt")
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
    finally:
        # Ensure cleanup
        await cli.client.aclose()
        print("🧹 Cleanup completed")

def signal_handler(signum, frame):
    """Handle SIGINT gracefully."""
    print(f"\n🛑 Received signal {signum}. Exiting...")
    sys.exit(0)

if __name__ == "__main__":
    # Set up signal handler
    signal.signal(signal.SIGINT, signal_handler)
    
    print("🚀 Starting test...")
    print("💡 You can press Ctrl+C at any time to test interrupt handling")
    print("=" * 50)
    
    # Set up minimal environment for testing
    os.environ.setdefault('OPENAI_API_KEY', 'test-key')
    os.environ.setdefault('LLM_MODEL', 'gpt-4o-mini')
    
    try:
        asyncio.run(test_fixed_app())
    except KeyboardInterrupt:
        print("\n✅ Test completed - KeyboardInterrupt handled properly")
    except Exception as e:
        print(f"❌ Test failed with error: {e}")