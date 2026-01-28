# ADR 004: Remove Google Calendar Integration from Prepare-Meeting Skill

## Status

Accepted

## Context

The `/prepare-meeting` skill previously included a step to check Google Calendar for the next scheduled meeting with the entity. This involved:

1. Using `mcp__google__list-events` to fetch today's calendar events
2. Matching event titles against the entity's `calendar_patterns`
3. Displaying the next meeting time in the output
4. Adding +0.1 to confidence score when a calendar match was found

### Problems with Calendar Integration

1. **Redundant information**: Users already know when their meeting is scheduled - they're explicitly running the skill to prepare for it. Displaying "Next meeting: Today 10:00 AM" adds no value.

2. **Pattern matching fragility**: Calendar pattern matching often fails to find matches due to:
   - Slight variations in meeting titles
   - Recurring meetings with different naming
   - Meetings created by others with different naming conventions

3. **Additional failure point**: The MCP call to Google Calendar adds:
   - Extra latency to skill execution
   - Another external dependency that can fail
   - Complexity in error handling

4. **Low value-add**: The core value proposition of the prepare-meeting skill is:
   - Notion content (meeting history, action items)
   - Structured database tasks
   - Local memory observations

   The calendar check contributes minimally to this core value.

## Decision

Remove Google Calendar integration from the `/prepare-meeting` skill entirely:

1. **Delete Step 2** (Check Calendar for Next Meeting)
2. **Remove output line**: `**Next meeting:** {time} (from calendar) OR No upcoming meeting found`
3. **Remove confidence factor**: `if calendar_match_found: confidence += 0.1`
4. **Remove error handling row**: `Calendar MCP unavailable | Skip calendar check, note in output`
5. **Renumber steps**: Steps 3-8 become Steps 2-7

## Consequences

### Positive

- **Faster execution**: One fewer MCP call reduces latency
- **Simpler skill**: Fewer steps, less error handling, easier to understand
- **More reliable**: Removes a fragile pattern-matching step that often failed
- **Focused output**: Only shows information the user doesn't already know
- **Reduced dependencies**: No longer requires Google Calendar MCP to be available

### Negative

- **No calendar confirmation**: Users won't see verification that the meeting is scheduled (though they already know this)
- **Slightly lower max confidence**: Maximum possible confidence score reduced by 0.1

### Neutral

- **Other skills unaffected**: `/prepare-day` and `/weekly-review` still use Google Calendar for their different purposes (enumerating all meetings)
- **Calendar patterns still useful**: Entity `calendar_patterns` remain useful for other skills

## Implementation

Files modified:
- `data/skills/prepare-meeting.md` - Removed Step 2, renumbered steps, updated output format and confidence scoring
- `.claude/commands/prepare-meeting.md` - Mirror of above changes

Steps renumbered:
| Old | New | Description |
|-----|-----|-------------|
| 1 | 1 | Look Up Entity |
| 2 | (removed) | Check Calendar for Next Meeting |
| 3 | 2 | Fetch Notion Page |
| 3.5 | 2.5 | Extract Tasks from Inline Databases |
| 4 | 3 | Parse Meeting Sections |
| 5 | 4 | Extract Open Actions |
| 6 | 5 | Load Local Memory |
| 7 | 6 | Calculate Confidence Score |
| 8 | 7 | Generate Suggested Topics |

## Verification

1. Run `/prepare-meeting <entity-id>` for any entity
2. Verify no Google Calendar MCP calls are made
3. Confirm output no longer includes "Next meeting" line
4. Check that confidence calculation works correctly without calendar factor
