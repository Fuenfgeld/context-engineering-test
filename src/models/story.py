"""Data models for story components."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List


@dataclass
class Character:
    """
    Represents a character in the story.
    
    Attributes:
        name: The character's name
        description: Physical and background description
        personality: Personality traits and characteristics
        speech_patterns: How the character speaks
        memories: List of significant memories/experiences
        relationships: Dict mapping character names to relationship descriptions
    """
    name: str
    description: str
    personality: str
    speech_patterns: str
    memories: List[str] = field(default_factory=list)
    relationships: Dict[str, str] = field(default_factory=dict)

    def to_dict(self) -> Dict:
        """Convert character to dictionary for JSON serialization."""
        return {
            "name": self.name,
            "description": self.description,
            "personality": self.personality,
            "speech_patterns": self.speech_patterns,
            "memories": self.memories,
            "relationships": self.relationships
        }

    @classmethod
    def from_dict(cls, data: Dict) -> Character:
        """Create character from dictionary."""
        return cls(
            name=data["name"],
            description=data["description"],
            personality=data["personality"],
            speech_patterns=data["speech_patterns"],
            memories=data.get("memories", []),
            relationships=data.get("relationships", {})
        )


@dataclass
class Scene:
    """
    Represents a scene in the story.
    
    Attributes:
        location: Where the scene takes place
        description: Detailed description of the scene
        atmosphere: Mood and feeling of the scene
        active_characters: List of character names present
        props: List of important objects in the scene
    """
    location: str
    description: str
    atmosphere: str
    active_characters: List[str] = field(default_factory=list)
    props: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict:
        """Convert scene to dictionary for JSON serialization."""
        return {
            "location": self.location,
            "description": self.description,
            "atmosphere": self.atmosphere,
            "active_characters": self.active_characters,
            "props": self.props
        }

    @classmethod
    def from_dict(cls, data: Dict) -> Scene:
        """Create scene from dictionary."""
        return cls(
            location=data["location"],
            description=data["description"],
            atmosphere=data["atmosphere"],
            active_characters=data.get("active_characters", []),
            props=data.get("props", [])
        )


@dataclass
class StoryWorld:
    """
    Represents the complete story world state.
    
    Attributes:
        premise: The core story premise
        setting: The world setting description
        conflicts: List of ongoing conflicts
        characters: Dict mapping character names to Character objects
        current_scene: The current scene
        history: List of story events and actions
    """
    premise: str
    setting: str
    conflicts: List[str] = field(default_factory=list)
    characters: Dict[str, Character] = field(default_factory=dict)
    current_scene: Scene = field(default_factory=lambda: Scene("", "", ""))
    history: List[str] = field(default_factory=list)

    def add_character(self, character: Character) -> None:
        """Add a character to the story world."""
        self.characters[character.name] = character

    def get_character(self, name: str) -> Character | None:
        """Get a character by name."""
        return self.characters.get(name)

    def add_history_entry(self, entry: str) -> None:
        """Add an entry to the story history."""
        self.history.append(entry)

    def to_dict(self) -> Dict:
        """Convert story world to dictionary for JSON serialization."""
        return {
            "premise": self.premise,
            "setting": self.setting,
            "conflicts": self.conflicts,
            "characters": {name: char.to_dict() for name, char in self.characters.items()},
            "current_scene": self.current_scene.to_dict(),
            "history": self.history
        }

    @classmethod
    def from_dict(cls, data: Dict) -> StoryWorld:
        """Create story world from dictionary."""
        characters = {
            name: Character.from_dict(char_data)
            for name, char_data in data.get("characters", {}).items()
        }

        current_scene = Scene.from_dict(data.get("current_scene", {
            "location": "",
            "description": "",
            "atmosphere": "",
            "active_characters": [],
            "props": []
        }))

        return cls(
            premise=data["premise"],
            setting=data["setting"],
            conflicts=data.get("conflicts", []),
            characters=characters,
            current_scene=current_scene,
            history=data.get("history", [])
        )
