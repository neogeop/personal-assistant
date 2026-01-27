"""Personal Assistant CLI."""

from datetime import date
from pathlib import Path
from typing import Annotated, Optional

import typer
from pydantic import ValidationError
from rich import print as rprint
from rich.console import Console
from rich.table import Table

from . import storage
from .schemas import CalendarNotionMapping, Person, Team

app = typer.Typer(
    name="pa",
    help="Personal Assistant CLI - Manage entities, mappings, and memory.",
    no_args_is_help=True,
)

entity_app = typer.Typer(help="Manage people and teams.")
map_app = typer.Typer(help="Manage calendar-notion mappings.")
memory_app = typer.Typer(help="Manage memory and observations.")
config_app = typer.Typer(help="Manage configuration.")

app.add_typer(entity_app, name="entity")
app.add_typer(map_app, name="map")
app.add_typer(memory_app, name="memory")
app.add_typer(config_app, name="config")

console = Console()


def slugify(name: str) -> str:
    """Convert a name to a slug ID."""
    import re
    # Convert to lowercase, replace spaces/underscores with hyphens
    slug = name.lower().replace(" ", "-").replace("_", "-")
    # Remove any characters that aren't alphanumeric or hyphens
    slug = re.sub(r"[^a-z0-9-]", "", slug)
    # Remove consecutive hyphens
    slug = re.sub(r"-+", "-", slug)
    # Remove leading/trailing hyphens
    slug = slug.strip("-")
    return slug


def _interactive_prompt(
    prompt_text: str,
    default: str = "",
    required: bool = False,
) -> str | None:
    """Prompt for input with skip support.

    Returns None if user skips (enters empty string) and not required.
    For required fields, re-prompts until a value is provided.
    """
    while True:
        if default:
            display_prompt = f"{prompt_text} [{default}]"
        elif required:
            display_prompt = prompt_text
        else:
            display_prompt = f"{prompt_text} (skip with Enter)"

        value = typer.prompt(display_prompt, default=default or "", show_default=False)

        if not value and required:
            rprint("[yellow]This field is required.[/yellow]")
            continue

        return value if value else None


def _parse_teams(team_input: list[str] | None) -> list[str]:
    """Parse team input, handling both multiple flags and comma-separated."""
    if not team_input:
        return []
    teams = []
    for item in team_input:
        teams.extend(t.strip() for t in item.split(",") if t.strip())
    return teams


def _auto_create_mappings(
    patterns: list[str],
    entity_id: str,
    entity_type: str,
    notion_page: str | None,
) -> None:
    """Auto-create calendar-notion mappings for entity patterns.

    Creates a mapping for each calendar pattern provided during entity creation.
    Silently skips patterns that would create duplicate mapping IDs.
    """
    mappings_created = 0
    for pattern in patterns:
        if not pattern:  # Skip empty patterns
            continue
        mapping_id = slugify(pattern)
        if not mapping_id:  # Skip if slugify produces empty string
            continue
        try:
            mapping = CalendarNotionMapping(
                id=mapping_id,
                calendar_pattern=pattern,
                entity_id=entity_id,
                entity_type=entity_type,
                notion_page=notion_page,
            )
            storage.add_mapping(mapping)
            mappings_created += 1
        except ValueError:
            # Mapping with this ID already exists, skip silently
            pass

    if mappings_created > 0:
        rprint(f"[dim]Auto-created {mappings_created} calendar mapping(s)[/dim]")


# --- Entity Commands ---


