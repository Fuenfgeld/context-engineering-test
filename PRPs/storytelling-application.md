# Storytelling Application PRP

## Goal
Build a command-line application for collaborative AI-driven storytelling that creates novel-like narratives through natural conversation. The application features a multi-agent architecture with one PydanticAI agent serving as the main storyteller and another PydanticAI agent functioning as a specialized tool for character embodiment and narrative control.

## Why
- **Enhanced Storytelling Experience**: Provides users with an immersive, collaborative storytelling environment where AI assists in creating rich narratives
- **Multi-Agent Architecture**: Demonstrates advanced PydanticAI capabilities with agent-as-tool pattern for specialized character handling
- **Persistent Narrative State**: Maintains story continuity across sessions with complete world state preservation
- **Natural Language Interface**: Allows users to interact with stories through conversational commands and meta-commands

## What
A CLI application that enables users to create, develop, and engage in interactive storytelling sessions with AI-powered narrative generation and character embodiment.

### Success Criteria
- [ ] CLI application starts and provides main menu for scenario creation or loading
- [ ] Scenario creation mode successfully generates complete story worlds through conversational dialogue
- [ ] Storytelling mode provides continuous narrative flow with natural prose
- [ ] Character agent successfully embodies NPCs with distinct personalities and speech patterns
- [ ] Meta-commands using `*asterisks*` notation seamlessly alter story direction
- [ ] Sessions persist to disk and can be resumed with complete state restoration
- [ ] All tests pass: `uv run pytest tests/ -v`
- [ ] No linting errors: `uv run ruff check --fix .`
- [ ] No type errors: `uv run mypy .`

## All Needed Context

### Documentation & References
```yaml
# MUST READ - Include these in your context window
- url: https://ai.pydantic.dev/
  why: Core PydanticAI framework documentation and patterns
  
- url: https://ai.pydantic.dev/agents/
  why: Agent creation, configuration, and system prompt patterns
  
- url: https://ai.pydantic.dev/tools/
  why: Tool creation patterns for agent-as-tool implementation
  
- url: https://ai.pydantic.dev/multi-agent-applications/
  why: Multi-agent patterns and agent delegation strategies
  
- file: examples/cli.py
  why: CLI structure, message handling, and async patterns to follow
  
- file: examples/agent/exampleAgent.py
  why: Agent creation patterns, tool decoration, and dependency injection
  
- file: PRPs/templates/prp_base.md
  why: Implementation structure and validation patterns
  
- file: CLAUDE.md
  why: Project rules, code structure, testing requirements, and style conventions
```

### Current Codebase Tree
```bash
context-engineering-test/
├── CLAUDE.md                 # Project rules and conventions
├── examples/
│   ├── agent/
│   │   └── exampleAgent.py   # Agent patterns to follow
│   └── cli.py                # CLI patterns to follow
├── INITIAL.md               # Feature requirements
├── PRPs/
│   ├── templates/
│   │   └── prp_base.md      # PRP template
│   └── EXAMPLE_multi_agent_prp.md
├── README.md                # Project documentation
└── venv/                    # Virtual environment (minimal dependencies)
```

### Desired Codebase Tree with Files to be Added
```bash
context-engineering-test/
├── src/
│   ├── __init__.py
│   ├── main.py              # Entry point CLI application
│   ├── models/              # Data models
│   │   ├── __init__.py
│   │   ├── story.py         # Story, Character, Scene models
│   │   └── session.py       # Session management models
│   ├── agents/              # AI agent implementations
│   │   ├── __init__.py
│   │   ├── storyteller.py   # Main storytelling agent
│   │   ├── character.py     # Character embodiment agent (tool)
│   │   └── prompts.py       # System prompts
│   ├── storage/             # Persistence layer
│   │   ├── __init__.py
│   │   ├── file_storage.py  # File-based storage implementation
│   │   └── models.py        # Storage data models
│   ├── cli/                 # CLI interface
│   │   ├── __init__.py
│   │   ├── commands.py      # Command handlers
│   │   └── interface.py     # User interface logic
│   └── utils/               # Utility functions
│       ├── __init__.py
│       └── helpers.py       # Common helper functions
├── tests/                   # Test files
│   ├── __init__.py
│   ├── test_agents.py       # Agent tests
│   ├── test_storage.py      # Storage tests
│   ├── test_cli.py          # CLI tests
│   └── conftest.py          # Pytest configuration
├── .env.example             # Environment variables template
├── requirements.txt         # Dependencies
└── pyproject.toml          # Project configuration
```

