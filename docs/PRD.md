# PRD: Personal Assistant

**Product:** Personal Leadership Assistant

**User:** Single user (you)

**Execution Environment:** Claude Code

**Primary Interfaces:** Chat (Data Plane) + Command-based CLI (Control Plane)

**Integrations:** Google Calendar (read-only via MCP), Notion (read/write with permission via MCP), Local Memory Store

**Status:** MVP Implemented (Phase 1)

---

## 1. Problem Statement

As a senior engineering leader, I spend significant time:

- Preparing for daily 1-1s and leadership meetings by manually scanning historical notes and recalling context.
- Identifying, at a weekly level, the most impactful actions to focus on across people, execution, and organizational health.
- Synthesizing scattered qualitative meeting data into actionable insights (KPIs, risks, top problems).

This process is time-consuming, cognitively expensive, and error-prone.

---

## 2. Goals & Success Metrics

### 2.1 Goals

1. **Reduce preparation time** for meetings through automated context synthesis.
2. **Improve quality of meetings** by surfacing:
    - Open actions
    - Historical commitments
    - Unresolved topics
    - Patterns across time
3. **Enable weekly focus** on the most impactful actions.
4. **Maintain high trust** through:
    - Advisory-only behavior
    - Explicit confidence indicators
    - Full auditability
    - Explicit user permission before any data mutation

### 2.2 Success Metrics

- Time saved per week (self-reported).
- Reduction in "missed" follow-ups.
- Ability to answer at any time:
    - "What are the top problems in the organization right now?"
    - "What should I focus on this week?"

---

## 3. Non-Goals (Explicit)

- No task execution on the user's behalf.
- No automatic commits to Notion.
- No email, Slack, or notification sending.
- No calendar mutations.
- No autonomous scheduling or reminders.

---

## 4. User Personas

- **Primary (Only) User:** Senior Engineering / Product Leader.
- High context switching.
- Strong preference for control, transparency, and correctness.
- Low tolerance for silent automation.

---

## 5. Architecture

### 5.1 Two-Plane Model

The system operates in two distinct modes:

| Plane | Interface | Purpose | Implementation |
|-------|-----------|---------|----------------|
| **Control Plane** | CLI (`pa` command) | Configuration, entity management, explicit memory writes | Python (Typer + Pydantic) |
| **Data Plane** | Claude Code chat | Querying, context synthesis, natural language interaction | Claude Code + MCP tools |

### 5.2 Memory Architecture

**Two-Layer Memory Model:**
1. **Notion (Primary)**: Company source of truth for meeting notes, decisions, actions
2. **Local Memory (Interpretive)**: Personal observations and context about entities

**Memory Hierarchy:**
- Notion content is the source of truth
- Local memory provides personal interpretation layer on top
- Local observations can annotate but not override Notion facts

**Write Permissions:**
- **Notion**: Read-only from Data Plane; writes via CLI with explicit approval
- **Local Memory**: Claude Code can write, all entries tagged with `source`:
  - `source: "user"` - Explicitly added via CLI
  - `source: "inferred"` - Added by Claude during conversation

---

## 6. Data Model

### 6.1 Storage Format

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

### 6.2 Entity Schemas

**Person** (`entities/people.yaml`)
```yaml
- id: john-doe
  name: John Doe
  role: Senior Engineer
  team_id: platform-team
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
- id: platform-team
  name: Platform Team
  team_type: engineering
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
on machine learning fundamentals.
```

---

## 7. CLI Commands (Control Plane)

### 7.1 Entity Management

```bash
# Add entities
pa entity add team --name "Platform Team" --type engineering
pa entity add person --name "John Doe" --team platform-team --role "Senior Engineer"

# List and show
pa entity list [people|teams]
pa entity show <id>

# Update
pa entity update <id> --name "..." --role "..." --add-tag "..." --remove-tag "..."

# Delete (with referential integrity)
pa entity delete <id>
```

### 7.2 Calendar-Notion Mappings

```bash
pa map add --calendar-pattern "1:1 with John" --entity john-doe --notion <page>
pa map list
pa map delete <id>
```

### 7.3 Memory/Observations

```bash
pa remember <entity-id> "Observation text" --context "1:1 meeting" --type observation
pa memory show <entity-id>
pa memory search "keyword"
```

### 7.4 Configuration

```bash
pa config set <key> <value>
pa config show
```

---

## 8. Data Plane (Claude Code)

### 8.1 How Claude Code Accesses Data