@entity_app.command("add")
def entity_add(
    entity_type: Annotated[str, typer.Argument(help="Entity type: 'person' or 'team'")],
    name: Annotated[Optional[str], typer.Option("--name", "-n", help="Name of the entity")] = None,
    team: Annotated[Optional[list[str]], typer.Option("--team", "-t", help="Team ID(s) - can be repeated or comma-separated")] = None,
    role: Annotated[Optional[str], typer.Option("--role", "-r", help="Role/title (for person)")] = None,
    entity_type_field: Annotated[
        Optional[str], typer.Option("--type", help="Team type (for team)")
    ] = None,
    tags: Annotated[Optional[str], typer.Option("--tags", help="Comma-separated tags")] = None,
    calendar_patterns: Annotated[
        Optional[str], typer.Option("--calendar-patterns", help="Comma-separated calendar patterns")
    ] = None,
    notion_page: Annotated[Optional[str], typer.Option("--notion", help="Notion page URL or ID")] = None,
    entity_id: Annotated[Optional[str], typer.Option("--id", help="Custom ID (default: derived from name)")] = None,
    interactive: Annotated[bool, typer.Option("--interactive", "-i", help="Interactive mode - prompts for each field")] = False,
) -> None:
    """Add a new person or team."""
    storage.ensure_data_dirs()

    # Validate entity type first
    if entity_type not in ("person", "team"):
        rprint(f"[red]Error:[/red] Unknown entity type '{entity_type}'. Use 'person' or 'team'.")
        raise typer.Exit(1)

    # Interactive mode: prompt for missing fields
    if interactive:
        rprint(f"\nEntity type: {entity_type}\n")

        # Name is required - prompt if not provided
        if name is None:
            name = _interactive_prompt("Name", required=True)

        # ID defaults to slugified name
        if entity_id is None:
            suggested_id = slugify(name)
            entity_id = _interactive_prompt("ID", default=suggested_id) or suggested_id

        if entity_type == "person":
            # Person-specific fields
            if role is None:
                role = _interactive_prompt("Role")

            if team is None:
                team_input = _interactive_prompt("Team ID(s) (comma-separated)")
                if team_input:
                    team = [team_input]  # Will be parsed by _parse_teams
                else:
                    team = None
                # Validate teams if provided
                team_list = _parse_teams(team)
                for t_id in team_list:
                    if not storage.get_team(t_id):
                        rprint(f"[red]Error:[/red] Team '{t_id}' does not exist. Create it first.")
                        raise typer.Exit(1)

            if tags is None:
                tags_input = _interactive_prompt("Tags (comma-separated)")
                tags = tags_input if tags_input else None

            if calendar_patterns is None:
                patterns_input = _interactive_prompt("Calendar patterns (comma-separated)")
                calendar_patterns = patterns_input if patterns_input else None

            if notion_page is None:
                notion_page = _interactive_prompt("Notion page")

        else:  # team
            # Team-specific fields
            if entity_type_field is None:
                entity_type_field = _interactive_prompt("Team type")

            if calendar_patterns is None:
                patterns_input = _interactive_prompt("Calendar patterns (comma-separated)")
                calendar_patterns = patterns_input if patterns_input else None

            if notion_page is None:
                notion_page = _interactive_prompt("Notion page")

        rprint()  # Blank line before output

    # Non-interactive mode requires name
    if name is None:
        rprint("[red]Error:[/red] --name is required (or use --interactive mode).")
        raise typer.Exit(1)

    generated_id = entity_id or slugify(name)
    tag_list = [t.strip() for t in tags.split(",")] if tags else []
    pattern_list = [p.strip() for p in calendar_patterns.split(",")] if calendar_patterns else []

    try:
        if entity_type == "person":
            # Parse and validate team references
            team_list = _parse_teams(team)
            for t_id in team_list:
                if not storage.get_team(t_id):
                    rprint(f"[red]Error:[/red] Team '{t_id}' does not exist. Create it first.")
                    raise typer.Exit(1)

            person = Person(
                id=generated_id,
                name=name,
                role=role,
                team_ids=team_list,
                tags=tag_list,
                calendar_patterns=pattern_list,
                notion_page=notion_page,
            )
            storage.add_person(person)
            rprint(f"[green]Added person:[/green] {person.id} ({person.name})")

            # Auto-seed mappings for calendar patterns
            if pattern_list:
                _auto_create_mappings(pattern_list, person.id, "person", notion_page)

        elif entity_type == "team":
            team_entity = Team(
                id=generated_id,
                name=name,
                team_type=entity_type_field,
                calendar_patterns=pattern_list,
                notion_page=notion_page,
            )
            storage.add_team(team_entity)
            rprint(f"[green]Added team:[/green] {team_entity.id} ({team_entity.name})")

            # Auto-seed mappings for calendar patterns
            if pattern_list:
                _auto_create_mappings(pattern_list, team_entity.id, "team", notion_page)

    except ValidationError as e:
        rprint(f"[red]Validation error:[/red] {e}")
        raise typer.Exit(1)
    except ValueError as e:
        rprint(f"[red]Error:[/red] {e}")
        raise typer.Exit(1)