### Known Gotchas of our Codebase & Library Quirks
```python
# CRITICAL: PydanticAI v0.0.14 requires specific patterns
# - Agent must specify deps_type for dependency injection
# - Tools must use RunContext[DepsType] for accessing dependencies
# - Multi-agent delegation requires careful usage tracking
# - Message history must be managed manually in CLI loops

# CRITICAL: Environment variable handling
# - Use python_dotenv and load_dotenv() for environment variables
# - Support multiple LLM providers (OpenAI, OpenRouter, etc.)
# - API keys should be optional with fallback behavior

# CRITICAL: File persistence requirements
# - Stories must be completely serializable to JSON
# - Session state includes message history and world state
# - File paths must be handled cross-platform

# CRITICAL: Testing requirements from CLAUDE.md
# - All functions need unit tests with pytest
# - Include 1 expected use, 1 edge case, 1 failure case per function
# - Use type hints throughout and validate with mypy
```

## Implementation Blueprint

### Data Models and Structure
Core data models ensure type safety and story state consistency:

```python
# Story and world state models
@dataclass
class Character:
    name: str
    description: str
    personality: str
    speech_patterns: str
    memories: List[str]
    relationships: Dict[str, str]

@dataclass
class Scene:
    location: str
    description: str
    atmosphere: str
    active_characters: List[str]
    props: List[str]

@dataclass
class StoryWorld:
    premise: str
    setting: str
    conflicts: List[str]
    characters: Dict[str, Character]
    current_scene: Scene
    history: List[str]

@dataclass
class StorySession:
    id: str
    world: StoryWorld
    message_history: List[ModelMessage]
    created_at: datetime
    last_updated: datetime
```

### List of Tasks to be Completed to Fulfill the PRP

```yaml
Task 1: Setup Project Structure and Dependencies
CREATE requirements.txt:
  - INCLUDE: pydantic-ai, python-dotenv, click, pytest, ruff, mypy
  - MIRROR pattern from: examples/agent/exampleAgent.py imports
  - ENSURE: All required dependencies for PydanticAI multi-agent setup

CREATE .env.example:

  - INCLUDE: LLM_MODEL, OPEN_ROUTER_API_KEY, OPENAI_API_KEY
  - MIRROR pattern from: examples/agent/exampleAgent.py environment setup

Task 2: Core Data Models
CREATE src/models/story.py:
  - IMPLEMENT: Character, Scene, StoryWorld dataclasses
  - INCLUDE: JSON serialization methods
  - MIRROR pattern from: Pydantic model validation

CREATE src/models/session.py:
  - IMPLEMENT: StorySession model with message history
  - INCLUDE: Session persistence methods
  - PRESERVE: PydanticAI message format compatibility

Task 3: Storage Layer
CREATE src/storage/file_storage.py:
  - IMPLEMENT: save_session, load_session, list_sessions methods
  - INCLUDE: Cross-platform file path handling
  - MIRROR pattern from: Standard Python JSON serialization

Task 4: Character Agent (Tool)
CREATE src/agents/character.py:
  - IMPLEMENT: Character embodiment agent as tool
  - INCLUDE: Personality-based response generation
  - MIRROR pattern from: examples/agent/exampleAgent.py tool decoration
  - PRESERVE: RunContext[DepsType] pattern for dependency injection

Task 5: Main Storyteller Agent
CREATE src/agents/storyteller.py:
  - IMPLEMENT: Main storytelling agent with character agent as tool
  - INCLUDE: Scenario creation and narrative generation
  - MIRROR pattern from: examples/agent/exampleAgent.py agent creation
  - PRESERVE: Multi-agent delegation patterns

CREATE src/agents/prompts.py:
  - IMPLEMENT: System prompts for both agents
  - INCLUDE: Role-specific instructions and behavior patterns
  - MIRROR pattern from: examples/agent/exampleAgent.py system_prompt

Task 6: CLI Interface
CREATE src/cli/interface.py:
  - IMPLEMENT: Menu system for scenario creation/loading
  - INCLUDE: Meta-command parsing with *asterisks*
  - MIRROR pattern from: examples/cli.py async chat loop

CREATE src/cli/commands.py:
  - IMPLEMENT: Command handlers for different modes
  - INCLUDE: Session management and story flow control
  - PRESERVE: Message history management pattern

Task 7: Main Application Entry Point
CREATE src/main.py:
  - IMPLEMENT: CLI entry point with command routing
  - INCLUDE: Environment setup and agent initialization
  - MIRROR pattern from: examples/cli.py main() function

Task 8: Unit Tests
CREATE tests/test_agents.py:
  - IMPLEMENT: Agent functionality tests
  - INCLUDE: 1 expected use, 1 edge case, 1 failure case per agent
  - MIRROR pattern from: Pytest async testing patterns

CREATE tests/test_storage.py:
  - IMPLEMENT: Storage layer tests
  - INCLUDE: File persistence and session management tests

CREATE tests/test_cli.py:
  - IMPLEMENT: CLI interface tests
  - INCLUDE: Command parsing and flow control tests

CREATE tests/conftest.py:
  - IMPLEMENT: Pytest configuration and fixtures
  - INCLUDE: Mock agents and test data setup
```

