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

### Step 2: Check Calendar for Next Meeting

1. Use the Google Calendar MCP tool to list today's events
2. For each event, check if the title matches any of the entity's `calendar_patterns`
3. If a match is found, record the meeting time
4. If no calendar match, note "No upcoming meeting found in calendar"

### Step 3: Fetch Notion Page

1. Check if the entity has a `notion_page` field set
2. If yes, use the Notion MCP tool to fetch the page content:
   - Use `mcp__notion__notion-fetch` with the page URL/ID
3. If no Notion page is set, skip to Step 6

### Step 4: Parse Meeting Sections

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

### Step 5: Extract Open Actions

From the parsed meetings, compile a list of all open actions:

1. Collect all `- [ ]` items from the last 3-5 meetings
2. Include the date when each action was created
3. Include the assignee if identifiable
4. Sort by date (oldest first, as these need attention)

### Step 6: Load Local Memory

1. Check if memory directory exists: `data/memory/people/{entity_id}/` or `data/memory/teams/{entity_id}/`
2. Read all `.md` files in the directory
3. Extract key observations, notes, and inferences
4. Note the dates of each memory entry

### Step 7: Calculate Confidence Score

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

# Calendar
if calendar_match_found:
    confidence += 0.1
```

**Confidence levels:**
- 0.0-0.4: Low
- 0.5-0.7: Medium
- 0.8-1.0: High

### Step 8: Generate Suggested Topics

Based on the collected context, suggest topics for the meeting:

1. Start with open actions that need follow-up
2. Add any recurring themes from recent meetings
3. Include observations from local memory that haven't been discussed
4. If it's been a while since the last meeting, suggest a general check-in

## Output Format

```markdown
## Meeting Prep: {entity_name}

**Entity:** {entity_id} ({role_or_type})
**Team:** {team_name} (if applicable)
**Next meeting:** {time} (from calendar) OR No upcoming meeting found
**Notion:** [{page_title}]({notion_url}) OR Not configured

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
- Calendar: {status}
```

## Error Handling

| Error | Response |
|-------|----------|
| Entity not found | "Entity '{entity_id}' not found. Use `pa entity list` to see available entities." |
| Notion fetch failed | Continue without Notion data, note in output, reduce confidence |
| No Notion page configured | Skip Notion steps, note "Notion page not configured" |
| No memory entries | Show "No local memory entries" |
| Calendar MCP unavailable | Skip calendar check, note in output |

## Example

Input: `/prepare meeting john-doe`

Output:
```markdown
## Meeting Prep: John Doe

**Entity:** john-doe (Senior Engineer)
**Team:** Platform
**Next meeting:** Today 10:00 AM
**Notion:** [John Doe / Georgios](https://notion.so/abc123)

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
1. Follow up on ML team exploration - any updates?
2. Check status of RFC draft and design review scheduling
3. Discuss current project priorities

---

**Confidence:** 0.85 (High)
- Notion: Page fetched, 3 recent meetings
- Recent meetings: Last meeting 7 days ago
- Local memory: 2 observations
- Calendar: Next meeting found today
```