@entity_app.command("list")
def entity_list(
    entity_type: Annotated[
        Optional[str], typer.Argument(help="Entity type: 'people' or 'teams' (default: both)")
    ] = None,
) -> None:
    """List all entities."""
    storage.ensure_data_dirs()

    if entity_type is None or entity_type == "people":
        people = storage.load_people()
        if people:
            table = Table(title="People")
            table.add_column("ID", style="cyan")
            table.add_column("Name")
            table.add_column("Role")
            table.add_column("Teams")
            table.add_column("Tags")

            for p in people:
                table.add_row(p.id, p.name, p.role or "", ", ".join(p.team_ids), ", ".join(p.tags))
            console.print(table)
        else:
            rprint("[dim]No people found.[/dim]")

    if entity_type is None or entity_type == "teams":
        teams = storage.load_teams()
        if teams:
            table = Table(title="Teams")
            table.add_column("ID", style="cyan")
            table.add_column("Name")
            table.add_column("Type")
            table.add_column("Members")

            people = storage.load_people()
            for t in teams:
                member_count = len([p for p in people if t.id in p.team_ids])
                table.add_row(t.id, t.name, t.team_type or "", str(member_count))
            console.print(table)
        else:
            rprint("[dim]No teams found.[/dim]")


@entity_app.command("show")
def entity_show(
    entity_id: Annotated[str, typer.Argument(help="Entity ID to show")],
) -> None:
    """Show details of a specific entity."""
    storage.ensure_data_dirs()

    # Try person first
    person = storage.get_person(entity_id)
    if person:
        rprint(f"[bold]Person:[/bold] {person.name}")
        rprint(f"  [dim]ID:[/dim] {person.id}")
        if person.role:
            rprint(f"  [dim]Role:[/dim] {person.role}")
        if person.team_ids:
            team_displays = []
            for t_id in person.team_ids:
                team = storage.get_team(t_id)
                team_name = team.name if team else t_id
                team_displays.append(f"{team_name} ({t_id})")
            rprint(f"  [dim]Teams:[/dim] {', '.join(team_displays)}")
        if person.tags:
            rprint(f"  [dim]Tags:[/dim] {', '.join(person.tags)}")
        if person.calendar_patterns:
            rprint(f"  [dim]Calendar patterns:[/dim] {', '.join(person.calendar_patterns)}")
        if person.notion_page:
            rprint(f"  [dim]Notion:[/dim] {person.notion_page}")

        # Show memory entries
        entries = storage.load_memory_entries("person", entity_id)
        if entries:
            rprint(f"\n[bold]Memory entries:[/bold] ({len(entries)})")
            for path, _ in entries:
                rprint(f"  - {path.name}")
        return

    # Try team
    team = storage.get_team(entity_id)
    if team:
        rprint(f"[bold]Team:[/bold] {team.name}")
        rprint(f"  [dim]ID:[/dim] {team.id}")
        if team.team_type:
            rprint(f"  [dim]Type:[/dim] {team.team_type}")
        if team.calendar_patterns:
            rprint(f"  [dim]Calendar patterns:[/dim] {', '.join(team.calendar_patterns)}")
        if team.notion_page:
            rprint(f"  [dim]Notion:[/dim] {team.notion_page}")

        # Show members
        people = storage.load_people()
        members = [p for p in people if team.id in p.team_ids]
        if members:
            rprint(f"\n[bold]Members:[/bold] ({len(members)})")
            for p in members:
                rprint(f"  - {p.name} ({p.id})")

        # Show memory entries
        entries = storage.load_memory_entries("team", entity_id)
        if entries:
            rprint(f"\n[bold]Memory entries:[/bold] ({len(entries)})")
            for path, _ in entries:
                rprint(f"  - {path.name}")
        return

    rprint(f"[red]Error:[/red] Entity '{entity_id}' not found.")
    raise typer.Exit(1)


