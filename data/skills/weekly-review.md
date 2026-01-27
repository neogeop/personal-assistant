# Skill: Weekly Review

Review the past week and identify focus areas for next week.

## Input

No input required. Automatically uses the current week (Monday to Sunday).

## Instructions

Follow these steps in order:

### Step 1: Determine Week Range

1. Calculate this week's date range:
   - Start: Most recent Monday (or today if Monday)
   - End: Today's date
2. Also calculate last week if reviewing on Monday

### Step 2: Fetch Week's Calendar Events

1. Use Google Calendar MCP to list events for the week:
   - Use `mcp__google__list-events` with the week's date range
2. For each event, extract:
   - Event title
   - Date
   - Attendees
3. Group events by day

### Step 3: Load All Entity Data

1. Read `data/entities/people.yaml` to get all people
2. Read `data/entities/teams.yaml` to get all teams
3. Build pattern matching lookup

### Step 4: Match Events to Entities

For each calendar event:

1. Match event title to entity `calendar_patterns`
2. Group matched events by entity
3. Count meetings per entity this week

### Step 5: For Each Entity with Meetings

For entities that had meetings this week:

#### 5a: Fetch Notion Updates

1. Fetch entity's Notion page
2. Parse meeting sections for this week's dates
3. Extract:
   - Topics discussed
   - Actions created
   - Actions completed (changed from `- [ ]` to `- [x]`)

#### 5b: Load Memory Changes

1. Check memory directory for this entity
2. Find entries from this week
3. Note new observations added

### Step 6: Identify Patterns and Themes

Analyze across all entities:

1. **Recurring topics**: Subjects mentioned in multiple meetings
2. **Cross-entity themes**: Issues affecting multiple people/teams
3. **Unresolved items**: Actions that keep appearing without resolution
4. **Sentiment patterns**: Positive/negative trends in observations

### Step 7: Compile Action Metrics

Calculate action item statistics:

1. **Actions created this week**: New `- [ ]` items
2. **Actions completed this week**: Items changed to `- [x]`
3. **Outstanding actions**: Open items from before this week
4. **Overdue actions**: Items open for more than 2 weeks

### Step 8: Generate Focus Recommendations

Based on analysis, suggest 3-5 focus areas for next week:

1. Prioritize overdue actions
2. Address recurring unresolved themes
3. Follow up on important observations
4. Consider relationship maintenance (people not met with recently)

### Step 9: Identify At-Risk Relationships

Flag entities that may need attention:

1. No meeting in 2+ weeks despite usually meeting weekly
2. Accumulating open actions
3. Negative trend in observations
4. Important topics flagged but not followed up

## Output Format

```markdown
## Weekly Review: {week_start} to {week_end}

### Meeting Summary

**Total meetings this week:** {count}
**Entities engaged:** {count}

| Entity | Meetings | Topics | New Actions | Completed |
|--------|----------|--------|-------------|-----------|
| {entity_name} | {count} | {topic_summary} | {new_count} | {done_count} |
| ... | ... | ... | ... | ... |

---

### Commitments Made

New actions created this week:

#### {entity_name}
- [ ] {action} ({date})
- [ ] {action} ({date})

#### {entity_name}
- [ ] {action} ({date})

**Total new commitments:** {count}

---

### Actions Completed

Items resolved this week:

#### {entity_name}
- [x] {action} (created {date}, completed {date})

**Total completed:** {count}

---

### Outstanding Actions

Open items requiring attention:

#### Overdue (2+ weeks)
- [ ] {action} - {entity_name} (from {date}) **OVERDUE**
- [ ] {action} - {entity_name} (from {date}) **OVERDUE**

#### This Week's Carryover
- [ ] {action} - {entity_name} (from {date})
- [ ] {action} - {entity_name} (from {date})

**Total outstanding:** {count}

---

### Patterns and Themes

**Recurring Topics:**
- {theme}: Mentioned in meetings with {entity_list}
- {theme}: Discussed {count} times this week

**Cross-Entity Issues:**
- {issue}: Affects {entity_1}, {entity_2}, {entity_3}

**Notable Observations:**
- {entity}: {observation_summary}

---

### Relationship Health

#### Needs Attention
| Entity | Last Meeting | Open Actions | Concern |
|--------|--------------|--------------|---------|
| {name} | {date} | {count} | No meeting in 3 weeks |
| {name} | {date} | {count} | 5 overdue actions |

#### Strong Engagement
- {entity}: {positive_note}
- {entity}: {positive_note}

---

### Focus Areas for Next Week

Based on this week's review, prioritize:

1. **{priority_1}**
   - Context: {why_important}
   - Action: {what_to_do}

2. **{priority_2}**
   - Context: {why_important}
   - Action: {what_to_do}

3. **{priority_3}**
   - Context: {why_important}
   - Action: {what_to_do}

4. **{priority_4}** (if applicable)
   - Context: {why_important}
   - Action: {what_to_do}

5. **{priority_5}** (if applicable)
   - Context: {why_important}
   - Action: {what_to_do}

---

**Review Confidence:** {score} ({level})
- Calendar events processed: {count}
- Notion pages fetched: {count}/{total}
- Memory entries reviewed: {count}
```

