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


# --- Entity Commands ---


@entity_app.command("add")
def entity_add(
    entity_type: Annotated[str, typer.Argument(help="Entity type: 'person' or 'team'")],
    name: Annotated[str, typer.Option("--name", "-n", help="Name of the entity")],
    team: Annotated[Optional[str], typer.Option("--team", "-t", help="Team ID (for person)")] = None,
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
) -> None:
    """Add a new person or team."""
    storage.ensure_data_dirs()

    generated_id = entity_id or slugify(name)
    tag_list = [t.strip() for t in tags.split(",")] if tags else []
    pattern_list = [p.strip() for p in calendar_patterns.split(",")] if calendar_patterns else []

    try:
        if entity_type == "person":
            # Validate team reference
            if team and not storage.get_team(team):
                rprint(f"[red]Error:[/red] Team '{team}' does not exist. Create it first.")
                raise typer.Exit(1)

            person = Person(
                id=generated_id,
                name=name,
                role=role,
                team_id=team,
                tags=tag_list,
                calendar_patterns=pattern_list,
                notion_page=notion_page,
            )
            storage.add_person(person)
            rprint(f"[green]Added person:[/green] {person.id} ({person.name})")

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

        else:
            rprint(f"[red]Error:[/red] Unknown entity type '{entity_type}'. Use 'person' or 'team'.")
            raise typer.Exit(1)

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
            table.add_column("Team")
            table.add_column("Tags")

            for p in people:
                table.add_row(p.id, p.name, p.role or "", p.team_id or "", ", ".join(p.tags))
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
                member_count = len([p for p in people if p.team_id == t.id])
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
        if person.team_id:
            team = storage.get_team(person.team_id)
            team_name = team.name if team else person.team_id
            rprint(f"  [dim]Team:[/dim] {team_name} ({person.team_id})")
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
        members = [p for p in people if p.team_id == team.id]
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
    team: Annotated[Optional[str], typer.Option("--team", "-t", help="New team ID")] = None,
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
            if not storage.get_team(team):
                rprint(f"[red]Error:[/red] Team '{team}' does not exist.")
                raise typer.Exit(1)
            updates["team_id"] = team
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