@entity_app.command("update")
def entity_update(
    entity_id: Annotated[str, typer.Argument(help="Entity ID to update")],
    name: Annotated[Optional[str], typer.Option("--name", "-n", help="New name")] = None,
    team: Annotated[Optional[list[str]], typer.Option("--team", "-t", help="Replace all teams (can be repeated or comma-separated)")] = None,
    add_team: Annotated[Optional[list[str]], typer.Option("--add-team", help="Add team(s) (can be repeated or comma-separated)")] = None,
    remove_team: Annotated[Optional[list[str]], typer.Option("--remove-team", help="Remove team(s) (can be repeated or comma-separated)")] = None,
    role: Annotated[Optional[str], typer.Option("--role", "-r", help="New role")] = None,
    entity_type_field: Annotated[Optional[str], typer.Option("--type", help="New team type")] = None,
    tags: Annotated[Optional[str], typer.Option("--tags", help="New comma-separated tags (replaces existing)")] = None,
    add_tag: Annotated[Optional[str], typer.Option("--add-tag", help="Add a tag")] = None,
    remove_tag: Annotated[Optional[str], typer.Option("--remove-tag", help="Remove a tag")] = None,
    notion_page: Annotated[Optional[str], typer.Option("--notion", help="New Notion page")] = None,
) -> None:
    """Update an entity."""
    storage.ensure_data_dirs()

    # Try person first
    person = storage.get_person(entity_id)
    if person:
        updates = {}
        if name:
            updates["name"] = name
        if team:
            # Replace all teams
            team_list = _parse_teams(team)
            for t_id in team_list:
                if not storage.get_team(t_id):
                    rprint(f"[red]Error:[/red] Team '{t_id}' does not exist.")
                    raise typer.Exit(1)
            updates["team_ids"] = team_list
        if add_team:
            # Add teams to existing list
            teams_to_add = _parse_teams(add_team)
            for t_id in teams_to_add:
                if not storage.get_team(t_id):
                    rprint(f"[red]Error:[/red] Team '{t_id}' does not exist.")
                    raise typer.Exit(1)
            current_teams = list(person.team_ids)
            for t_id in teams_to_add:
                if t_id not in current_teams:
                    current_teams.append(t_id)
            updates["team_ids"] = current_teams
        if remove_team:
            # Remove teams from existing list
            teams_to_remove = _parse_teams(remove_team)
            current_teams = list(person.team_ids)
            for t_id in teams_to_remove:
                if t_id in current_teams:
                    current_teams.remove(t_id)
            updates["team_ids"] = current_teams
        if role:
            updates["role"] = role
        if notion_page:
            updates["notion_page"] = notion_page
        if tags:
            updates["tags"] = [t.strip() for t in tags.split(",")]
        if add_tag:
            current_tags = list(person.tags)
            if add_tag not in current_tags:
                current_tags.append(add_tag)
            updates["tags"] = current_tags
        if remove_tag:
            current_tags = list(person.tags)
            if remove_tag in current_tags:
                current_tags.remove(remove_tag)
            updates["tags"] = current_tags

        if not updates:
            rprint("[yellow]No updates specified.[/yellow]")
            return

        try:
            updated = storage.update_person(entity_id, updates)
            rprint(f"[green]Updated person:[/green] {updated.id}")
        except ValueError as e:
            rprint(f"[red]Error:[/red] {e}")
            raise typer.Exit(1)
        return

    # Try team
    team_entity = storage.get_team(entity_id)
    if team_entity:
        updates = {}
        if name:
            updates["name"] = name
        if entity_type_field:
            updates["team_type"] = entity_type_field
        if notion_page:
            updates["notion_page"] = notion_page

        if not updates:
            rprint("[yellow]No updates specified.[/yellow]")
            return

        try:
            updated = storage.update_team(entity_id, updates)
            rprint(f"[green]Updated team:[/green] {updated.id}")
        except ValueError as e:
            rprint(f"[red]Error:[/red] {e}")
            raise typer.Exit(1)
        return

    rprint(f"[red]Error:[/red] Entity '{entity_id}' not found.")
    raise typer.Exit(1)


@entity_app.command("delete")
def entity_delete(
    entity_id: Annotated[str, typer.Argument(help="Entity ID to delete")],
    force: Annotated[bool, typer.Option("--force", "-f", help="Skip confirmation")] = False,
) -> None:
    """Delete an entity."""
    storage.ensure_data_dirs()

    # Try person first
    person = storage.get_person(entity_id)
    if person:
        if not force:
            confirm = typer.confirm(f"Delete person '{person.name}' ({person.id})?")
            if not confirm:
                rprint("[dim]Cancelled.[/dim]")
                return

        try:
            storage.delete_person(entity_id)
            rprint(f"[green]Deleted person:[/green] {entity_id}")
        except ValueError as e:
            rprint(f"[red]Error:[/red] {e}")
            raise typer.Exit(1)
        return

    # Try team
    team = storage.get_team(entity_id)
    if team:
        if not force:
            confirm = typer.confirm(f"Delete team '{team.name}' ({team.id})?")
            if not confirm:
                rprint("[dim]Cancelled.[/dim]")
                return

        try:
            storage.delete_team(entity_id)
            rprint(f"[green]Deleted team:[/green] {entity_id}")
        except ValueError as e:
            rprint(f"[red]Error:[/red] {e}")
            raise typer.Exit(1)
        return

    rprint(f"[red]Error:[/red] Entity '{entity_id}' not found.")
    raise typer.Exit(1)


