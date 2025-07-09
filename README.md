# Interactive Storytelling Application

A collaborative AI-driven storytelling application powered by PydanticAI multi-agent architecture. This application demonstrates advanced Context Engineering principles for building reliable AI systems.

> **Context Engineering is 10x better than prompt engineering and 100x better than vibe coding.**

## 🚀 Quick Start

```bash
# 1. Clone the repository
git clone <repository-url>
cd context-engineering-test

# 2. Set up Python virtual environment
python -m venv venv_linux
source venv_linux/bin/activate  # On Windows: venv_linux\Scripts\activate

# 3. Install dependencies
pip install -r requirements.txt

# 4. Configure environment variables
cp .env.example .env
# Edit .env and add your API keys (OpenAI or OpenRouter)

# 5. Run the application
cd src && PYTHONPATH=/home/max/projects/context-engineering-test/src:/home/max/projects/context-engineering-test python main.py
```

## 📋 Requirements

- Python 3.9+
- OpenAI API key OR OpenRouter API key
- Internet connection for AI model access

## 🛠️ Installation

### 1. Environment Setup
```bash
# Create virtual environment
python -m venv venv_linux
source venv_linux/bin/activate

# Install dependencies
pip install -r requirements.txt
```

### 2. Configuration
```bash
# Copy environment template (if available)
cp .env.example .env

# Create .env file with your API keys
echo "OPENAI_API_KEY=your_key_here" > .env
# OR
echo "OPEN_ROUTER_API_KEY=your_key_here" > .env

# Optional: Set model and logging
echo "LLM_MODEL=gpt-4o-mini" >> .env
echo "LOGFIRE_TOKEN=your_token_here" >> .env
```

### 3. Running the Application
```bash
# Navigate to src directory and run
cd src
PYTHONPATH=/home/max/projects/context-engineering-test/src:/home/max/projects/context-engineering-test python main.py
```

## 🎮 Usage

The application provides an interactive CLI for collaborative storytelling:

### Main Menu Options:
1. **🆕 Create new story scenario** - Generate a complete story world with characters
2. **📚 Load existing story session** - Continue a previously saved story
3. **📋 List all saved sessions** - View all your story sessions
4. **🗑️ Delete a story session** - Remove unwanted sessions
5. **❌ Exit** - Close the application

### Story Creation Process:
1. Enter your story concept (e.g., "A brave knight seeks a magical sword")
2. The AI generates a complete story world including:
   - **Premise**: Core story concept and quest
   - **Setting**: Detailed world description
   - **Conflicts**: Multiple storylines and challenges
   - **Characters**: Fully developed NPCs with personalities
   - **Opening Scene**: Starting location and atmosphere
3. Approve or refine the generated scenario
4. Begin interactive storytelling with character role-play

### Interactive Features:
- **Character Role-Play**: NPCs respond authentically based on their personalities
- **Story Progression**: AI maintains narrative consistency and continuity
- **Session Management**: Save/load stories to continue later
- **Memory System**: Characters remember past interactions

## 🧪 Testing

```bash
# Run all tests
python -m pytest

# Run with coverage
python -m pytest --cov=src

# Run specific test file
python -m pytest tests/test_agents.py

# Test the character agent specifically
cd src && PYTHONPATH=/home/max/projects/context-engineering-test/src:/home/max/projects/context-engineering-test python test_character_agent.py
```

## 🔧 Development

### Code Quality
```bash
# Format code
ruff format .

# Lint code
ruff check .

# Type checking
mypy src/
```

### Project Structure
```
src/
├── agents/          # AI agent implementations
│   ├── character.py            # Character embodiment agent
│   ├── character_creator.py    # Character creation agent
│   ├── scenario_generator.py   # Scenario generation agent
│   ├── storyteller.py         # Main orchestration agent
│   └── prompts.py             # System prompts
├── cli/            # Command-line interface
│   ├── interface.py           # Main CLI interface
│   └── commands.py            # CLI command handlers
├── models/         # Data models
│   ├── story.py              # Story world, characters, scenes
│   └── session.py            # Story session management
├── storage/        # Story persistence
│   └── file_storage.py       # File-based storage
├── utils/          # Utility functions
│   └── helpers.py            # Helper functions
└── main.py         # Application entry point
```

## 🤖 Multi-Agent Architecture

This application demonstrates advanced multi-agent patterns using PydanticAI:

