# Personal Assistant CLI

A Personal Leadership Assistant with two operational modes:
- **Control Plane**: CLI (`pa`) for configuration and entity management
- **Data Plane**: Claude Code for querying and synthesizing context

## Prerequisites

- Python 3.10+
- [uv](https://docs.astral.sh/uv/) package manager

### Installing uv

```bash
# macOS/Linux
curl -LsSf https://astral.sh/uv/install.sh | sh

# Or with Homebrew
brew install uv
```

## Installation

### Development Installation

Clone and install in development mode:

```bash
# Install dependencies and create virtual environment
uv sync

# Verify installation
uv run pa --help
```

### Global Installation

To install the CLI globally (available as `pa` without `uv run`):

```bash
# Build the package
uv build

# Install globally with pipx (recommended)
pipx install dist/personal_assistant-0.1.0-py3-none-any.whl

# Or install with pip
pip install dist/personal_assistant-0.1.0-py3-none-any.whl
```

## Usage

### Quick Start

```bash
# Add a team
uv run pa entity add team --name "Platform Team" --type engineering

# Add a person to the team
uv run pa entity add person --name "John Doe" --team platform-team --role "Senior Engineer"

# List all entities
uv run pa entity list

# Add a memory/observation
uv run pa remember john-doe "Great debugging skills, helped resolve production issue"

# Search memory
uv run pa memory search "debugging"
```

### Entity Management

```bash
# Add entities
pa entity add team --name "Platform Team" --type engineering
pa entity add person --name "John Doe" --team platform-team --role "Senior Engineer"

# List entities
pa entity list           # List all
pa entity list people    # List only people
pa entity list teams     # List only teams

# Show entity details
pa entity show john-doe
pa entity show platform-team

# Update entities
pa entity update john-doe --role "Staff Engineer"
pa entity update john-doe --add-tag "high-performer"
pa entity update john-doe --remove-tag "new-hire"

# Delete entities (with confirmation)
pa entity delete john-doe
pa entity delete john-doe --force  # Skip confirmation
```

### Calendar-Notion Mappings

```bash
# Add a mapping
pa map add --calendar-pattern "1:1 with John" --entity john-doe --notion "notion://page/abc123"

# List mappings
pa map list

# Delete a mapping
pa map delete 11-with-john
```

### Memory/Observations

```bash
# Add an observation
pa remember john-doe "Expressed interest in ML team"

# Add with context
pa remember john-doe "Mentioned burnout concerns" --context "1:1 meeting 2025-01-20"

# Add different types
pa remember john-doe "Note about project timeline" --type note

# Show all memory for an entity
pa memory show john-doe

# Search across all memory
pa memory search "ML"
```

### Configuration

```bash
# Show current config
pa config show

# Set config values
pa config set default_team platform-team
pa config set notion_workspace "https://notion.so/workspace"
```

## Data Storage

All data is stored in the `data/` directory:

```
data/
├── config.yaml              # Global preferences
├── entities/
│   ├── people.yaml          # Person definitions
│   └── teams.yaml           # Team/group definitions
├── mappings/
│   └── calendar-notion.yaml # Calendar→Notion links
└── memory/
    ├── people/
    │   └── {person-id}/
    │       └── {YYYY-MM-DD}_{type}_{source}.md
    └── teams/
        └── {team-id}/
            └── {YYYY-MM-DD}_{type}_{source}.md
```

## Testing

### Run Tests

```bash
# Run all tests
uv run pytest

# Run with coverage
uv run pytest --cov=personal_assistant

# Run specific test file
uv run pytest tests/test_cli.py
```

### Manual Testing

```bash
# Test entity workflow
uv run pa entity add team --name "Test Team" --type testing
uv run pa entity add person --name "Test User" --team test-team
uv run pa entity show test-user
uv run pa entity delete test-user --force
uv run pa entity delete test-team --force
```

## Development

### Project Structure

```
personal-assistant/
├── src/personal_assistant/
│   ├── __init__.py      # Package metadata
│   ├── cli.py           # Typer CLI commands
│   ├── schemas.py       # Pydantic models
│   └── storage.py       # YAML file operations
├── data/                # Data storage (gitignored)
├── adr/                 # Architecture Decision Records
├── tests/               # Test files
├── pyproject.toml       # Project configuration
└── README.md
```

### Adding Dependencies

```bash
# Add a runtime dependency
uv add <package>

# Add a development dependency
uv add --dev <package>
```

### Rebuilding After Changes

```bash
# Reinstall package after code changes
uv sync --reinstall
```

## Integration with Claude Code

The CLI manages the data that Claude Code reads for context synthesis. In Claude Code, you can ask:

- "What do I know about John?"
- "Who is on the Platform team?"
- "What observations have I made about the Platform team?"

Claude Code reads the YAML and Markdown files in `data/` to answer these queries.

## License

Private - Internal use only
