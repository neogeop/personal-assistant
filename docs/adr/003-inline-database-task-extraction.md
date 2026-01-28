# ADR 003: Inline Notion Database Task Extraction for Meeting Preparation

## Status

Accepted

## Context

The prepare-meeting skill currently parses meeting notes for checkbox-format actions (`- [ ]`) but ignores inline databases that contain structured task data. Many Notion pages for teams and individuals include inline databases (named "Items", "Tasks", "Actions", etc.) with rich metadata including:

- **Status**: In Progress, Not Started, Done, etc.
- **Impact**: High, Medium, Low, Critical
- **Due Date**: When the task is due
- **Created Date**: When the task was created

When a Notion page contains an inline database, it appears in the fetched content as:
```
<database url="..." inline="true" data-source-url="{{collection://UUID}}">Items</database>
```

This structured data is currently ignored, resulting in incomplete meeting preparation when important tasks exist only in these databases rather than as checkbox items.

## Decision

Enhance the prepare-meeting skill to:

1. **Detect inline databases** in fetched Notion pages by searching for `<database>` tags with `inline="true"` attribute
2. **Filter relevant databases** by name, processing only task-related databases: "Items", "Tasks", "Actions", "Backlog"
3. **Query databases** using `mcp__notion__notion-search` with the extracted `data_source_url`
4. **Rank items by impact** using an impact-dominant scoring formula
5. **Display top 5 items** in a new output section

### Ranking Formula

Tasks are scored using an impact-dominant formula:

```
score = (0.15 * status_score) + (0.60 * impact_score) + (0.10 * recency_score) + (0.15 * due_date_score)
```

| Factor | Value | Score |
|--------|-------|-------|
| Status | In Progress | 1.0 |
| Status | Not Started | 0.7 |
| Impact | High/Critical | 1.0 |
| Impact | Medium | 0.6 |
| Impact | Low | 0.3 |
| Impact | Not set | 0.1 |
| Recency | Created <7 days | 1.0 |
| Recency | Created <30 days | 0.7 |
| Recency | Older | 0.3 |
| Due Date | Overdue | 1.0 |
| Due Date | Due <7 days | 0.8 |
| Due Date | Due later | 0.5 |
| Due Date | No date | 0.3 |

The 60% weight on impact ensures high-impact items surface regardless of other factors.

### Status Filter

Only items with these statuses are included:
- "In Progress"
- "Not Started"

Items marked as "Done", "Cancelled", or similar are excluded.

### Database Name Filter

Only process databases with task-related names:
- Items
- Tasks
- Actions
- Backlog

Skip reference databases like:
- Members
- Projects
- Resources

## Consequences

### Positive

- **More comprehensive meeting prep**: Structured task data supplements checkbox-based action items
- **Impact-based ranking**: High-priority items surface first, improving meeting focus
- **Better decision support**: Due dates and status provide context for prioritization discussions
- **Graceful degradation**: If database query fails, skill continues with existing functionality

### Negative

- **Additional MCP calls**: One extra call per inline database may increase latency
- **Naming convention dependency**: Relies on consistent database naming ("Items", "Tasks", etc.)
- **Query limitations**: `mcp__notion__notion-search` may not support complex status filtering directly

### Neutral

- **Confidence scoring updated**: New factors add up to 0.18 points, normalized to max 1.0
- **Suggested topics prioritized**: High-impact database tasks appear first in suggestions

## Implementation

Changes made to `data/skills/prepare-meeting.md`:

1. **New Step 3.5**: Extract Tasks from Inline Databases (after fetching Notion page)
2. **Updated Output Format**: New "High-Impact Database Tasks" section with table format
3. **Updated Confidence Scoring**: Added factors for database detection and task extraction
4. **Updated Suggested Topics**: Prioritize high-impact database tasks first
5. **Updated Error Handling**: Added cases for database query failures

## Verification

1. Run `/prepare-meeting` for an entity with an inline database
2. Verify the database is detected in the Notion page content
3. Confirm the database is queried via MCP
4. Check that high-impact tasks appear in the new section
5. Verify ranking order reflects the impact-dominant scoring formula
6. Confirm suggested topics include high-impact tasks first
