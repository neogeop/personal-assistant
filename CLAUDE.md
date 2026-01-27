# Personal Leadership Assistant

A personal assistant CLI for engineering leaders to manage relationships, context, and meeting preparation.

## Architecture

This project uses a **two-plane model**:

| Plane | Interface | Purpose |
|-------|-----------|---------|
| **Control Plane** | CLI (`pa` command) | Configuration, entity management, explicit memory writes |
| **Data Plane** | Claude Code chat | Querying, context synthesis, MCP integration |

### Data Model

**Entities** (in `data/entities/`):
- **Person**: Individual with id, name, role, team_id, tags, calendar_patterns, notion_page
- **Team**: Group with id, name, team_type, calendar_patterns, notion_page

**Mappings** (in `data/mappings/`):
- **CalendarNotionMapping**: Links calendar event patterns to entities and their Notion pages

**Memory** (in `data/memory/`):
- Markdown files organized by entity type and ID
- File naming: `{YYYY-MM-DD}_{entry_type}_{source}.md`
- Entry types: observation, note, inference
- Sources: user, inferred

### External Integrations (MCP)

- **Google Calendar**: Fetch events, attendees, meeting times
- **Notion**: Read meeting notes, action items, context

### Data Directory Configuration

The CLI stores data in a configurable directory:

| Priority | Source | Default Value |
|----------|--------|---------------|
| 1 | `PA_DATA_DIR` environment variable | (none) |
| 2 | `XDG_DATA_HOME/personal-assistant` | `~/.local/share/personal-assistant` |

**Examples:**

```bash
# Use a custom directory
export PA_DATA_DIR=~/my-pa-data
pa entity list

# Or inline
PA_DATA_DIR=./data pa entity list
```

### Auto-Seeded Mappings

When adding entities with `--calendar-patterns`, mappings are **automatically created**:

```bash
pa entity add person --name "John" --calendar-patterns "1:1 John,John sync" --notion "https://..."
# Output:
# Added person: john (John)
# Auto-created 2 calendar mapping(s)
```

This eliminates the need to manually run `pa map add` after entity creation.

## CLI Commands

```bash
# Entity management
pa entity add person --name "John Doe" --role "Engineer"
pa entity add team --name "Platform" --type "engineering"
pa entity list [people|teams]
pa entity show <entity-id>
pa entity update <entity-id> --role "Senior Engineer"
pa entity delete <entity-id>

# Calendar-Notion mappings
pa map add --pattern "1:1 John" --entity john-doe --type person
pa map list
pa map delete <mapping-id>

# Memory
pa remember <entity-id> "Observation text"
pa remember <entity-id> --file notes.md
pa memory show <entity-id>
pa memory search "query"

# Config
pa config set notion_workspace "https://notion.so/workspace"
pa config show
```

## Custom Skills

The following skills can be invoked via `/skill-name` in Claude Code chat.

### /prepare meeting <entity-id>

Prepare context for a meeting with a specific person or team.

**Usage:**
```
/prepare meeting john-doe
/prepare meeting platform-team
```

**What it does:**
1. Looks up entity from `data/entities/`
2. Fetches their Notion page via MCP
3. Parses recent meeting sections (last 3-5 meetings)
4. Extracts open action items (unchecked boxes)
5. Reads local memory observations
6. Checks calendar for next meeting time
7. Synthesizes context with confidence scoring

**Skill file:** `data/skills/prepare-meeting.md`

### /prepare day

Prepare context for all meetings scheduled today.

**Usage:**
```
/prepare day
```

**What it does:**
1. Fetches today's calendar events via Google Calendar MCP
2. Matches each event to entities via `calendar_patterns`
3. Runs prepare-meeting logic for each matched entity
4. Aggregates into a daily brief with all meetings

**Skill file:** `data/skills/prepare-day.md`

### /weekly review

Review the past week and identify focus areas for next week.

**Usage:**
```
/weekly review
```

**What it does:**
1. Fetches this week's calendar events
2. For each entity with meetings this week:
   - Summarizes topics discussed
   - Lists new actions created
   - Lists actions completed
3. Identifies patterns and recurring themes
4. Generates focus recommendations for next week

**Skill file:** `data/skills/weekly-review.md`

## Confidence Scoring

All skill outputs include a confidence score (0.0-1.0) based on:

| Factor | Weight | Description |
|--------|--------|-------------|
| Notion page found | +0.2 | Entity has linked Notion page that was fetched |
| Recent meetings | +0.2 | Last meeting within 2 weeks |
| Open actions extracted | +0.1 | Found unchecked action items |
| Local memory present | +0.2 | Has observations in memory directory |
| Calendar match found | +0.1 | Next meeting found in calendar |
| Multiple sources agree | +0.2 | Corroboration across data sources |

**Display thresholds:**
- 0.0-0.4: Low confidence
- 0.5-0.7: Medium confidence
- 0.8-1.0: High confidence

## Data Directory Structure

```
data/
├── config.yaml                    # Global configuration
├── entities/
│   ├── people.yaml               # Person entities
│   └── teams.yaml                # Team entities
├── mappings/
│   └── calendar-notion.yaml      # Calendar-Notion mappings
├── memory/
│   ├── people/{person-id}/       # Memory files per person
│   │   └── {date}_{type}_{source}.md
│   └── teams/{team-id}/          # Memory files per team
│       └── {date}_{type}_{source}.md
└── skills/
    ├── prepare-meeting.md        # Meeting prep instructions
    ├── prepare-day.md            # Daily prep instructions
    └── weekly-review.md          # Weekly review instructions
```

## Notion Page Parsing

Meeting sections in Notion follow these patterns:

**Pattern A: Group/Team Meetings**
- Toggle headers with `<mention-date start="YYYY-MM-DD"/>`
- Subsections: "Actions from previous", "Topics to discuss", "Actions"
- Checkboxes: `- [ ]` (open) and `- [x]` (complete)
- Assignees via `<mention-user>` tags

**Pattern B: 1:1 Meetings**
- Date headers as H2/H3 with `<mention-date>`
- Subsections: "Topics:", "Actions:"
- Owner prefixes like `[KK]`, `[GP]`

**Common Elements:**
- All use `<mention-date start="YYYY-MM-DD"/>` for dating sections
- All use `- [ ]` checkbox format for actions
- Organized chronologically (newest first or last)

## Development

```bash
# Install dependencies
uv sync

# Run tests
uv run pytest

# Run CLI
uv run pa --help
```
