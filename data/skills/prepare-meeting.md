# Skill: Prepare Meeting

Prepare context for a meeting with a specific person or team.

## Input

- `entity_id`: The ID of the person or team (e.g., "john-doe", "platform-team")

## Instructions

Follow these steps in order:

### Step 1: Look Up Entity

1. Read `data/entities/people.yaml` and search for an entity with matching `id`
2. If not found in people, read `data/entities/teams.yaml` and search there
3. If still not found, report error: "Entity '{entity_id}' not found"
4. Record entity type: "person" or "team"

### Step 2: Fetch Notion Page

1. Check if the entity has a `notion_page` field set
2. If yes, use the Notion MCP tool to fetch the page content:
   - Use `mcp__notion__notion-fetch` with the page URL/ID
3. If no Notion page is set, skip to Step 5

### Step 2.5: Extract Tasks from Inline Databases

If Notion page was fetched successfully:

1. **Detect inline databases**:
   - Search for `<database>` tags with `inline="true"` attribute
   - Extract the `data-source-url` collection UUID (format: `collection://UUID`)
   - Note the database name from the tag content

2. **Filter relevant databases**:
   - Only process databases with task-related names: "Items", "Tasks", "Actions", "Backlog"
   - Skip reference databases (e.g., "Members", "Projects")

3. **Query each relevant database**:
   - Use `mcp__notion__notion-search` with `data_source_url` parameter:
     ```
     {
       "query": "status not started in progress",
       "data_source_url": "collection://{uuid}"
     }
     ```

4. **Parse and rank items by impact** (impact-dominant scoring):
   ```
   score = (0.15 * status_score) + (0.60 * impact_score) + (0.10 * recency_score) + (0.15 * due_date_score)

   status_score:   "In Progress" = 1.0, "Not Started" = 0.7
   impact_score:   "High"/"Critical" = 1.0, "Medium" = 0.6, "Low" = 0.3, default = 0.1
   recency_score:  Created <7 days = 1.0, <30 days = 0.7, older = 0.3
   due_date_score: Overdue = 1.0, Due <7 days = 0.8, Due later = 0.5, No date = 0.3
   ```

5. **Select top 5 items by score**

### Step 3: Parse Meeting Sections

From the Notion page content, extract the last 3-5 meeting sections:

1. Look for date patterns: `<mention-date start="YYYY-MM-DD"/>` or date headers
2. For each meeting section found, extract:
   - **Date**: The meeting date
   - **Topics**: Items discussed (look for "Topics" subsection or bullet points)
   - **Actions**: Action items with their status

**Parsing rules:**
- `- [ ]` = Open action item
- `- [x]` = Completed action item
- Look for assignee patterns like `<mention-user>` or prefixes like `[GP]`, `[KK]`
- Extract the last 3-5 meetings (most recent first)

### Step 4: Extract Open Actions

From the parsed meetings, compile a list of all open actions:

1. Collect all `- [ ]` items from the last 3-5 meetings
2. Include the date when each action was created
3. Include the assignee if identifiable
4. Sort by date (oldest first, as these need attention)

### Step 5: Load Local Memory

1. Check if memory directory exists: `data/memory/people/{entity_id}/` or `data/memory/teams/{entity_id}/`
2. Read all `.md` files in the directory
3. Extract key observations, notes, and inferences
4. Note the dates of each memory entry

### Step 6: Calculate Confidence Score

Calculate confidence based on available data:

```
confidence = 0.0

# Notion data
if notion_page_set:
    confidence += 0.1
if notion_page_fetched_successfully:
    confidence += 0.1
if meetings_found >= 3:
    confidence += 0.2
elif meetings_found >= 1:
    confidence += 0.1

# Inline database tasks
if inline_database_found:
    confidence += 0.05
if database_tasks_extracted:
    confidence += 0.08
if high_impact_tasks_found:
    confidence += 0.05

# Recency
if last_meeting_within_2_weeks:
    confidence += 0.2
elif last_meeting_within_4_weeks:
    confidence += 0.1

# Actions
if open_actions_found:
    confidence += 0.1

# Local memory
if memory_entries_found:
    confidence += 0.2

# Normalize to max 1.0
confidence = min(1.0, confidence)
```

