# Skill: Prepare Day

Prepare context for all meetings scheduled today.

## Input

No input required. Uses today's date automatically.

## Instructions

Follow these steps in order:

### Step 1: Get Today's Date

1. Note today's date in YYYY-MM-DD format
2. This will be used to filter calendar events

### Step 2: Fetch Today's Calendar Events

1. Use Google Calendar MCP to list today's events:
   - Use `mcp__google__list-events` with today's date range
2. For each event, extract:
   - Event title
   - Start time
   - End time
   - Attendees (if available)
3. Sort events by start time

### Step 3: Load Entity Data

1. Read `data/entities/people.yaml` to get all people
2. Read `data/entities/teams.yaml` to get all teams
3. Build a lookup map of `calendar_patterns` to entities

### Step 4: Match Events to Entities

For each calendar event:

1. Check if the event title matches any entity's `calendar_patterns`
2. Matching logic:
   - Case-insensitive substring match
   - Pattern "1:1 John" matches event "1:1 John Doe - Weekly"
   - Pattern "Platform Standup" matches event "Platform Team Standup"
3. If matched, link the event to the entity
4. If no match, mark as "Unmatched" (still show in output)

### Step 5: Prepare Each Matched Meeting

For each matched event, run the prepare-meeting logic:

1. Look up the entity details
2. Fetch Notion page (if configured)
3. Parse recent meeting sections
4. Extract open actions
5. Load local memory
6. Calculate confidence score

**Optimization:** Batch Notion fetches where possible to reduce API calls.

### Step 6: Aggregate Results

Compile all meeting preparations into a daily brief:

1. Group by time (chronological order)
2. Include both matched and unmatched events
3. For matched events, include full context
4. For unmatched events, just show event details

### Step 7: Calculate Overall Stats

Compile summary statistics:

1. Total meetings today
2. Matched vs unmatched events
3. Total open actions across all entities
4. Average confidence score

## Output Format

```markdown
## Today's Meetings ({date})

**Summary:** {total_count} meetings | {matched_count} with context | {action_count} open actions

---

### {time} - {event_title}
**Entity:** {entity_id} ({role_or_type}) OR *Unmatched*
**Notion:** [{page_title}]({url}) OR Not configured
**Duration:** {duration}

**Open Actions ({count}):**
- [ ] {action_text} (from {date})
- [ ] {action_text} (from {date})

**Recent Context:**
- Last meeting: {date} - {brief_summary}
- Key observation: {memory_highlight}

**Suggested Topics:**
- {topic_1}
- {topic_2}

**Confidence:** {score} ({level})

---

### {time} - {event_title}
*No matching entity found*
**Attendees:** {attendee_list}
**Duration:** {duration}

> Consider creating an entity or mapping for this recurring meeting.

---

... (repeat for each meeting)

---

## Day Overview

| Time | Meeting | Entity | Actions | Confidence |
|------|---------|--------|---------|------------|
| 9:00 | 1:1 John Doe | john-doe | 3 | High |
| 10:30 | Platform Standup | platform-team | 1 | Medium |
| 14:00 | External Call | *unmatched* | - | - |

**Focus Areas for Today:**
1. {highest_priority_action_or_topic}
2. {second_priority}
3. {third_priority}
```

## Error Handling

| Error | Response |
|-------|----------|
| Calendar MCP unavailable | "Unable to fetch calendar. Please check Google Calendar MCP connection." |
| No events today | "No meetings scheduled for today." |
| Entity file missing | Continue with available data, note missing file |
| Notion fetch failed for entity | Show entity without Notion context, reduce confidence |

## Tips for Matching

If events frequently show as "Unmatched":

1. Add `calendar_patterns` to entities:
   ```bash
   pa entity update john-doe --calendar-pattern "1:1 John"
   pa entity update platform-team --calendar-pattern "Platform Standup"
   ```

2. Create mappings for complex patterns:
   ```bash
   pa map add --pattern "Weekly Sync" --entity platform-team --type team
   ```

## Example

Input: `/prepare day`

Output:
```markdown
## Today's Meetings (2026-01-27)

**Summary:** 4 meetings | 3 with context | 5 open actions

---

### 9:00 AM - 1:1 John Doe
**Entity:** john-doe (Senior Engineer, Platform Team)
**Notion:** [John Doe / Georgios](https://notion.so/abc)
**Duration:** 30 min

**Open Actions (2):**
- [ ] Follow up on ML team exploration (from 2026-01-20)
- [ ] Share RFC draft (from 2026-01-13)

**Recent Context:**
- Last meeting: 2026-01-20 - Discussed product team changes, Appsmith rollout
- Key observation: Interested in ML team transition

**Suggested Topics:**
- ML team exploration follow-up
- RFC draft status check

**Confidence:** 0.85 (High)

---

### 10:30 AM - Platform Team Standup
**Entity:** platform-team (Engineering Team)
**Notion:** [Platform Team](https://notion.so/def)
**Duration:** 15 min

**Open Actions (1):**
- [ ] Complete Q1 roadmap review (from 2026-01-22)

**Recent Context:**
- Last meeting: 2026-01-24 - Sprint review, blockers discussion

**Suggested Topics:**
- Q1 roadmap review status

**Confidence:** 0.70 (Medium)

---

### 12:00 PM - Lunch with Alex
*No matching entity found*
**Duration:** 60 min

> Consider running: `pa entity add person --name "Alex"` if this is a recurring meeting.

---

### 14:00 PM - Engineering Group Leads
**Entity:** eng-group-leads (Leadership Team)
**Notion:** [Engineering Group Leads](https://notion.so/ghi)
**Duration:** 60 min

**Open Actions (2):**
- [ ] Review hiring pipeline (from 2026-01-20)
- [ ] Finalize Q1 OKRs (from 2026-01-13)

**Recent Context:**
- Last meeting: 2026-01-20 - Hiring updates, team capacity planning

**Suggested Topics:**
- Hiring pipeline review
- Q1 OKR finalization

**Confidence:** 0.80 (High)

---

## Day Overview

| Time | Meeting | Entity | Actions | Confidence |
|------|---------|--------|---------|------------|
| 9:00 | 1:1 John Doe | john-doe | 2 | High |
| 10:30 | Platform Standup | platform-team | 1 | Medium |
| 12:00 | Lunch with Alex | *unmatched* | - | - |
| 14:00 | Eng Group Leads | eng-group-leads | 2 | High |

**Focus Areas for Today:**
1. RFC draft and ML team discussion with John
2. Q1 roadmap and OKR finalization at leadership meeting
3. Create entity for Alex if recurring
```
