"""Helper functions for the storytelling application."""

from __future__ import annotations

import os
import re
from datetime import datetime
from typing import Optional, Any


def get_display_timestamp(dt: datetime) -> str:
    """
    Get a human-readable timestamp for display.
    
    Args:
        dt: Datetime object
        
    Returns:
        Formatted timestamp string
    """
    now = datetime.now()
    diff = now - dt

    if diff.days > 0:
        return f"{diff.days} day{'s' if diff.days != 1 else ''} ago"
    elif diff.seconds > 3600:
        hours = diff.seconds // 3600
        return f"{hours} hour{'s' if hours != 1 else ''} ago"
    elif diff.seconds > 60:
        minutes = diff.seconds // 60
        return f"{minutes} minute{'s' if minutes != 1 else ''} ago"
    else:
        return "Just now"


def sanitize_filename(filename: str) -> str:
    """
    Sanitize a filename for safe filesystem usage.
    
    Args:
        filename: Raw filename
        
    Returns:
        Sanitized filename
    """
    # Remove or replace unsafe characters
    sanitized = re.sub(r'[<>:"/\\|?*]', '_', filename)

    # Remove leading/trailing spaces and dots
    sanitized = sanitized.strip('. ')

    # Ensure it's not empty
    if not sanitized:
        sanitized = "untitled"

    # Limit length
    if len(sanitized) > 100:
        sanitized = sanitized[:100]

    return sanitized


def truncate_text(text: str, max_length: int, suffix: str = "...") -> str:
    """
    Truncate text to a maximum length with optional suffix.
    
    Args:
        text: Text to truncate
        max_length: Maximum length
        suffix: Suffix to add if truncated
        
    Returns:
        Truncated text
    """
    if len(text) <= max_length:
        return text

    return text[:max_length - len(suffix)] + suffix


def format_character_list(characters: dict[str, Any]) -> str:
    """
    Format a list of characters for display.
    
    Args:
        characters: Dictionary of character name to character object
        
    Returns:
        Formatted character list
    """
    if not characters:
        return "No characters"

    character_lines = []
    for i, (name, character) in enumerate(characters.items(), 1):
        description = truncate_text(character.description, 60)
        character_lines.append(f"{i}. {name} - {description}")

    return "\n".join(character_lines)


def validate_environment() -> dict[str, bool]:
    """
    Validate that required environment variables are set.
    
    Returns:
        Dictionary of validation results
    """
    required_vars = ['LLM_MODEL']
    optional_vars = ['OPENAI_API_KEY', 'OPEN_ROUTER_API_KEY', 'LOGFIRE_TOKEN']

    validation = {}

    # Check required variables
    for var in required_vars:
        validation[var] = os.getenv(var) is not None

    # Check that at least one API key is present
    has_api_key = any(os.getenv(var) for var in ['OPENAI_API_KEY', 'OPEN_ROUTER_API_KEY'])
    validation['api_key_present'] = has_api_key

    # Check optional variables
    for var in optional_vars:
        validation[f'{var}_optional'] = os.getenv(var) is not None

    return validation


def extract_meta_command(text: str) -> Optional[str]:
    """
    Extract meta-command from text if present.
    
    Args:
        text: Input text that might contain a meta-command
        
    Returns:
        Meta-command without asterisks, or None if not found
    """
    text = text.strip()
    if text.startswith('*') and text.endswith('*') and len(text) > 2:
        return text[1:-1].strip()
    return None


def is_valid_session_id(session_id: str) -> bool:
    """
    Check if a session ID is valid format.
    
    Args:
        session_id: Session ID to validate
        
    Returns:
        True if valid format, False otherwise
    """
    # Basic validation - UUID-like format or reasonable string
    if not session_id or len(session_id) < 3:
        return False

    # Allow alphanumeric, hyphens, and underscores
    return re.match(r'^[a-zA-Z0-9_-]+$', session_id) is not None


def format_story_history(history: list[str], max_entries: int = 5) -> str:
    """
    Format story history for display.
    
    Args:
        history: List of history entries
        max_entries: Maximum number of entries to display
        
    Returns:
        Formatted history string
    """
    if not history:
        return "No story history yet."

    # Get the most recent entries
    recent_history = history[-max_entries:] if len(history) > max_entries else history

    formatted_entries = []
    for i, entry in enumerate(recent_history, 1):
        # Truncate long entries
        truncated_entry = truncate_text(entry, 100)
        formatted_entries.append(f"{i}. {truncated_entry}")

    if len(history) > max_entries:
        formatted_entries.insert(0, f"... ({len(history) - max_entries} earlier entries)")

    return "\n".join(formatted_entries)
