## FEATURE:

- Pydantic AI agent that has another Pydantic AI agent as a tool.
Overview
A command-line application for collaborative AI-driven storytelling that creates novel-like narratives through natural conversation.

Core Functionality

 1. Scenario Creation Mode
- User provides initial story concept
- System engages in dialogue to develop:
  - Story premise and conflicts
  - Character profiles (appearance, personality, speech patterns)
  - World setting (environment, culture, rules)
- Iterative refinement until user approves
- Save complete scenario for future use

 2. Storytelling Mode  
- Load existing scenario or use newly created one
- User plays main character
- System acts as:
  - **Narrator**: Describes scenes, controls environment, manages time
  - **Characters**: Embodies NPCs with distinct personalities
- Natural prose output without rigid formatting
- Continuous narrative flow until user ends session

3. Meta-Commands
- User can insert commands using `*asterisks*` notation
- Commands alter story direction without acknowledgment
- No restrictions on what can be changed
- Changes integrate naturally into ongoing narrative

 4. Persistence
- Save complete story sessions to disk
- Load and resume previous sessions
- Maintain character memories across sessions
- Preserve world state and story history

5. Session Management
- Create new stories
- List available scenarios and saved sessions
- Load specific scenarios or continue previous stories
- Delete unwanted saves

 User Interaction Flow

1. **Start**: Choose to create new scenario or load existing
2. **Scenario Creation** (if new):
   - Conversational development of story elements
   - Review and approval of final scenario
3. **Story Session**:
   - Begin or resume narrative
   - Type character actions/dialogue
   - Receive narrative responses
   - Use meta-commands to guide story
   - Save progress automatically
4. **End**: Exit with session saved for later continuation

## System Behaviors

- All story elements visible to all system components
- Player has ultimate authority over story direction
- Focus on character relationships and narrative over game mechanics
- Support for 1-2 active NPCs plus minor characters
- Novel-style prose throughout
- No structured turn-taking or combat systems

## EXAMPLES:

In the `examples/` folder, there is a README for you to read to understand what the example is all about and also how to structure your own README when you create documentation for the above feature.

- `examples/cli.py` - use this as a template to create the CLI
- `examples/agent/` - read through all of the files here to understand best practices for creating Pydantic AI agents that support different providers and LLMs, handling agent dependencies, and adding tools to the agent.

Don't copy any of these examples directly, it is for a different project entirely. But use this as inspiration and for best practices.

## DOCUMENTATION:

Pydantic AI documentation: https://ai.pydantic.dev/
also there is the MCP context7 available

## OTHER CONSIDERATIONS:

- Include a .env.example, README with instructions for setup including how to configure Gmail and Brave.
- Include the project structure in the README.
- Virtual environment has already been set up with the necessary dependencies.
- Use python_dotenv and load_env() for environment variables