# Prepare Meeting

**Input:** `entity_id` - person or team ID (e.g., "john-doe", "platform-team")

## Steps

### Step 1: Look Up Entity

1. Read `data/entities/people.yaml` and search for matching `id`
2. If not found, check `data/entities/teams.yaml`
3. If still not found, abort: "Entity not found. Run `pa entity list`."
4. Record entity type: "person" or "team"

### Step 2: Fetch Notion Page

1. If entity has `notion_page` field, use `mcp__notion__notion-fetch` with the page URL/ID
2. If no Notion page configured, skip to Step 4

### Step 2.5: Extract Tasks from Inline Databases

If Notion page was fetched successfully:

1. **Detect inline databases**: Search for `<database>` tags with `inline="true"` attribute, extract `data-source-url` UUID
2. **Filter relevant databases**: Only "Items", "Tasks", "Actions", "Backlog" (skip "Members", "Projects")
3. **Query each database** using `mcp__notion__notion-search`:
   ```
   { "query": "status not started in progress", "data_source_url": "collection://{uuid}" }
   ```
4. **Rank by impact** (impact-dominant scoring):
   ```
   score = (0.15 * status) + (0.60 * impact) + (0.10 * recency) + (0.15 * due_date)

   status:   "In Progress" = 1.0, "Not Started" = 0.7
   impact:   "High"/"Critical" = 1.0, "Medium" = 0.6, "Low" = 0.3, default = 0.1
   recency:  <7 days = 1.0, <30 days = 0.7, older = 0.3
   due_date: Overdue = 1.0, <7 days = 0.8, later = 0.5, none = 0.3
   ```
5. **Select top 5 items by score**

### Step 3: Parse Meetings & Extract Actions

From the Notion page content, extract the last 3-5 meeting sections:

1. Look for date patterns: `<mention-date start="YYYY-MM-DD"/>` or date headers
2. For each meeting section, extract:
   - **Date**: The meeting date
   - **Topics**: Items discussed (bullet points or "Topics" subsection)
   - **Open actions**: `- [ ]` items with assignee if present (`<mention-user>` or `[GP]`)
3. Compile open actions sorted by date (oldest first - these need attention)

### Step 4: Load Local Memory

1. Check for memory directory: `data/memory/{people|teams}/{entity_id}/`
2. Read all `.md` files, extract observations, notes, and inferences with dates

### Step 5: Calculate Confidence Score

```
confidence = 0.0

if notion_page_fetched:         confidence += 0.25
if meetings_found >= 3:         confidence += 0.15
if database_tasks_found:        confidence += 0.15
if last_meeting_within_2_weeks: confidence += 0.20
if open_actions_found:          confidence += 0.10
if memory_entries_found:        confidence += 0.25

confidence = min(1.0, confidence)
```

**Levels:** Low (0-0.4), Medium (0.5-0.7), High (0.8-1.0)

### Step 6: Generate Suggested Topics

Prioritize topics in this order:
1. **High-impact database tasks** that need discussion
2. Open checkbox actions needing follow-up
3. Recurring themes from recent meetings
4. Observations from local memory not yet discussed
5. General check-in (if >2 weeks since last meeting)

## Output

Format (example for `john-doe`):

```markdown
## Meeting Prep: John Doe

**Entity:** john-doe (Senior Engineer)
**Team:** Platform
**Notion:** [John Doe / Georgios](https://notion.so/abc123)

### High-Impact Tasks (3)
*Source: Items*

| Rank | Task | Status | Impact | Due |
|------|------|--------|--------|-----|
| 1 | Finalize API migration plan | In Progress | High | 2026-01-28 |
| 2 | Review security audit findings | Not Started | High | 2026-01-30 |
| 3 | Update team onboarding docs | In Progress | Medium | 2026-02-05 |

### Open Actions (3)
- [ ] Follow up on ML team exploration (2026-01-20)
- [ ] Share RFC draft (2026-01-13)
- [ ] Schedule design review (2026-01-13)

### Recent Meetings (last 3)
- **2026-01-20**: Product team attrition, Appsmith rollout
- **2026-01-13**: RFC review, Transfer ins involvement
- **2025-12-16**: Q1 planning, collaboration with Angie's team

### Local Memory (2 entries)
- **2026-01-15**: Interested in moving to ML team
- **2025-12-01**: Strong debugging skills, helped with incident

### Suggested Topics
1. API migration status and blockers (High Impact)
2. Security audit findings before deadline (High Impact)
3. ML team exploration - any updates?
4. RFC draft and design review scheduling

---
**Confidence:** 0.85 (High)
```

## Errors

| Error | Response |
|-------|----------|
| Entity not found | Abort: "Entity not found. Run `pa entity list`." |
| Notion/database unavailable | Continue without; note in output |
| No memory entries | Show "No local memory" |
| No database tasks | Skip High-Impact Tasks section |

## Tips

- Run 15-30 minutes before the meeting for best context
- If Notion page missing, add via `pa entity update <id> --notion <url>`
- High-impact tasks surface items from inline databases named "Items", "Tasks", "Actions"
