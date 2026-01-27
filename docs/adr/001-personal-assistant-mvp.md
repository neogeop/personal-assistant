# Personal Assistant MVP Plan

## Overview

Build a Personal Leadership Assistant with two operational modes:
- **Control Plane**: CLI for configuration and entity management
- **Data Plane**: Claude Code for querying and synthesizing context

## MVP Scope (Foundation Phase)

### What MVP Delivers
1. **Entity Management**: Define people, groups/teams with relationships
2. **Calendar-Notion Mapping**: Link calendar events to Notion pages
3. **Memory/Observations**: Store and retrieve notes about entities
4. **Natural Language Query**: "What do I know about [person/team]?"

### What MVP Defers
- Daily meeting preparation (Phase 2)
- Weekly review/focus (Phase 2)
- Transcript ingestion (Phase 3)
- Confidence scoring (Phase 2+)

---

## Architecture Decision: CLI Implementation

### Option A: Shell Scripts + YAML
**Pros:**
- Zero dependencies, instant setup
- Human-readable/editable config files
- Simple for Claude Code to read

**Cons:**
- Validation is manual/fragile
- Relationship integrity not enforced
- No interactive features (tab completion, validation prompts)

### Option B: Python CLI (Click/Typer)
**Pros:**
- Type validation via Pydantic
- Relationship integrity checks at write time
- Extensible command structure
- Interactive prompts for complex inputs
- Easier to add SQLite later if needed

**Cons:**
- Requires Python environment setup
- More upfront code

### Recommendation: Python CLI (Typer + Pydantic)
For light relationships (person→team references), we need validation at write time. Python gives us:
- Schema validation with clear error messages
- Referential integrity (can't add person to non-existent team)
- Clean migration path to SQLite if query patterns demand it
- Still uses YAML files as storage (best of both worlds)

---

## Memory Architecture

### Two-Layer Memory Model
1. **Notion (Primary)**: Company source of truth for meeting notes, decisions, actions
2. **Local Memory (Interpretive)**: Personal observations and context about entities

### Memory Hierarchy
When answering queries:
- Notion content is the source of truth
- Local memory provides personal interpretation layer on top
- Local observations can annotate but not override Notion facts

### Write Permissions
- **Notion**: Read-only from Data Plane; writes via CLI with explicit approval
- **Local Memory**: Claude Code can write, all entries tagged with `source`:
  - `source: "user"` - Explicitly added via CLI
  - `source: "inferred"` - Added by Claude during conversation
  - Future refinement: approval workflow for inferred observations

---

## Data Model

### Storage Format: YAML Files
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
    │       └── {YYYY-MM-DD}_{type}_{source}.md  # e.g., 2025-01-27_observation_user.md
    └── teams/
        └── {team-id}/
            └── {YYYY-MM-DD}_{type}_{source}.md
```

**Note**: Data stored in project folder: `/Users/g.panagiotou/src/claude-playground/personal-assistant/data/`

### Entity Schemas

**Person** (`entities/people.yaml`)
```yaml
# People definitions
- id: john-doe
  name: John Doe
  role: Senior Engineer
  team_id: platform  # reference to team
  tags:
    - direct-report
    - high-performer
  calendar_patterns:
    - "1:1 with John"
    - "John sync"
  notion_page: "notion://page/abc123"
```

**Team** (`entities/teams.yaml`)
```yaml
# Team definitions
- id: platform
  name: Platform Team
  type: engineering
  calendar_patterns:
    - "Platform standup"
    - "Platform retro"
  notion_page: "notion://page/xyz789"
```

**Memory Entry** (`memory/people/john-doe/2025-01-27_observation_user.md`)
```markdown
# Observation: John Doe

Context: 1:1 meeting 2025-01-20

---

Expressed interest in moving to ML team. Has been doing some self-study
on machine learning fundamentals and mentioned he'd like to work on the
recommendation engine.
```

**Filename convention**: `{YYYY-MM-DD}_{type}_{source}.md`
- **type**: `observation` | `note` | `inference`
- **source**: `user` (CLI) | `inferred` (Claude Code)

---

## Control Plane CLI Commands

```bash
# Entity management
pa entity add person --name "John Doe" --team platform
pa entity add team --name "Platform Team" --type engineering
pa entity list [people|teams]
pa entity show <id>
pa entity update <id> --field value
pa entity delete <id>

# Calendar-Notion mapping
pa map add --calendar-pattern "1:1 with John" --entity john-doe --notion <page>
pa map list
pa map delete <id>

# Memory/observations
pa remember <entity-id> "Observation or note text"
pa memory show <entity-id>
pa memory search "keyword"

# Config
pa config set <key> <value>
pa config show
```

---

## Data Plane (Claude Code)

### How Claude Code Accesses Data
1. Read YAML files from `./data/` directory (project folder)
2. Use MCP tools for Google Calendar and Notion
3. Synthesize context by combining stored entities + live data

### Query Patterns (MVP)
- "What do I know about John?" → Read person entity + memory entries
- "Who is on the Platform team?" → Read team + filter people by team_id
- "What meetings do I have with John this week?" → Entity calendar_patterns + Google Calendar MCP
- "Show me John's Notion page" → Entity notion_page + Notion MCP

---

## Implementation Plan

### Phase 0: Documentation
- [x] Create `adr/` folder in repository
- [x] Store this plan as `adr/001-personal-assistant-mvp.md`

### Phase 1: Project Setup
- [ ] Initialize Python project with `uv` + Typer + Pydantic
- [ ] Create data directory structure
- [ ] Define Pydantic schemas for entities
- [ ] Implement `pa config` command

### Phase 2: Entity Management
- [ ] Implement `pa entity add/list/show/update/delete` for people
- [ ] Implement same for teams
- [ ] Add relationship validation (person.team_id must exist)

### Phase 3: Mappings
- [ ] Implement `pa map add/list/delete`
- [ ] Validate entity references

### Phase 4: Memory
- [ ] Implement `pa remember` command
- [ ] Implement `pa memory show/search`

### Phase 5: Claude Code Integration
- [ ] Document query patterns for Claude Code
- [ ] Test end-to-end: CLI config → Claude Code query → MCP data fetch

---

## Verification

### Manual Testing
1. Add a team, add a person to that team
2. Create calendar-notion mapping
3. Add memory observations
4. In Claude Code: "What do I know about [person]?"
5. Verify Claude Code can read entities + memory + fetch from Notion MCP

### Automated Tests
- Unit tests for Pydantic schema validation
- Integration tests for CLI commands
- Test referential integrity (can't delete team with members)

---

## Resolved Decisions

| Decision | Choice |
|----------|--------|
| CLI Implementation | Python (Typer + Pydantic) |
| File Format | YAML for config/entities, Markdown for memory entries |
| Package Manager | uv |
| Data Location | Project folder (`./data/`) |
| Memory Model | Two-layer: Notion (primary) + Local (interpretive) |
| Claude Code Memory Write | Allowed, tagged with `source: inferred` |
| Memory Merge Strategy | Notion primary, local adds context layer |

## Open Questions (Deferred)

1. Should memory entries support tags for filtering?
2. Do we need an "archive" vs "delete" distinction for entities?
3. Refinement of inferred observation approval workflow