**Confidence levels:**
- 0.0-0.4: Low
- 0.5-0.7: Medium
- 0.8-1.0: High

### Step 7: Generate Suggested Topics

Based on the collected context, suggest topics for the meeting:

1. Start with **high-impact database tasks** that need discussion (highest priority)
2. Follow with open checkbox actions that need follow-up
3. Add any recurring themes from recent meetings
4. Include observations from local memory that haven't been discussed
5. If it's been a while since the last meeting, suggest a general check-in

## Output Format

```markdown
## Meeting Prep: {entity_name}

**Entity:** {entity_id} ({role_or_type})
**Team:** {team_name} (if applicable)
**Notion:** [{page_title}]({notion_url}) OR Not configured

### High-Impact Database Tasks ({count})
*Source: {database_name}*

| Rank | Task | Status | Impact | Due |
|------|------|--------|--------|-----|
| 1 | {task_title} | {status} | {impact} | {due_date} |
| 2 | {task_title} | {status} | {impact} | {due_date} |
...

> Items ranked by impact. Showing "In Progress" and "Not Started" tasks.

### Open Actions ({count})
- [ ] {action_text} (from {date})
- [ ] {action_text} (from {date})
...

### Recent Meetings (last {n})
- **{date}**: {brief_topic_summary}
- **{date}**: {brief_topic_summary}
...

### Local Memory ({count} entries)
- **{date}**: {observation_summary}
- **{date}**: {observation_summary}
...

### Suggested Topics
1. {topic_suggestion}
2. {topic_suggestion}
3. {topic_suggestion}

---

**Confidence:** {score} ({level})
- Notion: {status}
- Recent meetings: {count} found
- Local memory: {count} entries
```

## Error Handling

| Error | Response |
|-------|----------|
| Entity not found | "Entity '{entity_id}' not found. Use `pa entity list` to see available entities." |
| Notion fetch failed | Continue without Notion data, note in output, reduce confidence |
| No Notion page configured | Skip Notion steps, note "Notion page not configured" |
| Inline database query failed | Continue without database tasks, note in output |
| No relevant databases found | Skip High-Impact Database Tasks section |
| Database has no matching items | Note "No open tasks in {database_name}" |
| No memory entries | Show "No local memory entries" |

## Example

Input: `/prepare meeting john-doe`

Output:
```markdown
## Meeting Prep: John Doe

**Entity:** john-doe (Senior Engineer)
**Team:** Platform
**Notion:** [John Doe / Georgios](https://notion.so/abc123)

### High-Impact Database Tasks (3)
*Source: Items*

| Rank | Task | Status | Impact | Due |
|------|------|--------|--------|-----|
| 1 | Finalize API migration plan | In Progress | High | 2026-01-28 |
| 2 | Review security audit findings | Not Started | High | 2026-01-30 |
| 3 | Update team onboarding docs | In Progress | Medium | 2026-02-05 |

> Items ranked by impact. Showing "In Progress" and "Not Started" tasks.

### Open Actions (3)
- [ ] Follow up on ML team exploration (from 2026-01-20)
- [ ] Share RFC draft (from 2026-01-13)
- [ ] Schedule design review (from 2026-01-13)

### Recent Meetings (last 3)
- **2026-01-20**: Product team attrition, Appsmith rollout discussion
- **2026-01-13**: RFC review, Transfer ins involvement
- **2025-12-16**: Q1 planning, collaboration with Angie's team

### Local Memory (2 entries)
- **2026-01-15**: Expressed interest in moving to ML team
- **2025-12-01**: Strong debugging skills, helped with production incident

### Suggested Topics
1. Discuss API migration plan status and blockers (High Impact)
2. Review security audit findings before deadline (High Impact)
3. Follow up on ML team exploration - any updates?
4. Check status of RFC draft and design review scheduling

---

**Confidence:** 0.85 (High)
- Notion: Page fetched, 3 recent meetings
- Database tasks: 3 high-impact items from "Items"
- Recent meetings: Last meeting 7 days ago
- Local memory: 2 observations
```
