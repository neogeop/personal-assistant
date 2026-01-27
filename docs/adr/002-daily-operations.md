# Daily Operations (Phase 2)

## Overview

Phase 2 extends the Personal Leadership Assistant with daily operational workflows:
- **Meeting Preparation**: Context synthesis before meetings
- **Daily Brief**: Aggregated prep for all today's meetings
- **Weekly Review**: Retrospective analysis and focus recommendations

## What Phase 2 Delivers

1. `/prepare meeting <entity-id>` - Single meeting context preparation
2. `/prepare day` - Daily brief for all meetings
3. `/weekly review` - Weekly retrospective and focus areas
4. **Confidence Scoring** - Trust indicators for all outputs

## What Phase 2 Defers

- Automated scheduling/triggers (manual invocation only)
- Transcript ingestion (Phase 3)
- Push notifications/reminders
- Cross-week trend analysis

---

## Architecture Decision: Execution Model

### Options Considered

#### Option A: Python CLI Commands
**Pros:**
- Consistent with Phase 1 implementation
- Testable, type-safe
- Works offline

**Cons:**
- Would need to implement MCP client in Python
- Duplicates Claude Code's synthesis capabilities
- More code to maintain

#### Option B: Claude Code Custom Skills
**Pros:**
- Leverages Claude Code's natural language synthesis
- Direct access to MCP tools (Calendar, Notion)
- Instruction-based, easy to iterate
- No additional code to write

**Cons:**
- Less testable than Python code
- Depends on Claude Code session
- Skill instructions stored in data directory

### Decision: Claude Code Custom Skills

Skills are implemented as markdown instruction files in `data/skills/`. Claude Code reads these instructions and executes the workflow using available tools (file reads, MCP).