# --- Map Commands ---


@map_app.command("add")
def map_add(
    calendar_pattern: Annotated[str, typer.Option("--calendar-pattern", "-c", help="Calendar event pattern")],
    entity: Annotated[str, typer.Option("--entity", "-e", help="Entity ID (person or team)")],
    notion: Annotated[Optional[str], typer.Option("--notion", "-n", help="Notion page URL or ID")] = None,
    mapping_id: Annotated[Optional[str], typer.Option("--id", help="Custom mapping ID")] = None,
) -> None:
    """Add a calendar-notion mapping."""
    storage.ensure_data_dirs()

    # Determine entity type
    person = storage.get_person(entity)
    team = storage.get_team(entity)

    if not person and not team:
        rprint(f"[red]Error:[/red] Entity '{entity}' not found.")
        raise typer.Exit(1)

    entity_type = "person" if person else "team"
    generated_id = mapping_id or slugify(calendar_pattern)

    try:
        mapping = CalendarNotionMapping(
            id=generated_id,
            calendar_pattern=calendar_pattern,
            entity_id=entity,
            entity_type=entity_type,
            notion_page=notion,
        )
        storage.add_mapping(mapping)
        rprint(f"[green]Added mapping:[/green] {mapping.id}")
        rprint(f"  Pattern: '{calendar_pattern}' -> {entity_type} '{entity}'")
    except ValidationError as e:
        rprint(f"[red]Validation error:[/red] {e}")
        raise typer.Exit(1)
    except ValueError as e:
        rprint(f"[red]Error:[/red] {e}")
        raise typer.Exit(1)


@map_app.command("list")
def map_list() -> None:
    """List all calendar-notion mappings."""
    storage.ensure_data_dirs()

    mappings = storage.load_mappings()
    if not mappings:
        rprint("[dim]No mappings found.[/dim]")
        return

    table = Table(title="Calendar-Notion Mappings")
    table.add_column("ID", style="cyan")
    table.add_column("Calendar Pattern")
    table.add_column("Entity Type")
    table.add_column("Entity ID")
    table.add_column("Notion Page")

    for m in mappings:
        table.add_row(m.id, m.calendar_pattern, m.entity_type, m.entity_id, m.notion_page or "")
    console.print(table)


@map_app.command("delete")
def map_delete(
    mapping_id: Annotated[str, typer.Argument(help="Mapping ID to delete")],
    force: Annotated[bool, typer.Option("--force", "-f", help="Skip confirmation")] = False,
) -> None:
    """Delete a mapping."""
    storage.ensure_data_dirs()

    mappings = storage.load_mappings()
    mapping = next((m for m in mappings if m.id == mapping_id), None)

    if not mapping:
        rprint(f"[red]Error:[/red] Mapping '{mapping_id}' not found.")
        raise typer.Exit(1)

    if not force:
        confirm = typer.confirm(f"Delete mapping '{mapping_id}'?")
        if not confirm:
            rprint("[dim]Cancelled.[/dim]")
            return

    try:
        storage.delete_mapping(mapping_id)
        rprint(f"[green]Deleted mapping:[/green] {mapping_id}")
    except ValueError as e:
        rprint(f"[red]Error:[/red] {e}")
        raise typer.Exit(1)


# --- Memory Commands ---