## Error Handling

| Error | Response |
|-------|----------|
| Calendar MCP unavailable | "Unable to fetch calendar for weekly review. Please check Google Calendar MCP connection." |
| No events this week | Show "No meetings this week" with focus on relationship maintenance |
| Notion fetch failed | Continue with available data, note incomplete review |
| No entities defined | "No entities configured. Add people and teams first using `pa entity add`" |

## Timing Recommendations

Best times to run `/weekly review`:

- **Friday afternoon**: Review week, set priorities for Monday
- **Monday morning**: Review last week before starting new week
- **Sunday evening**: Prepare for the week ahead

## Example

Input: `/weekly review`

Output:
```markdown
## Weekly Review: 2026-01-20 to 2026-01-27

### Meeting Summary

**Total meetings this week:** 12
**Entities engaged:** 6

| Entity | Meetings | Topics | New Actions | Completed |
|--------|----------|--------|-------------|-----------|
| John Doe | 1 | ML team, RFC | 2 | 1 |
| Platform Team | 3 | Sprint, blockers | 1 | 2 |
| Eng Group Leads | 2 | Hiring, OKRs | 3 | 0 |
| Sarah Chen | 1 | Onboarding | 1 | 0 |
| Data Team | 2 | Pipeline issues | 2 | 1 |
| Product Sync | 3 | Roadmap, priorities | 0 | 0 |

---

### Commitments Made

New actions created this week:

#### John Doe
- [ ] Follow up on ML team exploration (2026-01-20)
- [ ] Review his RFC draft (2026-01-20)

#### Eng Group Leads
- [ ] Review hiring pipeline (2026-01-20)
- [ ] Finalize Q1 OKRs (2026-01-22)
- [ ] Schedule team capacity planning (2026-01-22)

#### Platform Team
- [ ] Complete Q1 roadmap review (2026-01-22)

#### Data Team
- [ ] Investigate pipeline latency (2026-01-21)
- [ ] Review data quality metrics (2026-01-24)

**Total new commitments:** 9

---

### Actions Completed

Items resolved this week:

#### John Doe
- [x] Share project status update (created 2026-01-13, completed 2026-01-20)

#### Platform Team
- [x] Fix CI/CD pipeline (created 2026-01-15, completed 2026-01-22)
- [x] Update deployment docs (created 2026-01-17, completed 2026-01-23)

#### Data Team
- [x] Resolve ETL failures (created 2026-01-14, completed 2026-01-21)

**Total completed:** 4

---

### Outstanding Actions

Open items requiring attention:

#### Overdue (2+ weeks)
- [ ] Complete performance review for Sam - Sarah Chen (from 2026-01-06) **OVERDUE**
- [ ] Finalize team structure proposal - Eng Group Leads (from 2026-01-08) **OVERDUE**

#### This Week's Carryover
- [ ] Share RFC draft - John Doe (from 2026-01-13)
- [ ] Schedule design review - John Doe (from 2026-01-13)

**Total outstanding:** 13

---

### Patterns and Themes

**Recurring Topics:**
- Q1 Planning: Mentioned in meetings with Eng Group Leads, Platform Team, Product Sync
- Pipeline Issues: Discussed 4 times this week across Data Team and Platform Team

**Cross-Entity Issues:**
- Hiring capacity: Affects Eng Group Leads, Platform Team, Data Team
- OKR alignment: Discussed in multiple leadership contexts

**Notable Observations:**
- John Doe: Strong interest in ML team move - may need to discuss career path
- Data Team: Pipeline issues recurring - may need architectural review

---

### Relationship Health

#### Needs Attention
| Entity | Last Meeting | Open Actions | Concern |
|--------|--------------|--------------|---------|
| Alex Kim | 2026-01-06 | 2 | No meeting in 3 weeks |
| QA Lead | 2025-12-20 | 0 | No meeting in 5 weeks |

#### Strong Engagement
- Platform Team: Regular standups, good action completion rate
- John Doe: Productive 1:1, clear follow-ups identified

---

### Focus Areas for Next Week

Based on this week's review, prioritize:

1. **Address overdue performance review for Sam**
   - Context: Sarah Chen has had this open for 3 weeks
   - Action: Check in with Sarah on blockers, offer support

2. **Finalize team structure proposal**
   - Context: Blocking downstream planning decisions
   - Action: Schedule dedicated time at Eng Group Leads meeting

3. **Follow up on John's ML team interest**
   - Context: This has been mentioned twice, needs explicit discussion
   - Action: Discuss at next 1:1, explore timeline and options

4. **Reconnect with Alex Kim**
   - Context: No meeting in 3 weeks, unusual for weekly 1:1
   - Action: Reach out, schedule catch-up

5. **Review Data Team pipeline architecture**
   - Context: Recurring issues suggest systemic problem
   - Action: Propose architecture review session

---

**Review Confidence:** 0.82 (High)
- Calendar events processed: 12
- Notion pages fetched: 5/6
- Memory entries reviewed: 8
```
