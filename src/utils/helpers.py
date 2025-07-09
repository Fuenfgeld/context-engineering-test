"""Helper functions for the storytelling application."""

from __future__ import annotations

import os
import re
from datetime import datetime
from typing import Optional, Any

from colorama import init, Fore, Back, Style

# Initialize colorama for cross-platform colored output
init(autoreset=True)


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


def format_character_speech(character_name: str, speech: str) -> str:
    """
    Format character speech with distinctive coloring.
    
    Args:
        character_name: Name of the character speaking
        speech: The character's speech/dialogue
        
    Returns:
        Formatted string with character name in color and speech styled
    """
    # Use different colors for different characters
    character_colors = {
        'Gandalf': Fore.BLUE,
        'Frodo': Fore.GREEN,
        'Aragorn': Fore.CYAN,
        'Legolas': Fore.YELLOW,
        'Gimli': Fore.RED,
        'Boromir': Fore.MAGENTA,
        'Elysia': Fore.LIGHTBLUE_EX,
        'Max': Fore.LIGHTGREEN_EX,
        'Gamal': Fore.LIGHTCYAN_EX,
        'Kael': Fore.LIGHTYELLOW_EX,
        'Agatha': Fore.LIGHTMAGENTA_EX,
        'Guide': Fore.LIGHTWHITE_EX,
    }
    
    # Default color for unknown characters
    character_color = character_colors.get(character_name, Fore.LIGHTBLUE_EX)
    
    # Format the character name with color and bold
    formatted_name = f"{character_color}{Style.BRIGHT}{character_name}{Style.RESET_ALL}"
    
    # Format the speech with slight styling
    formatted_speech = f"{character_color}{speech}{Style.RESET_ALL}"
    
    return f"{formatted_name}: {formatted_speech}"


def format_narrator_text(text: str) -> str:
    """
    Format narrator text with distinctive styling.
    
    Args:
        text: The narrator's text
        
    Returns:
        Formatted narrator text
    """
    return f"{Fore.WHITE}{text}{Style.RESET_ALL}"


def format_system_message(message: str) -> str:
    """
    Format system messages with distinctive styling.
    
    Args:
        message: The system message
        
    Returns:
        Formatted system message
    """
    return f"{Fore.CYAN}{Style.BRIGHT}📖 {message}{Style.RESET_ALL}"


def format_error_message(message: str) -> str:
    """
    Format error messages with distinctive styling.
    
    Args:
        message: The error message
        
    Returns:
        Formatted error message
    """
    return f"{Fore.RED}{Style.BRIGHT}❌ {message}{Style.RESET_ALL}"


def format_success_message(message: str) -> str:
    """
    Format success messages with distinctive styling.
    
    Args:
        message: The success message
        
    Returns:
        Formatted success message
    """
    return f"{Fore.GREEN}{Style.BRIGHT}✅ {message}{Style.RESET_ALL}"


def parse_character_speech(text: str) -> list[tuple[str, str]]:
    """
    Parse text to extract all character speech patterns.
    
    Args:
        text: The text to parse
        
    Returns:
        List of tuples (character_name, speech) for all found dialogue
    """
    # Look for patterns with both regular and smart quotes
    patterns = [
        # "Speech," Character said/exclaimed/etc.
        r'["""]([^"""]+)["""],?\s*([A-Z][a-zA-Z]+)\s+(?:said|says|replied|responds?|exclaimed|whispered|shouted|declared|asked|continued)',
        # Character said/exclaimed: "Speech"
        r'([A-Z][a-zA-Z]+)\s+(?:said|says|replied|responds?|exclaimed|whispered|shouted|declared|asked|continued)[^"""]*["""]([^"""]+)["""]',
        # Character: "Speech" (direct format)
        r'([A-Z][a-zA-Z]+):\s*["""]([^"""]+)["""]',
        # More complex patterns for embedded speech
        r'([A-Z][a-zA-Z]+)[^"""]*["""]([^"""]+)["""]',
    ]
    
    speeches = []
    used_positions = set()  # Track used text positions to avoid overlaps
    
    for pattern in patterns:
        matches = re.finditer(pattern, text, re.DOTALL)
        for match in matches:
            # Skip if this match overlaps with already used text
            if any(pos in used_positions for pos in range(match.start(), match.end())):
                continue
                
            groups = match.groups()
            if len(groups) == 2:
                # Check if pattern is speech-first or character-first
                if pattern.startswith('["""'):
                    # Speech comes first in pattern
                    speech, character_name = groups
                else:
                    # Character comes first in pattern
                    character_name, speech = groups
                
                # Clean up the speech text
                speech = speech.strip()
                character_name = character_name.strip()
                
                # Validate character name (avoid false positives)
                if (len(character_name) > 20 or 
                    character_name.lower() in ['the', 'a', 'an', 'and', 'or', 'but', 'so', 'yet', 'for', 'nor'] or
                    not character_name.isalpha()):
                    continue
                
                # Avoid duplicates
                if (character_name, speech) not in speeches:
                    speeches.append((character_name, speech))
                    # Mark this text position as used
                    for pos in range(match.start(), match.end()):
                        used_positions.add(pos)
    
    return speeches


def format_story_with_colored_dialogue(text: str) -> str:
    """
    Format story text with colored character dialogue.
    
    Args:
        text: The story text containing narrative and dialogue
        
    Returns:
        Formatted text with colored character speech
    """
    # Find all character speeches
    speeches = parse_character_speech(text)
    
    if not speeches:
        # No character speech found, format as narrator text
        return format_narrator_text(text)
    
    # Replace character speech with colored versions
    formatted_text = text
    for character_name, speech in speeches:
        # Create colored speech
        colored_speech = f"{format_character_speech(character_name, speech)}"
        
        # Replace the original speech with colored version
        # Handle both regular and smart quotes
        for quote_char in ['"', '"', '"']:
            original_pattern = f'{quote_char}{re.escape(speech)}{quote_char}'
            if re.search(original_pattern, formatted_text):
                formatted_text = re.sub(original_pattern, colored_speech, formatted_text, count=1)
                break
    
    return format_narrator_text(formatted_text)


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
