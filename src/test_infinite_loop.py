#!/usr/bin/env python3
"""Test script to reproduce the infinite loop issue."""

import asyncio
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.main import main

async def test_infinite_loop():
    """Test function to trigger the infinite loop."""
    print("Testing infinite loop scenario...")
    
    # Run the main function but we'll interrupt it manually
    try:
        await main()
    except KeyboardInterrupt:
        print("Test interrupted by user")
    except Exception as e:
        print(f"Error during test: {e}")

if __name__ == "__main__":
    asyncio.run(test_infinite_loop())