@app.command("remember")
def remember(
    entity_id: Annotated[str, typer.Argument(help="Entity ID to attach memory to")],
    text: Annotated[Optional[str], typer.Argument(help="Memory/observation text")] = None,
    context: Annotated[Optional[str], typer.Option("--context", "-c", help="Context (e.g., meeting reference)")] = None,
    entry_type: Annotated[str, typer.Option("--type", "-t", help="Entry type: observation, note, inference")] = "observation",
    file: Annotated[Optional[Path], typer.Option("--file", "-f", help="Path to markdown file containing memory content")] = None,
) -> None:
    """Add a memory/observation about an entity.

    Provide memory content either as a text argument or via --file option.
    When using --file, the markdown file content is used as the memory text.
    """
    storage.ensure_data_dirs()

    # Validate input: either text or file must be provided, but not both
    if text is None and file is None:
        rprint("[red]Error:[/red] Either provide text argument or --file option.")
        raise typer.Exit(1)

    if text is not None and file is not None:
        rprint("[red]Error:[/red] Cannot provide both text argument and --file option.")
        raise typer.Exit(1)

    # Read content from file if provided
    if file is not None:
        if not file.exists():
            rprint(f"[red]Error:[/red] File not found: {file}")
            raise typer.Exit(1)
        if not file.is_file():
            rprint(f"[red]Error:[/red] Not a file: {file}")
            raise typer.Exit(1)
        content = file.read_text()
    else:
        content = text

    # Determine entity type
    person = storage.get_person(entity_id)
    team = storage.get_team(entity_id)

    if not person and not team:
        rprint(f"[red]Error:[/red] Entity '{entity_id}' not found.")
        raise typer.Exit(1)

    entity_type = "person" if person else "team"
    entity_name = person.name if person else team.name

    today = date.today().isoformat()

    filepath = storage.save_memory_entry(
        entity_type=entity_type,
        entity_id=entity_id,
        content=content,
        entry_date=today,
        entry_type=entry_type,
        source="user",
        context=context,
    )

    rprint(f"[green]Saved memory for {entity_name}:[/green]")
    rprint(f"  {filepath.name}")


@memory_app.command("show")
def memory_show(
    entity_id: Annotated[str, typer.Argument(help="Entity ID to show memory for")],
) -> None:
    """Show all memory entries for an entity."""
    storage.ensure_data_dirs()

    # Determine entity type
    person = storage.get_person(entity_id)
    team = storage.get_team(entity_id)

    if not person and not team:
        rprint(f"[red]Error:[/red] Entity '{entity_id}' not found.")
        raise typer.Exit(1)

    entity_type = "person" if person else "team"
    entity_name = person.name if person else team.name

    entries = storage.load_memory_entries(entity_type, entity_id)

    if not entries:
        rprint(f"[dim]No memory entries for {entity_name}.[/dim]")
        return

    rprint(f"[bold]Memory for {entity_name}:[/bold]\n")
    for path, content in entries:
        rprint(f"[cyan]--- {path.name} ---[/cyan]")
        rprint(content)
        rprint()


@memory_app.command("search")
def memory_search(
    query: Annotated[str, typer.Argument(help="Search query")],
) -> None:
    """Search memory entries across all entities."""
    storage.ensure_data_dirs()

    results = storage.search_memory(query)

    if not results:
        rprint(f"[dim]No results for '{query}'.[/dim]")
        return

    rprint(f"[bold]Found {len(results)} result(s) for '{query}':[/bold]\n")
    for entity_type, entity_id, path, content in results:
        rprint(f"[cyan]{entity_type}/{entity_id}: {path.name}[/cyan]")
        # Show a snippet around the match
        lines = content.split("\n")
        for i, line in enumerate(lines):
            if query.lower() in line.lower():
                start = max(0, i - 1)
                end = min(len(lines), i + 2)
                for j in range(start, end):
                    prefix = ">" if j == i else " "
                    rprint(f"  {prefix} {lines[j]}")
                break
        rprint()


# --- Config Commands ---


@config_app.command("set")
def config_set(
    key: Annotated[str, typer.Argument(help="Config key")],
    value: Annotated[str, typer.Argument(help="Config value")],
) -> None:
    """Set a configuration value."""
    storage.ensure_data_dirs()

    config = storage.load_config()
    valid_keys = ["default_team", "notion_workspace"]

    if key not in valid_keys:
        rprint(f"[red]Error:[/red] Unknown config key '{key}'.")
        rprint(f"Valid keys: {', '.join(valid_keys)}")
        raise typer.Exit(1)

    setattr(config, key, value)
    storage.save_config(config)
    rprint(f"[green]Set {key}:[/green] {value}")


@config_app.command("show")
def config_show() -> None:
    """Show current configuration."""
    storage.ensure_data_dirs()

    config = storage.load_config()

    rprint("[bold]Configuration:[/bold]")
    rprint(f"  [dim]default_team:[/dim] {config.default_team or '(not set)'}")
    rprint(f"  [dim]notion_workspace:[/dim] {config.notion_workspace or '(not set)'}")


if __name__ == "__main__":
    app()