### Per Task Pseudocode

```python
# Task 4: Character Agent Implementation
class CharacterAgent:
    """Agent that embodies NPCs with distinct personalities"""
    
    def __init__(self, deps_type: Type[StoryDeps]):
        self.agent = Agent(
            model=get_model(),
            deps_type=deps_type,
            system_prompt=CHARACTER_SYSTEM_PROMPT,
            retries=2
        )
    
    @agent.tool
    async def embody_character(
        ctx: RunContext[StoryDeps], 
        character_name: str, 
        situation: str
    ) -> str:
        """Embody a character and respond to situation"""
        # PATTERN: Access character from story world
        character = ctx.deps.story_world.characters.get(character_name)
        if not character:
            return f"Character {character_name} not found"
        
        # PATTERN: Generate response based on personality
        response = await self.agent.run(
            f"Embody {character_name} in this situation: {situation}",
            deps=ctx.deps
        )
        
        # PATTERN: Update character memories
        character.memories.append(f"Responded to: {situation}")
        return response.data

# Task 5: Main Storyteller Agent
class StorytellerAgent:
    """Main agent that orchestrates storytelling"""
    
    def __init__(self):
        self.character_agent = CharacterAgent(StoryDeps)
        self.agent = Agent(
            model=get_model(),
            deps_type=StoryDeps,
            system_prompt=STORYTELLER_SYSTEM_PROMPT,
            tools=[self.character_agent.embody_character],
            retries=2
        )
    
    async def create_scenario(self, initial_concept: str) -> StoryWorld:
        """Create complete story scenario through dialogue"""
        # PATTERN: Iterative refinement with user approval
        scenario_prompt = f"Help develop this story concept: {initial_concept}"
        
        # GOTCHA: Must track conversation state during creation
        creation_messages = []
        
        while not user_approved:
            result = await self.agent.run(
                scenario_prompt,
                message_history=creation_messages
            )
            
            # PATTERN: Present to user and get feedback
            user_response = await get_user_input(result.data)
            if user_response.lower() == 'approve':
                break
                
            creation_messages.extend(result.new_messages())
        
        # PATTERN: Extract structured data from conversation
        return extract_story_world(creation_messages)
    
    async def continue_story(self, user_input: str, story_world: StoryWorld) -> str:
        """Continue story based on user input"""
        # PATTERN: Parse meta-commands with *asterisks*
        if user_input.startswith('*') and user_input.endswith('*'):
            meta_command = user_input[1:-1]
            # PATTERN: Apply meta-command without acknowledgment
            return await self.handle_meta_command(meta_command, story_world)
        
        # PATTERN: Generate narrative response
        narrative_prompt = f"Continue the story: {user_input}"
        
        result = await self.agent.run(
            narrative_prompt,
            deps=StoryDeps(story_world=story_world)
        )
        
        # PATTERN: Update story world state
        story_world.history.append(f"User: {user_input}")
        story_world.history.append(f"Narrator: {result.data}")
        
        return result.data
```

