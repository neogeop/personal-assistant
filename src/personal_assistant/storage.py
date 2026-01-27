"""Storage layer for reading and writing YAML files."""

from pathlib import Path

import yaml

from .schemas import CalendarNotionMapping, Config, Person, Team

# Data directory relative to project root
DATA_DIR = Path(__file__).parent.parent.parent / "data"


def ensure_data_dirs() -> None:
    """Ensure all data directories exist."""
    dirs = [
        DATA_DIR,
        DATA_DIR / "entities",
        DATA_DIR / "mappings",
        DATA_DIR / "memory" / "people",
        DATA_DIR / "memory" / "teams",
    ]
    for d in dirs:
        d.mkdir(parents=True, exist_ok=True)


def _load_yaml(path: Path) -> list | dict | None:
    """Load YAML file, return None if doesn't exist."""
    if not path.exists():
        return None
    with open(path) as f:
        return yaml.safe_load(f)


def _save_yaml(path: Path, data: list | dict) -> None:
    """Save data to YAML file."""
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w") as f:
        yaml.dump(data, f, default_flow_style=False, allow_unicode=True, sort_keys=False)


# --- Config ---


def load_config() -> Config:
    """Load global config."""
    path = DATA_DIR / "config.yaml"
    data = _load_yaml(path)
    if data is None:
        return Config()
    return Config.model_validate(data)


def save_config(config: Config) -> None:
    """Save global config."""
    path = DATA_DIR / "config.yaml"
    _save_yaml(path, config.model_dump(exclude_none=True))


# --- People ---


def load_people() -> list[Person]:
    """Load all people."""
    path = DATA_DIR / "entities" / "people.yaml"
    data = _load_yaml(path)
    if data is None:
        return []
    return [Person.model_validate(p) for p in data]


def save_people(people: list[Person]) -> None:
    """Save all people."""
    path = DATA_DIR / "entities" / "people.yaml"
    _save_yaml(path, [p.model_dump(exclude_none=True) for p in people])


def get_person(person_id: str) -> Person | None:
    """Get a person by ID."""
    for p in load_people():
        if p.id == person_id:
            return p
    return None


def add_person(person: Person) -> None:
    """Add a person. Raises ValueError if ID already exists."""
    people = load_people()
    if any(p.id == person.id for p in people):
        raise ValueError(f"Person with ID '{person.id}' already exists")
    people.append(person)
    save_people(people)


def update_person(person_id: str, updates: dict) -> Person:
    """Update a person. Returns updated person. Raises ValueError if not found."""
    people = load_people()
    for i, p in enumerate(people):
        if p.id == person_id:
            updated_data = p.model_dump()
            updated_data.update(updates)
            updated = Person.model_validate(updated_data)
            people[i] = updated
            save_people(people)
            return updated
    raise ValueError(f"Person with ID '{person_id}' not found")


def delete_person(person_id: str) -> None:
    """Delete a person. Raises ValueError if not found."""
    people = load_people()
    original_count = len(people)
    people = [p for p in people if p.id != person_id]
    if len(people) == original_count:
        raise ValueError(f"Person with ID '{person_id}' not found")
    save_people(people)


# --- Teams ---


def load_teams() -> list[Team]:
    """Load all teams."""
    path = DATA_DIR / "entities" / "teams.yaml"
    data = _load_yaml(path)
    if data is None:
        return []
    return [Team.model_validate(t) for t in data]


def save_teams(teams: list[Team]) -> None:
    """Save all teams."""
    path = DATA_DIR / "entities" / "teams.yaml"
    _save_yaml(path, [t.model_dump(exclude_none=True) for t in teams])


def get_team(team_id: str) -> Team | None:
    """Get a team by ID."""
    for t in load_teams():
        if t.id == team_id:
            return t
    return None


def add_team(team: Team) -> None:
    """Add a team. Raises ValueError if ID already exists."""
    teams = load_teams()
    if any(t.id == team.id for t in teams):
        raise ValueError(f"Team with ID '{team.id}' already exists")
    teams.append(team)
    save_teams(teams)


def update_team(team_id: str, updates: dict) -> Team:
    """Update a team. Returns updated team. Raises ValueError if not found."""
    teams = load_teams()
    for i, t in enumerate(teams):
        if t.id == team_id:
            updated_data = t.model_dump()
            updated_data.update(updates)
            updated = Team.model_validate(updated_data)
            teams[i] = updated
            save_teams(teams)
            return updated
    raise ValueError(f"Team with ID '{team_id}' not found")