1. Read YAML files from `./data/` directory
2. Use MCP tools for Google Calendar and Notion
3. Synthesize context by combining stored entities + live data

### 8.2 Query Patterns

- "What do I know about John?" → Read person entity + memory entries
- "Who is on the Platform team?" → Read team + filter people by team_id
- "What meetings do I have with John this week?" → Entity calendar_patterns + Google Calendar MCP
- "Show me John's Notion page" → Entity notion_page + Notion MCP

### 8.3 Future Commands (Phase 2+)

| Command | Phase | Description |
|---------|-------|-------------|
| `prepare day` | 2 | Daily meeting preparation with context synthesis |
| `prepare meeting --entity <id>` | 2 | Single meeting preparation |
| `weekly review` | 2 | Weekly retrospective |
| `weekly focus` | 2 | Weekly priority identification |
| `ingest transcript` | 3 | Process meeting transcripts |
| `suggest notion update` | 3 | Propose Notion edits from transcripts |

---

## 9. Phased Implementation

### Phase 1: Foundation (MVP) ✅

- [x] Entity management (people, teams with relationships)
- [x] Calendar-Notion mappings
- [x] Memory/observations storage and search
- [x] Natural language query via Claude Code
- [x] Pydantic validation with referential integrity

### Phase 2: Daily Operations

- [ ] `prepare day` command
- [ ] `prepare meeting` command
- [ ] Weekly review and focus
- [ ] Confidence scoring for outputs

### Phase 3: Transcript Processing

- [ ] Transcript ingestion
- [ ] Notion update suggestions
- [ ] Delta detection vs existing notes

### Phase 4: Advanced Features

- [ ] Approval workflow for inferred observations
- [ ] Pattern detection across meetings
- [ ] KPI derivation

---

## 10. Integrations

### 10.1 Notion (via MCP)

**Assumptions:**
- Meetings have date-separated pages
- Action items may be structured (DB), semi-structured (headers), or free text

**Requirements:**
- Read existing content
- Detect structure dynamically
- Propose edits, never auto-commit
- Maintain "Assistant Suggestions" section (optional)

### 10.2 Google Calendar (via MCP)

**Capabilities:**
- Read-only access
- Event metadata: title, attendees, time, description

**Meeting Classification:**
- Via calendar_patterns in entity definitions
- Entity (Person / Group) → Calendar title → Linked Notion page

---

## 11. Auditability & Trust

Every output must support:

- "Why am I seeing this?"
- "What data was used?"
- "What assumptions were made?"

### Confidence Scoring (Phase 2+)

Required for:
- Inferences
- Summaries
- Risk flags

---

## 12. Permissions Model

| Action | Requires Permission |
|--------|---------------------|
| Read Notion | Yes (MCP configured) |
| Suggest Notion edits | Yes |
| Commit Notion edits | Explicit approval |
| Append transcript insights | Explicit approval |
| Memory writes (user) | Implicit via CLI |
| Memory writes (inferred) | Logged with source tag |

---

## 13. Technical Implementation

### 13.1 Technology Stack

| Component | Technology |
|-----------|------------|
| Package Manager | uv |
| CLI Framework | Typer |
| Validation | Pydantic v2 |
| Output Formatting | Rich |
| Data Format | YAML (entities), Markdown (memory) |
| MCP Integrations | Google Calendar, Notion |

### 13.2 Key Design Decisions

| Decision | Choice | Rationale |
|----------|--------|-----------|
| CLI Implementation | Python (Typer + Pydantic) | Type validation, referential integrity, extensible |
| File Format | YAML + Markdown | Human-readable, editable, Claude-friendly |
| Data Location | Project folder (`./data/`) | Simple, version-controllable |
| Memory Model | Two-layer (Notion primary, local interpretive) | Maintains source of truth while adding context |

---

## 14. Acceptance Criteria

### Phase 1 (MVP) ✅

- [x] Can add teams and people with relationship validation
- [x] Can create calendar-notion mappings linked to entities
- [x] Can store and search memory observations
- [x] Claude Code can read entities and answer "What do I know about X?"
- [x] Referential integrity enforced (can't delete team with members)

### Phase 2

- [ ] Can prepare a day with multiple meetings using only commands
- [ ] Can generate a weekly focus list grounded in real data
- [ ] Provides confidence indicators for all non-trivial outputs

### Phase 3

- [ ] Can ingest a transcript and produce a diff-like Notion proposal
- [ ] Never mutates external systems without approval