**Rationale:**
- Meeting preparation is fundamentally a synthesis task (Claude Code's strength)
- MCP integration is already available in Claude Code
- Instruction files allow rapid iteration without code changes
- Keeps Control Plane (CLI) focused on data management

---

## Skill Implementation

### Skill Registration

Skills are registered in `CLAUDE.md`:

```markdown
## Custom Skills

### /prepare meeting <entity-id>
Prepare context for a meeting with a specific person or team.
Skill file: data/skills/prepare-meeting.md

### /prepare day
Prepare context for all meetings today.
Skill file: data/skills/prepare-day.md

### /weekly review
Review the past week and identify focus areas.
Skill file: data/skills/weekly-review.md
```

### Skill File Structure

Each skill file (`data/skills/*.md`) contains:
1. **Input**: Expected arguments
2. **Instructions**: Step-by-step workflow
3. **Output Format**: Template for results
4. **Error Handling**: How to handle failures
5. **Example**: Sample output

---

## Data Flow

### `/prepare meeting` Flow

```
User invokes: /prepare meeting john-doe
       │
       ▼
┌─────────────────────────────────────┐
│ 1. Read data/entities/people.yaml   │
│    Find entity by ID                │
└─────────────────────────────────────┘
       │
       ▼
┌─────────────────────────────────────┐
│ 2. Google Calendar MCP              │
│    Find next meeting via patterns   │
└─────────────────────────────────────┘
       │
       ▼
┌─────────────────────────────────────┐
│ 3. Notion MCP                       │
│    Fetch entity's notion_page       │
│    Parse meeting sections           │
│    Extract open actions             │
└─────────────────────────────────────┘
       │
       ▼
┌─────────────────────────────────────┐
│ 4. Read data/memory/people/{id}/    │
│    Load local observations          │
└─────────────────────────────────────┘
       │
       ▼
┌─────────────────────────────────────┐
│ 5. Calculate confidence score       │
│ 6. Generate suggested topics        │
│ 7. Format output                    │
└─────────────────────────────────────┘
       │
       ▼
     Output
```

### `/prepare day` Flow

```
User invokes: /prepare day
       │
       ▼
┌─────────────────────────────────────┐
│ 1. Google Calendar MCP              │
│    Fetch today's events             │
└─────────────────────────────────────┘
       │
       ▼
┌─────────────────────────────────────┐
│ 2. Load all entities                │
│    Build calendar_patterns lookup   │
└─────────────────────────────────────┘
       │
       ▼
┌─────────────────────────────────────┐
│ 3. Match events to entities         │
│    via pattern matching             │
└─────────────────────────────────────┘
       │
       ▼
┌─────────────────────────────────────┐
│ 4. For each matched event:          │
│    Run prepare-meeting workflow     │
└─────────────────────────────────────┘
       │
       ▼
┌─────────────────────────────────────┐
│ 5. Aggregate into daily brief       │
│    Include unmatched events         │
└─────────────────────────────────────┘
       │
       ▼
     Output
```

---

## Notion Parsing Strategy

### Observed Patterns

Analysis of existing Notion pages revealed two structural patterns:

**Pattern A: Group/Team Meetings**
- Toggle headers with `<mention-date start="YYYY-MM-DD"/>`
- Subsections: "Actions from previous", "Topics to discuss", "Actions"
- Checkboxes with assignees via `<mention-user>` tags

**Pattern B: 1:1 Meetings**
- Date headers as H2/H3 with `<mention-date>`
- Subsections: "Topics:", "Actions:"
- Owner prefixes: `[KK]`, `[GP]`

### Parsing Approach

Rather than implementing rigid parsers, we use heuristic extraction:

1. **Date Detection**: Look for `<mention-date start="YYYY-MM-DD"/>` or date-formatted headers
2. **Action Extraction**: Find `- [ ]` (open) and `- [x]` (complete) patterns
3. **Section Grouping**: Associate content with nearest date marker
4. **Recency Filter**: Only process last 3-5 meeting sections

This approach handles both patterns without pattern-specific code.

---

## Confidence Scoring

### Scoring Model

Confidence reflects data availability and recency:

| Factor | Points | Description |
|--------|--------|-------------|
| Notion page configured | +0.1 | Entity has `notion_page` set |
| Notion page fetched | +0.1 | Successfully retrieved content |
| Recent meetings (< 2 weeks) | +0.2 | Last meeting section is recent |
| Meetings found (3+) | +0.2 | Sufficient historical context |
| Open actions found | +0.1 | Actionable items identified |
| Local memory present | +0.2 | Personal observations exist |
| Calendar match found | +0.1 | Upcoming meeting confirmed |

**Total possible: 1.0**

### Display Thresholds

| Range | Label | Meaning |
|-------|-------|---------|
| 0.0 - 0.4 | Low | Limited data, proceed with caution |
| 0.5 - 0.7 | Medium | Reasonable context, some gaps |
| 0.8 - 1.0 | High | Comprehensive data available |

### Presentation

```markdown
**Confidence:** 0.85 (High)
- Notion: Page fetched, 3 recent meetings
- Recent meetings: Last meeting 7 days ago
- Local memory: 2 observations
- Calendar: Next meeting found today
```

---

## Calendar-Entity Matching

### Pattern Matching Logic

Entities define `calendar_patterns` for matching:

```yaml
# entities/people.yaml
- id: john-doe
  name: John Doe
  calendar_patterns:
    - "1:1 John"
    - "John Doe"
    - "Weekly John"
```

Matching rules:
1. Case-insensitive substring match
2. Pattern "1:1 John" matches event "1:1 John Doe - Weekly Sync"
3. First matching entity wins (patterns should be specific)

### Unmatched Events

Events without entity matches are still shown in `/prepare day`:
- Marked as "Unmatched"
- Suggests creating entity or mapping
- Preserves visibility of all meetings

---

## File Structure

```
data/
├── skills/
│   ├── prepare-meeting.md   # Meeting prep instructions
│   ├── prepare-day.md       # Daily brief instructions
│   └── weekly-review.md     # Weekly review instructions
├── entities/
│   ├── people.yaml          # (existing)
│   └── teams.yaml           # (existing)
├── memory/
│   └── ...                  # (existing)
└── mappings/
    └── ...                  # (existing)

CLAUDE.md                    # Skill registration + project docs
```

---

## Implementation Phases

### Phase 2a: `/prepare meeting` (Complete)
- [x] Create `CLAUDE.md` with skill definitions
- [x] Create `data/skills/prepare-meeting.md`
- [x] Define output format template
- [x] Define confidence scoring rules

### Phase 2b: `/prepare day` (Complete)
- [x] Create `data/skills/prepare-day.md`
- [x] Define calendar event matching logic
- [x] Define aggregated output format

### Phase 2c: `/weekly review` (Complete)
- [x] Create `data/skills/weekly-review.md`
- [x] Define action tracking format
- [x] Define focus recommendations structure

---

## Verification

### Testing `/prepare meeting`

1. Create a test entity with `notion_page` configured:
   ```bash
   pa entity add person --name "Test Person" --notion-page "https://notion.so/..."
   ```

2. Add some memory observations:
   ```bash
   pa remember test-person "Test observation for verification"
   ```

3. Run the skill:
   ```
   /prepare meeting test-person
   ```

4. Verify output includes:
   - Entity details
   - Notion content (if MCP connected)
   - Local memory entries
   - Confidence score

### Testing `/prepare day`

1. Ensure entities have `calendar_patterns` matching today's events
2. Run `/prepare day`
3. Verify:
   - All calendar events listed
   - Matched events have full context
   - Unmatched events are flagged

### Testing `/weekly review`

1. Run on a day with historical data
2. Verify:
   - Meeting summary table
   - Action tracking (created/completed)
   - Focus recommendations generated

---

## Resolved Decisions

| Decision | Choice |
|----------|--------|
| Execution model | Claude Code custom skills |
| Skill storage | `data/skills/*.md` instruction files |
| Confidence scoring | Weighted factors (0.0-1.0 scale) |
| Calendar matching | Case-insensitive substring matching |
| Notion parsing | Heuristic extraction (not rigid parsers) |
| Output format | Markdown with structured sections |

## Open Questions (Deferred)

1. Should confidence thresholds be configurable?
2. Add caching for Notion content to reduce API calls?
3. Support for recurring meeting templates?
4. Integration with task management systems?