def delete_team(team_id: str) -> None:
    """Delete a team. Raises ValueError if not found or has members."""
    # Check for members
    people = load_people()
    members = [p for p in people if p.team_id == team_id]
    if members:
        member_names = ", ".join(p.name for p in members)
        raise ValueError(f"Cannot delete team '{team_id}': has members ({member_names})")

    teams = load_teams()
    original_count = len(teams)
    teams = [t for t in teams if t.id != team_id]
    if len(teams) == original_count:
        raise ValueError(f"Team with ID '{team_id}' not found")
    save_teams(teams)


# --- Mappings ---


def load_mappings() -> list[CalendarNotionMapping]:
    """Load all calendar-notion mappings."""
    path = DATA_DIR / "mappings" / "calendar-notion.yaml"
    data = _load_yaml(path)
    if data is None:
        return []
    return [CalendarNotionMapping.model_validate(m) for m in data]


def save_mappings(mappings: list[CalendarNotionMapping]) -> None:
    """Save all mappings."""
    path = DATA_DIR / "mappings" / "calendar-notion.yaml"
    _save_yaml(path, [m.model_dump(exclude_none=True) for m in mappings])


def add_mapping(mapping: CalendarNotionMapping) -> None:
    """Add a mapping. Raises ValueError if ID already exists."""
    mappings = load_mappings()
    if any(m.id == mapping.id for m in mappings):
        raise ValueError(f"Mapping with ID '{mapping.id}' already exists")
    mappings.append(mapping)
    save_mappings(mappings)


def delete_mapping(mapping_id: str) -> None:
    """Delete a mapping. Raises ValueError if not found."""
    mappings = load_mappings()
    original_count = len(mappings)
    mappings = [m for m in mappings if m.id != mapping_id]
    if len(mappings) == original_count:
        raise ValueError(f"Mapping with ID '{mapping_id}' not found")
    save_mappings(mappings)


# --- Memory ---


def get_memory_dir(entity_type: str, entity_id: str) -> Path:
    """Get the memory directory for an entity."""
    # Use consistent pluralization: person -> people, team -> teams
    plural = "people" if entity_type == "person" else "teams"
    return DATA_DIR / "memory" / plural / entity_id


def save_memory_entry(
    entity_type: str,
    entity_id: str,
    content: str,
    entry_date: str,
    entry_type: str = "observation",
    source: str = "user",
    context: str | None = None,
) -> Path:
    """Save a memory entry as a markdown file. Returns the file path."""
    memory_dir = get_memory_dir(entity_type, entity_id)
    memory_dir.mkdir(parents=True, exist_ok=True)

    filename = f"{entry_date}_{entry_type}_{source}.md"
    filepath = memory_dir / filename

    # Check if file exists and append a number if needed
    counter = 1
    while filepath.exists():
        filename = f"{entry_date}_{entry_type}_{source}_{counter}.md"
        filepath = memory_dir / filename
        counter += 1

    # Format the markdown content
    entity_display = entity_id.replace("-", " ").title()
    md_content = f"# {entry_type.title()}: {entity_display}\n\n"
    if context:
        md_content += f"Context: {context}\n\n"
    md_content += "---\n\n"
    md_content += content

    with open(filepath, "w") as f:
        f.write(md_content)

    return filepath


def load_memory_entries(entity_type: str, entity_id: str) -> list[tuple[Path, str]]:
    """Load all memory entries for an entity. Returns list of (path, content)."""
    memory_dir = get_memory_dir(entity_type, entity_id)
    if not memory_dir.exists():
        return []

    entries = []
    for filepath in sorted(memory_dir.glob("*.md")):
        with open(filepath) as f:
            entries.append((filepath, f.read()))
    return entries


def search_memory(query: str) -> list[tuple[str, str, Path, str]]:
    """Search all memory entries for a query string.
    Returns list of (entity_type, entity_id, path, content)."""
    results = []
    memory_base = DATA_DIR / "memory"

    for entity_type_dir in ["people", "teams"]:
        type_dir = memory_base / entity_type_dir
        if not type_dir.exists():
            continue

        entity_type = entity_type_dir.rstrip("s")  # people -> person

        for entity_dir in type_dir.iterdir():
            if not entity_dir.is_dir():
                continue

            for filepath in entity_dir.glob("*.md"):
                with open(filepath) as f:
                    content = f.read()
                    if query.lower() in content.lower():
                        results.append((entity_type, entity_dir.name, filepath, content))

    return results