### Agent Specialization
- **Scenario Generator Agent**: Creates immersive story premises, settings, conflicts, and opening scenes
- **Character Creation Agent**: Generates detailed characters with personalities, descriptions, and speech patterns  
- **Character Embodiment Agent**: Allows characters to speak and act authentically during gameplay
- **Storyteller Agent**: Orchestrates the overall narrative and coordinates between agents

### Agent Tools & Delegation
Each agent uses specialized tools and can delegate to other agents:
- Scenario creation generates character concepts that are passed to the character creator
- The storyteller uses the character embodiment tool to make NPCs respond in character
- Enhanced logging captures the complete data flow between agents

### Key Features
- **Role-Play System**: Characters maintain consistent personalities and speech patterns
- **Memory Management**: Characters remember past interactions and build relationships
- **Narrative Continuity**: Story world state is maintained across sessions
- **Multi-Agent Coordination**: Agents work together seamlessly to create cohesive stories

## 📚 Table of Contents

- [What is Context Engineering?](#what-is-context-engineering)
- [Template Structure](#template-structure)
- [Step-by-Step Guide](#step-by-step-guide)
- [Writing Effective INITIAL.md Files](#writing-effective-initialmd-files)
- [The PRP Workflow](#the-prp-workflow)
- [Using Examples Effectively](#using-examples-effectively)
- [Best Practices](#best-practices)

## What is Context Engineering?

Context Engineering represents a paradigm shift from traditional prompt engineering:

### Prompt Engineering vs Context Engineering

**Prompt Engineering:**
- Focuses on clever wording and specific phrasing
- Limited to how you phrase a task
- Like giving someone a sticky note

**Context Engineering:**
- A complete system for providing comprehensive context
- Includes documentation, examples, rules, patterns, and validation
- Like writing a full screenplay with all the details

### Why Context Engineering Matters

1. **Reduces AI Failures**: Most agent failures aren't model failures - they're context failures
2. **Ensures Consistency**: AI follows your project patterns and conventions
3. **Enables Complex Features**: AI can handle multi-step implementations with proper context
4. **Self-Correcting**: Validation loops allow AI to fix its own mistakes

## Template Structure

```
context-engineering-intro/
├── .claude/
│   ├── commands/
│   │   ├── generate-prp.md    # Generates comprehensive PRPs
│   │   └── execute-prp.md     # Executes PRPs to implement features
│   └── settings.local.json    # Claude Code permissions
├── PRPs/
│   ├── templates/
│   │   └── prp_base.md       # Base template for PRPs
│   └── EXAMPLE_multi_agent_prp.md  # Example of a complete PRP
├── examples/                  # Your code examples (critical!)
├── CLAUDE.md                 # Global rules for AI assistant
├── INITIAL.md               # Template for feature requests
├── INITIAL_EXAMPLE.md       # Example feature request
└── README.md                # This file
```

This template doesn't focus on RAG and tools with context engineering because I have a LOT more in store for that soon. ;)

## Step-by-Step Guide

### 1. Set Up Global Rules (CLAUDE.md)

The `CLAUDE.md` file contains project-wide rules that the AI assistant will follow in every conversation. The template includes:

- **Project awareness**: Reading planning docs, checking tasks
- **Code structure**: File size limits, module organization
- **Testing requirements**: Unit test patterns, coverage expectations
- **Style conventions**: Language preferences, formatting rules
- **Documentation standards**: Docstring formats, commenting practices

**You can use the provided template as-is or customize it for your project.**

### 2. Create Your Initial Feature Request

Edit `INITIAL.md` to describe what you want to build:

```markdown
## FEATURE:
[Describe what you want to build - be specific about functionality and requirements]

## EXAMPLES:
[List any example files in the examples/ folder and explain how they should be used]

## DOCUMENTATION:
[Include links to relevant documentation, APIs, or MCP server resources]

## OTHER CONSIDERATIONS:
[Mention any gotchas, specific requirements, or things AI assistants commonly miss]
```

**See `INITIAL_EXAMPLE.md` for a complete example.**

### 3. Generate the PRP

PRPs (Product Requirements Prompts) are comprehensive implementation blueprints that include:

- Complete context and documentation
- Implementation steps with validation
- Error handling patterns
- Test requirements

They are similar to PRDs (Product Requirements Documents) but are crafted more specifically to instruct an AI coding assistant.

Run in Claude Code:
```bash
/generate-prp INITIAL.md
```

**Note:** The slash commands are custom commands defined in `.claude/commands/`. You can view their implementation:
- `.claude/commands/generate-prp.md` - See how it researches and creates PRPs
- `.claude/commands/execute-prp.md` - See how it implements features from PRPs

The `$ARGUMENTS` variable in these commands receives whatever you pass after the command name (e.g., `INITIAL.md` or `PRPs/your-feature.md`).

This command will:
1. Read your feature request
2. Research the codebase for patterns
3. Search for relevant documentation
4. Create a comprehensive PRP in `PRPs/your-feature-name.md`

### 4. Execute the PRP

Once generated, execute the PRP to implement your feature:

```bash
/execute-prp PRPs/your-feature-name.md
```

The AI coding assistant will:
1. Read all context from the PRP
2. Create a detailed implementation plan
3. Execute each step with validation
4. Run tests and fix any issues
5. Ensure all success criteria are met

## Writing Effective INITIAL.md Files

### Key Sections Explained

**FEATURE**: Be specific and comprehensive
- ❌ "Build a web scraper"
- ✅ "Build an async web scraper using BeautifulSoup that extracts product data from e-commerce sites, handles rate limiting, and stores results in PostgreSQL"

**EXAMPLES**: Leverage the examples/ folder
- Place relevant code patterns in `examples/`
- Reference specific files and patterns to follow
- Explain what aspects should be mimicked

**DOCUMENTATION**: Include all relevant resources
- API documentation URLs
- Library guides
- MCP server documentation
- Database schemas

**OTHER CONSIDERATIONS**: Capture important details
- Authentication requirements
- Rate limits or quotas
- Common pitfalls
- Performance requirements

## The PRP Workflow

### How /generate-prp Works

The command follows this process:

1. **Research Phase**
   - Analyzes your codebase for patterns
   - Searches for similar implementations
   - Identifies conventions to follow

2. **Documentation Gathering**
   - Fetches relevant API docs
   - Includes library documentation
   - Adds gotchas and quirks

3. **Blueprint Creation**
   - Creates step-by-step implementation plan
   - Includes validation gates
   - Adds test requirements

4. **Quality Check**
   - Scores confidence level (1-10)
   - Ensures all context is included

### How /execute-prp Works

1. **Load Context**: Reads the entire PRP
2. **Plan**: Creates detailed task list using TodoWrite
3. **Execute**: Implements each component
4. **Validate**: Runs tests and linting
5. **Iterate**: Fixes any issues found
6. **Complete**: Ensures all requirements met

See `PRPs/EXAMPLE_multi_agent_prp.md` for a complete example of what gets generated.

## Using Examples Effectively

The `examples/` folder is **critical** for success. AI coding assistants perform much better when they can see patterns to follow.

### What to Include in Examples

1. **Code Structure Patterns**
   - How you organize modules
   - Import conventions
   - Class/function patterns

2. **Testing Patterns**
   - Test file structure
   - Mocking approaches
   - Assertion styles

3. **Integration Patterns**
   - API client implementations
   - Database connections
   - Authentication flows

4. **CLI Patterns**
   - Argument parsing
   - Output formatting
   - Error handling

### Example Structure

```
examples/
├── README.md           # Explains what each example demonstrates
├── cli.py             # CLI implementation pattern
├── agent/             # Agent architecture patterns
│   ├── agent.py      # Agent creation pattern
│   ├── tools.py      # Tool implementation pattern
│   └── providers.py  # Multi-provider pattern
└── tests/            # Testing patterns
    ├── test_agent.py # Unit test patterns
    └── conftest.py   # Pytest configuration
```

## Best Practices

### 1. Be Explicit in INITIAL.md
- Don't assume the AI knows your preferences
- Include specific requirements and constraints
- Reference examples liberally

### 2. Provide Comprehensive Examples
- More examples = better implementations
- Show both what to do AND what not to do
- Include error handling patterns

### 3. Use Validation Gates
- PRPs include test commands that must pass
- AI will iterate until all validations succeed
- This ensures working code on first try

### 4. Leverage Documentation
- Include official API docs
- Add MCP server resources
- Reference specific documentation sections

### 5. Customize CLAUDE.md
- Add your conventions
- Include project-specific rules
- Define coding standards

## Resources

- [Claude Code Documentation](https://docs.anthropic.com/en/docs/claude-code)
- [Context Engineering Best Practices](https://www.philschmid.de/context-engineering)