### Integration Points
```yaml
DEPENDENCIES:
  - install: "pip install pydantic-ai python-dotenv click pytest ruff mypy"
  - pattern: "Use venv_linux activation from CLAUDE.md"
  
ENVIRONMENT:
  - add to: .env.example
  - pattern: "LLM_MODEL=gpt-4o-mini"
  - pattern: "OPEN_ROUTER_API_KEY=your_key_here"
  
ENTRY_POINT:
  - add to: src/main.py
  - pattern: "if __name__ == '__main__': asyncio.run(main())"
  
STORAGE:
  - create: "stories/" directory for session persistence
  - pattern: "JSON serialization with datetime handling"
```

## Validation Loop

### Level 1: Syntax & Style
```bash
# Run these FIRST - fix any errors before proceeding
source venv/bin/activate
ruff check src/ --fix        # Auto-fix what's possible
mypy src/                   # Type checking

# Expected: No errors. If errors, READ the error and fix.
```

### Level 2: Unit Tests
```python
# CREATE comprehensive test suite:
def test_character_agent_embody():
    """Test character embodiment with personality"""
    # Expected use case
    character = Character(name="Alice", personality="cheerful")
    result = await character_agent.embody_character("Alice", "greeting")
    assert "cheerful" in result.lower()

def test_storyteller_scenario_creation():
    """Test scenario creation workflow"""
    # Expected use case
    concept = "A detective story in Victorian London"
    world = await storyteller.create_scenario(concept)
    assert world.setting == "Victorian London"
    assert len(world.characters) > 0

def test_meta_command_parsing():
    """Test meta-command handling"""
    # Edge case
    command = "*suddenly it starts raining*"
    result = await storyteller.continue_story(command, test_world)
    assert "rain" in result.lower()

def test_session_persistence():
    """Test session save/load functionality"""
    # Expected use case
    session = create_test_session()
    storage.save_session(session)
    loaded = storage.load_session(session.id)
    assert loaded.world.premise == session.world.premise

def test_invalid_character_request():
    """Test character agent with non-existent character"""
    # Failure case
    with pytest.raises(ValueError):
        await character_agent.embody_character("NonExistent", "test")
```

```bash
# Run and iterate until passing:
source venv/bin/activate
uv run pytest tests/ -v
# If failing: Read error, understand root cause, fix code, re-run
```

### Level 3: Integration Test
```bash
# Start the application
source venv/bin/activate
python src/main.py

# Test scenario creation
# Input: "1" (create new scenario)
# Input: "A space adventure on Mars"
# Expected: Conversational development of story elements

# Test storytelling mode
# Input: "Hello, I'm ready to explore"
# Expected: Narrative response with character interactions

# Test meta-command
# Input: "*suddenly the lights go out*"
# Expected: Story naturally incorporates darkness without acknowledgment

# Test session persistence
# Input: "quit" to save and exit
# Restart application
# Input: "2" (load existing session)
# Expected: Story continues from where it left off
```

## Final Validation Checklist
- [ ] All tests pass: `uv run pytest tests/ -v`
- [ ] No linting errors: `uv run ruff check src/`
- [ ] No type errors: `uv run mypy src/`
- [ ] CLI starts without errors: `python src/main.py`
- [ ] Scenario creation works end-to-end
- [ ] Storytelling mode provides natural narrative
- [ ] Meta-commands integrate seamlessly
- [ ] Session persistence works correctly
- [ ] Character agent embodies NPCs distinctly
- [ ] Error cases handled gracefully
- [ ] All dependencies documented in requirements.txt

## Anti-Patterns to Avoid
- ❌ Don't create agents without proper dependency injection
- ❌ Don't ignore message history management in CLI loops
- ❌ Don't hardcode API keys or model names
- ❌ Don't skip async/await patterns for agent calls
- ❌ Don't create tools without proper error handling
- ❌ Don't forget to activate virtual environment for testing
- ❌ Don't use sync functions in async context
- ❌ Don't skip type hints and docstrings
- ❌ Don't create files over 500 lines (per CLAUDE.md)
- ❌ Don't forget to serialize message history for persistence